"""Truy hồi dense bằng BGE-M3 ở cấp TITLE. Nguồn thứ 4, KHÁC LOẠI với ba nguồn đang dùng.

Vì sao đáng làm dù đã có `slug_bm25` + `bm25_rank` + `bm25_meta`: đo được trên leaderboard,
nguồn thứ 2 cho **+22%** DOCS_F2, nguồn thứ 3 chỉ **+2,6%**, còn nguồn thứ 4 CÙNG LOẠI
(`bm25_body`, tương quan 82% với `bm25_rank`) thì **THUA** (0,1058 so với 0,1077). Cả ba nguồn
hiện tại đều dựa trên trùng khớp từ; dense là cái đầu tiên không.

Vì sao chỉ TITLE, chưa chunk: 1,13M title so với ~6M chunk (rẻ 5×), và với site Q&A thì title
**chính là câu hỏi bệnh nhân** - khớp query↔title là khớp câu hỏi với câu hỏi. Đó cũng là lý do
`bm25.py` cho `title` trọng số cao nhất (3,0). Chunk-level để sau, nếu title-level ăn.

Và BGE-M3 **đa ngôn ngữ**: query tiếng Việt khớp trực tiếp title tiếng Trung, KHÔNG cần dịch.
Đó là thứ BM25 không làm được - nó phải chờ bản dịch của Qwen/Hy-MT2 rồi mới chạm được 83%
corpus phía tiếng Trung.

Đầu ra cùng định dạng với `slug_bm25`/`bm25` nên `fuse.py` nhận được ngay:
    {"id": 1, "candidates": [{"doc_id": "254453", "score": 0.8123}, ...]}

    python dense.py --encode --db data/corpus_new.sqlite --out data/dense_emb   # cần GPU
    python dense.py --rank --emb data/dense_emb --out data/dense_rank.jsonl
    python dense.py --demo
"""
import argparse
import heapq
import json
import os
import sqlite3
import sys

import numpy as np

MODEL = "BAAI/bge-m3"
DIM = 1024
# Lô encode. 128 vừa với 24 GB VRAM khi có người khác dùng chung card; title ngắn nên
# không cần lô lớn, và lô lớn chỉ làm tăng đỉnh VRAM.
BATCH = 128


def load_model(device=None, name=None, mem_fraction=None):
    """Nạp mô hình embedding. `name` mặc định BGE-M3.

    `mem_fraction`: trần VRAM của tiến trình này (vd. 0,5 = 12 GB trên card 24 GB). Máy GPU DÙNG
    CHUNG với người khác, không có trần thì một lần nạp mô hình lớn có thể làm tiến trình của họ
    hết bộ nhớ. Qwen3-Embedding: fp16 và `padding_side=left` (theo model card).
    """
    from sentence_transformers import SentenceTransformer
    import torch
    name = name or MODEL
    dev = device or ("cuda" if torch.cuda.is_available() else "cpu")
    if mem_fraction and dev.startswith("cuda"):
        idx = torch.device(dev).index
        if idx is None:                       # "cuda" không kèm số card -> dùng card hiện tại
            idx = torch.cuda.current_device()
        torch.cuda.set_per_process_memory_fraction(mem_fraction, idx)
    kw = {}
    if "qwen3" in name.lower():
        kw = {"model_kwargs": {"torch_dtype": torch.float16},
              "tokenizer_kwargs": {"padding_side": "left"}}
    print(f"Nạp {name} trên {dev}" + (f" (trần VRAM {mem_fraction:.0%})" if mem_fraction else ""))
    model = SentenceTransformer(name, device=dev, **kw)
    if dev.startswith("cuda") and "qwen3" not in name.lower():
        model.half()          # BGE-M3 fp16: ~2x nhanh, ~1,1 GB thay vì 2,3 GB; vector lưu fp16 nên không đổi thứ hạng ở mức cần
    return model


def iter_titles(db, min_title=10, limit=None, min_body=200, body_chars=0):
    """Sinh (doc_id, title) của doc có nội dung dùng được, theo lô để không nạp hết vào RAM.

    `min_body=0` dành cho store CHỈ CHỨA TITLE: máy local không chạy được BGE-M3 (`transformers`
    kéo `torchaudio` lệch phiên bản → `WinError 127`), nên title được xuất ra một store nhỏ
    75 MB rồi embed trên máy GPU, thay vì chuyển cả store 4,4 GB qua tunnel.
    """
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    # body_chars > 0: embed title + N ký tự đầu của body (tín hiệu nội dung, không chỉ tiêu đề)
    sel = f"title || char(10) || substr(body, 1, {int(body_chars)})" if body_chars else "title"
    sql = (f"SELECT doc_id, {sel} FROM doc "
           "WHERE length(ifnull(title,'')) >= ? AND length(ifnull(body,'')) >= ?")
    if limit:
        sql += f" LIMIT {int(limit)}"
    try:
        cur = conn.execute(sql, (min_title, min_body))
        while True:
            rows = cur.fetchmany(10000)
            if not rows:
                return
            yield rows
    finally:
        conn.close()        # Windows giữ handle file nếu không đóng -> không xoá được store


def encode_docs(db, out_prefix, batch=BATCH, min_title=10, limit=None, model=None,
                min_body=200, body_chars=0):
    """Embed title -> `{out}.npy` (fp16, đã chuẩn hoá) + `{out}.ids.json`.

    fp16 vì 1,13M × 1024 × 4 byte = 4,6 GB ở fp32, còn fp16 là 2,3 GB. Sai số fp16 trên
    vector đã chuẩn hoá không đổi thứ hạng ở mức ta cần (top-1000).
    """
    model = model or load_model()
    ids, blocks, n = [], [], 0
    for rows in iter_titles(db, min_title, limit, min_body, body_chars):
        texts = [r[1] for r in rows]
        emb = model.encode(texts, batch_size=batch, normalize_embeddings=True,
                           convert_to_numpy=True, show_progress_bar=False)
        blocks.append(emb.astype(np.float16))
        ids.extend(str(r[0]) for r in rows)
        n += len(rows)
        print(f"  đã embed {n:,} title", flush=True)
    if not ids:
        sys.exit("Không có doc nào có title + body dùng được")
    E = np.concatenate(blocks)
    np.save(out_prefix + ".npy", E)
    with open(out_prefix + ".ids.json", "w", encoding="utf-8") as f:
        json.dump(ids, f)
    print(f"-> {out_prefix}.npy  {E.shape}  {E.nbytes/1e9:.2f} GB")
    return E, ids


def rank(emb_prefix, queries, topk=1000, block=100_000, model=None, prompt=None):
    """Cosine giữa query và mọi title, lấy top-k. Quét theo khối để không phình RAM.

    Giữ `heapq` theo từng query thay vì sort toàn bộ: bộ nhớ O(số query × topk), không phụ
    thuộc kích thước corpus - cùng lý do `bm25.py` phải streaming hai lượt.
    """
    E = np.load(emb_prefix + ".npy", mmap_mode="r")
    with open(emb_prefix + ".ids.json", encoding="utf-8") as f:
        ids = json.load(f)
    assert len(ids) == len(E), f"ids {len(ids)} != vectors {len(E)}"
    model = model or load_model()
    kw = {"prompt": prompt} if prompt else {}      # Qwen3-Embedding: tiền tố chỉ dẫn CHỈ ở câu hỏi
    Q = model.encode([q["query"] for q in queries], batch_size=32,
                     normalize_embeddings=True, convert_to_numpy=True, **kw).astype(np.float32)
    heaps = [[] for _ in queries]
    for s in range(0, len(E), block):
        sim = Q @ np.asarray(E[s:s + block], dtype=np.float32).T
        k = min(topk, sim.shape[1])
        part = np.argpartition(-sim, k - 1, axis=1)[:, :k]
        for i, cols in enumerate(part):
            h = heaps[i]
            for c in cols:
                item = (float(sim[i, c]), ids[s + int(c)])
                if len(h) < topk:
                    heapq.heappush(h, item)
                elif item > h[0]:
                    heapq.heapreplace(h, item)
        print(f"  đã quét {min(s + block, len(E)):,}/{len(E):,} title", flush=True)
    del E                   # thả mmap: Windows giữ handle file .npy nếu không thả
    out = []
    for q, h in zip(queries, heaps):
        cands = [{"doc_id": d, "score": round(sc, 5)}
                 for sc, d in sorted(h, key=lambda x: -x[0])]
        out.append({"id": q["id"], "candidates": cands})
    return out


def write_jsonl(path, rows):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"-> {path} | {len(rows)} câu | "
          f"trung bình {sum(len(r['candidates']) for r in rows)/max(1,len(rows)):.0f} ứng viên/câu")


def read_queries(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def demo():
    """Self-check trên dữ liệu giả, không cần GPU lẫn mô hình.

    Thay `model` bằng một bộ encode giả: vector one-hot theo từ đầu tiên. Kiểm đúng phần
    logic dễ sai - heap top-k qua nhiều khối, và ánh xạ chỉ số khối -> doc_id.
    """
    import tempfile

    class FakeModel:
        VOCAB = {"dau": 0, "day": 1, "rang": 2, "gan": 3}

        def encode(self, texts, **kw):
            self.last_kw = kw                      # để kiểm: tiền tố chỉ dẫn có được truyền không
            v = np.zeros((len(texts), 4), dtype=np.float32)
            for i, t in enumerate(texts):
                for w in t.lower().split():
                    if w in self.VOCAB:
                        v[i, self.VOCAB[w]] = 1.0
            n = np.linalg.norm(v, axis=1, keepdims=True)
            return v / np.where(n == 0, 1, n)

    fm = FakeModel()
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
        db = os.path.join(d, "t.sqlite")
        conn = sqlite3.connect(db)
        conn.executescript("CREATE TABLE doc (doc_id TEXT PRIMARY KEY, title TEXT, body TEXT);")
        conn.executemany("INSERT INTO doc VALUES (?,?,?)", [
            ("1", "dau day", "x" * 300),
            ("2", "dau rang", "x" * 300),
            ("3", "gan nhiem mo", "x" * 300),
            ("4", "ngan", "x" * 300),            # title quá ngắn -> phải bị loại
            ("5", "dau day nhieu", "x" * 10),    # body quá ngắn -> phải bị loại
        ])
        conn.commit()
        pre = os.path.join(d, "emb")
        E, ids = encode_docs(db, pre, model=fm, min_title=5)
        assert ids == ["1", "2", "3"], f"lọc title/body sai: {ids}"
        assert E.dtype == np.float16 and E.shape == (3, 4)

        qs = [{"id": 1, "query": "dau day"}, {"id": 2, "query": "gan"}]
        # `block=2` để chắc chắn đi qua nhiều khối: lỗi ánh xạ chỉ số chỉ lộ ra khi >1 khối
        res = rank(pre, qs, topk=2, block=2, model=fm)
        assert "prompt" not in fm.last_kw, "không đặt --query-instruct thì KHÔNG được truyền prompt"
        rank(pre, qs, topk=2, block=2, model=fm, prompt="Instruct: X\nQuery:")
        assert fm.last_kw.get("prompt") == "Instruct: X\nQuery:","tiền tố phải đến được encode câu hỏi"
        assert res[0]["candidates"][0]["doc_id"] == "1", res[0]
        assert res[1]["candidates"][0]["doc_id"] == "3", res[1]
        assert len(res[0]["candidates"]) == 2, "topk phải giới hạn đúng"
        # doc "2" chia một từ với query 1 nên phải có điểm, nhưng thấp hơn doc "1"
        assert res[0]["candidates"][1]["doc_id"] == "2"
        assert res[0]["candidates"][0]["score"] > res[0]["candidates"][1]["score"]
    print("demo OK")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/corpus_new.sqlite")
    ap.add_argument("--queries", default="data/queries.jsonl")
    ap.add_argument("--emb", default="data/dense_emb", help="tiền tố file vector")
    ap.add_argument("--out", default="data/dense_rank.jsonl")
    ap.add_argument("--encode", action="store_true", help="chỉ embed title của store")
    ap.add_argument("--rank", action="store_true", help="chỉ xếp hạng từ vector đã có")
    ap.add_argument("--topk", type=int, default=1000)
    ap.add_argument("--batch", type=int, default=BATCH)
    ap.add_argument("--block", type=int, default=100_000)
    ap.add_argument("--limit", type=int, default=None, help="chỉ lấy N doc đầu (để thử)")
    ap.add_argument("--min-body", type=int, default=200,
                    help="0 nếu store chỉ chứa title (xem `iter_titles`)")
    ap.add_argument("--min-title", type=int, default=10,
                    help="độ dài title tối thiểu (ký tự); zh ngắn hơn vi nên dùng ~3")
    ap.add_argument("--body-chars", type=int, default=0,
                    help="embed title + N ký tự đầu body (0 = chỉ title)")
    ap.add_argument("--model", default=None, help=f"mặc định {MODEL}; vd. Qwen/Qwen3-Embedding-4B")
    ap.add_argument("--query-instruct", default=None,
                    help="tiền tố chỉ dẫn cho CÂU HỎI (Qwen3-Embedding cần, doc thì không)")
    ap.add_argument("--mem-fraction", type=float, default=None,
                    help="trần VRAM của tiến trình (0-1). Máy GPU dùng chung nên nên đặt, vd. 0.5")
    ap.add_argument("--max-len", type=int, default=None,
                    help="cắt độ dài token (title ngắn nên 64-128 là đủ, nhanh hơn nhiều)")
    ap.add_argument("--device", default=None, help="vd. cuda:0 (mặc định cuda nếu có)")
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    if a.demo:
        return demo()
    demo()
    do_encode = a.encode or not (a.encode or a.rank)
    do_rank = a.rank or not (a.encode or a.rank)
    model = load_model(device=a.device, name=a.model, mem_fraction=a.mem_fraction)
    if a.max_len:
        model.max_seq_length = a.max_len
    if do_encode:
        encode_docs(a.db, a.emb, batch=a.batch, limit=a.limit, model=model,
                    min_body=a.min_body, min_title=a.min_title, body_chars=a.body_chars)
    if do_rank:
        rows = rank(a.emb, read_queries(a.queries), topk=a.topk, block=a.block, model=model,
                    prompt=a.query_instruct)
        write_jsonl(a.out, rows)


if __name__ == "__main__":
    sys.exit(main())
