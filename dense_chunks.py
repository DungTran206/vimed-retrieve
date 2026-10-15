"""BGE-M3 trên CHUNK (cùng offset với bảng chunk của store), rồi xếp hạng lại ứng viên theo chunk khớp câu hỏi nhất.

Điểm của doc = max độ tương đồng các chunk của nó (nguồn đầu tiên đọc TOÀN thân bài, không chỉ 600 ký tự đầu);
kèm `best_idx` = chunk khớp nhất, để chọn chunk nộp bài theo nội dung thay vì chunk đầu.
    --encode : offsets (doc_id, idx, start, end) + bodies (vi_full.sqlite) -> {out}.npy (fp16) + {out}.ids.json
    --rank   : với mỗi câu, chỉ chấm các chunk của doc trong --cands (top --topn); ghi {id, candidates:[{doc_id, score, best_idx}]}
"""
import argparse
import json
import sqlite3
import sys
import time

import numpy as np

MODEL = "BAAI/bge-m3"


def load(a, max_len):
    """BGE-M3 (fp16) hoặc Qwen3-Embedding (fp16, padding_side=left), tuỳ --model; --mem-fraction cho máy dùng chung."""
    from sentence_transformers import SentenceTransformer
    import torch
    if a.mem_fraction:
        torch.cuda.set_per_process_memory_fraction(a.mem_fraction)
    q3 = "qwen3" in a.model.lower()
    kw = {"model_kwargs": {"torch_dtype": torch.float16}, "tokenizer_kwargs": {"padding_side": "left"}} if q3 else {}
    m = SentenceTransformer(a.model, device="cuda", **kw)
    m.max_seq_length = max_len
    if not q3:
        m.half()
    return m


def encode(a):
    model = load(a, a.max_len)
    off = sqlite3.connect(f"file:{a.offsets}?mode=ro", uri=True)
    bod = sqlite3.connect(f"file:{a.bodies}?mode=ro", uri=True)
    rows = off.execute("SELECT doc_id, idx, start, end FROM off ORDER BY doc_id, idx").fetchall()
    if a.docs_file:                                  # chỉ embed chunk của doc trong danh sách (pilot nhỏ)
        keep = {str(d) for d in json.load(open(a.docs_file))}
        rows = [r for r in rows if str(r[0]) in keep]
    print(f"{len(rows):,} chunk cần embed", flush=True)
    ids, blocks, t0, done = [], [], time.time(), 0
    for s in range(0, len(rows), 20000):
        part = rows[s:s + 20000]
        docs = sorted({r[0] for r in part})
        body = {}
        for i in range(0, len(docs), 900):
            sub = docs[i:i + 900]
            for d, b in bod.execute(f"SELECT doc_id, body FROM doc WHERE doc_id IN ({','.join('?' * len(sub))})", sub):
                body[str(d)] = b or ""
        texts = [body.get(str(d), "")[st:en] for d, _, st, en in part]
        order = sorted(range(len(texts)), key=lambda i: len(texts[i]))       # theo độ dài để ít đệm
        emb = model.encode([texts[i] for i in order], batch_size=a.batch, normalize_embeddings=True,
                           convert_to_numpy=True, show_progress_bar=False)
        out = np.zeros_like(emb)
        out[order] = emb
        blocks.append(out.astype(np.float16))
        ids.extend([str(d), int(i)] for d, i, _, _ in part)
        done += len(part)
        print(f"  {done:,}/{len(rows):,} | {time.time() - t0:.0f}s", flush=True)
    np.save(a.out + ".npy", np.concatenate(blocks))
    json.dump(ids, open(a.out + ".ids.json", "w"))
    print("-> " + a.out)


def rank(a):
    model = load(a, 512)
    E = np.load(a.out + ".npy")
    ids = json.load(open(a.out + ".ids.json"))
    span = {}
    for r, (d, i) in enumerate(ids):
        lo, _ = span.get(d, (r, r))
        span[d] = (lo, r + 1)
    qs = {json.loads(l)["id"]: json.loads(l)["query"] for l in open(a.queries, encoding="utf-8")}
    cands = {json.loads(l)["id"]: [str(c["doc_id"]) for c in json.loads(l)["candidates"]][:a.topn]
             for l in open(a.cands, encoding="utf-8")}
    qids = sorted(cands)
    if a.qids_file:
        keep = set(json.load(open(a.qids_file)))
        qids = [q for q in qids if q in keep]
    kw = {"prompt": a.query_instruct} if a.query_instruct else {}      # Qwen3-Embedding: chỉ dẫn CHỈ ở câu hỏi
    Q = model.encode([qs[q] for q in qids], batch_size=32, normalize_embeddings=True, convert_to_numpy=True, **kw)
    miss = 0
    with open(a.rank_out, "w", encoding="utf-8") as o:
        for k, q in enumerate(qids):
            res = []
            for d in cands[q]:
                if d not in span:
                    miss += 1; continue
                lo, hi = span[d]
                sims = E[lo:hi].astype(np.float32) @ Q[k]
                j = int(np.argmax(sims))
                res.append((d, float(sims[j]), ids[lo + j][1]))
            res.sort(key=lambda x: -x[1])
            o.write(json.dumps({"id": q, "candidates": [{"doc_id": d, "score": round(s, 6), "best_idx": b}
                                                        for d, s, b in res]}, ensure_ascii=False) + "\n")
    print(f"-> {a.rank_out} | ứng viên không có vector chunk: {miss}")


def rank_full(a):
    """Tìm chunk gần câu hỏi nhất trên TOÀN BỘ vector (nhiều phần), gộp theo doc (max), ghi top-N doc kèm best_idx."""
    from sentence_transformers import SentenceTransformer
    import torch
    parts = a.parts.split(",")
    E = torch.cat([torch.from_numpy(np.load(p + ".npy")) for p in parts]).cuda()
    ids = []
    for p in parts:
        ids.extend(json.load(open(p + ".ids.json")))
    print(f"{len(ids):,} chunk, {E.shape}", flush=True)
    model = SentenceTransformer(MODEL, device="cuda")
    model.max_seq_length = 512
    model.half()
    qs = [json.loads(l) for l in open(a.queries, encoding="utf-8") if l.strip()]
    Q = model.encode([q["query"] for q in qs], batch_size=32, normalize_embeddings=True, convert_to_numpy=True)
    Qt = torch.from_numpy(Q).half().cuda()
    with open(a.rank_out, "w", encoding="utf-8") as o:
        for s in range(0, len(qs), 16):
            S = Qt[s:s + 16] @ E.T                                   # (16, n_chunk)
            top = S.topk(a.topchunks, dim=1)
            for r in range(S.shape[0]):
                best = {}
                for sc, ix in zip(top.values[r].float().tolist(), top.indices[r].tolist()):
                    d, i = ids[ix]
                    if d not in best:
                        best[d] = (sc, i)
                res = sorted(best.items(), key=lambda x: -x[1][0])[:a.topn]
                o.write(json.dumps({"id": qs[s + r]["id"], "candidates": [
                    {"doc_id": d, "score": round(v[0], 6), "best_idx": v[1]} for d, v in res]}, ensure_ascii=False) + "\n")
    print("->", a.rank_out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--encode", action="store_true")
    ap.add_argument("--rank", action="store_true")
    ap.add_argument("--rank-full", action="store_true")
    ap.add_argument("--parts", default="data/emb_chunk_pilot,data/emb_chunk_s0,data/emb_chunk_s1")
    ap.add_argument("--topchunks", type=int, default=1500)
    ap.add_argument("--offsets", default="data/chunk_offsets.sqlite")
    ap.add_argument("--bodies", default="data/vi_full.sqlite")
    ap.add_argument("--out", default="data/emb_chunk")
    ap.add_argument("--queries", default="data/queries.jsonl")
    ap.add_argument("--cands", default="data/f_H.jsonl")
    ap.add_argument("--topn", type=int, default=400)
    ap.add_argument("--rank-out", default="data/dense_chunk_rank.jsonl")
    ap.add_argument("--max-len", type=int, default=1024)
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--mem-fraction", type=float, default=0)
    ap.add_argument("--docs-file", default="")
    ap.add_argument("--qids-file", default="")
    ap.add_argument("--query-instruct", default="")
    ap.add_argument("--batch", type=int, default=32)
    a = ap.parse_args()
    if a.encode:
        encode(a)
    if a.rank:
        rank(a)
    if a.rank_full:
        rank_full(a)


if __name__ == "__main__":
    sys.exit(main())
