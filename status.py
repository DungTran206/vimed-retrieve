"""Kiểm crawl đang chạy hay đã chết, và chạy nhanh bao nhiêu. Chạy được trên cả hai máy.

Đọc DB chứ KHÔNG đọc log: `nohup python ... > file` làm stdout block-buffered nên log có thể
trống hàng phút dù crawl vẫn chạy bình thường. DB là sự thật duy nhất.

Lần chạy đầu chỉ in trạng thái; từ lần thứ hai in thêm **tốc độ thật** (so với lần trước).

  python status.py                        # toàn bộ
  python status.py --domain familydoctor  # chỉ domain khớp (so khớp chuỗi con)
  python status.py --watch 60             # tự lặp mỗi 60 giây
"""
import argparse
import json
import os
import re
import subprocess
import sqlite3
import sys
import time

DB = "data/corpus.sqlite"
SNAP = "data/.status_snapshot.json"
NAMES = {0: "chờ", 1: "xong", 2: "thất bại", 3: "bị chặn"}


def procs():
    """[(pid, elapsed, cpu%)] của các process crawler GỐC (bỏ process con của pool).

    Pool worker có cùng cmdline với process chính nên `grep | wc -l` ra 24 chứ không phải 1 -
    phải lọc theo ppid. Trên Windows dùng tasklist, không có ppid nên chỉ đếm.
    """
    if os.name == "nt":
        # `tasklist` không cho CommandLine nên nó đếm cả python của việc khác -> báo động
        # sai. Win32_Process có cả CommandLine và ParentProcessId, dùng được logic giống Linux.
        ps = ("Get-CimInstance Win32_Process -Filter \"Name like '%python%'\" | "
              "ForEach-Object { \"$($_.ProcessId) $($_.ParentProcessId) ? ? $($_.CommandLine)\" }")
        try:
            out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                                 capture_output=True, text=True, timeout=30).stdout
        except Exception:
            return []
    else:
        try:
            out = subprocess.run(["ps", "-eo", "pid,ppid,etime,pcpu,args"],
                                 capture_output=True, text=True, timeout=20).stdout
        except Exception:
            return []
    rows = []
    for line in out.splitlines():
        if "crawler.py" not in line or "grep" in line:
            continue
        f = line.split(None, 4)
        if len(f) >= 5:
            rows.append((f[0], f[1], f[2], f[3]))
    # Process GỐC = cái có ppid KHÔNG nằm trong tập pid crawler. Dùng `ppid == 1` là SAI:
    # `nohup ... &` chỉ cho ppid=1 SAU KHI shell khởi chạy đã thoát; shell còn sống thì
    # ppid là pid của shell -> báo "0 process" dù crawl vẫn chạy.
    pids = {r[0] for r in rows}
    return [(pid, et, cpu) for pid, ppid, et, cpu in rows if ppid not in pids]


def snapshot(db=DB, domain=None):
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    where, args = "", []
    if domain:
        where, args = " WHERE domain LIKE ?", [f"%{domain}%"]
    q = conn.execute(f"SELECT state, count(*) FROM queue{where} GROUP BY state", args)
    st = dict(q.fetchall())
    dwhere = " AND domain LIKE ?" if domain else ""
    n, b = conn.execute(f"SELECT count(*), coalesce(sum(length(body)),0) FROM doc "
                        f"WHERE length(body)>=200{dwhere}", args).fetchone()
    # Máy chỉ crawl thì chưa có bảng `chunk` (chunk.py chưa chạy) - không phải lỗi
    try:
        ch, = conn.execute("SELECT count(*) FROM chunk").fetchone()
    except sqlite3.OperationalError:
        ch = None
    conn.close()
    return {"t": time.time(), "state": {str(k): v for k, v in st.items()},
            "doc": n, "bytes": b, "chunk": ch}


def show(cur, prev, domain=None, snap_path=SNAP):
    tag = f" (domain ~ {domain})" if domain else ""
    print(f"=== Crawl{tag} ===")
    tot = sum(cur["state"].values())
    for k in sorted(cur["state"], key=int):
        n = cur["state"][k]
        d = n - prev["state"].get(k, n) if prev else 0
        delta = f"  {d:+,}" if d else ""
        print(f"  {NAMES.get(int(k), k):9} {n:>10,}{delta}")
    print(f"  {'tổng':9} {tot:>10,}")
    print(f"\n  doc dùng được {cur['doc']:>10,}"
          + (f"  {cur['doc']-prev['doc']:+,}" if prev else ""))
    print(f"  body          {cur['bytes']/1024**2:>9.0f} MB")
    ch = cur.get("chunk")
    print(f"  chunk         {ch:>10,}" if ch is not None
          else "  chunk          (chưa chạy chunk.py trên máy này)")

    if prev:
        dt = cur["t"] - prev["t"]
        dn = cur["doc"] - prev["doc"]
        if dt > 0:
            rate = dn / dt
            print(f"\n  TỐC ĐỘ: {rate:.1f} trang/s  (trong {dt/60:.1f} phút qua)")
            left = cur["state"].get("0", 0)
            if rate > 0.01 and left:
                print(f"  Còn {left:,} URL → ~{left/rate/3600:.1f} giờ")
            elif dn == 0:
                print("  ⚠️ KHÔNG tăng doc nào — crawl có thể đã chết hoặc bị chặn")
    else:
        print("\n  (lần đầu — chạy lại lệnh này sau vài phút để thấy tốc độ)")

    p = procs()
    print(f"\n=== Process crawler gốc: {len(p)} ===")
    for pid, et, cpu in p:
        print(f"  pid {pid}  chạy {et}  cpu {cpu}%")
    if not p:
        print("  ⚠️ KHÔNG có process nào — crawl đã dừng. Chạy lại là resume từ chỗ dừng.")
    elif len(p) > 1:
        print("  ⚠️ NHIỀU HƠN MỘT process cùng crawl → gửi trùng request, dễ bị chặn.")
        print("     Dừng hết rồi chạy lại một cái: pkill -f crawler.py")

    try:
        os.makedirs(os.path.dirname(snap_path) or ".", exist_ok=True)
        json.dump(cur, open(snap_path, "w"))
    except Exception as e:
        print(f"  (không lưu được snapshot: {e})")


def demo():
    """Self-check: đọc/ghi snapshot, tính tốc độ, lọc process gốc."""
    import tempfile
    conn = sqlite3.connect(":memory:")
    conn.executescript("""
      CREATE TABLE queue (doc_id TEXT, domain TEXT, state INT);
      CREATE TABLE doc (doc_id TEXT, domain TEXT, body TEXT);
      CREATE TABLE chunk (chunk_id INTEGER PRIMARY KEY);""")
    conn.executemany("INSERT INTO queue VALUES (?,?,?)",
                     [("1", "a.vn", 1), ("2", "a.vn", 0), ("3", "familydoctor.com.cn", 3)])
    conn.execute("INSERT INTO doc VALUES ('1','a.vn',?)", ("x" * 300,))
    conn.commit()

    # Tính tốc độ: 100 doc trong 50 giây = 2 trang/s
    prev = {"t": 1000.0, "state": {"1": 1}, "doc": 0, "bytes": 0, "chunk": 0}
    cur = {"t": 1050.0, "state": {"1": 101, "0": 3600}, "doc": 100, "bytes": 0, "chunk": 0}
    assert (cur["doc"] - prev["doc"]) / (cur["t"] - prev["t"]) == 2.0

    with tempfile.TemporaryDirectory() as d:
        sp = os.path.join(d, "snap.json")
        import contextlib
        import io as _io
        with contextlib.redirect_stdout(_io.StringIO()) as buf:
            show(cur, prev, snap_path=sp)
        out = buf.getvalue()
        assert "2.0 trang/s" in out, out
        assert "Còn 3,600 URL" in out, out
        assert os.path.exists(sp), "phải lưu snapshot để lần sau tính được tốc độ"
        assert json.load(open(sp))["doc"] == 100

        # dn == 0 -> phải CẢNH BÁO
        with contextlib.redirect_stdout(_io.StringIO()) as buf2:
            show(dict(cur, t=2000.0), cur, snap_path=sp)
        assert "KHÔNG tăng doc nào" in buf2.getvalue()

        # Không có prev -> không crash, nói rõ là lần đầu
        with contextlib.redirect_stdout(_io.StringIO()) as buf3:
            show(cur, None, snap_path=sp)
        assert "lần đầu" in buf3.getvalue()

        # Lọc process gốc: pool worker có ppid = pid của process chính nên phải bị loại.
        # Và process chính KHÔNG nhất thiết có ppid == 1 (shell còn sống thì ppid = shell).
        import unittest.mock as _mk
        fake = "\n".join([
            "  PID  PPID ELAPSED %CPU COMMAND",
            "  100  9999 05:00 240 python crawler.py --domains x",   # chính, ppid = shell
            "  101   100 05:00  10 python crawler.py --domains x",   # con của pool
            "  102   100 05:00  10 python crawler.py --domains x",
            "  200     1 01:00  90 python crawler.py --shard 0/3",   # chính thứ hai
            "  999   500 00:10   0 grep crawler.py",                 # phải bỏ
        ])

        class _R:
            stdout = fake

        with _mk.patch("subprocess.run", return_value=_R()), _mk.patch("os.name", "posix"):
            got = procs()
        assert sorted(x[0] for x in got) == ["100", "200"], got

        # Định dạng Windows (PowerShell) phải đi qua cùng đường lọc, và KHÔNG đếm
        # python của việc khác
        win = "\n".join([
            "100 9999 ? ? python crawler.py --domains x",
            "101 100 ? ? python crawler.py --domains x",
            "300 9999 ? ? python chunk.py",          # việc khác -> phải bỏ
            "301 9999 ? ? python -c import torch",   # việc khác -> phải bỏ
        ])

        class _W:
            stdout = win

        with _mk.patch("subprocess.run", return_value=_W()), _mk.patch("os.name", "nt"):
            gotw = procs()
        assert [x[0] for x in gotw] == ["100"], gotw

        # Máy chỉ crawl: không có bảng `chunk` -> phải chạy được, không crash
        c2 = sqlite3.connect(":memory:")
        c2.executescript("CREATE TABLE queue (doc_id TEXT, domain TEXT, state INT);"
                         "CREATE TABLE doc (doc_id TEXT, domain TEXT, body TEXT);")
        c2.execute("INSERT INTO queue VALUES ('1','a.vn',1)")
        c2.commit()
        import unittest.mock as _m
        with _m.patch("sqlite3.connect", return_value=c2):
            snp = snapshot()
        assert snp["chunk"] is None, snp
        with contextlib.redirect_stdout(_io.StringIO()) as buf4:
            show(snp, None, snap_path=sp)
        assert "chưa chạy chunk.py" in buf4.getvalue()
    print("demo OK")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DB)
    ap.add_argument("--domain", default=None)
    ap.add_argument("--watch", type=int, default=0, metavar="GIAY")
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    if a.demo:
        return demo()
    snap = f"{SNAP}.{a.domain}" if a.domain else SNAP
    prev = None
    if os.path.exists(snap):
        try:
            prev = json.load(open(snap))
        except Exception:
            prev = None
    while True:
        show(snapshot(a.db, a.domain), prev, a.domain, snap)
        if not a.watch:
            return 0
        prev = json.load(open(snap))
        time.sleep(a.watch)
        print()


if __name__ == "__main__":
    sys.exit(main())
