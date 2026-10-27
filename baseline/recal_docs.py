"""Bài D — bước 4: sửa p̂ theo phần dư (PROGRESS 26/10 "PHÂN TÍCH PHẦN DƯ"), rồi chọn lại tập doc bằng ngưỡng chung
(TB 160 doc/câu). Đầu vào: data/val/z80base_scores.json (p̂ của 380 ứng viên, `baseline.select_docs --dump`).

Đồng thuận = số nguồn vi (BM25F có dấu, dense title+600, chunk-dense toàn kho) xếp doc vào top-100.
  --mode gamma --gamma 1.2 : doc vi đồng thuận ≥2 → p̂·γ, đúng 1 → p̂/γ (MỘT tham số, không nhãn ngoài việc chọn γ)
  --mode full              : hệ số nhân theo ô (đồng thuận 0/1/2+ × vi / zh theo domain) HỌC TỪ NHÃN val
                             (data/lb/val.jsonl, co về 1 với α=20) — vùng xám như ngưỡng 160, ghi rõ khi khai báo.
Ghi data/val/recal_<tag>_scores.json (cùng định dạng z80base_scores.json) và data/val/docs_recal_<tag>.json.
  python -m baseline.recal_docs --mode full --tag dfull          # bài D; bài ltr/gbm dùng p̂' này làm phân bố tham chiếu
  python -m baseline.recal_docs --mode gamma --gamma 1.2 --tag dg12
"""
import argparse
import collections
import json
import sqlite3

SCORES = "data/val/z80base_scores.json"
BASE_DOCS = "data/val/docs_z80base160.json"
SOURCES = ("data/bm25d3_rank.jsonl", "data/dense_viB3_rank.jsonl", "data/dense_chunk_full_rank.jsonl")
ZH_DOMAINS = ("120ask.com", "cnkang.com", "familydoctor.com.cn", "ask.39.net")


def top100(path):
    return {str(r["id"]): {c["doc_id"] for c in r["candidates"][:100]} for r in map(json.loads, open(path, encoding="utf-8"))}


def cell(cons, dom, lang):
    if lang == "zh":
        return "zh:" + (dom if dom in ZH_DOMAINS else "khác")
    return f"vi:{min(cons, 2)}"


def fit_factors(S, feats, alpha=20.0):
    """Hệ số nhân mỗi ô = (tỉ lệ vàng/p̂ của ô) / (tỉ lệ chung), co về 1 với α cặp giả."""
    y, p = collections.Counter(), collections.Counter()
    for line in open("data/lb/val.jsonl", encoding="utf-8"):
        r = json.loads(line)
        if r["G"] == 0:
            continue
        q, gold, ng = str(r["id"]), set(map(str, r["gold"])), set(map(str, r["not_gold"]))
        for d, s in S[q]:
            if d in gold or d in ng:
                c = feats[(q, d)]
                y[c] += d in gold
                p[c] += s
    tot = sum(y.values()) / sum(p.values())
    return {c: ((y[c] + alpha * tot) / (p[c] + alpha)) / tot for c in p}


def select(S2, k_mean):
    """Ngưỡng chung: giữ k_mean × số câu cặp điểm cao nhất (≥1 doc/câu)."""
    allp = sorted(((s, q, d) for q, v in S2.items() for d, s in v), reverse=True)
    keep = collections.defaultdict(list)
    for s, q, d in allp[:k_mean * len(S2)]:
        keep[q].append(d)
    for q, v in S2.items():
        if not keep[q]:
            keep[q] = [v[0][0]]
    return {q: keep[q] for q in S2}, allp[k_mean * len(S2) - 1][0]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mode", choices=("gamma", "full"), required=True)
    ap.add_argument("--gamma", type=float, default=1.2)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--k", type=int, default=160)
    a = ap.parse_args()
    S = {q: [(str(d), p) for d, p in v] for q, v in json.load(open(SCORES, encoding="utf-8")).items()}
    T = [top100(p) for p in SOURCES]
    docs = sorted({d for v in S.values() for d, _ in v})
    con = sqlite3.connect("file:data/corpus_new.sqlite?mode=ro", uri=True)
    meta = {}
    for i in range(0, len(docs), 900):
        b = docs[i:i + 900]
        meta.update({d: ((dom or "").replace("www.", ""), lang) for d, dom, lang in con.execute(
            f"SELECT doc_id, domain, lang FROM doc WHERE doc_id IN ({','.join('?' * len(b))})", b)})
    feats = {}
    for q, v in S.items():
        for d, _ in v:
            dom, lang = meta.get(d, ("", "vi"))
            feats[(q, d)] = cell(sum(d in t.get(q, ()) for t in T), dom, lang)
    if a.mode == "full":
        fac = fit_factors(S, feats)
    else:
        fac = {"vi:2": a.gamma, "vi:1": 1 / a.gamma}
    print("hệ số:", {c: round(f, 3) for c, f in sorted(fac.items())})
    S2 = {q: sorted(((d, s * fac.get(feats[(q, d)], 1.0)) for d, s in v), key=lambda x: -x[1]) for q, v in S.items()}
    D, thr = select(S2, a.k)
    base = json.load(open(BASE_DOCS, encoding="utf-8"))
    n = [len(v) for v in D.values()]
    same = sum(len(set(D[q]) & set(map(str, base[q]))) for q in D) / len(D)
    zh = sum(meta.get(d, ("", ""))[1] == "zh" for v in D.values() for d in v) / len(D)
    print(f"ngưỡng p̂' {thr:.5f} | doc/câu TB {sum(n) / len(n):.1f} (min {min(n)}, max {max(n)}) | "
          f"trùng tập gốc {same:.1f}/câu | zh/câu {zh:.1f}")
    json.dump({q: [[d, round(s, 6)] for d, s in v] for q, v in S2.items()},
              open(f"data/val/recal_{a.tag}_scores.json", "w", encoding="utf-8"))
    json.dump(D, open(f"data/val/docs_recal_{a.tag}.json", "w", encoding="utf-8"))
    print(f"-> data/val/recal_{a.tag}_scores.json, data/val/docs_recal_{a.tag}.json")


if __name__ == "__main__":
    main()
