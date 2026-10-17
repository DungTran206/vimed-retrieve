"""Xuất TOÀN BỘ doc vi (body >= 200 ký tự, đã clean) từ store sống ra sqlite gọn cho bm25.py / bm25_ent.py chạy trên máy GPU.
    python export_vi_full.py --store data/corpus_new.sqlite --out data/vi_full.sqlite"""
import argparse
import sqlite3
import sys
import time


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", default="data/corpus_new.sqlite")
    ap.add_argument("--out", default="data/vi_full.sqlite")
    a = ap.parse_args()
    src = sqlite3.connect(f"file:{a.store}?mode=ro", uri=True, timeout=120)
    dst = sqlite3.connect(a.out)
    dst.execute("DROP TABLE IF EXISTS doc")
    dst.execute("CREATE TABLE doc (doc_id TEXT, lang TEXT, title TEXT, descr TEXT, tags TEXT, body TEXT)")
    t0, n, batch = time.time(), 0, []
    for row in src.execute("SELECT doc_id, lang, title, descr, tags, body FROM doc "
                           "WHERE lang='vi' AND length(coalesce(body,''))>=200"):
        batch.append(row); n += 1
        if len(batch) >= 5000:
            dst.executemany("INSERT INTO doc VALUES (?,?,?,?,?,?)", batch); batch = []
            if n % 100000 == 0:
                print(f"  {n:,} doc | {time.time()-t0:.0f}s", flush=True)
    dst.executemany("INSERT INTO doc VALUES (?,?,?,?,?,?)", batch)
    dst.execute("CREATE INDEX IF NOT EXISTS ix_doc ON doc(doc_id)")
    dst.commit()
    print(f"-> {a.out}: {n:,} doc vi")


if __name__ == "__main__":
    sys.exit(main())
