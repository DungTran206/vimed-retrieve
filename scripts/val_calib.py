"""Tập kiểm chứng NỘI BỘ từ lịch sử nộp bài (chỉ dùng số TỔNG hợp của leaderboard, không dò nhãn từng câu).

Mỗi bài đã chấm là một phương trình:  DOCS_P = (1/1200) · Σ_q  mean_{d ∈ bài_q} p(gold | đặc trưng(q, d))
→ khớp p theo ngăn đặc trưng (Qwen P(yes), ngôn ngữ, có/không điểm Qwen) bằng bình phương tối thiểu có ràng buộc [0, 1],
kiểm chứng bỏ-một-bài (leave-one-out) và trên các CẶP SÁT NHAU (BGE vs 8B zh, w04 vs w045...).
    python scripts/val_calib.py --extract   # rút danh sách doc từ runs/*.zip → data/val/docs_<bài>.jsonl (một lần)
    python scripts/val_calib.py             # gắn đặc trưng, khớp, in sai số
    python scripts/val_calib.py --demo      # tự kiểm trên dữ liệu giả
"""
import json, os, re, sys, zipfile, sqlite3, collections

# (bài, DOCS_P trên leaderboard) — chỉ bài chấm từ 09/10 (thời pool H / qwen_all_h); nguồn: PROGRESS.md
REG = {
    "p50_head": 0.3125, "p50_fH": 0.2925, "p50_dvib3": 0.2894, "p50_bm25": 0.1501, "p50_chunk": 0.3136,
    "p50_headchunk": 0.3380, "p50_c10w1": 0.3200, "p50_c10w3": 0.3055,
    "e1_A_c5plus": 0.2462, "e1_B_c3_4": 0.1710, "e1_C_c2": 0.0875, "e1_D_c1": 0.0453,
    "e3_congdong_site": 0.1054, "e3_congdong_ctl": 0.1071, "e3_longchau_site": 0.4182, "e3_longchau_ctl": 0.3997,
    "e3_medlatec_site": 0.3642, "e3_medlatec_ctl": 0.3162,
    "xq_in": 0.1130, "xq_out": 0.1074, "e6_aspect_match": 0.1976, "e6_aspect_miss": 0.1932,
    "r300_p50_base": 0.0749, "p50_q4chunk_rrf": 0.0760, "p50_bgechunk": 0.0691,
    "p50_subq_rrf": 0.0743, "p50_subq_ctl": 0.0733,
    "p50_zh_in": 0.066, "p50_zh3_in": 0.1103, "p50_zh8_in": 0.0827, "p50_zh38w_in": 0.115,
    "blendQB8b_e120": 0.1780, "blendQB8w05_e120": 0.1779, "blendQB11_e120": 0.1785, "blendQB13af_e120": 0.181,
    "blendQB13bf_e120": 0.1727, "blendQB14_e120": 0.1846, "blendQB14_w035_e120": 0.1865,
    "w04_zh38w_e120": 0.1878, "w045_zh38w_e120": 0.1884, "w05_zh38w_e120": 0.1881,
}
VAL = "data/val"
PAT = re.compile(rb'"id":\s*(\d+),\s*"relevant_docs":\s*\[([^\]]*)\]')   # có/không dấu cách (json.dumps mặc định)


def extract_zip(path):
    """Đọc JSON trong ZIP THEO LUỒNG (bài lớn ~600 MB): chỉ lấy id + relevant_docs, không json.load cả file."""
    out, buf = {}, b""
    with zipfile.ZipFile(path) as z, z.open(z.namelist()[0]) as f:
        while True:
            blk = f.read(1 << 24)
            buf += blk
            last = 0
            for m in PAT.finditer(buf):
                out[int(m.group(1))] = [x.strip().strip(b'"').decode() for x in m.group(2).split(b",") if x.strip()]
                last = m.end()
            buf = buf[max(last, len(buf) - (1 << 20)):] if blk else b""
            if not blk:
                break
    return out


def bin_of(lang, qy):
    """Ngăn đặc trưng. zh tách riêng (Qwen chỉ chấm pool vi); vi theo dải P(yes), thiếu điểm là một ngăn."""
    if lang == "zh":
        return "zh"
    if qy is None:
        return "vi_noq"
    for t, n in ((0.1, "q<.1"), (0.3, "q.1-.3"), (0.5, "q.3-.5"), (0.7, "q.5-.7"), (0.85, "q.7-.85"), (0.95, "q.85-.95")):
        if qy < t:
            return n
    return "q>=.95"


def design(docs, qwen, lang):
    """Mỗi bài → vector hệ số theo ngăn: Σ_q (số doc ngăn b ở câu q / k_q) / 1200."""
    row = collections.Counter()
    for q, ds in docs.items():
        if not ds:
            continue
        for d in ds:
            row[bin_of(lang.get(d), qwen.get(q, {}).get(d))] += 1 / len(ds) / 1200
    return row


def fit(rows, ys, bins):
    """Bình phương tối thiểu có ràng buộc 0 ≤ p ≤ 1 (scipy lsq_linear)."""
    import numpy as np
    from scipy.optimize import lsq_linear
    A = np.array([[r.get(b, 0.0) for b in bins] for r in rows]); y = np.array(ys)
    return lsq_linear(A, y, bounds=(0, 1)).x


def main():
    if "--demo" in sys.argv:
        import numpy as np
        rng = np.random.default_rng(0); bins = ["a", "b", "c"]; true = np.array([0.6, 0.2, 0.05])
        rows = [dict(zip(bins, w / w.sum())) for w in rng.random((12, 3))]
        ys = [sum(r[b] * t for b, t in zip(bins, true)) for r in rows]
        p = fit(rows, ys, bins)
        assert np.allclose(p, true, atol=1e-6), p
        assert bin_of("zh", 0.9) == "zh" and bin_of("vi", None) == "vi_noq" and bin_of("vi", 0.96) == "q>=.95"
        print("demo OK", p.round(3)); return
    os.makedirs(VAL, exist_ok=True)
    if "--extract" in sys.argv:
        for n in REG:
            o = f"{VAL}/docs_{n}.json"
            if os.path.exists(o) or not os.path.exists(f"runs/{n}.zip"):
                continue
            D = extract_zip(f"runs/{n}.zip")
            json.dump(D, open(o, "w"))
            print(f"{n}: {sum(1 for v in D.values() if v)} câu có doc, TB {sum(map(len, D.values()))/max(1,sum(1 for v in D.values() if v)):.1f} doc", flush=True)
        return
    names = [n for n in REG if os.path.exists(f"{VAL}/docs_{n}.json")]
    print("thiếu zip:", [n for n in REG if n not in names])
    docs = {n: {int(k): v for k, v in json.load(open(f"{VAL}/docs_{n}.json")).items()} for n in names}
    allq = collections.defaultdict(set)
    for D in docs.values():
        for q, ds in D.items():
            allq[q].update(ds)
    qwen = {}
    for l in open("data/qwen_all_h.jsonl", encoding="utf-8"):
        r = json.loads(l)
        need = allq.get(r["id"], set())
        qwen[r["id"]] = {str(c["doc_id"]): c["score"] for c in r["candidates"] if str(c["doc_id"]) in need}
    ids = sorted({d for s in allq.values() for d in s}); lang = {}
    c = sqlite3.connect("file:data/corpus_new.sqlite?mode=ro", uri=True)
    for i in range(0, len(ids), 900):
        p = ids[i:i + 900]
        lang.update({str(d): l for d, l in c.execute(f"select doc_id,lang from doc where doc_id in ({','.join('?'*len(p))})", p)})
    rows = {n: design(docs[n], qwen, lang) for n in names}
    bins = sorted({b for r in rows.values() for b in r})
    print("ngăn:", bins)
    for n in names:
        tot = sum(rows[n].values()); print(f"  {n:22} phủ {tot*1200/max(1,sum(1 for v in docs[n].values() if v)):.2f} | " +
                                          " ".join(f"{b}:{rows[n].get(b,0)/max(tot,1e-9):.2f}" for b in bins))
    p = fit([rows[n] for n in names], [REG[n] for n in names], bins)
    print("\np(gold | ngăn), khớp trên tất cả:", {b: round(float(x), 3) for b, x in zip(bins, p)})
    print("\nbỏ-một-bài (dự đoán vs thật):")
    pred = {}
    for n in names:
        rest = [m for m in names if m != n]
        pp = fit([rows[m] for m in rest], [REG[m] for m in rest], bins)
        pred[n] = sum(rows[n].get(b, 0) * x for b, x in zip(bins, pp))
        print(f"  {n:22} thật {REG[n]:.4f} | dự đoán {pred[n]:.4f} | lệch {pred[n]-REG[n]:+.4f}")
    print("\ncặp sát nhau (thật Δ vs dự đoán Δ):")
    for a, b in (("p50_zh3_in", "p50_zh8_in"), ("p50_zh38w_in", "p50_zh3_in"), ("w045_zh38w_e120", "w04_zh38w_e120"),
                 ("w05_zh38w_e120", "w045_zh38w_e120"), ("p50_subq_rrf", "p50_subq_ctl"), ("p50_headchunk", "p50_head"),
                 ("p50_c10w1", "p50_c10w3"), ("blendQB13bf_e120", "blendQB13af_e120"), ("e3_medlatec_site", "e3_medlatec_ctl")):
        if a in pred and b in pred:
            dt, dp = REG[a] - REG[b], pred[a] - pred[b]
            print(f"  {a} − {b}: thật {dt:+.4f} | dự đoán {dp:+.4f} | {'ĐÚNG chiều' if dt * dp > 0 else 'SAI chiều'}")


def load_scores(path, need):
    out = {}
    for l in open(path, encoding="utf-8"):
        r = json.loads(l); s = need.get(r["id"], set())
        out[r["id"]] = {str(c["doc_id"]): c["score"] for c in r["candidates"] if str(c["doc_id"]) in s}
    return out


def logit_main():
    """Mô hình ít tham số: p = sigmoid(β·đặc trưng). Đặc trưng vi: logit P(yes) Qwen, cosine chunk-dense (kèm cờ có/không);
    zh: cờ zh + cosine BGE zh (max câu vi / câu dịch zh). Khớp bằng bình phương tối thiểu trên phương trình tổng."""
    import numpy as np
    from scipy.optimize import least_squares
    names = [n for n in REG if os.path.exists(f"{VAL}/docs_{n}.json")]
    docs = {n: {int(k): v for k, v in json.load(open(f"{VAL}/docs_{n}.json")).items()} for n in names}
    need = collections.defaultdict(set)
    for D in docs.values():
        for q, ds in D.items():
            need[q].update(ds)
    Q = load_scores("data/qwen_all_h.jsonl", need); C = load_scores("data/dense_chunk_full_rank.jsonl", need)
    Zv = load_scores("data/dense_zhC3_vi_rank.jsonl", need); Zq = load_scores("data/dense_zhC3_zhq_rank.jsonl", need)
    ids = sorted({d for s in need.values() for d in s}); lang = {}
    c = sqlite3.connect("file:data/corpus_new.sqlite?mode=ro", uri=True)
    for i in range(0, len(ids), 900):
        p = ids[i:i + 900]
        lang.update({str(d): l for d, l in c.execute(f"select doc_id,lang from doc where doc_id in ({','.join('?'*len(p))})", p)})
    X, W = {}, {}
    for n in names:
        rows, ws = [], []
        for q, ds in docs[n].items():
            for d in ds:
                qy, cs = Q.get(q, {}).get(d), C.get(q, {}).get(d)
                zc = max(Zv.get(q, {}).get(d, -1), Zq.get(q, {}).get(d, -1))
                if lang.get(d) == "zh":
                    rows.append([0, 0, 0, 0, 1, max(zc, 0), zc >= 0])
                else:
                    lq = np.log(min(max(qy, 1e-3), 1 - 1e-3) / (1 - min(max(qy, 1e-3), 1 - 1e-3))) if qy is not None else 0
                    rows.append([lq, qy is not None, cs or 0, cs is not None, 0, 0, 0])
                ws.append(1 / len(ds) / 1200)
        X[n], W[n] = np.array(rows, float), np.array(ws)
    sig = lambda z: 1 / (1 + np.exp(-z))
    pred = lambda b, n: float(W[n] @ sig(b[0] + X[n] @ b[1:]))

    def solve(ns):
        return least_squares(lambda b: [pred(b, n) - REG[n] for n in ns], np.zeros(8)).x
    b = solve(names)
    json.dump(list(b), open(f"{VAL}/beta.json", "w"))
    print("β (chặn, logitQ, cóQ, cos, cóCos, zh, cosZh, cóZh):", b.round(2))
    for t in (0.1, 0.3, 0.5, 0.7, 0.9, 0.97):
        for cs in (0.6, 0.7):
            lq = np.log(t / (1 - t))
            print(f"  vi P(yes)={t:<4} cos={cs}: p(gold) ≈ {sig(b[0] + b[1]*lq + b[2] + b[3]*cs + b[4]):.3f}")
    pl = {}
    for n in names:
        pl[n] = pred(solve([m for m in names if m != n]), n)
    err = [abs(pl[n] - REG[n]) for n in names]
    print(f"\nbỏ-một-bài: sai số TB {np.mean(err):.4f}, lớn nhất {max(err):.4f} ({names[int(np.argmax(err))]})")
    ok = 0; pairs = (("p50_zh3_in", "p50_zh8_in"), ("p50_zh38w_in", "p50_zh3_in"), ("w045_zh38w_e120", "w04_zh38w_e120"),
                     ("w05_zh38w_e120", "w045_zh38w_e120"), ("p50_subq_rrf", "p50_subq_ctl"), ("p50_headchunk", "p50_head"),
                     ("p50_c10w1", "p50_c10w3"), ("blendQB13bf_e120", "blendQB13af_e120"), ("e3_medlatec_site", "e3_medlatec_ctl"),
                     ("p50_chunk", "p50_dvib3"), ("p50_head", "p50_fH"), ("e1_A_c5plus", "e1_B_c3_4"))
    for a, bb in pairs:
        dt, dp = REG[a] - REG[bb], pl[a] - pl[bb]; ok += dt * dp > 0
        print(f"  {a} − {bb}: thật {dt:+.4f} | dự đoán {dp:+.4f} | {'ĐÚNG' if dt*dp > 0 else 'SAI'}")
    print(f"đúng chiều {ok}/{len(pairs)}")


def score_cands(path, out, top=200):
    """Chấm p(gold) cho top-`top` doc mỗi câu của file ứng viên bằng β đã khớp (--logit) → {id, candidates:[{doc_id, p}]}."""
    import numpy as np
    b = np.array(json.load(open(f"{VAL}/beta.json")))
    R = {json.loads(l)["id"]: [str(c["doc_id"]) for c in json.loads(l)["candidates"]][:top] for l in open(path, encoding="utf-8")}
    need = {q: set(v) for q, v in R.items()}
    Q = load_scores("data/qwen_all_h.jsonl", need); C = load_scores("data/dense_chunk_full_rank.jsonl", need)
    Zv = load_scores("data/dense_zhC3_vi_rank.jsonl", need); Zq = load_scores("data/dense_zhC3_zhq_rank.jsonl", need)
    ids = sorted({d for s in need.values() for d in s}); lang = {}
    c = sqlite3.connect("file:data/corpus_new.sqlite?mode=ro", uri=True)
    for i in range(0, len(ids), 900):
        p = ids[i:i + 900]
        lang.update({str(d): l for d, l in c.execute(f"select doc_id,lang from doc where doc_id in ({','.join('?'*len(p))})", p)})
    with open(out, "w", encoding="utf-8") as o:
        for q, ds in R.items():
            rows = []
            for d in ds:
                qy, cs = Q.get(q, {}).get(d), C.get(q, {}).get(d)
                zc = max(Zv.get(q, {}).get(d, -1), Zq.get(q, {}).get(d, -1))
                if lang.get(d) == "zh":
                    rows.append([0, 0, 0, 0, 1, max(zc, 0), zc >= 0])
                else:
                    t = min(max(qy, 1e-3), 1 - 1e-3) if qy is not None else 0.5
                    rows.append([np.log(t / (1 - t)) if qy is not None else 0, qy is not None, cs or 0, cs is not None, 0, 0, 0])
            p = 1 / (1 + np.exp(-(b[0] + np.array(rows, float) @ b[1:])))
            o.write(json.dumps({"id": q, "candidates": [{"doc_id": d, "p": round(float(x), 4)} for d, x in zip(ds, p)]}) + "\n")


if __name__ == "__main__":
    if "--score" in sys.argv:
        i = sys.argv.index("--score"); score_cands(sys.argv[i + 1], sys.argv[i + 2])
    else:
        logit_main() if "--logit" in sys.argv else main()
