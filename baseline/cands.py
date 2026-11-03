"""Bước 1: ứng viên mỗi câu = 300 doc vi + --n-zh doc zh (bài nộp: 80) — chỉ doc thuộc kho BTC, cộng vinmec.com.

vi : RRF(k=60, trọng số 1/1/1) của 3 nguồn top-1000:
       data/bm25d3_rank.jsonl          BM25F giữ dấu, title 3 · tags 2 · descr 1,5 · body 1 (index/bm25.py)
       data/dense_viB3_rank.jsonl      BGE-M3, title + 600 ký tự đầu body (index/dense.py --body-chars 600)
       data/dense_chunk_full_rank.jsonl BGE-M3 trên mọi chunk ~900 token, điểm doc = chunk khớp nhất (index/dense_chunks.py)
     → bỏ doc ngoài kho → lấy 300 doc đầu.
zh : RRF của 4 danh sách (mỗi danh sách cắt 400 — giữ để tái lập đúng; bỏ cắt chỉ đổi ~1,4 doc/câu, số doc vàng như nhau):
       BGE-M3 câu vi (w1) · BGE-M3 câu dịch zh (w1) · Qwen3-Embedding-8B câu vi (w0,3) · 8B câu zh (w0,3)
       (doc zh: title + 600 ký tự đầu body; 109 câu dịch lỗi dùng bản vá *_zhq109_rank)
     → bỏ doc ngoài kho → 40 doc đầu.
Ghi {id, candidates:[{doc_id, score, lang}]}; score chỉ giữ thứ tự (vi trước, zh sau — hạng tính RIÊNG mỗi ngôn ngữ ở bước 2).
  python -m baseline.cands --out data/clean_cands.jsonl
"""
import argparse
import json
import sqlite3

import pandas as pd

from index.fuse import load, rrf

VI = [("data/bm25d3_rank.jsonl", 1), ("data/dense_viB3_rank.jsonl", 1), ("data/dense_chunk_full_rank.jsonl", 1)]
ZH = [("zhC3", "vi", 1), ("zhC3", "zhq", 1), ("zhQ8", "vi", 0.3), ("zhQ8", "zhq", 0.3)]


def zh_lists(cut=400):
    out = []
    for m, q, w in ZH:
        r = load(f"data/dense_{m}_{q}_rank.jsonl")
        if q == "zhq":
            r.update(load(f"data/dense_{m}_zhq109_rank.jsonl"))
        out.append((f"{m}_{q}", {i: v[:cut] for i, v in r.items()}, w))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/clean_cands.jsonl")
    ap.add_argument("--n-vi", type=int, default=300)
    ap.add_argument("--n-zh", type=int, default=40)
    a = ap.parse_args()
    new = set(pd.read_parquet("data/vibiomir_new/links_corpus_vi_en_zh.parquet")["id"].astype(str))
    Fv = rrf([(p, load(p), w) for p, w in VI], topk=1500)    # topk chỉ là trần: doc hợp lệ thứ 300 xa nhất ở hạng 688
    Fz = rrf(zh_lists(), topk=1000)
    ids = sorted({d for q in Fv for _, d in Fv[q][:800]})
    c = sqlite3.connect("file:data/corpus_new.sqlite?mode=ro", uri=True)
    vin = set()
    for i in range(0, len(ids), 900):
        p = ids[i:i + 900]
        vin |= {str(d) for (d,) in c.execute(
            f"SELECT doc_id FROM doc WHERE domain='vinmec.com' AND doc_id IN ({','.join('?' * len(p))})", p)}
    ok = lambda d: d in new or d in vin
    n = 0
    with open(a.out, "w", encoding="utf-8") as f:
        for q in sorted(Fv):
            vi = [d for _, d in Fv[q] if ok(d)][:a.n_vi]
            s = set(vi)
            zh = [d for _, d in Fz.get(q, []) if d in new and d not in s][:a.n_zh]
            L = vi + zh
            n += len(L)
            f.write(json.dumps({"id": q, "candidates": [{"doc_id": d, "score": round(1 - i / (len(L) + 1), 6),
                                                         "lang": "vi" if i < len(vi) else "zh"} for i, d in enumerate(L)]}) + "\n")
    print(f"-> {a.out} · {n / len(Fv):.1f} ứng viên/câu")


if __name__ == "__main__":
    main()
