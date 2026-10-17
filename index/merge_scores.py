"""Hợp điểm Qwen từ nhiều file (cùng thang Qwen-4B, P(yes)); trùng doc thì lấy max; sắp giảm dần mỗi câu.
    python merge_scores.py data/qwen_all_g.jsonl data/qwen_all.jsonl data/qwen_g.jsonl [data/qwen_g2.jsonl ...]
"""
import json
import sys


def load(p):
    return {json.loads(l)["id"]: {str(c["doc_id"]): c["score"] for c in json.loads(l)["candidates"]}
            for l in open(p, encoding="utf-8")}


def main():
    out, ins = sys.argv[1], sys.argv[2:]
    assert ins, "cần ít nhất một file đầu vào"
    srcs = [load(p) for p in ins]
    ids = sorted(set().union(*[set(s) for s in srcs]))
    dup = 0
    with open(out, "w", encoding="utf-8") as o:
        for q in ids:
            d = {}
            for s in srcs:
                for k, v in s.get(q, {}).items():
                    if k in d:
                        dup += 1
                    d[k] = max(d.get(k, -1.0), v)
            c = sorted(d.items(), key=lambda x: -x[1])
            o.write(json.dumps({"id": q, "candidates": [{"doc_id": k, "score": v} for k, v in c]}, ensure_ascii=False) + "\n")
    print(f"-> {out}: {len(ids)} câu | doc trùng giữa các file: {dup}")


if __name__ == "__main__":
    sys.exit(main())
