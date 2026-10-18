"""Lưới an toàn cuối: bỏ khỏi danh sách mọi doc ngoài kho mới (parquet 1,19M), TRỪ vinmec.com (nhãn vi cũ còn hiệu lực), rồi bù đủ 200 doc từ danh sách sâu hơn.
    python crawl/filter_new_corpus.py in.jsonl deeper.jsonl out.jsonl      (in = 200 doc đã có thứ tự đầu; deeper = danh sách sâu để bù)"""
import json, sqlite3, sys
import pandas as pd
inp, deep, out = sys.argv[1:4]
new = set(pd.read_parquet("data/vibiomir_new/links_corpus_vi_en_zh.parquet")["id"].astype(str))
def L(p): return {json.loads(l)["id"]: [str(c["doc_id"]) for c in json.loads(l)["candidates"]] for l in open(p, encoding="utf-8")}
A, D = L(inp), L(deep)
c = sqlite3.connect("file:data/corpus_new.sqlite?mode=ro", uri=True, timeout=120)
ids = sorted({d for q in A for d in A[q]} | {d for q in D for d in D[q]}); vin = set()
for i in range(0, len(ids), 900):
    p = ids[i:i + 900]
    vin |= {str(d) for (d,) in c.execute(f"select doc_id from doc where domain='vinmec.com' and doc_id in ({','.join('?' * len(p))})", p)}
keep = lambda d: d in new or d in vin
drop = add = 0
with open(out, "w", encoding="utf-8") as o:
    for q in sorted(A):
        lst = [d for d in A[q] if keep(d)]; drop += len(A[q]) - len(lst); s = set(lst); n0 = len(lst)
        for d in D[q]:
            if len(lst) >= 200: break
            if keep(d) and d not in s: lst.append(d); s.add(d)
        add += len(lst) - n0
        o.write(json.dumps({"id": q, "candidates": [{"doc_id": d, "score": round(1 - i / (len(lst) + 1), 6)} for i, d in enumerate(lst)]}) + "\n")
print(f"bỏ {drop / len(A):.2f} doc/câu ngoài kho mới (trừ vinmec), bù {add / len(A):.2f}")
