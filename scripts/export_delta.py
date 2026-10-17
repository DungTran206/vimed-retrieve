"""Xuất doc vi MỚI (có body, chưa có vector trong emb_vi2) từ store ra sqlite nhỏ để embed trên máy GPU.

    python export_delta.py --store data/corpus_new.sqlite --emb data/emb_vi2 --out data/vi_text_delta2.sqlite
Chạy SAU `clean.py --apply` (body đã sạch). Chỉ đọc store; ghi file mới.
"""
import argparse
import json
import sqlite3
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", default="data/corpus_new.sqlite")
    ap.add_argument("--emb", default="data/emb_vi2")
    ap.add_argument("--out", default="data/vi_text_delta2.sqlite")
    ap.add_argument("--min-body", type=int, default=200)
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    have = {str(d) for d in json.load(open(a.emb + ".ids.json"))}
    src = sqlite3.connect(f"file:{a.store}?mode=ro", uri=True, timeout=60)
    dst = sqlite3.connect(a.out)
    dst.execute("DROP TABLE IF EXISTS doc")
    dst.execute("CREATE TABLE doc (doc_id TEXT PRIMARY KEY, title TEXT, body TEXT)")
    n = 0
    # chỉ doc vi: lang='vi' (zh nằm ở store GPU, không đưa vào đây)
    cur = src.execute("SELECT doc_id, title, body FROM doc WHERE lang='vi' AND length(coalesce(body,''))>=?", (a.min_body,))
    batch = []
    for d, t, b in cur:
        if str(d) in have:
            continue
        batch.append((str(d), t or "", b)); n += 1
        if len(batch) >= 5000:
            dst.executemany("INSERT OR IGNORE INTO doc VALUES (?,?,?)", batch); batch = []
    dst.executemany("INSERT OR IGNORE INTO doc VALUES (?,?,?)", batch)
    dst.commit()
    print(f"-> {a.out}: {n} doc mới (chưa có vector trong {a.emb})")


if __name__ == "__main__":
    sys.exit(main())
