"""Rerank top-k bằng cross-encoder `bge-reranker-v2-m3`. Sắp lại thứ tự, không thêm ứng viên.

Vì sao đáng làm dù không tăng recall: đo được hai lần trên leaderboard rằng **cải thiện đầu
danh sách ăn CẢ HAI tầng**. Khi thêm `dense vi`, tầng chunk tăng +32,7% rồi +13,5% mà KHÔNG đổi
một tham số chunk nào - chỉ vì 55 doc đầu đúng hơn (chunk chỉ lấy từ `--chunk-from-top` doc đầu).
Nên một đòn thuần tuý sắp xếp lại vẫn được tính đôi.

Khác bi-encoder (`dense.py`): cross-encoder đọc query và tài liệu CÙNG LÚC nên bắt được quan hệ
giữa chúng, đổi lại không index trước được - phải chạy từng cặp. Vì vậy chỉ dùng cho top-k nhỏ.

Văn bản đem rerank là `title` + đoạn đầu `body`: title là câu hỏi bệnh nhân với site Q&A (tín
hiệu mạnh nhất, xem `bm25.py`), còn đoạn đầu body cho ngữ cảnh mà title thiếu.

    python rerank.py --cands data/fused_dvi25.jsonl --topk 200 --out data/rerank_rank.jsonl
    python rerank.py --demo
"""
import argparse
import json
import os
import sqlite3
import sys
import time

MODEL = "BAAI/bge-reranker-v2-m3"
# 256 token đủ cho title + mở đầu body, và chi phí cross-encoder tăng theo bình phương độ dài.
MAX_LEN = 256
BATCH = 64
# Số ký tự body lấy thêm sau title. ~700 ký tự tiếng Việt ≈ 200 token (đo 3,40 ký tự/token).
BODY_CHARS = 700


def load_model(device=None):
    from sentence_transformers import CrossEncoder
    import torch
    dev = device or ("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Nạp {MODEL} trên {dev}")
    return CrossEncoder(MODEL, max_length=MAX_LEN, device=dev)


def doc_texts(db, doc_ids):
    """{doc_id: 'title. body[:BODY_CHARS]'} cho các doc có trong store."""
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        out = {}
        ids = list(doc_ids)
        for i in range(0, len(ids), 900):          # SQLite giới hạn số tham số mỗi câu
            part = ids[i:i + 900]
            qs = ",".join("?" * len(part))
            for d, t, b in conn.execute(
                    f"SELECT doc_id, ifnull(title,''), substr(ifnull(body,''),1,{BODY_CHARS}) "
                    f"FROM doc WHERE doc_id IN ({qs})", part):
                txt = (t + ". " + b).strip() if t else b
                if txt:
                    out[str(d)] = txt
        return out
    finally:
        conn.close()


def rerank(cands, db, topk=200, model=None, batch=BATCH, log_every=50, partial_path=None):
    """Sắp lại top-k của từng câu. Doc không có text trong store giữ nguyên thứ tự cũ, xếp sau.

    Giữ lại doc không có text thay vì bỏ: ở cấp document chúng vẫn tính điểm (chỉ cần id), và
    đã đo được DOCS_RECALL vượt độ phủ crawl đúng nhờ chuyện này.
    """
    model = model or load_model()
    out, t0 = [], time.monotonic()
    # Ghi dần: 1.200 câu mất ~1,8 giờ trên RTX 4050, ghi một lần ở cuối thì job chết là mất
    # sạch. Cùng thiếu sót `expand_queries` từng mắc, cùng cách sửa.
    pf = open(partial_path, "w", encoding="utf-8") if partial_path else None
    for i, row in enumerate(cands, 1):
        head = row["candidates"][:topk]
        tail = row["candidates"][topk:]
        texts = doc_texts(db, [str(c["doc_id"]) for c in head])
        pairs, idx = [], []
        for j, c in enumerate(head):
            t = texts.get(str(c["doc_id"]))
            if t:
                pairs.append((row["query"], t))
                idx.append(j)
        scored = list(head)
        if pairs:
            s = model.predict(pairs, batch_size=batch, show_progress_bar=False)
            for j, sc in zip(idx, s):
                scored[j] = {**head[j], "score": round(float(sc), 5), "_rr": True}
        # doc có điểm rerank lên trước, giữ thứ tự cũ cho doc không rerank được
        has = [c for c in scored if c.get("_rr")]
        no = [c for c in scored if not c.get("_rr")]
        has.sort(key=lambda c: -c["score"])
        merged = [{k: v for k, v in c.items() if k != "_rr"} for c in has + no] + tail
        out.append({"id": row["id"], "candidates": merged})
        if pf:
            pf.write(json.dumps({"id": row["id"], "candidates": merged},
                                ensure_ascii=False) + "\n")
            pf.flush()
        if i % log_every == 0:
            el = time.monotonic() - t0
            print(f"  {i}/{len(cands)} câu | {el/i:.1f}s/câu | còn ~{(len(cands)-i)*el/i/60:.0f} phút",
                  flush=True)
    if pf:
        pf.close()
    return out


def read_cands(path, queries_path):
    qs = {}
    with open(queries_path, encoding="utf-8") as f:
        for line in f:
            o = json.loads(line)
            qs[int(o["id"])] = o["query"]
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            o = json.loads(line)
            o["query"] = qs[int(o["id"])]
            rows.append(o)
    return rows


def write_jsonl(path, rows):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps({"id": r["id"], "candidates": r["candidates"]},
                               ensure_ascii=False) + "\n")
    print(f"-> {path} | {len(rows)} câu")


def demo():
    """Self-check: model giả chấm điểm theo số từ chung, kiểm đúng phần dễ sai là thứ tự."""
    import tempfile

    class FakeCE:
        def predict(self, pairs, **kw):
            return [len(set(q.lower().split()) & set(t.lower().split())) for q, t in pairs]

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
        db = os.path.join(d, "t.sqlite")
        conn = sqlite3.connect(db)
        conn.executescript("CREATE TABLE doc (doc_id TEXT PRIMARY KEY, title TEXT, body TEXT);")
        conn.executemany("INSERT INTO doc VALUES (?,?,?)", [
            ("1", "gan nhiem mo", "benh gan"),
            ("2", "dau da day", "trieu chung da day"),
        ])
        conn.commit()
        conn.close()
        cands = [{"id": 1, "query": "dau da day",
                  "candidates": [{"doc_id": "1", "score": 9.0},     # đang đứng đầu
                                 {"doc_id": "2", "score": 1.0},     # nhưng khớp hơn
                                 {"doc_id": "99", "score": 0.5}]}]  # không có trong store
        res = rerank(cands, db, topk=3, model=FakeCE())
        got = [c["doc_id"] for c in res[0]["candidates"]]
        assert got == ["2", "1", "99"], f"thứ tự sai: {got}"
        assert "_rr" not in res[0]["candidates"][0], "không được rò trường nội bộ ra file"
        # doc không có text phải GIỮ LẠI (ở cấp document vẫn tính điểm), xếp sau
        assert got[-1] == "99"
    print("demo OK")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cands", default="data/fused_dvi25.jsonl")
    ap.add_argument("--queries", default="data/queries.jsonl")
    ap.add_argument("--db", default="data/corpus.sqlite")
    ap.add_argument("--out", default="data/rerank_rank.jsonl")
    ap.add_argument("--topk", type=int, default=200, help="chỉ rerank N doc đầu mỗi câu")
    ap.add_argument("--batch", type=int, default=BATCH)
    ap.add_argument("--limit", type=int, default=None, help="chỉ chạy N câu đầu (để thử)")
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    if a.demo:
        return demo()
    demo()
    cands = read_cands(a.cands, a.queries)
    if a.limit:
        cands = cands[:a.limit]
    partial = a.out + ".partial"
    rows = rerank(cands, a.db, topk=a.topk, batch=a.batch, partial_path=partial)
    write_jsonl(a.out, rows)
    if os.path.exists(partial):
        os.remove(partial)              # đã có file đầy đủ thì bỏ bản ghi dần


if __name__ == "__main__":
    sys.exit(main())
