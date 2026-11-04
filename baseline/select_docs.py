"""Bước 2: điểm doc p̂ → một ngưỡng chung → danh sách doc mỗi câu; xuất p̂ của mọi ứng viên (--dump) cho các bước sau.

1. MaxP(q,d) = max P(yes) Qwen3-Reranker-4B trên mọi chunk của doc (bước 2, rerank/chunk_rerank.py).
2. p̂ = sigmoid(β·[logit MaxP, log(1 + hạng trong ngôn ngữ), cờ zh, zh·logit MaxP] + b),
   β học bằng hồi quy logistic từ nhãn giả `gold`/`not_gold` do Qwen3-32B inference sinh ra
   ở C:/Users/DumgTran/Downloads/val_fixed.jsonl.
3. Ngưỡng chung t = p̂ đứng thứ (--docs × số câu) trên toàn đề → câu q giữ mọi doc p̂ ≥ t (xếp p̂ giảm dần).
   --docs 160 giữ nguyên cấu hình chọn số lượng doc hiện có.
Bài nộp (380 ứng viên = 300 vi + 80 zh):
  python -m baseline.select_docs --cands data/clean_cands_z80.jsonl \
      --scores data/cc_scores.jsonl data/ccq_a_scores.jsonl data/ccq_b_scores.jsonl data/z80base_scores.jsonl \
      --docs 160 --out data/val/docs_z80base160.json --dump data/val/z80base_scores.json
"""
import argparse
import json

import numpy as np
from sklearn.linear_model import LogisticRegression

SCORES = ["data/cc_scores.jsonl", "data/ccq_a_scores.jsonl", "data/ccq_b_scores.jsonl"]


def logit(x):
    x = np.clip(x, 1e-4, 1 - 1e-4)
    return np.log(x / (1 - x))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cands", default="data/clean_cands.jsonl")
    ap.add_argument("--labels", default="C:/Users/DumgTran/Downloads/val_fixed.jsonl",
                    help="nhãn giả {id, gold, not_gold} do Qwen3-32B sinh")
    ap.add_argument("--docs", type=float, default=160)
    ap.add_argument("--out", default="data/val/docs_clean160.json")
    ap.add_argument("--scores", nargs="+", default=SCORES, help="các file điểm chunk Qwen (MaxP = max theo chunk của doc)")
    ap.add_argument("--dump", help="ghi p̂ của MỌI ứng viên {q: [[doc, p̂], ...]} giảm dần (đầu vào baseline.recal_docs)")
    a = ap.parse_args()
    L = {r["id"]: [(str(c["doc_id"]), c["lang"]) for c in r["candidates"]] for r in map(json.loads, open(a.cands, encoding="utf-8"))}
    cand = {(q, d) for q, ds in L.items() for d, _ in ds}
    S = {}                                   # (q, doc) -> {idx chunk: P(yes)}; chunk chấm ở nhiều file thì file SAU thắng
    for p in a.scores:
        for l in open(p, encoding="utf-8"):
            r = json.loads(l)
            k = (r["id"], str(r["doc_id"]))
            if k in cand:
                S.setdefault(k, {})[r["idx"]] = r["score"]
    M = {k: max(v.values()) for k, v in S.items()}
    X, keys = [], []
    for q, ds in L.items():
        nv = sum(g == "vi" for _, g in ds)
        for j, (d, g) in enumerate(ds):
            z = g == "zh"
            m = logit(M.get((q, d), 0.0))
            X.append([m, np.log(1 + (j - nv if z else j)), z, z * m])
            keys.append((q, d))
    X = np.array(X, dtype=float)
    labels = {}
    with open(a.labels, encoding="utf-8") as f:
        for r in map(json.loads, f):
            labels.update({(r["id"], str(d)): 0 for d in r["not_gold"]})
            labels.update({(r["id"], str(d)): 1 for d in r["gold"]})
    idx = [i for i, key in enumerate(keys) if key in labels]
    if not idx:
        raise ValueError(f"Không có cặp ứng viên nào khớp nhãn trong {a.labels}")
    y = np.array([labels[keys[i]] for i in idx])
    lr = LogisticRegression(C=100, max_iter=1000).fit(X[idx], y)
    ph = lr.predict_proba(X)[:, 1]
    print(f"hệ số {np.round(lr.coef_[0], 3)} chặn {lr.intercept_[0]:.3f} trên {len(idx)} nhãn Qwen3-32B từ {a.labels}")
    t = np.sort(ph)[::-1][round(a.docs * len(L)) - 1]
    by = {}
    for (q, d), p in zip(keys, ph):
        if p >= t:
            by.setdefault(q, []).append((p, d))
    D = {q: [d for _, d in sorted(by.get(q, []), key=lambda x: -x[0])] for q in sorted(L)}
    json.dump(D, open(a.out, "w"))
    if a.dump:
        allp = {}
        for (q, d), p in zip(keys, ph):
            allp.setdefault(str(q), []).append([d, float(p)])
        json.dump({q: sorted(v, key=lambda x: -x[1]) for q, v in allp.items()}, open(a.dump, "w"))
    n = [len(v) for v in D.values()]
    print(f"ngưỡng p̂ {t:.5f} → {sum(n) / len(n):.1f} doc/câu (ít nhất {min(n)}) -> {a.out}")


if __name__ == "__main__":
    main()
