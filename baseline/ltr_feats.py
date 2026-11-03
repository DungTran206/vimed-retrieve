"""Bước 4: đặc trưng cho MỌI cặp (câu, doc) trong 380 ứng viên z80 (1.200 câu × 380 = 456.000 cặp).

Chỉ dùng danh sách truy hồi, điểm Qwen3-Reranker-4B GỐC và metadata doc; KHÔNG dùng việc doc từng nằm trong bài đã nộp.
  lp, lm     logit p̂ (baseline.select_docs --dump) và logit MaxP Qwen gốc (max theo chunk, chunk chấm ở nhiều file thì file SAU thắng)
  nchunk     số chunk đã chấm của doc
  r_<list>   log(1 + hạng) trong 12 danh sách top-1000 (ngoài top-1000 → hạng 1001); cons100 = số danh sách xếp doc vào top-100
  bge_cos    cos BGE-M3 thô câu ↔ title + 600 ký tự (dense_viB3 cho doc vi, dense_zhC3_vi cho doc zh) — gbm2, gbm3
  s_/d_<list> cos thô / cos − top-1 của câu trong 5 danh sách BGE-M3 (BGE_LISTS) — gbm3
  zh, dom, loglen, rk_lang   ngôn ngữ, domain, log độ dài body, log hạng trong ngôn ngữ theo p̂
  ent        độ phủ thực thể tốt nhất của câu hỏi (âm tiết vi / bigram ký tự zh) trong title + 3.000 ký tự đầu body
  tov        tỉ lệ âm tiết (vi) / bigram (zh) của title có trong câu hỏi (bản dịch zh với doc zh)
  qlen, nent log số từ của câu, số thực thể vi
  python -m baseline.ltr_feats        # → data/val/ltr_feats.pkl (~2 phút)
"""
import argparse
import ast
import json
import math
import pickle
import re
import sqlite3

import numpy as np
import pandas as pd

SCORES = ["data/cc_scores.jsonl", "data/ccq_a_scores.jsonl", "data/ccq_b_scores.jsonl", "data/z80base_scores.jsonl"]
LISTS = ["bm25d3", "dense_viB3", "dense_chunk_full", "dense_vi2", "bm25ent3", "prf20", "dense_q4t", "slug_rank1000",
         "dense_zhC3_vi", "dense_zhC3_zhq", "dense_zhQ8_vi", "bm25zh_new"]
BGE_LISTS = ["dense_viB3", "dense_chunk_full", "dense_vi2", "dense_zhC3_vi", "dense_zhC3_zhq"]


def lg(p):
    return math.log(max(p, 1e-6) / max(1 - p, 1e-6))


def bigrams(t):
    return {t[i:i + 2] for i in range(len(t) - 1)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--phat", default="data/val/z80base_scores.json", help="p̂ của mọi ứng viên (select_docs --dump)")
    ap.add_argument("--out", default="data/val/ltr_feats.pkl")
    a = ap.parse_args()
    S = json.load(open(a.phat, encoding="utf-8"))
    rows = [(int(q), str(d), p) for q, v in S.items() for d, p in v]
    df = pd.DataFrame(rows, columns=["q", "d", "p"])
    key = {(q, d): i for i, (q, d, _) in enumerate(rows)}

    M = {}
    for fn in SCORES:
        for l in open(fn, encoding="utf-8"):
            r = json.loads(l)
            k = (int(r["id"]), str(r["doc_id"]))
            if k in key:
                M.setdefault(k, {})[r["idx"]] = r["score"]
    df["lp"] = df.p.map(lg)
    df["lm"] = [lg(max(M[k].values())) if k in M else np.nan for k in zip(df.q, df.d)]
    df["nchunk"] = [len(M.get(k, ())) for k in zip(df.q, df.d)]

    for nm in LISTS:
        rk = np.full(len(df), 1001, dtype=np.int32)
        for l in open(f"data/{nm}.jsonl" if nm.endswith("1000") else f"data/{nm}_rank.jsonl", encoding="utf-8"):
            r = json.loads(l)
            q = int(r["id"])
            for i, c in enumerate(r["candidates"][:1000], 1):
                j = key.get((q, str(c["doc_id"])))
                if j is not None and i < rk[j]:
                    rk[j] = i
        df["r_" + nm] = np.log1p(rk)
        df["t_" + nm] = rk <= 100
        print("đọc", nm, flush=True)
    df["cons100"] = df[[c for c in df if c.startswith("t_")]].sum(axis=1)
    df = df.drop(columns=[c for c in df if c.startswith("t_")])
    # cos BGE-M3 thô (câu vi ↔ title + 600 ký tự): doc vi từ dense_viB3, doc zh từ dense_zhC3_vi (file trước thắng);
    # không có trong danh sách → min của câu − 0,01. Chỉ gbm2 dùng (ltr_docs).
    cos = np.full(len(df), np.nan)
    for nm in ("dense_viB3", "dense_zhC3_vi"):
        for l in open(f"data/{nm}_rank.jsonl", encoding="utf-8"):
            r = json.loads(l)
            for c in r["candidates"]:
                j = key.get((int(r["id"]), str(c["doc_id"])))
                if j is not None and np.isnan(cos[j]):
                    cos[j] = c["score"]
    df["bge_cos"] = cos
    df["bge_cos"] = df.bge_cos.fillna(df.groupby("q").bge_cos.transform("min") - 0.01).fillna(0)
    # gbm3: cos thô s_<list> và tương đối d_<list> = cos − cos top-1 của câu, cho 5 danh sách BGE-M3
    for nm in BGE_LISTS:
        raw, top = np.full(len(df), np.nan), np.full(len(df), np.nan)
        for l in open(f"data/{nm}_rank.jsonl", encoding="utf-8"):
            r = json.loads(l)
            c0 = r["candidates"][0]["score"] if r["candidates"] else np.nan
            for c in r["candidates"]:
                j = key.get((int(r["id"]), str(c["doc_id"])))
                if j is not None and np.isnan(raw[j]):
                    raw[j], top[j] = c["score"], c0
        s = pd.Series(raw, index=df.index)
        s = s.fillna(s.groupby(df.q).transform("min") - 0.01).fillna(0)
        df["s_" + nm] = s
        df["d_" + nm] = (s - pd.Series(top, index=df.index).groupby(df.q).transform("max")).fillna(-1)

    con = sqlite3.connect("file:data/corpus_new.sqlite?mode=ro", uri=True)
    docs = sorted(set(df.d))
    meta = {}
    for i in range(0, len(docs), 900):
        b = docs[i:i + 900]
        for d, dom, lang, n in con.execute(
                f"SELECT doc_id, domain, lang, length(body) FROM doc WHERE doc_id IN ({','.join('?' * len(b))})", b):
            meta[d] = ((dom or "").replace("www.", ""), lang or "vi", n or 0)
    df["dom"] = df.d.map(lambda d: meta.get(d, ("", "vi", 0))[0])
    df["zh"] = df.d.map(lambda d: meta.get(d, ("", "vi", 0))[1] == "zh").astype(np.int8)
    df["loglen"] = df.d.map(lambda d: math.log1p(meta.get(d, ("", "vi", 0))[2]))
    df["rk_lang"] = np.log1p(df.groupby(["q", "zh"]).p.rank(ascending=False, method="first"))

    QE = {}
    for r in map(json.loads, open("data/queries_enriched.jsonl", encoding="utf-8")):
        try:
            es = r["entities"] if isinstance(r["entities"], list) else ast.literal_eval(r["entities"])
        except Exception:
            es = []
        QE[int(r["id"])] = r
        r["_vi"] = [set(re.findall(r"\w+", e.get("vi", "").lower())) for e in es if e.get("vi")]
        r["_zh"] = [bigrams(e["zh"]) for e in es if len(e.get("zh") or "") >= 2]
        r["_qv"] = set(re.findall(r"\w+", r["query"].lower()))
        r["_qz"] = bigrams(r.get("zh") or "")
    byd = {}
    for j, (q, d) in enumerate(zip(df.q, df.d)):
        byd.setdefault(d, []).append((j, q))
    ent = np.zeros(len(df), dtype=np.float32)
    tov = np.zeros(len(df), dtype=np.float32)
    for i in range(0, len(docs), 900):
        b = docs[i:i + 900]
        for d, t, body, lang in con.execute(
                f"SELECT doc_id, title, substr(body,1,3000), lang FROM doc WHERE doc_id IN ({','.join('?' * len(b))})", b):
            t = (t or "").lower()
            if lang == "zh":
                tx, tt = bigrams(t + " " + (body or "")), bigrams(t)
            else:
                tx, tt = set(re.findall(r"\w+", t + " " + (body or "").lower())), set(re.findall(r"\w+", t))
            for j, q in byd[d]:
                r = QE[q]
                es, qq = (r["_zh"], r["_qz"]) if lang == "zh" else (r["_vi"], r["_qv"])
                ent[j] = max((len(e & tx) / len(e) for e in es if e), default=0)
                tov[j] = len(tt & qq) / len(tt) if tt else 0
    df["ent"], df["tov"] = ent, tov
    df["qlen"] = df.q.map(lambda q: math.log(len(QE[q]["query"].split())))
    df["nent"] = df.q.map(lambda q: len(QE[q]["_vi"]))
    pickle.dump(df, open(a.out, "wb"))
    print(f"-> {a.out} {df.shape} · thiếu MaxP {df.lm.isna().sum()}")


if __name__ == "__main__":
    main()
