"""Bài gbm — bước 4b: chấm lại 380 ứng viên bằng đặc trưng (baseline.ltr_feats) rồi chọn tập doc bằng ngưỡng CHUNG 160 doc/câu.

  --mode bge1 : p̂ − 1,0 × TB log(1+hạng) của 5 danh sách BGE-M3 (MỘT tham số; β = 1 chọn bằng nhãn val)
  --mode ltr  : hồi quy logistic 44 đặc trưng (C = 0,1), học trên cặp có nhãn của 593 câu public
  --mode gbm  : HistGradientBoosting cùng 44 đặc trưng (lr 0,05 · 200 vòng · 31 lá · L2 1,0 · random_state 0)
ltr/gbm HỌC TỪ NHÃN public (data/lb/val.jsonl, từ file chấm chi tiết của leaderboard) — VÙNG XÁM, phải khai báo.
Điểm mới được ánh xạ PHÂN VỊ về phân bố p̂ tham chiếu (bge1: z80base_scores.json; ltr/gbm: recal_dfull_scores.json của
baseline.recal_docs --mode full), nên ngưỡng 160 doc/câu và luật giá trị τ 0,09 ở baseline.value_chunks hành xử như bài gốc.
Ghi data/val/recal_<tag>_scores.json + docs_recal_<tag>.json (định dạng của recal_docs) → value_chunks --recal <tag>.
  python -m baseline.ltr_docs --mode gbm --tag gbm
  python -m baseline.ltr_docs --mode gbm --cv          # chỉ đo: doc F2 đo chéo 5 fold theo câu (p̂ gốc vs mô hình)
"""
import argparse
import json
import pickle
from collections import Counter

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

BGE = ["r_dense_viB3", "r_dense_chunk_full", "r_dense_vi2", "r_dense_zhC3_vi", "r_dense_zhC3_zhq"]
REF = {"bge1": "data/val/z80base_scores.json", "ltr": "data/val/recal_dfull_scores.json",
       "gbm": "data/val/recal_dfull_scores.json"}


def load_labels(path="data/lb/val.jsonl"):
    val = {r["id"]: r for r in map(json.loads, open(path, encoding="utf-8")) if r["G"] > 0}
    gold = {q: set(map(str, r["gold"])) for q, r in val.items()}
    lab = {q: gold[q] | set(map(str, r["not_gold"])) for q, r in val.items()}
    return val, gold, lab


def add_feats(df, val):
    """Thêm one-hot 20 domain phổ biến nhất (đếm trên câu có nhãn) + 2 đặc trưng phái sinh; trả danh sách 44 cột."""
    df["lm"] = df.lm.fillna(df.lm.median())
    top = [d for d, _ in Counter(df[df.q.isin(val)].dom).most_common(20)]
    for d in top:
        df["dm_" + d] = (df.dom == d).astype(np.int8)
    df["lnchunk"] = np.log1p(df.nchunk)
    df["zh_lm"] = df.zh * df.lm
    return ["lp", "lm", "zh_lm", "lnchunk", "cons100", "zh", "loglen", "rk_lang", "ent", "tov", "qlen", "nent"] + \
           [c for c in df if c.startswith("r_")] + ["dm_" + d for d in top]


def fit_score(mode, tr, y, feat):
    """Học trên cặp có nhãn tr, trả hàm chấm điểm (càng cao càng có khả năng là doc vàng)."""
    if mode == "gbm":
        m = HistGradientBoostingClassifier(learning_rate=0.05, max_iter=200, max_leaf_nodes=31, l2_regularization=1.0,
                                           random_state=0).fit(tr[feat], y)
        return lambda x: m.predict_proba(x[feat])[:, 1]
    sc = StandardScaler().fit(tr[feat])
    m = LogisticRegression(C=0.1, max_iter=2000).fit(sc.transform(tr[feat]), y)
    return lambda x: m.decision_function(sc.transform(x[feat]))


def quantile_map(s, ref):
    """Thay điểm s bằng giá trị cùng phân vị trong ref (cùng số phần tử): giữ thứ tự của s, phân bố của ref."""
    ref = np.sort(np.asarray(ref, dtype=float))
    assert len(ref) == len(s)
    return ref[pd.Series(np.asarray(s)).rank(method="first").astype(int).values - 1]


def select(S2, k_mean=160):
    """Ngưỡng chung: giữ k_mean × số câu cặp điểm cao nhất toàn đề (≥ 1 doc/câu)."""
    allp = sorted(((p, q, d) for q, v in S2.items() for d, p in v), reverse=True)[:k_mean * len(S2)]
    D = {q: [] for q in S2}
    for _, q, d in allp:
        D[q].append(d)
    return {q: v or [S2[q][0][0]] for q, v in D.items()}, allp[-1][0]


def cv(df, mode, feat, val, gold, lab, k=160):
    fo = json.load(open("data/lb/folds.json"))["random"]
    d = df[df.q.isin(val)].copy()
    d["y"] = [x in gold[q] for q, x in zip(d.q, d.d)]
    d["lab"] = [x in lab[q] for q, x in zip(d.q, d.d)]
    d["fold"] = d.q.map(lambda q: fo[str(q)])
    out = {"p̂": [], mode: []}
    for f in range(5):
        tr, ev = d[(d.fold != f) & d.lab], d[d.fold == f]
        for name, s in (("p̂", ev.p.values), (mode, fit_score(mode, tr, tr.y, feat)(ev))):
            n = ev.q.nunique()
            keep = ev.assign(s=s).nlargest(k * n, "s")
            g = keep.groupby("q").y.sum().reindex(ev.q.unique(), fill_value=0)
            kk = keep.groupby("q").size().reindex(ev.q.unique(), fill_value=0)
            G = np.array([val[q]["G"] for q in ev.q.unique()])
            out[name].append(5 * g.values / (4 * G + kk.values))
    for name, v in out.items():
        print(f"doc F2 đo chéo 5 fold ({len(np.concatenate(v))} câu) {name}: {np.concatenate(v).mean():.4f}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mode", choices=("bge1", "ltr", "gbm"), required=True)
    ap.add_argument("--tag", help="tên đầu ra (mặc định = --mode)")
    ap.add_argument("--feats", default="data/val/ltr_feats.pkl")
    ap.add_argument("--cv", action="store_true", help="chỉ đo đo chéo, không ghi file")
    a = ap.parse_args()
    df = pickle.load(open(a.feats, "rb"))
    if a.mode == "bge1":
        s = df.lp - 1.0 * df[BGE].mean(axis=1)
    else:
        val, gold, lab = load_labels()
        feat = add_feats(df, val)
        if a.cv:
            return cv(df, a.mode, feat, val, gold, lab)
        tr = df[[q in lab and d in lab[q] for q, d in zip(df.q, df.d)]]
        s = fit_score(a.mode, tr, [d in gold[q] for q, d in zip(tr.q, tr.d)], feat)(df)
    df["p2"] = quantile_map(s, [p for v in json.load(open(REF[a.mode], encoding="utf-8")).values() for _, p in v])
    S2 = {str(q): sorted(([d, round(float(p), 6)] for d, p in zip(g.d, g.p2)), key=lambda x: -x[1])
          for q, g in df.groupby("q")}
    D, thr = select(S2)
    tag = a.tag or a.mode
    json.dump(S2, open(f"data/val/recal_{tag}_scores.json", "w", encoding="utf-8"))
    json.dump(D, open(f"data/val/docs_recal_{tag}.json", "w", encoding="utf-8"))
    n = [len(v) for v in D.values()]
    print(f"{tag}: ngưỡng {thr:.5f} · doc/câu TB {np.mean(n):.1f} (min {min(n)}, max {max(n)}) "
          f"-> data/val/recal_{tag}_scores.json, data/val/docs_recal_{tag}.json")


if __name__ == "__main__":
    main()
