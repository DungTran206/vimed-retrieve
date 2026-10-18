"""Ghép: TẬP doc top-K của danh sách base + THỨ TỰ N doc đầu của danh sách alt (hai tầng chấm độc lập: doc theo tập, chunk theo đầu danh sách).
    python index/hybrid_cands.py base.jsonl alt.jsonl N out.jsonl [K=200]
Điểm ra giảm đều theo vị trí (submission.load_candidates sắp lại theo điểm)."""
import json
import sys


def load(p):
    return {json.loads(l)["id"]: [str(c["doc_id"]) for c in json.loads(l)["candidates"]] for l in open(p, encoding="utf-8")}


def main():
    base, alt, n, out = load(sys.argv[1]), load(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    k = int(sys.argv[5]) if len(sys.argv) > 5 else 200
    lost = 0
    with open(out, "w", encoding="utf-8") as o:
        for q in sorted(base):
            S = base[q][:k]; SS = set(S)
            head = [d for d in alt[q][:n * 2] if d in SS][:n]          # alt xếp trong tập base
            lost += n - len(head)
            hs = set(head); order = head + [d for d in S if d not in hs]
            o.write(json.dumps({"id": q, "candidates": [{"doc_id": d, "score": round(1 - i / (len(order) + 1), 6)}
                                                        for i, d in enumerate(order)]}, ensure_ascii=False) + "\n")
    print(f"-> {out} | doc đầu của alt không nằm trong tập base: {lost / len(base):.1f}/câu (đã thay bằng doc kế tiếp của alt)")


if __name__ == "__main__":
    sys.exit(main())
