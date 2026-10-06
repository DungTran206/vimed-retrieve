"""Chạy cả chuỗi xử lý dữ liệu bằng một lệnh, từ store đã crawl đến file ZIP nộp bài.

    crawler.py  →  clean.py  →  chunk.py  →  audit.py  →  bm25.py ×2  →  fuse.py  →  submission.py
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                        file này lo phần này

Ba điều nó bảo đảm, mỗi điều đến từ một lỗi đã gặp thật:

  1. **Thứ tự `clean` → `chunk` là bắt buộc.** `clean.py` đổi `doc.body` nên mọi offset chunk
     cũ sai. Nó tự xoá chunk của doc bị sửa, và `chunk.py` phải chạy SAU để cắt lại.
  2. **Dừng ngay nếu `audit.py` đỏ.** Không sinh bài nộp từ dữ liệu sai - đã từng có 2 doc
     lọt `\\r` vào `chunk_text` và 5 chunk vượt trần 1.024 token.
  3. **Dừng crawl trước khi nộp.** Crawl giữ 60-80 kết nối TCP làm xuống cấp NAT router,
     upload 60 MB có thể treo giữa đường.

Mỗi bước ghi log riêng vào `data/pipeline/`, và bỏ qua bước đã xong (so dấu thời gian đầu
ra với đầu vào) nên chạy lại được sau khi bị ngắt.

  python run_pipeline.py                  # cả chuỗi, dừng ở file ZIP
  python run_pipeline.py --from bm25      # chạy từ bước bm25 trở đi
  python run_pipeline.py --only chunk     # một bước
  python run_pipeline.py --force          # bỏ qua kiểm tra "đã xong", chạy lại hết
  python run_pipeline.py --dry-run        # chỉ in ra sẽ chạy gì
  python run_pipeline.py --demo
"""
import argparse
import os
import subprocess
import sys
import time

PY = sys.executable
LOGDIR = "data/pipeline"
DB = "data/corpus.sqlite"

# (tên, lệnh, [file đầu vào], [file đầu ra])
# Đầu ra cũ hơn đầu vào -> cần chạy lại. DB luôn là đầu vào nên mọi bước chạy lại sau crawl.
STEPS = [
    ("clean", [PY, "clean.py", "--apply"], [DB], []),
    ("chunk", [PY, "chunk.py"], [DB], []),
    ("audit", [PY, "audit.py"], [DB], []),
    ("bm25", [PY, "bm25.py", "--topk", "1000", "--out", "data/bm25_rank.jsonl"],
     [DB], ["data/bm25_rank.jsonl"]),
    ("bm25_meta", [PY, "bm25.py", "--topk", "1000", "--w-body", "0",
                   "--out", "data/bm25_meta.jsonl"], [DB], ["data/bm25_meta.jsonl"]),
    ("slug", [PY, "slug_bm25.py", "--topk", "1000", "--out", "data/slug_rank1000.jsonl"],
     ["data/queries.jsonl"], ["data/slug_rank1000.jsonl"]),
    ("fuse", [PY, "fuse.py", "data/slug_rank1000.jsonl", "data/bm25_rank.jsonl",
              "data/bm25_meta.jsonl", "--out", "data/fused3.jsonl"],
     ["data/slug_rank1000.jsonl", "data/bm25_rank.jsonl", "data/bm25_meta.jsonl"],
     ["data/fused3.jsonl"]),
]
# Bước cuối sinh bài nộp. `--chunk-from-top` tính theo ngân sách 90 MB (ngưỡng Cloudflare
# là 100 MB), xem `PROGRESS.md`. `--int-ids` BẮT BUỘC: kiểu chuỗi cho FINAL = 0.
# k=200: đỉnh PHẲNG, đã đo k=150 (0,1274) / 200 (0,1280) / 265 (0,1261).
# 2 chunk × 50 doc: `deep` thắng `wide` ở cùng mức dung lượng - 100.580 chunk cho CHUNKS_F2
# 0,0879 so với 0,0863 của 1 chunk × 90 doc (104.154 chunk). FINAL 0,1079, tốt nhất đã đo.
SUBMIT = [PY, "submission.py", "--cands", "data/fused3.jsonl", "--topk", "200",
          "--int-ids", "--store", DB, "--chunks-per-doc", "2",
          "--chunk-from-top", "50", "--out", "runs/pipeline_k200"]


def newest(paths):
    """Dấu thời gian mới nhất trong `paths`. None nếu có file chưa tồn tại."""
    ts = []
    for p in paths:
        if not os.path.exists(p):
            return None
        ts.append(os.path.getmtime(p))
    return max(ts) if ts else None


def need_run(ins, outs, force=False):
    """Bước có cần chạy không: thiếu đầu ra, hoặc đầu ra cũ hơn đầu vào."""
    if force or not outs:
        return True            # không khai đầu ra (clean/chunk/audit) -> luôn chạy
    t_out = newest(outs)
    if t_out is None:
        return True
    t_in = newest(ins)
    return t_in is None or t_in > t_out


def stop_crawlers():
    """Dừng crawler VÀ process pool con của nó.

    `Stop-Process` chỉ diệt process chính; `ProcessPoolExecutor` trên Windows để lại 7
    process mồ côi mỗi lần. Đã gặp: 28 process mồ côi ngốn 2.500 giây CPU mỗi cái, chiếm
    hết 8 core nên crawl mới gần như không chạy được.

    Chỉ chạm process có `crawler.py` trong cmdline, và worker `multiprocessing` mồ côi.
    Bản đầu quét "mọi python có cha đã chết" nên **tự diệt chính run_pipeline.py** khi
    chạy nền - cha của nó là shell đã thoát, khớp đúng điều kiện mồ côi.
    """
    me = os.getpid()
    if os.name != "nt":
        subprocess.run(["pkill", "-f", "crawler.py"], capture_output=True)
        return 0
    ps = (
        '$me = ' + str(me) + '; $n = 0; '
        '$a = Get-CimInstance Win32_Process -Filter "Name like \'%python%\'"; '
        # 1. Process crawler CHÍNH (có crawler.py, không phải worker)
        '$main = $a | Where-Object { $_.CommandLine -like "*crawler.py*" -and '
        '$_.CommandLine -notlike "*multiprocessing*" -and $_.ProcessId -ne $me }; '
        # 2. Diệt CON trước, CHA sau - ngược lại sẽ để lại mồ côi
        'foreach($x in $main){ '
        '$a | Where-Object { $_.ParentProcessId -eq $x.ProcessId } | ForEach-Object { '
        'Stop-Process -Id $_.ProcessId -Force -EA SilentlyContinue; $n++ }; '
        'Stop-Process -Id $x.ProcessId -Force -EA SilentlyContinue; $n++ }; '
        'Start-Sleep 3; '
        # 3. Quét worker multiprocessing mồ côi. CHỈ worker - không chạm python khác,
        #    nếu không sẽ diệt cả chính script này.
        '$b = Get-CimInstance Win32_Process -Filter "Name like \'%python%\'"; '
        '$ids = $b.ProcessId; '
        '$b | Where-Object { $_.CommandLine -like "*multiprocessing*" -and '
        '$_.ProcessId -ne $me -and ($ids -notcontains $_.ParentProcessId) } | '
        'ForEach-Object { Stop-Process -Id $_.ProcessId -Force -EA SilentlyContinue; $n++ }; '
        'Write-Output $n')
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                       capture_output=True, text=True, timeout=120)
    try:
        return int((r.stdout or "0").strip().splitlines()[-1])
    except Exception:
        return 0


def run_step(name, cmd, dry=False):
    """Chạy một bước, ghi log, trả (thành công, số giây)."""
    os.makedirs(LOGDIR, exist_ok=True)
    log = os.path.join(LOGDIR, f"{name}.log")
    print(f"\n{'='*70}\n[{name}] {' '.join(cmd[1:])}\n  log: {log}")
    if dry:
        print("  (dry-run, không chạy)")
        return True, 0.0
    t0 = time.monotonic()
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
    with open(log, "w", encoding="utf-8") as f:
        p = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, env=env)
    el = time.monotonic() - t0
    tail = ""
    try:
        with open(log, encoding="utf-8") as f:
            tail = "".join(f.readlines()[-4:])
    except Exception:
        pass
    print(f"  {'OK' if p.returncode == 0 else 'LỖI rc=' + str(p.returncode)}"
          f"  {el/60:.1f} phút")
    if tail:
        print("  " + tail.replace("\n", "\n  ").rstrip())
    return p.returncode == 0, el


def demo():
    """Self-check: logic bỏ qua bước, và lệnh nộp bài có đúng cờ bắt buộc."""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        a, b = os.path.join(d, "in"), os.path.join(d, "out")
        open(a, "w").write("x")
        assert need_run([a], [b]), "thiếu đầu ra -> phải chạy"
        time.sleep(0.02)
        open(b, "w").write("y")
        assert not need_run([a], [b]), "đầu ra mới hơn -> bỏ qua"
        time.sleep(0.02)
        open(a, "w").write("z")
        assert need_run([a], [b]), "đầu vào đổi -> phải chạy lại"
        assert need_run([a], [b], force=True)
        assert need_run([a], []), "bước không khai đầu ra -> luôn chạy"
        assert need_run([os.path.join(d, "khong-co")], [b]), "đầu vào thiếu -> vẫn chạy"

    # Thứ tự clean -> chunk -> audit là BẮT BUỘC (clean đổi body, offset chunk cũ sai)
    names = [s[0] for s in STEPS]
    assert names.index("clean") < names.index("chunk") < names.index("audit"), names
    # fuse phải sau cả ba nguồn
    for src in ("bm25", "bm25_meta", "slug"):
        assert names.index(src) < names.index("fuse"), (src, names)

    # Bước ăn đầu ra của bước trước thì phải chạy theo, dù file cũ còn mới
    # (dry-run không đổi mtime nên không thể dựa vào mtime)
    outs_by = {s[0]: s[3] for s in STEPS}
    ins_by = {s[0]: s[2] for s in STEPS}
    assert any(o in ins_by["fuse"] for o in outs_by["bm25"]),         "fuse phải ăn đầu ra của bm25, nếu không chuỗi phụ thuộc sai"
    assert any(o in ins_by["fuse"] for o in outs_by["bm25_meta"])
    # slug KHÔNG phụ thuộc store: nó xếp hạng từ URL, nên bỏ qua được sau crawl
    assert DB not in ins_by["slug"], "slug không được phụ thuộc corpus.sqlite"

    # stop_crawlers KHÔNG được tự diệt chính mình: bản đầu quét "mọi python có cha đã
    # chết" nên khi chạy nền (cha là shell đã thoát) nó kill luôn run_pipeline.py.
    import inspect
    src = inspect.getsource(stop_crawlers)
    assert "$_.ProcessId -ne $me" in src, "thiếu loại trừ chính process này"
    assert src.count("$_.ProcessId -ne $me") >= 2, "phải loại trừ ở CẢ hai lượt quét"
    assert 'CommandLine -like "*multiprocessing*"' in src, \
        "lượt quét mồ côi phải giới hạn ở worker multiprocessing"
    assert "os.getpid()" in src

    # Bài nộp phải có --int-ids (kiểu chuỗi cho FINAL = 0, đã đo trên leaderboard)
    assert "--int-ids" in SUBMIT, SUBMIT
    assert "--chunk-from-top" in SUBMIT, "phải giới hạn chunk theo doc đầu"
    assert "--store" in SUBMIT, "thiếu --store thì chunk rỗng"
    i = SUBMIT.index("--topk")
    assert 100 <= int(SUBMIT[i + 1]) <= 400, "topk ngoài vùng hợp lý"
    print("demo OK")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="start", default=None,
                    help="chạy từ bước này trở đi: " + ", ".join(s[0] for s in STEPS))
    ap.add_argument("--only", default=None, help="chỉ một bước")
    ap.add_argument("--force", action="store_true", help="chạy lại cả bước đã xong")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-submit", action="store_true", help="dừng trước bước sinh bài nộp")
    ap.add_argument("--keep-crawl", action="store_true",
                    help="KHÔNG dừng crawler (mặc định dừng: nó tranh write lock SQLite "
                         "và chiếm kết nối TCP làm chậm upload)")
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    if a.demo:
        return demo()
    demo()

    names = [s[0] for s in STEPS]
    if a.only and a.only not in names:
        sys.exit(f"--only phải là một trong: {', '.join(names)}")
    if a.start and a.start not in names:
        sys.exit(f"--from phải là một trong: {', '.join(names)}")

    if not a.keep_crawl and not a.dry_run:
        n = stop_crawlers()
        print(f"Đã dừng crawler và {n} process liên quan "
              f"(tránh tranh write lock SQLite với clean/chunk)")

    sel = [s for s in STEPS if (s[0] == a.only if a.only
                                else names.index(s[0]) >= names.index(a.start) if a.start
                                else True)]
    t_all = time.monotonic()
    ran, skipped = [], []
    # Đầu ra sẽ được sinh lại trong lần chạy này. Bước nào ăn chúng thì cũng phải chạy -
    # cần cho `--dry-run` nói đúng, vì dry-run không đổi dấu thời gian file.
    will_make = set()
    for name, cmd, ins, outs in sel:
        upstream = any(i in will_make for i in ins)
        if not upstream and not need_run(ins, outs, a.force):
            print(f"[{name}] bỏ qua (đầu ra mới hơn đầu vào)")
            skipped.append(name)
            continue
        ok, el = run_step(name, cmd, a.dry_run)
        ran.append(name)
        will_make.update(outs)
        if not ok:
            print(f"\nDỪNG ở bước '{name}'. Xem {LOGDIR}/{name}.log")
            if name == "audit":
                print("audit đỏ nghĩa là dữ liệu có vấn đề - ĐỪNG nộp bài từ nó.")
            return 1

    if not a.only and not a.no_submit:
        ok, _ = run_step("submission", SUBMIT, a.dry_run)
        ran.append("submission")
        if not ok:
            return 1

    print(f"\n{'='*70}")
    print(f"XONG trong {(time.monotonic()-t_all)/60:.1f} phút | "
          f"đã chạy: {', '.join(ran) or '—'} | bỏ qua: {', '.join(skipped) or '—'}")
    if "submission" in ran and not a.dry_run:
        z = "runs/pipeline_k200.zip"
        if os.path.exists(z):
            mb = os.path.getsize(z) / 1024**2
            print(f"\nBài nộp: {z}  ({mb:.0f} MB)")
            if mb > 95:
                print("  ⚠️ VƯỢT ngưỡng Cloudflare 100 MB -> giảm --chunk-from-top")
            else:
                print("  Dưới ngưỡng 100 MB của Cloudflare, nộp được.")
            print("\nSau khi nộp, thêm điểm vào PROGRESS.md §2b và predict.py HISTORY.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
