"""Dựng store gọn chỉ gồm doc thuộc KHO MỚI của BTC (links_corpus_vi_en_zh.parquet) + vinmec.com
(nhãn vi cũ còn hiệu lực). SAO CHÉP, không sửa store nguồn. Bỏ bảng chunk_t400/chunk_t900 cũ và raw_html.
    python make_store_new.py [NGUỒN] [ĐÍCH]      mặc định data/corpus_vifull.sqlite -> data/corpus_new.sqlite
Sau khi dựng: dựng lại bài tốt nhất từ store mới và so vân tay doc/chunk (phải y hệt).
"""
import os
import sqlite3
import sys

import pandas as pd

src, dst = (sys.argv[1:3] + ["data/corpus_vifull.sqlite", "data/corpus_new.sqlite"][len(sys.argv[1:3]):])
assert not os.path.exists(dst), f"{dst} đã tồn tại - xoá tay nếu muốn dựng lại"
keep = set(pd.read_parquet("data/vibiomir_new/links_corpus_vi_en_zh.parquet")["id"].astype(str))

c = sqlite3.connect(dst)
c.execute("PRAGMA journal_mode=OFF"); c.execute("PRAGMA synchronous=OFF")
c.execute("ATTACH DATABASE ? AS s", (src,))
schema = {n: q for n, q in c.execute("SELECT name, sql FROM s.sqlite_master WHERE sql IS NOT NULL")}
for t in ("doc", "queue", "chunk", "boilerplate"):
    c.execute(schema[t])
keep |= {d for (d,) in c.execute("SELECT doc_id FROM s.doc WHERE domain='vinmec.com'")}
c.execute("CREATE TEMP TABLE k(doc_id TEXT PRIMARY KEY)")
c.executemany("INSERT INTO k VALUES (?)", ((d,) for d in keep))
cols = [r[1] for r in c.execute("PRAGMA s.table_info(doc)")]
sel = ",".join("NULL" if x == "raw_html" else f"d.{x}" for x in cols)
c.execute(f"INSERT INTO doc ({','.join(cols)}) SELECT {sel} FROM s.doc d JOIN k USING(doc_id)")
c.execute("INSERT INTO queue SELECT q.* FROM s.queue q JOIN k USING(doc_id)")
c.execute("INSERT INTO chunk SELECT x.* FROM s.chunk x JOIN k USING(doc_id)")
c.execute("INSERT INTO boilerplate SELECT * FROM s.boilerplate")
c.commit()
for n, q in schema.items():                      # index của 4 bảng giữ lại (trừ autoindex, không có sql)
    if n.startswith(("q_", "d_", "ch_")):
        c.execute(q)
c.commit()
for t in ("doc", "queue", "chunk"):
    print(t, f"{c.execute(f'SELECT count(*) FROM {t}').fetchone()[0]:,}")
print("doc có body >=200:", f"{c.execute('SELECT count(*) FROM doc WHERE length(body)>=200').fetchone()[0]:,}")
