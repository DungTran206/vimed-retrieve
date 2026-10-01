"""Tính P/R/F2 macro cho một bài nộp, khi có nhãn vàng (tập dev tự gán).

Chỉ dùng stdlib. Dùng để chỉnh ngưỡng/topk offline mà không tốn lượt nộp.

Định dạng nhãn vàng, JSONL một dòng mỗi câu:
    {"id": 1,
     "relevant_docs": ["123", "456"],
     "info": ["phần thông tin cần thiết 1", "phần thông tin 2"]}

Cấp document: P = |D∩G|/|D|,  R = |D∩G|/|G|
Cấp chunk   : một chunk là relevant nếu CHỨA hoặc overlap đủ với ít nhất một phần trong I.
              P = số chunk relevant / tổng chunk trả về
              R = số phần thông tin được bao phủ / |I|
F2 = 5PR/(4P+R), lấy trung bình macro trên các câu.

  python score.py --sub runs/sub_top20.json --gold data/dev_gold.jsonl
  python score.py --sub runs/sub_top20.json --gold data/dev_gold.jsonl --sweep
  python score.py --demo
"""
import argparse
import json
import re
import sys
import unicodedata

OVERLAP = 0.5          # tỉ lệ token của một phần thông tin phải nằm trong chunk


def norm(s):
    """Chuẩn hoá nhẹ để so khớp: NFC, chữ thường, thu gọn khoảng trắng."""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", s).lower()).strip()


def toks(s):
    return re.findall(r"\w+", norm(s))


def f2(p, r):
    return 5 * p * r / (4 * p + r) if (p + r) > 0 and (4 * p + r) > 0 else 0.0


def covers(chunk, info, overlap=OVERLAP):
    """Chunk có chứa / overlap đủ với một phần thông tin không?"""
    if not info.strip():
        return False
    if norm(info) in norm(chunk):           # chứa nguyên văn
        return True
    it, ct = toks(info), set(toks(chunk))
    if not it:
        return False
    return sum(1 for t in it if t in ct) / len(it) >= overlap


def score_query(sub, gold, overlap=OVERLAP):
    """Trả (P_doc, R_doc, F2_doc, P_chunk, R_chunk, F2_chunk) cho một câu."""
    D, G = [str(d) for d in sub["relevant_docs"]], {str(d) for d in gold["relevant_docs"]}
    hit = len(set(D) & G)
    pd = hit / len(D) if D else 0.0
    rd = hit / len(G) if G else 0.0

    chunks, info = sub["relevant_chunks"], gold.get("info", [])
    if chunks and info:
        rel = sum(1 for c in chunks if any(covers(c["chunk_text"], i, overlap) for i in info))
        cov = sum(1 for i in info
                  if any(covers(c["chunk_text"], i, overlap) for c in chunks))
        pc, rc = rel / len(chunks), cov / len(info)
    else:
        pc = rc = 0.0
    return pd, rd, f2(pd, rd), pc, rc, f2(pc, rc)


def score(sub_records, gold_records, overlap=OVERLAP):
    """Trung bình macro, chỉ trên các câu CÓ nhãn vàng."""
    gold = {int(g["id"]): g for g in gold_records}
    sub = {int(s["id"]): s for s in sub_records}
    rows = [score_query(sub.get(qid, {"relevant_docs": [], "relevant_chunks": []}), g, overlap)
            for qid, g in gold.items()]
    if not rows:
        return None
    n = len(rows)
    keys = ["P_doc", "R_doc", "F2_doc", "P_chunk", "R_chunk", "F2_chunk"]
    return dict(zip(keys, [sum(r[i] for r in rows) / n for i in range(6)]), n=n)


def demo():
    """Self-check: các trường hợp biên và tính nhất quán của F2."""
    assert f2(0, 0) == 0 and f2(1, 1) == 1
    assert abs(f2(0.5, 0.5) - 0.5) < 1e-12
    # F2 nặng recall 4x: recall cao precision thấp phải hơn trường hợp ngược lại
    assert f2(0.2, 0.8) > f2(0.8, 0.2), "F2 phải ưu tiên recall"

    assert covers("bệnh viêm dạ dày trợt xung huyết mạn tính", "viêm dạ dày trợt")
    assert not covers("cách phòng ngừa sốt xuất huyết", "viêm dạ dày trợt xung huyết")
    assert covers("A B C D E F", "A B C")                   # overlap 3/3
    assert not covers("A B C D", "X Y Z W")
    assert not covers("bất kỳ", "")

    gold = [{"id": 1, "relevant_docs": ["1", "2"], "info": ["viêm dạ dày trợt xung huyết"]}]
    # Trả đúng 1/2 doc, chunk phủ được phần thông tin
    sub = [{"id": 1, "relevant_docs": ["1", "9"],
            "relevant_chunks": [{"doc_id": "1",
                                 "chunk_text": "bệnh viêm dạ dày trợt xung huyết mạn tính"}]}]
    m = score(sub, gold)
    assert m["P_doc"] == 0.5 and m["R_doc"] == 0.5, m
    assert m["P_chunk"] == 1.0 and m["R_chunk"] == 1.0, m
    # Khớp công thức rút gọn F2 = 5g/(4G+k): g=1, G=2, k=2 -> 5/(8+2) = 0.5
    assert abs(m["F2_doc"] - 5 * 1 / (4 * 2 + 2)) < 1e-12, m["F2_doc"]

    # Câu có nhãn nhưng bài nộp bỏ trống -> điểm 0, không được crash
    assert score([], gold)["F2_doc"] == 0.0
    print("demo OK")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sub", required=False, help="file .json của bài nộp")
    ap.add_argument("--gold", required=False, help="JSONL nhãn vàng (tập dev)")
    ap.add_argument("--cands", help="với --sweep: JSONL ứng viên để quét topk")
    ap.add_argument("--sweep", action="store_true", help="quét topk, in F2 từng mức")
    ap.add_argument("--overlap", type=float, default=OVERLAP)
    ap.add_argument("--demo", action="store_true")
    args = ap.parse_args()
    if args.demo:
        return demo()
    demo()
    if not args.gold:
        sys.exit("Cần --gold (tập dev có nhãn). Chưa có nhãn thì dùng leaderboard để đo.")

    gold = [json.loads(l) for l in open(args.gold, encoding="utf-8")]

    if args.sweep:
        if not args.cands:
            sys.exit("--sweep cần --cands")
        from submission import build, load_candidates
        cands = load_candidates(args.cands)
        print(f"{'topk':>6} {'P_doc':>7} {'R_doc':>7} {'F2_doc':>7}")
        best = (0, None)
        for k in (3, 5, 10, 20, 30, 50, 75, 100, 150, 200):
            m = score(build(cands, k, None, None, 1), gold, args.overlap)
            print(f"{k:>6} {m['P_doc']:>7.4f} {m['R_doc']:>7.4f} {m['F2_doc']:>7.4f}")
            if m["F2_doc"] > best[0]:
                best = (m["F2_doc"], k)
        print(f"\nTốt nhất: topk={best[1]}  F2_doc={best[0]:.4f}")
        print("Lưu ý: chọn ngưỡng ở vùng PHẲNG của đường cong, không lấy đỉnh nhọn "
              "- private test là câu hỏi mới.")
        return

    if not args.sub:
        sys.exit("Cần --sub")
    m = score(json.load(open(args.sub, encoding="utf-8")), gold, args.overlap)
    print(f"Chấm trên {m['n']} câu có nhãn vàng:\n")
    print(f"  Document:  P {m['P_doc']:.4f}  R {m['R_doc']:.4f}  F2 {m['F2_doc']:.4f}")
    print(f"  Chunk   :  P {m['P_chunk']:.4f}  R {m['R_chunk']:.4f}  F2 {m['F2_chunk']:.4f}")


if __name__ == "__main__":
    sys.exit(main())
