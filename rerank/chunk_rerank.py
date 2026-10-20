"""Chọn chunk bằng Qwen3-Reranker: chấm MỌI chunk của doc top-N có ≥3 chunk (doc ≤2 chunk đã lấy đủ, không có gì để chọn).

    python chunk_rerank.py --prep   # local: đọc store, ghi data/chunk_cands.jsonl
    python chunk_rerank.py --score  # máy GPU: chấm, ghi data/chunk_scores.jsonl (chạy tiếp được)
Dùng ở submission.py --chunk-scores data/chunk_scores.jsonl. chunk_text vẫn là lát nguyên văn body[start:end].
"""
import argparse
import json
import os
import sqlite3
import sys

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def prep(a):
    qs = {json.loads(l)["id"]: json.loads(l)["query"] for l in open(a.queries, encoding="utf-8") if l.strip()}
    conn = sqlite3.connect(f"file:{a.store}?mode=ro", uri=True)
    n = 0
    with open(a.cands_out, "w", encoding="utf-8") as o:
        for l in open(a.cands, encoding="utf-8"):
            r = json.loads(l)
            ids = [str(c["doc_id"]) for c in r["candidates"]][:a.top]
            rows = conn.execute(
                f"SELECT c.doc_id, c.start, c.end, d.body FROM chunk c JOIN doc d USING(doc_id) "
                f"WHERE c.doc_id IN ({','.join('?' * len(ids))}) ORDER BY c.doc_id, c.chunk_id", ids).fetchall()
            by = {}
            for d, s, e, body in rows:
                t = body[s:e]
                if t.strip():
                    by.setdefault(str(d), []).append(t)       # đúng lọc chunk rỗng như fetch_chunks
            for d, ts in by.items():
                if len(ts) >= a.min_chunks:
                    for i, t in enumerate(ts):
                        o.write(json.dumps({"id": r["id"], "doc_id": d, "idx": i, "query": qs[r["id"]], "text": t},
                                           ensure_ascii=False) + "\n")
                        n += 1
    print(f"-> {a.cands_out}: {n} chunk")


def score(a):
    from rerank import qwen_rerank as qr
    qr.DOC_CHARS = a.doc_chars
    rows = [json.loads(l) for l in open(a.cands_out, encoding="utf-8")]
    done = set()
    if os.path.exists(a.scores):
        for l in open(a.scores, encoding="utf-8"):
            r = json.loads(l)
            done.add((r["id"], r["doc_id"], r["idx"]))
    todo = [r for r in rows if (r["id"], r["doc_id"], r["idx"]) not in done]
    print(f"cần chấm {len(todo)}/{len(rows)}", flush=True)
    tok, model, yes, no, dev = qr.load_model(mem_fraction=a.mem_fraction)
    with open(a.scores, "a", encoding="utf-8") as o:
        for s in range(0, len(todo), 256):
            b = todo[s:s + 256]
            ps = qr.score_pairs(tok, model, yes, no, dev, [(r["query"], r["text"]) for r in b], batch=a.batch,
                                max_len=a.max_len)
            for r, p in zip(b, ps):
                o.write(json.dumps({"id": r["id"], "doc_id": r["doc_id"], "idx": r["idx"], "score": round(p, 6)}) + "\n")
            o.flush()
            print(f"{min(s + 256, len(todo))}/{len(todo)}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prep", action="store_true")
    ap.add_argument("--score", action="store_true")
    ap.add_argument("--cands", default="data/blendQB3x.jsonl")
    ap.add_argument("--queries", default="data/queries.jsonl")
    ap.add_argument("--store", default="data/corpus_new.sqlite")
    ap.add_argument("--cands-out", default="data/chunk_cands.jsonl")
    ap.add_argument("--scores", default="data/chunk_scores.jsonl")
    ap.add_argument("--top", type=int, default=40)
    ap.add_argument("--min-chunks", type=int, default=3, help="chỉ chấm doc có ≥ N chunk (baseline gọn: 1 = mọi doc)")
    ap.add_argument("--doc-chars", type=int, default=2800)
    ap.add_argument("--max-len", type=int, default=1400)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--mem-fraction", type=float, default=None)
    a = ap.parse_args()
    if a.prep:
        prep(a)
    if a.score:
        score(a)


if __name__ == "__main__":
    sys.exit(main())
