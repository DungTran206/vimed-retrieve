"""Bước 2: điểm doc p̂ → một ngưỡng chung → danh sách doc mỗi câu; xuất p̂ của mọi ứng viên (--dump) cho các bước sau.

1. MaxP(q,d) = max P(yes) Qwen3-Reranker-4B trên mọi chunk của doc (bước 2, rerank/chunk_rerank.py).
2. p̂ = sigmoid(β·[logit MaxP, log(1 + hạng trong ngôn ngữ), cờ zh, zh·logit MaxP] + b),
   β khớp bằng hồi quy logistic vào nhãn MỀM p(gold) (data/val/p_w045.jsonl, scripts/val_calib.py) trên doc cũ có p.
   Hệ số đã dùng cho bài nộp: 0,359 / −0,272 / −0,698 / −0,087, chặn −0,722.
3. Ngưỡng chung t = p̂ đứng thứ (--docs × số câu) trên toàn đề → câu q giữ mọi doc p̂ ≥ t (xếp p̂ giảm dần).
   --docs 160 chọn bằng nhãn thật 593 câu public (doc F2 offline 143: 0,3787 · 160: 0,3799 · 180: 0,3777).
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
    ap.add_argument("--fit", default="data/val/p_w045.jsonl")
    ap.add_argument("--docs", type=float, default=160)
    ap.add_argument("--out", default="data/val/docs_clean160.json")
    ap.add_argument("--scores", nargs="+", default=SCORES, help="các file điểm chunk Qwen (MaxP = max theo chunk của doc)")
    ap.add_argument("--dump", help="ghi p̂ của MỌI ứng viên {q: [[doc, p̂], ...]} giảm dần (đầu vào baseline.recal_docs)")
    a = ap.parse_args()
    L = {r["id"]: [(c["doc_id"], c["lang"]) for c in r["candidates"]] for r in map(json.loads, open(a.cands, encoding="utf-8"))}
    cand = {(q, d) for q, ds in L.items() for d, _ in ds}
    S = {}                                   # (q, doc) -> {idx chunk: P(yes)}; chunk chấm ở nhiều file thì file SAU thắng
    for p in a.scores:
        for l in open(p, encoding="utf-8"):
            r = json.loads(l)
            k = (r["id"], r["doc_id"])
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
    P = {r["id"]: {c["doc_id"]: c["p"] for c in r["candidates"]} for r in map(json.loads, open(a.fit, encoding="utf-8"))}
    idx = [i for i, (q, d) in enumerate(keys) if d in P[q]]
    y = np.array([P[keys[i][0]][keys[i][1]] for i in idx])
    # nhãn mềm: mỗi mẫu nhân đôi (nhãn 1 trọng số p, nhãn 0 trọng số 1−p)
    lr = LogisticRegression(C=100, max_iter=1000).fit(np.vstack([X[idx], X[idx]]), np.r_[np.ones(len(idx)), np.zeros(len(idx))],
                                                      sample_weight=np.r_[y, 1 - y])
    ph = lr.predict_proba(X)[:, 1]
    print(f"hệ số {np.round(lr.coef_[0], 3)} chặn {lr.intercept_[0]:.3f} trên {len(idx)} doc có p")
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
