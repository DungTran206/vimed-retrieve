"""Gộp doc zh của kho mới (240k) từ các store crawl rời vào store sống `corpus_new.sqlite`.

Khác `crawler.py --merge` (INSERT OR IGNORE: dòng lỗi cũ chặn mất bản crawl thành công):
- chỉ lấy doc thuộc zh kho mới, body >= 200 ký tự, tỉ lệ chữ Hán >= 0,3 (lọc mojibake/nhận nhầm);
- chỉ ghi khi store đích CHƯA có body dùng được (INSERT OR REPLACE dòng lỗi cũ);
- gán lang='zh', đặt queue.state = DONE; ghi danh sách doc mới vào data/zh_new_ids.json.
    python merge_zh_new.py data/zh_missing.sqlite C:/Users/.../queue_zh2.sqlite ...
    python merge_zh_new.py --demo
"""
import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawl import crawler

HAN = re.compile(r"[\u4e00-\u9fff]")
LETTER = re.compile(r"[\u4e00-\u9fffA-Za-z\u00c0-\u1ef9]")
COLS = ["doc_id", "url", "domain", "lang", "status", "err", "via", "title", "descr", "tags",
        "pub_date", "body", "raw_html", "simhash", "fetched"]


def han_ratio(text):
    s = text[:2000]
    n = len(LETTER.findall(s))
    return len(HAN.findall(s)) / n if n else 0.0


def merge(dst, sources, want):
    have = set()
    ids = list(want)
    for i in range(0, len(ids), 900):
        p = ids[i:i + 900]
        have.update(d for (d,) in dst.execute(
            f"SELECT doc_id FROM doc WHERE doc_id IN ({','.join('?' * len(p))}) AND length(body) >= 200", p))
    added, bad = [], 0
    for path in sources:
        src = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        n0 = len(added)
        for row in src.execute(f"SELECT {','.join(COLS)} FROM doc WHERE length(body) >= 200"):
            d = str(row[0])
            if d not in want or d in have:
                continue
            if han_ratio((row[7] or "") + "\n" + row[11]) < 0.3:
                bad += 1
                continue
            r = list(row); r[0] = d; r[3] = "zh"; r[12] = None          # bỏ raw_html cho nhẹ
            dst.execute(f"INSERT OR REPLACE INTO doc ({','.join(COLS)}) VALUES ({','.join('?' * len(COLS))})", r)
            dst.execute("UPDATE queue SET state=? WHERE doc_id=?", (crawler.DONE, d))
            have.add(d); added.append(d)
        src.close()
        print(f"{path}: +{len(added) - n0:,}", flush=True)
    dst.commit()
    print(f"Tổng +{len(added):,} doc zh | loại vì tỉ lệ chữ Hán < 0,3: {bad:,}")
    return added


def demo():
    import os, tempfile
    dst = crawler.open_db(":memory:")
    fd, src_path = tempfile.mkstemp(suffix=".sqlite"); os.close(fd)
    src = crawler.open_db(src_path)
    rows = [("1", "健康问答内容" * 50), ("2", "Bai viet tieng Viet " * 30), ("3", "肝炎的症状" * 60), ("4", "x" * 300)]
    for d, b in rows:
        src.execute("INSERT INTO doc (doc_id, body, lang) VALUES (?,?,'vi')", (d, b))
    src.commit()
    dst.execute("INSERT INTO doc (doc_id, status, err) VALUES ('3', 403, 'captcha')")  # dòng lỗi cũ không được chặn
    dst.execute("INSERT INTO queue VALUES ('3','u','d',0,2)")
    added = merge(dst, [src_path], {"1", "2", "3"})
    src.close(); os.remove(src_path)
    assert sorted(added) == ["1", "3"], added                     # 2: không phải zh; 4: ngoài kho mới
    assert dst.execute("SELECT lang, length(body) FROM doc WHERE doc_id='3'").fetchone() == ("zh", 300)
    assert dst.execute("SELECT state FROM queue WHERE doc_id='3'").fetchone()[0] == crawler.DONE
    print("demo OK")


if __name__ == "__main__":
    if sys.argv[1:] == ["--demo"]:
        demo(); sys.exit()
    want = {d for d, _, _ in json.load(open("data/zh_missing_ids.json"))}
    import pandas as pd
    N = pd.read_parquet("data/vibiomir_new/links_corpus_vi_en_zh.parquet")
    want |= set(N[N["url"].map(lambda u: crawler.is_zh_domain(crawler.domain_of(u)))]["id"].astype(str))
    dst = sqlite3.connect(crawler.DB, timeout=120)
    added = merge(dst, sys.argv[1:], want)
    json.dump(added, open("data/zh_new_ids.json", "w"))
