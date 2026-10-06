"""Báo cáo sức khoẻ crawl (CHỈ ĐỌC): từng domain đang chạy đạt bao nhiêu % rate cấu hình.

Lý do tồn tại: hơn mười lỗi của crawler (khoá, đói luồng, phạt ghim sàn...) đều lộ ra bằng cách
đo tay tốc độ từng domain rồi so với rate cấu hình, mỗi lần mất cả buổi. Tiêu chí nghiệm thu:
**một domain chạy dưới 50% rate cấu hình trong khi còn việc là CÓ LỖI**, phải cảnh báo ngay.

    python crawl_health.py                       # đọc data/corpus.sqlite
    python crawl_health.py --db data/queue_zh.sqlite --shard 2/5
"""
import argparse
import sqlite3
import subprocess
import sys
import time

import crawler

DOMAINS = ("cnkang.com,120ask.com,ask.39.net,a-hospital.com,zhongyibaodian.net,zydcd.com,"
           "wujue.com,youlai.cn,qihuangzhishu.com,jb39.com,test.pmphai.com")


def main_processes():
    """[(pid, giây đã chạy)] của các crawler CHÍNH (cha không phải crawler). Chỉ Linux/Mac."""
    try:
        out = subprocess.check_output(["ps", "-eo", "pid,ppid,etimes,args"], text=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    rows = [l.split(None, 3) for l in out.splitlines()[1:] if "crawler.py" in l and "grep" not in l
            and "crawl_health" not in l]
    pids = {r[0] for r in rows}
    return [(r[0], int(r[2])) for r in rows if r[1] not in pids]


def report(db, shard, domains, window=None):
    flags = []
    mains = main_processes()
    if mains is None:
        secs = window or 600
        print("(không đọc được danh sách tiến trình trên máy này, dùng cửa sổ cố định)")
    else:
        print(f"crawler chính đang chạy: {len(mains)}  {[p for p, _ in mains]}")
        if len(mains) != 1:
            flags.append(f"có {len(mains)} crawler chính, cần ĐÚNG 1 (trùng việc, gấp đôi tải)")
        secs = window or (min(s for _, s in mains) if mains else 600)
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    since = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time() - secs))
    last, = conn.execute("SELECT max(fetched) FROM doc").fetchone()
    age = time.time() - time.mktime(time.strptime(last, "%Y-%m-%d %H:%M:%S")) + time.timezone \
        if last else None
    if mains and age is not None and age > 180:
        flags.append(f"không ghi doc nào trong {age/60:.0f} phút (crawler đứng?)")
    doms = domains.split(",")
    qs = ",".join("?" * len(doms))
    sh, sa = "", ()
    if shard:
        i, n = (int(x) for x in shard.split("/"))
        sh, sa = " AND CAST(doc_id AS INTEGER) % ? = ?", (n, i)
    got = {d: (n, ok) for d, n, ok in conn.execute(
        f"SELECT domain, count(*), sum(length(ifnull(body,''))>=200) FROM doc "
        f"WHERE fetched>=? AND domain IN ({qs}){sh} GROUP BY domain", (since, *doms, *sa))}
    pend = {d: n for d, n in conn.execute(
        f"SELECT domain, count(*) FROM queue WHERE state=0 AND domain IN ({qs}){sh} GROUP BY domain",
        (*doms, *sa))}
    print(f"cửa sổ đo: {secs/60:.0f} phút\n")
    print(f"{'domain':20} {'cấu hình':>8} {'đo được':>8} {'đạt':>5} {'dùng được':>9} {'còn chờ':>9} {'còn ~giờ':>9}")
    for d in sorted(pend, key=lambda x: -pend[x]):
        n, ok = got.get(d, (0, 0))
        cfg = crawler.RATES.get(d, crawler.DEFAULT_RATE)
        rate = n / secs
        pct = rate / cfg * 100
        eta = pend[d] / rate / 3600 if rate > 0 else float("inf")
        use = ok / n * 100 if n else 0.0
        mark = ""
        if pend[d] > 500 and pct < 50:
            mark = "  <-- DƯỚI 50% RATE CẤU HÌNH"
            flags.append(f"{d} chỉ đạt {pct:.0f}% rate cấu hình ({rate:.2f}/{cfg} doc/s)")
        if n >= 50 and use < 70:
            mark += "  <-- DÙNG ĐƯỢC < 70%"
            flags.append(f"{d} chỉ {use:.0f}% dùng được")
        print(f"{d:20} {cfg:>8g} {rate:>8.2f} {pct:>4.0f}% {use:>8.0f}% {pend[d]:>9,} {eta:>9.1f}{mark}")
    print()
    if flags:
        print("CẢNH BÁO:")
        for f in flags:
            print("  -", f)
    else:
        print("OK: mọi domain còn việc đều đạt >= 50% rate cấu hình, một crawler duy nhất, có ghi doc.")
    return flags


def demo():
    """Self-check: phát hiện đúng domain chạy dưới 50% và nhiều crawler."""
    import os
    import tempfile
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
        db = os.path.join(d, "t.sqlite")
        c = crawler.open_db(db)
        now = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        for i in range(2000):
            c.execute("INSERT INTO queue VALUES (?,?,?,?,0)", (str(i), f"u{i}", "cnkang.com", 0.0))
        for i in range(30):                                     # cnkang: chỉ 30 doc / 600s = 0,05/s
            c.execute("INSERT INTO doc (doc_id,url,domain,body,fetched) VALUES (?,?,?,?,?)",
                      (f"d{i}", f"u{i}", "cnkang.com", "x" * 300, now))
        c.commit(); c.close()
        flags = report(db, None, "cnkang.com", window=600)
        assert any("cnkang.com chỉ đạt" in f for f in flags), flags
    print("demo OK")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/corpus.sqlite")
    ap.add_argument("--shard", default=None, metavar="I/N")
    ap.add_argument("--domains", default=DOMAINS)
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    if a.demo:
        demo()
    else:
        sys.exit(1 if report(a.db, a.shard, a.domains) else 0)
