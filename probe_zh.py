"""Kiểm tra nhanh: IP/mạng này có crawl được 4 domain tiếng Trung lớn không? (~1 phút)

Dùng đúng `crawler.fetch()` + `extract_doc()` như lúc crawl thật, nên "OK" ở đây nghĩa là
crawl thật sẽ chạy được. Chạy TRƯỚC khi bỏ ra hàng chục giờ crawl: nếu IP bị chặn thì biết
ngay thay vì phát hiện sau một đêm.

    python probe_zh.py
"""
import time

import crawler

# URL thật lấy từ hàng đợi (đo 04/10: cả 4 trả 200, body 584-889 ký tự trên IP máy GPU)
URLS = {
    "cnkang.com": "http://www.cnkang.com/dise/155/1122384.html",
    "120ask.com": "http://www.120ask.com/question/13180897.htm",
    "ask.39.net": "https://ask.39.net/question/34827119.html",
    "a-hospital.com": "https://www.a-hospital.com/w/%E5%A4%96%E7%A7%91%E5%AD%A6%E6%80%BB%E8%AE%BA/"
                      "%E7%83%A7%E4%BC%A4%E4%BC%91%E5%85%8B",
}


TRIES = 3          # một lần duy nhất không đại diện: server nước ngoài hay timeout ngẫu nhiên
NEED = 2           # đạt khi >= 2/3 lần thành công (crawl thật đo được ~97,8%)


def try_once(dom, url, lim):
    t0 = time.monotonic()
    try:
        status, raw, via = crawler.fetch(url, lim)
        d = crawler.extract_doc(raw, url, dom) if status == 200 and raw else {}
        body = len(d.get("body") or "")
        cap = crawler.looks_captcha((d.get("title") or "") + (d.get("body") or ""),
                                    len(raw or b""))
        good = status == 200 and body >= 200 and not cap
        return good, f"status={status} body={body:>5} captcha={cap}", time.monotonic() - t0
    except Exception as e:
        return False, f"{type(e).__name__}", time.monotonic() - t0


def main():
    lim = crawler.AdaptiveLimiter(1.0)
    passed = 0
    for dom, url in URLS.items():
        res = [try_once(dom, url, lim) for _ in range(TRIES)]
        n_ok = sum(r[0] for r in res)
        detail = " | ".join(f"{'ok' if g else 'LOI'} {t:.0f}s" for g, _, t in res)
        good = n_ok >= NEED
        passed += good
        print(f"{'OK  ' if good else 'LOI '} {dom:16} {n_ok}/{TRIES}   {detail}")
        if not good:
            print(f"       ly do cuoi: {res[-1][1]}")
    print()
    if passed == len(URLS):
        print(f"{passed}/{len(URLS)} domain OK -> mang nay crawl duoc, chay buoc 2.")
    else:
        print(f"{passed}/{len(URLS)} domain OK -> KHONG chay tiep. Gui ket qua nay cho nguoi giao viec.")


if __name__ == "__main__":
    main()
