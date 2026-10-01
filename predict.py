"""Áng điểm TRƯỚC khi nộp — bộ lọc để không tiêu lượt nộp vào câu hỏi đã biết đáp án.

Không có nhãn vàng nên **không dự đoán được F2 tuyệt đối cho một phương pháp MỚI**.
Nhưng ba việc sau thì làm được, và chúng đủ để chặn phần lớn lượt nộp vô ích:

  1. `--curve`   Khớp đường cong từ các lượt đã nộp → đoán F2 ở k chưa thử.
                 Chỉ đúng cho CÙNG một phương pháp xếp hạng (cùng nguồn ứng viên).
  2. `--overlap` So hai file ứng viên: trùng nhau bao nhiêu %. Nếu file mới trùng ~95%
                 với file đã có điểm thì **đừng nộp** - điểm sẽ gần như y hệt.
  3. `--chunks`  Đo độ phủ chunk của một bài nộp → ước mức tăng CHUNKS_RECALL.
                 Cái này đáng tin vì recall cấp chunk tỉ lệ gần thẳng với độ phủ.

Cách duy nhất dự đoán F2 tuyệt đối cho phương pháp mới: **tập dev có nhãn** rồi dùng
`score.py`. Chưa có nhãn.

  python predict.py --curve
  python predict.py --overlap data/slug_rank.jsonl data/bm25_rank.jsonl --at 200
  python predict.py --chunks runs/s_k200_allchunk.json
  python predict.py --demo
"""
import argparse
import io
import json
import math
import sqlite3
import sys

# Lịch sử leaderboard. THÊM MỖI LƯỢT NỘP VÀO ĐÂY - đó là toàn bộ nhãn ta có.
# (k, nguồn ứng viên, DOCS_P, DOCS_R, DOCS_F2, CHUNKS_P, CHUNKS_R, CHUNKS_F2)
HISTORY = [
    (20, "slug", 0.1154, 0.0485, 0.0497, 0.0525, 0.0071, 0.0076),
    (100, "slug", 0.0589, 0.1108, 0.0788, 0.0454, 0.0102, 0.0093),
    (200, "slug", 0.0419, 0.1450, 0.0821, 0.0377, 0.0111, 0.0093),
    (500, "slug", 0.0256, 0.2066, 0.0754, 0.0246, 0.0123, 0.0093),
]


def f2(p, r):
    return 5 * p * r / (4 * p + r) if (p + r) > 0 else 0.0


def fit_power(ks, gs):
    """Khớp g(k) = c·k^β bằng bình phương tối thiểu trên log-log."""
    xs = [math.log(k) for k in ks]
    ys = [math.log(g) for g in gs]
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    beta = sxy / sxx if sxx else 0.0
    return math.exp(my - beta * mx), beta


def fit_G(ks, gs, f2s, c, beta):
    """Tìm G khớp nhất với F2 = 5g/(4G+k) qua các điểm đã đo (dò lưới, đủ cho 4 điểm)."""
    best = (None, float("inf"))
    G = 10.0
    while G <= 300:
        err = sum((5 * c * k ** beta / (4 * G + k) - y) ** 2 for k, y in zip(ks, f2s))
        if err < best[1]:
            best = (G, err)
        G += 0.5
    return best[0]


def interp_peak(ks, f2s):
    """Đỉnh bằng parabol qua 3 điểm đo cao nhất, trên trục ln(k).

    ĐÁNG TIN HƠN mô hình tham số 5g/(4G+k): `F2MACRO` là trung bình F2 TỪNG CÂU, còn G
    biến động giữa các câu, nên một G duy nhất không khớp được (sai tới 19% trên dữ liệu
    thật, và đoán lệch đỉnh đi 60%). Nội suy không giả định gì về dạng hàm.
    """
    pts = sorted(zip(ks, f2s), key=lambda t: -t[1])[:3]
    if len(pts) < 3:
        return None
    pts.sort()
    (k1, y1), (k2, y2), (k3, y3) = pts
    x1, x2, x3 = (math.log(k) for k in (k1, k2, k3))
    s12 = (y2 - y1) / (x2 - x1)
    s23 = (y3 - y2) / (x3 - x2)
    if abs(s12 - s23) < 1e-12:
        return None
    m12, m23 = (x1 + x2) / 2, (x2 + x3) / 2
    return math.exp(m12 + s12 / (s12 - s23) * (m23 - m12))


def curve(source="slug"):
    rows = [h for h in HISTORY if h[1] == source]
    if len(rows) < 3:
        sys.exit(f"Cần ≥3 lượt nộp cùng nguồn '{source}', đang có {len(rows)}")
    ks = [r[0] for r in rows]
    gs = [r[2] * r[0] for r in rows]          # g = P·k
    f2s = [r[4] for r in rows]
    c, beta = fit_power(ks, gs)
    G = fit_G(ks, gs, f2s, c, beta)

    print(f"Khớp từ {len(rows)} lượt nộp nguồn '{source}':")
    print(f"  g(k) = {c:.3f} · k^{beta:.3f}        (số doc vàng tìm được ở độ sâu k)")
    print(f"  G    ≈ {G:.0f}                      (số doc vàng mỗi câu)")
    print(f"\n{'k':>6} {'g dự đoán':>10} {'F2 dự đoán':>11} {'F2 đo được':>11} {'sai':>8}")
    seen = {r[0]: r[4] for r in rows}
    for k in (20, 50, 100, 150, 200, 250, 300, 500, 1000):
        g = c * k ** beta
        pred = 5 * g / (4 * G + k)
        real = seen.get(k)
        mark = f"{real:>11.4f} {abs(pred-real)/real*100:>7.1f}%" if real else f"{'—':>11} {'—':>8}"
        star = "  ← đã đo, cao nhất" if real and real == max(f2s) else ""
        print(f"{k:>6} {g:>10.2f} {pred:>11.4f} {mark}{star}")

    res = max(abs(5 * c * k ** beta / (4 * G + k) - y) / y for k, y in zip(ks, f2s))
    kstar_model = 4 * G * beta / (1 - beta) if beta < 1 else float("inf")
    kstar_interp = interp_peak(ks, f2s)
    kbest = max(zip(ks, f2s), key=lambda t: t[1])

    print(f"\n--- Đỉnh k*: hai cách tính, DÙNG CÁI NỘI SUY ---")
    print(f"  nội suy qua điểm đo (TIN CÁI NÀY) : k* ≈ {kstar_interp:.0f}")
    print(f"  mô hình 5g/(4G+k)                : k* ≈ {kstar_model:.0f}   "
          f"(sai {res*100:.0f}% trên chính điểm đã đo)")
    print(f"  k tốt nhất ĐÃ THỬ THẬT           : k = {kbest[0]} → F2 {kbest[1]:.4f}")
    if kstar_interp and abs(kstar_model - kstar_interp) / kstar_interp > 0.25:
        print(f"\n  ⚠️ Hai cách lệch nhau >25%. Mô hình tham số giả định MỘT G duy nhất,")
        print(f"     nhưng F2MACRO là trung bình F2 từng câu và G biến động giữa các câu.")
        print(f"     → Dùng k ≈ {kstar_interp:.0f}, đừng dùng {kstar_model:.0f}.")

    print(f"\n⚠️ Đường cong này CHỈ đúng cho nguồn ứng viên '{source}'.")
    print("   Phương pháp xếp hạng mới có c, β khác → PHẢI nộp 1 lượt để đo lại.")
    print("   Và không dự đoán được F2 tuyệt đối cho phương pháp mới: cần tập dev có nhãn.")
    return c, beta, G


def load_ids(path, at):
    """{qid: [doc_id top-at]} từ file ứng viên hoặc file bài nộp."""
    out = {}
    with open(path, encoding="utf-8") as f:
        head = f.read(1)
        f.seek(0)
        if head == "[":                       # file bài nộp .json
            for r in json.load(f):
                out[int(r["id"])] = [str(x) for x in r["relevant_docs"]][:at]
            return out
        for line in f:                        # file ứng viên .jsonl
            o = json.loads(line)
            out[int(o["id"])] = [str(c["doc_id"]) for c in o["candidates"]][:at]
    return out


def overlap(path_a, path_b, at):
    """Hai tập ứng viên trùng nhau bao nhiêu → lượt nộp mới có đáng không."""
    A, B = load_ids(path_a, at), load_ids(path_b, at)
    qs = sorted(set(A) & set(B))
    if not qs:
        sys.exit("Hai file không có câu hỏi nào chung")
    jac, inter, newfrac = [], [], []
    for q in qs:
        a, b = set(A[q]), set(B[q])
        if not (a | b):
            continue
        jac.append(len(a & b) / len(a | b))
        inter.append(len(a & b))
        newfrac.append(len(b - a) / len(b) if b else 0)
    n = len(jac)
    mj, mnew = sum(jac) / n, sum(newfrac) / n
    print(f"So ở top-{at} trên {n} câu:")
    print(f"  Jaccard trung bình        : {mj:.3f}")
    print(f"  doc trùng trung bình/câu  : {sum(inter)/n:.1f}/{at}")
    print(f"  % doc MỚI trong file B    : {mnew*100:.1f}%")
    print()
    if mnew < 0.05:
        print("  → ĐỪNG NỘP: gần như trùng hoàn toàn, điểm sẽ y hệt. Tiết kiệm một lượt.")
    elif mnew < 0.25:
        print("  → Cân nhắc: chỉ đổi ít. Điểm có thể nhúc nhích trong sai số.")
    else:
        print("  → ĐÁNG NỘP: khác đủ nhiều, điểm không suy ra được từ lượt cũ.")
    return mj, mnew


def chunks(sub_path, db="data/corpus.sqlite"):
    """Độ phủ chunk của bài nộp → ước mức tăng CHUNKS_RECALL."""
    recs = json.load(open(sub_path, encoding="utf-8"))
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    have = {r[0] for r in conn.execute("SELECT DISTINCT doc_id FROM chunk")}
    ids = {str(x) for r in recs for x in r["relevant_docs"]}
    cov = len(ids & have) / len(ids) if ids else 0
    nch = sum(len(r["relevant_chunks"]) for r in recs)
    withch = sum(1 for r in recs if r["relevant_chunks"])
    print(f"Bài nộp {sub_path}:")
    print(f"  doc_id duy nhất        : {len(ids):>8,}")
    print(f"  trong đó đã cắt chunk  : {len(ids & have):>8,}  = {cov*100:.2f}%")
    print(f"  tổng chunk             : {nch:>8,}  ({nch/len(recs):.1f}/câu)")
    print(f"  câu có ≥1 chunk        : {withch:>8,}/{len(recs)}")

    base = next((h for h in HISTORY if h[7]), None)
    if base and cov > 0:
        # Recall cấp chunk tỉ lệ gần thẳng với độ phủ: không có trang thì không nộp được chunk
        _, _, _, _, _, cp, cr, cf = base
        for target in (cov, 0.5, 1.0):
            scale = target / cov
            r2 = min(cr * scale, 1.0)
            print(f"\n  Nếu độ phủ chunk = {target*100:>5.1f}%  (×{scale:.0f}):")
            for pname, p2 in (("P giữ nguyên", cp), ("P giảm 1/2", cp / 2),
                              ("P giảm 1/4", cp / 4)):
                print(f"    {pname:14} R={r2:.4f} → CHUNKS_F2 ≈ {f2(p2, r2):.4f}"
                      f"  FINAL ≈ {(0.0821 + f2(p2, r2))/2:.4f}")
    print("\nĐáng tin hơn --curve: recall cấp chunk tỉ lệ gần THẲNG với độ phủ,")
    print("vì không có trang trong máy thì không nộp được chunk nào của nó.")


def demo():
    """Self-check: khớp đường cong phải tái tạo được các điểm đã đo."""
    assert abs(f2(0.5, 0.5) - 0.5) < 1e-12
    assert f2(0.2, 0.8) > f2(0.8, 0.2) and f2(0, 0) == 0

    # Khớp dữ liệu sinh ra từ chính mô hình -> phải lấy lại đúng tham số
    c0, b0 = 0.47, 0.54
    ks = [20, 100, 200, 500]
    gs = [c0 * k ** b0 for k in ks]
    c, b = fit_power(ks, gs)
    assert abs(c - c0) < 1e-6 and abs(b - b0) < 1e-6, (c, b)
    G0 = 55.0
    f2s = [5 * g / (4 * G0 + k) for k, g in zip(ks, gs)]
    assert abs(fit_G(ks, gs, f2s, c, b) - G0) < 1.0, fit_G(ks, gs, f2s, c, b)

    # Khớp trên dữ liệu THẬT: sai phải ở mức dùng được
    ksr = [h[0] for h in HISTORY]
    gsr = [h[2] * h[0] for h in HISTORY]
    f2r = [h[4] for h in HISTORY]
    c, b = fit_power(ksr, gsr)
    G = fit_G(ksr, gsr, f2r, c, b)
    worst = max(abs(5 * c * k ** b / (4 * G + k) - y) / y for k, y in zip(ksr, f2r))
    assert worst < 0.20, f"khớp sai {worst*100:.0f}% - mô hình không dùng được"
    # Nội suy phải ra đỉnh GẦN điểm đo cao nhất, và gần hơn mô hình tham số
    ki = interp_peak(ksr, f2r)
    kbest = max(zip(ksr, f2r), key=lambda t: t[1])[0]
    assert ki is not None and 100 < ki < 400, f"nội suy ra k* = {ki} vô lý"
    kmodel = 4 * G * b / (1 - b)
    assert abs(ki - kbest) < abs(kmodel - kbest), \
        f"nội suy ({ki:.0f}) phải gần điểm đo tốt nhất ({kbest}) hơn mô hình ({kmodel:.0f})"

    # Parabol đối xứng: đỉnh phải nằm đúng giữa trên trục log
    import math as _m
    ks3 = [100, 200, 400]
    ys3 = [0.05, 0.08, 0.05]
    assert abs(interp_peak(ks3, ys3) - 200) < 1, interp_peak(ks3, ys3)

    # overlap: tập giống hệt -> 0% mới; tập rời nhau -> 100% mới
    import tempfile
    import os
    with tempfile.TemporaryDirectory() as d:
        pa, pb, pc = (os.path.join(d, n) for n in ("a.jsonl", "b.jsonl", "c.jsonl"))
        mk = lambda p, ids: open(p, "w", encoding="utf-8").write(
            json.dumps({"id": 1, "candidates": [{"doc_id": i} for i in ids]}) + "\n")
        mk(pa, ["1", "2", "3", "4"])
        mk(pb, ["1", "2", "3", "4"])
        mk(pc, ["5", "6", "7", "8"])
        # Chặn output của self-check để không lẫn vào kết quả thật
        import contextlib
        with contextlib.redirect_stdout(io.StringIO()):
            same = overlap(pa, pb, 4)[1]
            diff = overlap(pa, pc, 4)[1]
        assert abs(same) < 1e-9, "tập giống hệt phải ra 0% mới"
        assert abs(diff - 1.0) < 1e-9, "tập rời phải ra 100% mới"
    print("demo OK")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--curve", action="store_true")
    ap.add_argument("--source", default="slug")
    ap.add_argument("--overlap", nargs=2, metavar=("A", "B"))
    ap.add_argument("--at", type=int, default=200)
    ap.add_argument("--chunks", metavar="SUB.json")
    ap.add_argument("--db", default="data/corpus.sqlite")
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    if a.demo:
        return demo()
    demo()
    if a.curve:
        curve(a.source)
    if a.overlap:
        overlap(a.overlap[0], a.overlap[1], a.at)
    if a.chunks:
        chunks(a.chunks, a.db)
    if not (a.curve or a.overlap or a.chunks):
        ap.print_help()


if __name__ == "__main__":
    sys.exit(main())
