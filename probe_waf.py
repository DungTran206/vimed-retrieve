# Probe 3 domain tra 403: thu cac bien the de biet co vuot duoc khong.
import sys, json
import os
sys.path.insert(0, os.path.expanduser("~/vimed"))
import requests
from curl_cffi import requests as creq

URLS = {
 "familydoctor": "https://www.familydoctor.com.cn/a/202110/2724050.html",
 "zysjonline": "https://zysjonline.com/articles/misc/1000/",
 "vov.vn": "https://vov.vn/an-sach-song-khoe/thanh-hoa-bat-xe-tai-cho-21-tan-muc-kho-moc-hoi-thoi-di-tieu-thu-507671.vov",
 "youmed.vn": "https://youmed.vn/tin-tuc/dung-thuoc-khang-sinh-khi-mang-thai/",
 "pharmacity": "https://pmc-ecm-healthblog.beta.pharmacity.io/benh-vien-k-ha-noi/",
}
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
FULL = {"User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Upgrade-Insecure-Requests": "1", "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate", "Sec-Fetch-Site": "none", "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0", "Connection": "keep-alive"}

def mark(code, body):
    return f"{code} ({len(body or b'')}B)"

for name, url in URLS.items():
    print(f"\n=== {name}")
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=20)
        print(f"  requests UA-only       {mark(r.status_code, r.content)}")
    except Exception as e: print("  requests UA-only       ERR", type(e).__name__)
    try:
        r = requests.get(url, headers=FULL, timeout=20)
        print(f"  requests full headers  {mark(r.status_code, r.content)}")
    except Exception as e: print("  requests full headers  ERR", type(e).__name__)
    for prof in ("chrome", "chrome131", "chrome124", "safari17_0", "firefox133", "edge101"):
        try:
            r = creq.get(url, headers=FULL, timeout=20, impersonate=prof)
            print(f"  curl_cffi {prof:12} {mark(r.status_code, r.content)}")
        except Exception as e:
            print(f"  curl_cffi {prof:12} ERR {type(e).__name__}")
    # session: lay cookie tu trang chu roi goi lai
    try:
        s = creq.Session(impersonate="chrome")
        host = "https://" + url.split("/")[2]
        h = s.get(host, headers=FULL, timeout=20)
        r = s.get(url, headers={**FULL, "Referer": host, "Sec-Fetch-Site": "same-origin"}, timeout=20)
        print(f"  session home->page     home {h.status_code} then {mark(r.status_code, r.content)}")
    except Exception as e: print("  session home->page     ERR", type(e).__name__)
