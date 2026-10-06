"""Chạy crawl tiếng Trung cho đồng đội: tải về là chạy.

    python chay.py 2 5       # LẦN ĐẦU: bạn là phần số 2 trong 5 phần (I=2, N=5)
    python chay.py           # các lần sau: tự chạy tiếp đúng phần đã nhận
    python chay.py status    # xem tiến độ phần của bạn

Script tự lo: cài thư viện còn thiếu, giải nén danh sách URL, kiểm tra mạng, chạy crawler với
tham số đã đo (KHÔNG chỉnh được rate/luồng ở đây, cố ý), và nén kết quả để gửi lại khi xong.
Phần đã nhận được lưu lại: chạy lần sau với I/N khác sẽ bị từ chối, vì đổi giữa chừng nghĩa
là crawl sang phần của người khác (trùng và phí).
"""
import gzip
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import time

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join("data", "queue_zh.sqlite")
GZ = "queue_zh.sqlite.gz"
ASSIGN = os.path.join("data", "assignment.json")
PROBE_OK = os.path.join("data", "probe_ok.txt")
LOG = "crawl.log"
PACKAGES = {"requests": "requests", "curl_cffi": "curl_cffi", "trafilatura": "trafilatura",
            "lxml": "lxml"}
# Danh sách domain CỐ ĐỊNH: loại 14 domain *.39.net bị CAPTCHA (kéo vào là crawl tụt về 0 trang/s)
DOMAINS = ("cnkang.com,120ask.com,ask.39.net,a-hospital.com,zhongyibaodian.net,zydcd.com,"
           "wujue.com,youlai.cn,qihuangzhishu.com,jb39.com,test.pmphai.com")
CRAWL_ARGS = ["--workers", "40", "--procs", "4", "--batch", "1000"]


def ensure_packages():
    missing = []
    for mod, pkg in PACKAGES.items():
        try:
            __import__(mod)
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"Cài thư viện còn thiếu: {', '.join(missing)} ...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", *missing])


def ensure_store():
    if os.path.exists(DB):
        return
    if not os.path.exists(GZ):
        sys.exit(f"Thiếu {GZ} và {DB}. Giải nén đủ gói zip vào cùng thư mục với chay.py.")
    os.makedirs("data", exist_ok=True)
    print(f"Giải nén {GZ} -> {DB} (lần đầu, ~270 MB) ...")
    tmp = DB + ".tmp"
    with gzip.open(GZ, "rb") as f, open(tmp, "wb") as o:
        shutil.copyfileobj(f, o, 1 << 22)
    os.replace(tmp, DB)             # đổi tên nguyên tử: ngắt giữa chừng không để lại file hỏng


def load_assignment(args):
    """Trả (I, N). Từ chối nếu đổi phần so với lần đầu."""
    saved = None
    if os.path.exists(ASSIGN):
        with open(ASSIGN) as f:
            saved = json.load(f)
    if len(args) == 2:
        try:
            i, n = int(args[0]), int(args[1])
        except ValueError:
            sys.exit("Dùng: python chay.py I N   (hai số nguyên, vd. python chay.py 2 5)")
        if not (n >= 1 and 0 <= i < n):
            sys.exit(f"I={i}, N={n} không hợp lệ: cần 0 <= I < N.")
        if saved and (saved["i"], saved["n"]) != (i, n):
            sys.exit(f"DỪNG: máy này đã nhận phần {saved['i']}/{saved['n']}, bạn đang gõ {i}/{n}.\n"
                     f"Đổi phần giữa chừng là crawl sang phần của người khác (trùng và phí).\n"
                     f"Muốn chạy tiếp phần cũ thì gõ: python chay.py")
        return i, n
    if len(args) == 0:
        if not saved:
            sys.exit("Lần đầu cần cho biết phần được giao, vd:  python chay.py 2 5")
        return saved["i"], saved["n"]
    sys.exit("Dùng: python chay.py I N   |   python chay.py   |   python chay.py status")


def save_assignment(i, n):
    os.makedirs("data", exist_ok=True)
    with open(ASSIGN, "w") as f:
        json.dump({"i": i, "n": n}, f)


def progress(i, n, db=DB):
    """{'cho','xong','that_bai','tong'} của phần I/N trong các domain an toàn."""
    doms = DOMAINS.split(",")
    qs = ",".join("?" * len(doms))
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        rows = c.execute(
            f"SELECT state, count(*) FROM queue WHERE domain IN ({qs}) "
            f"AND CAST(doc_id AS INTEGER) % ? = ? GROUP BY state", (*doms, n, i)).fetchall()
    finally:
        c.close()
    d = {s: k for s, k in rows}
    out = {"cho": d.get(0, 0), "xong": d.get(1, 0), "that_bai": d.get(2, 0)}
    out["tong"] = sum(out.values())
    return out


def show_status(i, n):
    p = progress(i, n)
    pct = p["xong"] / p["tong"] * 100 if p["tong"] else 100.0
    print(f"Phần {i}/{n}: {p['xong']:,}/{p['tong']:,} URL xong ({pct:.1f}%) | "
          f"còn {p['cho']:,} | thất bại {p['that_bai']:,}")


def run_probe():
    if os.path.exists(PROBE_OK):
        return
    sys.path.insert(0, HERE)
    import probe_zh
    print("Kiểm tra mạng (1-2 phút, chỉ lần đầu) ...")
    if not probe_zh.main():
        sys.exit("\nMạng này chưa crawl được cả 4 domain. KHÔNG chạy tiếp: chụp màn hình kết quả "
                 "ở trên gửi lại cho người giao việc.")
    with open(PROBE_OK, "w") as f:
        f.write(time.strftime("%Y-%m-%d %H:%M:%S\n"))


def run_crawler(i, n):
    cmd = [sys.executable, "-u", "crawler.py", "--db", DB, "--domains", DOMAINS,
           "--shard-ids", f"{i}/{n}", *CRAWL_ARGS]
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    print(f"\nChạy crawl phần {i}/{n}. Nhật ký lưu ở {LOG}. Dừng: bấm Ctrl+C MỘT lần rồi chờ.\n")
    with open(LOG, "ab") as log:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
        try:
            for line in p.stdout:
                log.write(line)
                log.flush()
                sys.stdout.buffer.write(line)
                sys.stdout.buffer.flush()
        except KeyboardInterrupt:
            print("\nĐang dừng: chờ crawler ghi nốt phần còn trong hàng đợi (có thể ~1 phút). "
                  "ĐỪNG bấm Ctrl+C nữa ...")
        while True:
            try:
                p.wait()
                break
            except KeyboardInterrupt:
                print("(vẫn đang ghi nốt, chờ thêm ...)")
    return p.returncode


def finish(i, n):
    """Hết URL của phần mình thì nén kết quả để gửi."""
    p = progress(i, n)
    if p["cho"] > 0:
        print(f"\nCòn {p['cho']:,} URL. Chạy lại `python chay.py` để tiếp tục.")
        return
    out = f"queue_zh_{i}_of_{n}.sqlite.gz"
    print(f"\nXONG phần {i}/{n}. Nén kết quả -> {out} ...")
    with open(DB, "rb") as f, gzip.open(out, "wb", compresslevel=6) as o:
        shutil.copyfileobj(f, o, 1 << 22)
    print(f"GỬI LẠI FILE NÀY: {out} ({os.path.getsize(out)/1e6:.0f} MB)")


def demo():
    """Self-check offline: chia phần, từ chối đổi phần, giải nén nguyên tử, đếm tiến độ."""
    import tempfile
    here = os.getcwd()
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
        os.chdir(d)
        try:
            os.makedirs("data")
            db = sqlite3.connect(DB)
            db.execute("CREATE TABLE queue (doc_id TEXT, url TEXT, domain TEXT, prio REAL, state INT)")
            rows = [(str(k), f"http://x/{k}", "cnkang.com", 0.0, 1 if k % 7 == 0 else 0)
                    for k in range(100)]
            db.executemany("INSERT INTO queue VALUES (?,?,?,?,?)", rows)
            db.commit(); db.close()
            # N phần phải phủ đủ và không chồng lấn
            tot = sum(progress(i, 5)["tong"] for i in range(5))
            assert tot == 100, f"5 phần phải cộng đủ 100 URL, đang {tot}"
            p0 = progress(0, 5)
            assert p0["tong"] == 20 and p0["xong"] == len([k for k in range(0, 100, 5) if k % 7 == 0])
            # nhận phần lần đầu, rồi từ chối đổi phần
            assert load_assignment(["2", "5"]) == (2, 5)
            save_assignment(2, 5)
            assert load_assignment([]) == (2, 5), "chạy lại không tham số phải dùng phần đã nhận"
            assert load_assignment(["2", "5"]) == (2, 5)
            for bad in (["3", "5"], ["2", "3"]):
                try:
                    load_assignment(bad)
                    raise AssertionError(f"phải từ chối đổi phần {bad}")
                except SystemExit:
                    pass
            try:
                load_assignment(["5", "5"])
                raise AssertionError("I=N không hợp lệ")
            except SystemExit:
                pass
            # giải nén: tạo gz, xoá db, ensure_store phải dựng lại đúng
            with open(DB, "rb") as f, gzip.open(GZ, "wb") as o:
                shutil.copyfileobj(f, o)
            size = os.path.getsize(DB)
            os.remove(DB)
            ensure_store()
            assert os.path.getsize(DB) == size and not os.path.exists(DB + ".tmp")
        finally:
            os.chdir(here)
    print("demo OK")


def main():
    os.chdir(HERE)
    args = sys.argv[1:]
    if args == ["demo"]:
        return demo()
    ensure_packages()
    ensure_store()
    if args == ["status"]:
        i, n = load_assignment([])
        return show_status(i, n)
    i, n = load_assignment(args)
    save_assignment(i, n)
    run_probe()
    show_status(i, n)
    rc = run_crawler(i, n)
    if rc not in (0, None):
        print(f"\nCrawler thoát với mã {rc}. Gửi {LOG} cho người giao việc nếu không hiểu lỗi.")
    show_status(i, n)
    finish(i, n)


if __name__ == "__main__":
    main()
