"""Probe crawl: đo thông số thật trên mẫu phân tầng trước khi viết crawler đầy đủ.

Trả lời hai câu hỏi đang chặn:
  1. Quét hết 4,39M URL mất bao lâu thật? (tỉ lệ thành công, byte text sau trích, rate limit)
  2. 770k URL bị WAF chặn 403 có cứu được bằng curl_cffi (giả TLS fingerprint Chrome) không?

Lấy mẫu phân tầng theo domain: mỗi domain tối thiểu `--min-per-domain` URL để cả 97 domain
đều có số đo (đuôi dài chưa ai biết gì), phần còn lại chia theo tỉ lệ.

  python probe_crawl.py                      # 2.000 URL -> data/probe_crawl.jsonl + báo cáo
  python probe_crawl.py --n 300 --workers 8  # chạy nhẹ
  python probe_crawl.py --demo               # self-check, không cần mạng

ponytail: chưa có hàng đợi resume (probe chỉ chạy một lượt ~5 phút). Crawler thật cần
bảng SQLite (url, status, fetched_at) resume theo từng URL - thêm khi viết crawler.
"""
import argparse
import collections
import json
import statistics
import sys
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

from pubmed_module.http import RateLimiter   # dùng lại, không viết lại

BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
HEADERS = {
    "User-Agent": BROWSER_UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8,zh-CN;q=0.7",
}
# Status cần thử lại bằng curl_cffi (WAF chặn ở tầng TLS fingerprint, không phải UA)
WAF_STATUS = {403, 406, 429, 503}


def domain_of(url: str) -> str:
    try:
        host = urllib.parse.urlsplit(url).netloc.lower().split("@")[-1].split(":")[0]
    except ValueError:
        return "<invalid>"
    return host[4:] if host.startswith("www.") else (host or "<empty>")


def allocate(counts: dict, n: int, min_per_domain: int) -> dict:
    """Chia n mẫu cho các domain: mỗi domain tối thiểu min_per_domain, phần dư theo tỉ lệ.

    Không domain nào được nhiều hơn số URL nó có. Nếu riêng phần tối thiểu đã vượt n
    thì giữ phần tối thiểu (phủ hết domain quan trọng hơn là đúng đủ n mẫu).
    """
    alloc = {d: min(min_per_domain, c) for d, c in counts.items()}
    room = {d: counts[d] - alloc[d] for d in counts if counts[d] > alloc[d]}
    total = sum(room.values())
    if n <= sum(alloc.values()) or not total:
        return alloc

    need = n - sum(alloc.values())
    for d, r in room.items():                      # phần nguyên theo tỉ lệ
        alloc[d] += min(r, need * r // total)
    # Phần dư của phép chia nguyên: rải từng cái một, ưu tiên domain lớn, lặp đến hết
    left = n - sum(alloc.values())
    order = sorted(room, key=lambda d: -counts[d])
    while left > 0:
        progressed = False
        for d in order:
            if left <= 0:
                break
            if alloc[d] < counts[d]:
                alloc[d] += 1
                left -= 1
                progressed = True
        if not progressed:                         # mọi domain đã lấy hết, không thể chia thêm
            break
    return alloc


def sample(min_per_domain: int, n: int):
    """Trả [(doc_id, url, domain)] lấy mẫu phân tầng từ links_corpus."""
    import pandas as pd
    from huggingface_hub import hf_hub_download

    links = pd.read_parquet(hf_hub_download("AIGuruTinix/ViBioMIR", "links_corpus.parquet",
                                            repo_type="dataset"))
    links["domain"] = links["url"].map(domain_of)
    counts = links["domain"].value_counts().to_dict()
    alloc = allocate(counts, n, min_per_domain)
    print(f"Mẫu: {sum(alloc.values())} URL trên {len(alloc)} domain "
          f"(tối thiểu {min_per_domain}/domain)")
    out = []
    for dom, k in alloc.items():
        if k <= 0:
            continue
        rows = links.loc[links["domain"] == dom].sample(k, random_state=0)
        out += [(str(r.id), r.url, dom) for r in rows.itertuples()]
    return out, counts


def fetch_requests(url):
    import requests
    r = requests.get(url, headers=HEADERS, timeout=20, allow_redirects=True)
    return r.status_code, r.content


def fetch_curl_cffi(url):
    """Giả TLS fingerprint Chrome - cách duy nhất vượt WAF kiểu Cloudflare/Akamai."""
    from curl_cffi import requests as creq
    r = creq.get(url, headers=HEADERS, timeout=20, impersonate="chrome", allow_redirects=True)
    return r.status_code, r.content


def crawl_one(item, limiters, extract):
    doc_id, url, dom = item
    rec = {"doc_id": doc_id, "url": url, "domain": dom, "via": "requests"}
    # `ms` chỉ đo thời gian mạng; thời gian chờ rate limiter tách sang `wait_ms`,
    # nếu không thì số đo phồng theo số thread và vô nghĩa.
    wait = net = 0.0
    try:
        t = time.monotonic()
        limiters[dom].wait()
        wait += time.monotonic() - t
        t = time.monotonic()
        status, body = fetch_requests(url)
        net += time.monotonic() - t
        # Bị WAF chặn -> thử lại bằng TLS fingerprint giả
        if status in WAF_STATUS:
            rec["status_requests"] = status
            t = time.monotonic()
            limiters[dom].wait()
            wait += time.monotonic() - t
            t = time.monotonic()
            status, body = fetch_curl_cffi(url)
            net += time.monotonic() - t
            rec["via"] = "curl_cffi"
    except Exception as e:                       # mọi lỗi mạng đều là số đo, không phải crash
        rec |= {"status": None, "error": type(e).__name__,
                "ms": int(net * 1000), "wait_ms": int(wait * 1000)}
        return rec

    rec |= {"status": status, "html_bytes": len(body),
            "ms": int(net * 1000), "wait_ms": int(wait * 1000)}
    if status == 200:
        text = extract(body)
        rec["text_chars"] = len(text) if text else 0
        rec["extract_ok"] = bool(text and len(text) >= 200)
    return rec


def report(recs, counts, rate_per_domain):
    n = len(recs)
    ok = [r for r in recs if r.get("status") == 200]
    good = [r for r in ok if r.get("extract_ok")]
    print("\n" + "=" * 78)
    print(f"TỔNG: {n} URL | HTTP 200: {len(ok)} ({len(ok)/n*100:.1f}%) | "
          f"trích được text ≥200 ký tự: {len(good)} ({len(good)/n*100:.1f}%)")

    err = collections.Counter(r.get("error") or r.get("status") for r in recs if r.get("status") != 200)
    if err:
        print("Thất bại:", dict(err.most_common(8)))

    rescued = [r for r in ok if r["via"] == "curl_cffi"]
    tried = [r for r in recs if r.get("status_requests")]
    print(f"\ncurl_cffi: thử {len(tried)} URL bị chặn → cứu được {len(rescued)} "
          f"({len(rescued)/len(tried)*100:.0f}%)" if tried else "\ncurl_cffi: không URL nào bị chặn")

    if good:
        html_kb = statistics.median(r["html_bytes"] for r in good) / 1024
        text_ch = statistics.median(r["text_chars"] for r in good)
        ms = statistics.median(r["ms"] for r in good)
        print(f"\nTrung vị mỗi trang: HTML {html_kb:.1f} KB | text {text_ch:,.0f} ký tự "
              f"({text_ch*1.5/1024:.1f} KB utf-8) | mạng {ms:.0f} ms "
              f"(+ chờ rate limit {statistics.median(r.get('wait_ms', 0) for r in good):.0f} ms)")
        total = sum(counts.values())
        print(f"\nNGOẠI SUY cho {total:,} URL (tỉ lệ thành công {len(good)/n:.1%}):")
        print(f"  HTML thô nếu lưu : {total * html_kb / 1024 / 1024:>7.0f} GB  ← không lưu")
        print(f"  Text đã trích    : {total * text_ch * 1.5 / 1024**3:>7.1f} GB  "
              f"(nén zstd ~{total * text_ch * 1.5 / 1024**3 * 0.3:.1f} GB)")
        worst, wn = max(counts.items(), key=lambda kv: kv[1])
        print(f"  Nghẽn ở {worst} ({wn:,} URL) @ {rate_per_domain} req/s "
              f"= {wn / rate_per_domain / 3600:.0f} giờ  ← tổng thời gian quét")

    print("\n--- Theo domain (chỉ domain có vấn đề hoặc ≥20 mẫu) ---")
    by = collections.defaultdict(list)
    for r in recs:
        by[r["domain"]].append(r)
    rows = []
    for dom, rs in by.items():
        n_ok = sum(1 for r in rs if r.get("extract_ok"))
        rows.append((n_ok / len(rs), dom, len(rs), n_ok, counts.get(dom, 0),
                     collections.Counter(r.get("error") or r.get("status") for r in rs
                                         if not r.get("extract_ok"))))
    for pct, dom, total_s, n_ok, in_corpus, errs in sorted(rows):
        if pct >= 0.9 and total_s < 20:
            continue
        flag = "  ⚠️" if pct < 0.5 else ""
        print(f"  {pct*100:5.0f}%  {n_ok:>3}/{total_s:<3} mẫu  {in_corpus:>9,} URL  {dom:<34}"
              f"{dict(errs.most_common(3)) if errs else ''}{flag}")


def demo():
    """Self-check: chia mẫu phải đủ số và không vượt số URL có thật; trích text phải chạy."""
    import trafilatura
    counts = {"a": 1000, "b": 500, "c": 3, "d": 1}
    alloc = allocate(counts, 100, 5)
    assert all(alloc[d] <= counts[d] for d in counts), f"vượt số URL có thật: {alloc}"
    assert alloc["c"] == 3 and alloc["d"] == 1, f"domain nhỏ phải lấy hết: {alloc}"
    assert sum(alloc.values()) == 100, f"tổng mẫu phải đúng 100, nhận {sum(alloc.values())}"
    # n lớn hơn tổng số URL -> lấy hết, không vượt
    assert allocate(counts, 9999, 5) == counts, "n vượt corpus thì phải lấy hết"
    # n nhỏ hơn tổng tối thiểu -> giữ phần tối thiểu để phủ hết domain
    small = allocate(counts, 2, 5)
    assert small == {"a": 5, "b": 5, "c": 3, "d": 1}, f"phải giữ phần tối thiểu: {small}"

    assert domain_of("http://www.cnkang.com/dise/1.html") == "cnkang.com"
    assert domain_of("https://ask.39.net/q/1.html") == "ask.39.net"

    html = b"""<html><head><title>T</title></head><body><nav>Trang chu Lien he</nav>
    <article><p>Viem da day trot xung huyet man tinh la tinh trang niem mac da day bi
    viem va tron, keo dai nhieu thang. Benh thuong gap o nguoi lon tuoi va co the dieu tri
    duoc bang thuoc uc che bom proton ket hop khang sinh neu co vi khuan HP.</p></article>
    <footer>Copyright 2026</footer></body></html>"""
    text = trafilatura.extract(html)
    assert text and "niem mac da day" in text, f"không trích được nội dung chính: {text!r}"
    assert "Copyright" not in text and "Trang chu" not in text, f"còn lẫn boilerplate: {text!r}"
    print("demo OK")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=2000)
    ap.add_argument("--min-per-domain", type=int, default=5)
    ap.add_argument("--workers", type=int, default=24)
    ap.add_argument("--rate", type=float, default=2.0, help="req/s cho MỖI domain")
    ap.add_argument("--out", default="data/probe_crawl.jsonl")
    ap.add_argument("--demo", action="store_true")
    args = ap.parse_args()
    if args.demo:
        return demo()
    demo()

    import trafilatura

    def extract(body):
        try:
            return trafilatura.extract(body, include_comments=False, include_tables=True)
        except Exception:
            return None

    items, counts = sample(args.min_per_domain, args.n)
    limiters = collections.defaultdict(lambda: RateLimiter(args.rate))
    for dom in {d for _, _, d in items}:
        limiters[dom] = RateLimiter(args.rate)

    print(f"Đang crawl {len(items)} URL, {args.workers} thread, {args.rate} req/s mỗi domain...")
    t0 = time.monotonic()
    with ThreadPoolExecutor(args.workers) as ex:
        recs = []
        for i, rec in enumerate(ex.map(lambda it: crawl_one(it, limiters, extract), items), 1):
            recs.append(rec)
            if i % 200 == 0:
                print(f"  {i}/{len(items)}  ({time.monotonic()-t0:.0f}s)")
    print(f"Xong trong {time.monotonic()-t0:.0f}s")

    with open(args.out, "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Đã ghi {args.out}")
    report(recs, counts, args.rate)


if __name__ == "__main__":
    sys.exit(main())
