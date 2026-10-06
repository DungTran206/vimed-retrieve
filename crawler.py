"""Crawler cho 4,39M URL: SQLite store, resume theo từng URL, rate limit riêng mỗi domain.

Thiết kế theo `PIPELINE.md` §1. Mọi tham số mặc định dưới đây đều từ số đo thật
(`PROGRESS.md` §2), không phải đoán.

Nguyên tắc quan trọng nhất: `body` là **văn bản chính tắc bất biến**. Chunk về sau chỉ lưu
`(doc_id, start, end)` và `chunk_text = body[start:end]`, nên ràng buộc "nguyên văn" được
bảo đảm bằng cấu trúc. Crawler KHÔNG chia chunk - đó là bước riêng, chạy lại được với
budget khác mà không cần crawl lại.

Không lưu HTML thô (4,39M x 53,7 KB = 225 GB), CHỈ lưu khi trích thất bại để viết parser
mà không phải crawl lại.

  # Lô ưu tiên: 128k URL có điểm slug cao nhất
  python crawler.py --prio data/slug_rank.jsonl --limit 130000

  # Quét nốt toàn bộ (chạy trong tmux trên máy GPU)
  python crawler.py

  python crawler.py --demo          # self-check, không cần mạng
  python crawler.py --stats         # xem tiến độ
"""
import argparse
import collections
import hashlib
import json
import os
import queue
import re
import sqlite3
import sys
import threading
import time
import unicodedata
import urllib.parse
from concurrent.futures import (ProcessPoolExecutor, ThreadPoolExecutor, as_completed,
                                wait, FIRST_COMPLETED)

from pubmed_module.http import RateLimiter      # dùng lại, không viết lại

# Console Windows mặc định là cp1252: `print` tiếng Việt và ký hiệu cảnh báo ném
# `UnicodeEncodeError` và GIẾT crawler - ngay lúc khởi động, hoặc tệ hơn là giữa chừng ở lần
# in cảnh báo đầu tiên (có thể sau nhiều giờ). Máy dev không dính vì luôn đặt
# PYTHONIOENCODING, nhưng người nhận script thì không biết. `errors="replace"` để một ký tự
# lạ không bao giờ làm chết cả đợt crawl.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

DB = "data/corpus.sqlite"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7,zh-CN;q=0.6",
    "Upgrade-Insecure-Requests": "1",
}
WAF_STATUS = {403, 406, 429, 503}      # thử lại bằng curl_cffi (giả TLS fingerprint Chrome)
# Status mà server đang nói "chậm lại". 429 là nói thẳng; 403/503 hàng loạt thường là hệ quả.
BACKOFF_STATUS = {429, 403, 503}
# Không request nào trong batch xong trong khoảng này -> coi như mắc kẹt, bỏ batch.
# 25s timeout x 2 (requests + curl_cffi) = 50s là trường hợp chậm nhất bình thường.
# Timeout mỗi request (giây). Mặc định 25 (hành vi cũ), ghi đè bằng `--timeout`. Đo 05/10 trên
# `cnkang.com`: response là LƯỠNG CỰC - hoặc về trong ~1-9 giây, hoặc treo quá 60 giây (4/8 URL
# vừa timeout vẫn treo khi tải lại riêng, 3/8 về trong ~1 giây). Chờ 25 giây cho request sẽ
# treo thì chỉ giữ luồng vô ích.
TIMEOUT = 25
BATCH_STALL_SEC = 180

# Thách đố cookie: server trả HTTP 200 với một mẩu JS đặt cookie rồi reload. Giá trị cookie
# nằm SẴN trong phản hồi nên không cần chạy JS - chỉ cần set lại rồi gọi lần hai.
#   laodong.vn (31.282 URL): document.cookie="D1N=af1d42e1..."; window.location.reload(true);
COOKIE_CHALLENGE = re.compile(rb"""document\.cookie\s*=\s*["']([^"'=;]{1,64})=([^"';]{1,256})["']""")
CHALLENGE_MAX_BYTES = 4096        # trang thật không bao giờ nhỏ thế này

# Rate limit req/s theo từng domain. Đo được: cnkang/120ask/ask.39.net chịu tải tốt
# (99-100% thành công), a-hospital trả 502 ở 28/65 mẫu nên phải hạ hẳn.
# req/s mỗi domain. Đặt theo tỉ lệ thành công ĐO ĐƯỢC, không phải đoán:
#   99-100% dùng được  -> nâng lên 12
#   trả 429/403        -> hạ hẳn, và AdaptiveLimiter sẽ tự hạ thêm nếu còn phản đối
RATES = {
    # tiếng Trung, đo 99-100%
    # 04/10: ba domain này là LỚN nhất phía zh và chính chúng bị drop kết nối nhiều nhất
    # (NewConnectionError 59,5%) khi chạy ở mức cũ 12/12/10. Hạ xuống 4 - cùng lý do như
    # giadinhonline/youmed phía vi: mức khởi đầu thấp tốt hơn bị phạt xuống đáy.
    # 04/10 tối: nâng 4 → 8. Mức 4 đặt lúc NewConnectionError chiếm 59,5%, nhưng khi đó còn
    # HAI lỗi khác chưa sửa (pool 32/thread làm cạn file descriptor, `writer_loop` chết vì store
    # bị khoá) - sửa xong thì tỉ lệ dùng được là 97,8%, tức rate 4 quá thận trọng. Hai domain này
    # chiếm 77% phần zh còn lại nên rate của chúng CHÍNH LÀ trần: 4 → 66 giờ, 8 → 33 giờ.
    # An toàn hơn lần hạ trước vì `AdaptiveLimiter` giờ phạt cả LỖI MẠNG (không chỉ HTTP status)
    # rồi tự hạ, và `reward()` nới lại khi ổn định.
    # ĐÃ THỬ 8 VÀ SAI (04/10 tối): rate 8 cho 3,3 trang/s và 81,5% dùng được, so với rate 4
    # cho 16,1 trang/s và 97,8% - CHẬM GẤP 5 LẦN. Server chặn nhiều hơn nên tổng thông lượng
    # giảm dù mỗi giây gửi nhiều hơn. Lần thứ ba cùng một bài học (sau giadinhonline, youmed):
    # mức khởi đầu thấp tốt hơn bị phạt, và backoff KHÔNG cứu được mức khởi đầu sai.
    "cnkang.com": 4, "120ask.com": 4, "ask.39.net": 4,
    "a-hospital.com": 1.5,                      # 502 ở 28/65 mẫu
    "familydoctor.com.cn": 15,                  # 100% trên 54k doc, 90 lỗi
    # tiếng Việt, đo 99-100% trên hàng nghìn doc
    "suckhoecongdongonline.vn": 12, "suckhoedoisong.vn": 12, "thanhnien.vn": 12,
    "phunusuckhoe.giadinhonline.vn": 12, "vinmec.com": 12, "medlatec.vn": 12,
    "baohaiphong.vn": 10, "giadinhonline.vn": 10, "baonghean.vn": 10,
    "vietnamnet.vn": 10, "baodanang.vn": 10, "baocantho.com.vn": 10,
    "baoangiang.com.vn": 10, "laodong.vn": 10,
    # 01/10 bị chặn vì đập quá nhanh ở IP local: 15.062 lần 403 + 5.352 lần 429, chỉ 315 doc
    # dùng được -> phải hạ xuống 0,5 req/s (= 32 GIỜ cho 58k URL).
    # 03/10 đo trên IP MÁY GPU: 3/3 URL thật trả 200 ở 3 req/s, body 2.821-3.747 ký tự
    # -> 0,5 là giới hạn của IP bị flag, KHÔNG phải của server. Ở 3 req/s còn 5,4 giờ.
    # An toàn hơn lần trước vì giờ đã có `AdaptiveLimiter` (tự hạ khi 429) và `looks_captcha`.
    "nhathuoclongchau.com.vn": 3,
    # Đo 03/10: ăn 429 ngay ở mức cũ (giadinhonline 10, youmed/vov mặc định 5). Hạ mức
    # KHỞI ĐẦU còn hơn để AdaptiveLimiter phải phạt - phạt thì mất cả đợt mới nới lại.
    # vov.vn chịu được 3 req/s (0 lần 429). Hai domain kia 429 ngay cả ở 3 và 1 req/s, và
    # một lần bị phạt là rơi xuống 0,03 (= 94 GIỜ cho 10k URL) vì 429 liên tục reset chuỗi
    # thắng của AIMD -> thà bắt đầu ở mức thấp mà không bao giờ bị phạt.
    "giadinhonline.vn": 1, "youmed.vn": 0.5, "vov.vn": 3,
}
DEFAULT_RATE = 5

# Domain đã đo là chặn, không vượt được bằng code (xem PROGRESS.md). Đánh dấu BLOCKED ngay,
# không tốn request. Có IP mới thì `--retry-blocked` chạy lại đúng phần này.
BLOCKED = {"familydoctor.com.cn", "zysjonline.com", "baidianfeng.familydoctor.com.cn",
           "qy.familydoctor.com.cn", "v.familydoctor.com.cn", "ask.familydoctor.com.cn",
           "yanglao.familydoctor.com.cn", "ypk.familydoctor.com.cn", "familydoctor.cn",
           "bingli.iiyi.com", "article.iiyi.com"}

PENDING, DONE, FAILED, BLOCKED_ST = 0, 1, 2, 3

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA busy_timeout=60000;
PRAGMA synchronous=NORMAL;
CREATE TABLE IF NOT EXISTS doc (
  doc_id TEXT PRIMARY KEY, url TEXT, domain TEXT, lang TEXT,
  status INTEGER, err TEXT, via TEXT,
  title TEXT, descr TEXT, tags TEXT, pub_date TEXT,
  body TEXT,                      -- VĂN BẢN CHÍNH TẮC, BẤT BIẾN
  raw_html TEXT,                  -- chỉ khi trích thất bại, để viết parser
  simhash INTEGER, fetched TEXT
);
CREATE TABLE IF NOT EXISTS queue (
  doc_id TEXT PRIMARY KEY, url TEXT, domain TEXT, prio REAL DEFAULT 0, state INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS q_next ON queue(state, prio DESC);
CREATE INDEX IF NOT EXISTS q_dom ON queue(domain, state, prio DESC);
CREATE INDEX IF NOT EXISTS d_domain ON doc(domain);
"""


# ---------------------------------------------------------------- tiện ích

class Deferred(Exception):
    """URL được hoãn: domain đang quá tải hàng đợi. KHÔNG ghi gì, URL vẫn PENDING."""


class AdaptiveLimiter(RateLimiter):
    """RateLimiter tự CHẬM LẠI khi server trả 429/403.

    Đã mất ~20.000 URL của `nhathuoclongchau.com.vn` vì thiếu đúng việc này: crawl ở
    5 req/s, server trả 429 (Too Many Requests) rồi chuyển sang 403 hàng loạt, mà crawler
    cứ tiếp tục ở nguyên tốc độ. 20.742 lượt thử chỉ còn 315 cái dùng được.

    AIMD: giảm NHÂN khi bị phạt (nhân đôi interval, chặn trên ở MAX_INTERVAL), nới CỘNG
    rất chậm khi thành công liên tiếp, và không bao giờ nhanh hơn `base`. Nửa "nới lại"
    này cần thiết vì 429 lúc khởi động là do burst thoáng qua: thiếu nó, `youmed.vn` bị
    ghim ở 0,03 req/s suốt đợt -> 3.473 URL thành 32 GIỜ thay vì nửa giờ. Nới có chặn
    trên ở `base` nên không tái diễn vụ mất 20.000 URL ở trên.
    """
    MAX_INTERVAL = 30.0          # chậm nhất: 1 request mỗi 30 giây
    WIN_STREAK = 15              # số lần 200 liên tiếp trước khi dám nới
    EASE = 1.5                   # nới chậm hơn lúc phạt (phạt ×2) -> thiên về an toàn

    # Nới theo THỜI GIAN: cứ RECOVER_AFTER giây không bị phạt thì nới một bậc. `reward()` một
    # mình KHÔNG đủ: nó cần WIN_STREAK lần thành công LIÊN TIẾP, mà ở rate đã bị hạ sát đáy thì
    # chỉ cần một timeout lẻ là chuỗi về 0 - limiter kẹt vĩnh viễn. Đo 04/10: `ask.39.net` kẹt ở
    # 0,03 req/s và `cnkang` ở 0,50, crawl đứng với CPU 2% suốt hàng giờ dù cả hai domain đã
    # probe 3/3 OK từ chính IP đó. Chạy qua đêm không ai canh thì đó là chết lâm sàng.
    RECOVER_AFTER = 300.0

    def __init__(self, rate_per_sec):
        super().__init__(rate_per_sec)
        self.base = self.interval
        self.strikes = 0
        self.wins = 0
        self.last_penalty = time.monotonic()
        self._soft_times = collections.deque()

    def recover(self, now=None):
        """Nới một bậc nếu đã RECOVER_AFTER giây không bị phạt. Trả True nếu có nới."""
        now = time.monotonic() if now is None else now
        with self.lock:
            if self.interval <= self.base or now - self.last_penalty < self.RECOVER_AFTER:
                return False
            self.interval = max(self.base, self.interval / self.EASE)
            self.last_penalty = now          # bậc kế tiếp phải đợi thêm RECOVER_AFTER
            return True

    def wait(self):
        """Đặt chỗ TRONG khoá, rồi NGỦ NGOÀI khoá.

        `RateLimiter.wait()` gốc ngủ khi đang GIỮ khoá. Luồng chính - nơi duy nhất `q.put` kết
        quả - lại gọi `penalize()`/`reward()` của cùng domain, mà hai hàm đó cần đúng khoá ấy. Khi
        một domain bị hạ xuống 0,12 req/s, hàng chục luồng xếp hàng, mỗi luồng giữ khoá 8 giây,
        nên luồng chính đứng chờ khoá và KHÔNG xử lý kết quả của bất kỳ domain nào: 0 doc được ghi
        trong 15 phút (crawler s0d, 05/10), và trước đó là 2.129 doc dồn vào một phút sau hàng giờ
        im lặng. Đặt chỗ rồi ngủ ngoài khoá giữ nguyên nhịp request mà khoá chỉ bị giữ vài micro
        giây.
        """
        self.recover()
        with self.lock:
            now = time.monotonic()
            slot = max(now, self.next_t)
            if slot - now > self.MAX_QUEUE_WAIT:
                # Hàng đợi domain đã quá dài: KHÔNG đặt chỗ, nhả luồng ngay. Nếu không, mỗi luồng
                # nhặt một URL của domain đang bị hạ (0,03 req/s = 33 giây/lượt, xếp nối đuôi)
                # sẽ ngủ hàng phút, dần dần cả 160 luồng đều ngủ chờ domain đó và mọi domain khác
                # hết luồng: ba domain rate 6/4/1,5 cùng ra ~0,77 doc/giây (05/10).
                raise Deferred(f"hàng đợi {slot - now:.0f}s")
            self.next_t = slot + self.interval
        delay = slot - now
        if delay > 0:
            time.sleep(delay)

    MAX_QUEUE_WAIT = 20.0        # chờ quá số giây này thì hoãn URL thay vì ngủ giữ luồng
    SOFT_WINDOW = 60.0           # cửa sổ đếm lỗi mạng (giây)
    SOFT_BURST = 10              # số lỗi mạng trong cửa sổ mới tính là "một loạt" và bị phạt
    SOFT_FACTOR = 1.3            # phạt lỗi mạng: nhẹ hơn nhiều so với 429/403
    SOFT_CAP = 8                 # lỗi mạng không được hạ quá base/8

    def penalize(self, soft=False, now=None):
        """Server phản đối -> giãn khoảng cách. Trả (số lần bị phạt, interval mới).

        `soft=True` cho LỖI MẠNG (status None). Phân biệt là cần thiết: 429/403 là server nói
        thẳng "chậm lại", còn timeout/reset xảy ra ngẫu nhiên và KHÔNG có nghĩa rate quá cao.
        Đo 04/10: chỉ 5 lần lỗi mạng đã hạ `cnkang.com` từ 4 xuống **0,12 req/s** (nhân đôi 5
        lần = ×32), tức 945k URL của nó cần 2.187 GIỜ. Phạt nhẹ ×1,3 và chặn dưới ở base/8.
        """
        with self.lock:
            if soft:
                # Lỗi mạng LẺ TẺ là nhiễu bình thường; chỉ một LOẠT mới là server từ chối. Đo
                # 05/10: cnkang ~1 lỗi kết nối mỗi 70 giây (57 trong 66 phút, 2%) mà mỗi lỗi reset
                # đồng hồ nới lại 300 giây, nên limiter không bao giờ hồi và bị kéo dần về sàn
                # (rate 6 cấu hình nhưng chỉ ra 0,76 doc/giây ≈ 6/8). Chỉ phạt khi đủ
                # SOFT_BURST lỗi trong SOFT_WINDOW giây.
                now = time.monotonic() if now is None else now
                dq = self._soft_times
                dq.append(now)
                while dq and now - dq[0] > self.SOFT_WINDOW:
                    dq.popleft()
                if len(dq) < self.SOFT_BURST:
                    return self.strikes, self.interval       # lỗi lẻ: chưa phạt
                dq.clear()                                    # đã phạt: bắt đầu đếm lại
            self.strikes += 1
            self.wins = 0
            self.last_penalty = time.monotonic()
            factor = self.SOFT_FACTOR if soft else 2.0
            ceiling = self.base * self.SOFT_CAP if soft else self.MAX_INTERVAL
            self.interval = min(self.interval * factor, ceiling, self.MAX_INTERVAL)
            return self.strikes, self.interval

    def reward(self):
        """Đủ WIN_STREAK lần thành công liên tiếp -> nới về phía `base`. Trả interval mới
        nếu có đổi, ngược lại None (đang ở `base` thì không làm gì)."""
        with self.lock:
            if self.interval <= self.base:
                return None
            self.wins += 1
            if self.wins < self.WIN_STREAK:
                return None
            self.wins = 0
            self.interval = max(self.base, self.interval / self.EASE)
            return self.interval


def domain_of(url):
    try:
        host = urllib.parse.urlsplit(url).netloc.lower().split("@")[-1].split(":")[0]
    except ValueError:
        return "<invalid>"
    return host[4:] if host.startswith("www.") else (host or "<empty>")


def detect_lang(text, domain):
    """Suy ngôn ngữ. Đo được domain đủ cho 66/69 domain, nên domain là chính, đếm ký tự
    Hán để kiểm lại (>15% ký tự là Hán -> zh)."""
    if not text:
        return "zh" if domain.endswith((".cn", ".com.cn")) else "vi"
    han = sum(1 for c in text[:3000] if "一" <= c <= "鿿")
    return "zh" if han > len(text[:3000]) * 0.15 else "vi"


def normalize(text):
    """NFC, thu gọn khoảng trắng NGANG, giữ nguyên '\\n' (ranh giới đoạn duy nhất -
    đo được trafilatura không dùng '\\n\\n')."""
    text = unicodedata.normalize("NFC", text)
    # Quy về '\n' TRƯỚC mọi việc khác: `\r` từng sót lại và lọt vào
    # `chunk_text` (2 doc baotayninh.vn, audit bắt được).
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t 　 -    ]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def simhash64(text):
    """Simhash 64 bit trên 5-shingle, để gom bản gần trùng. Đo được có cụm sao chép hệ
    thống (a-hospital <-> zhongyibaodian, Jaccard 0,82-0,87). Dùng để embed chung một
    đại diện - KHÔNG BAO GIỜ để xoá doc_id."""
    toks = re.findall(r"\w+", text.lower())
    if not toks:
        return 0
    bits = [0] * 64
    for i in range(max(1, len(toks) - 4)):
        h = int.from_bytes(hashlib.md5(" ".join(toks[i:i + 5]).encode()).digest()[:8], "big")
        for b in range(64):
            bits[b] += 1 if (h >> b) & 1 else -1
    v = sum(1 << b for b in range(64) if bits[b] > 0)
    return v - (1 << 64) if v >= (1 << 63) else v        # ép vào int64 có dấu của SQLite


def extract_fallback(html):
    """Khi trafilatura trả None: lấy thẻ khối có nhiều text nhất bằng lxml (đã cài sẵn).

    Rẻ, bắt được phần lớn ca lỗi (baotayninh.vn: 156 KB HTML nhưng trafilatura ra 0 ký tự).
    """
    try:
        from lxml import html as lh
        root = lh.fromstring(html)
    except Exception:
        return None
    for bad in root.xpath("//script|//style|//nav|//footer|//header|//aside|//form"):
        bad.getparent().remove(bad)
    best, best_len = None, 0
    for el in root.xpath("//article|//main|//div|//section"):
        t = " ".join(el.itertext())
        n = len(re.sub(r"\s+", " ", t).strip())
        if n > best_len:
            best, best_len = el, n
    if best is None or best_len < 200:
        return None
    return "\n".join(p.strip() for p in best.itertext() if p.strip())


# ---------------------------------------------------------------- store

COLS = ("doc_id", "url", "domain", "lang", "status", "err", "via",
        "title", "descr", "tags", "pub_date", "body", "raw_html", "simhash")


# Domain tiếng Trung không nhận ra được bằng TLD: nhiều cái là .net/.com. Danh sách này
# lấy từ `data/domain_stats.csv` (97 domain, đã phân loại tay một lần).
ZH_EXACT = {"cnkang.com", "120ask.com", "zysjonline.com", "a-hospital.com",
            "zhongyibaodian.net", "zydcd.com", "wujue.com", "youlai.cn",
            "qihuangzhishu.com", "baidu.com", "test.pmphai.com", "msdmanuals.cn",
            "jb39.com", "health.people.com.cn", "fk.99.com.cn"}


def is_zh_domain(dom):
    """True nếu domain chứa nội dung tiếng Trung."""
    return (dom.endswith(".cn") or dom.endswith("39.net") or ".39.net" in dom
            or "iiyi" in dom or dom in ZH_EXACT)


def lang_domains(conn, lang):
    """Danh sách domain của một ngôn ngữ, lấy từ chính queue (bỏ domain đã chặn).

    Chia theo NGÔN NGỮ để hai máy không tranh nhau: mỗi domain do đúng một máy phụ trách,
    nên rate limit theo domain vẫn đúng, và `--merge` về sau không có xung đột.
    """
    doms = [d for d, in conn.execute(
        "SELECT DISTINCT domain FROM queue WHERE state != ?", (BLOCKED_ST,))]
    sel = [d for d in doms if (is_zh_domain(d) if lang == "zh" else not is_zh_domain(d))]
    n = 0
    if sel:
        qs = ",".join("?" * len(sel))
        n, = conn.execute(f"SELECT count(*) FROM queue WHERE state != ? AND domain IN ({qs})",
                          (BLOCKED_ST, *sel)).fetchone()
    print(f"lang={lang}: {len(sel)} domain, {n:,} URL chưa chặn")
    return sel


def shard_domains(conn, idx, total):
    """Chia 97 domain thành `total` phần cân bằng theo số URL; trả danh sách của phần `idx`.

    Chia theo DOMAIN chứ không theo id: nếu hai máy cùng crawl `cnkang.com` thì mỗi máy
    giữ rate limit riêng 10 req/s → tổng 20 req/s về cùng một server, vừa bất lịch sự
    vừa dễ bị chặn. Chia theo domain thì mỗi domain do đúng một máy phụ trách.

    Xếp thùng kiểu greedy: domain to nhất vào thùng đang nhẹ nhất.
    """
    doms = conn.execute("SELECT domain, count(*) FROM queue WHERE state!=? "
                        "GROUP BY domain ORDER BY 2 DESC", (BLOCKED_ST,)).fetchall()
    bins = [[] for _ in range(total)]
    load = [0] * total
    for dom, n in doms:
        i = load.index(min(load))
        bins[i].append(dom)
        load[i] += n
    print(f"Chia {len(doms)} domain thành {total} phần: "
          + " | ".join(f"#{i}: {len(b)} domain / {load[i]:,} URL"
                       for i, b in enumerate(bins)))
    return bins[idx]


def merge_shard(conn, other_path):
    """Gộp store của một máy khác vào store này. An toàn khi chạy lại nhiều lần."""
    conn.execute("ATTACH DATABASE ? AS src", (other_path,))
    before, = conn.execute("SELECT count(*) FROM doc").fetchone()
    cols = ",".join(COLS)
    conn.execute(f"INSERT OR IGNORE INTO doc ({cols}, fetched) "
                 f"SELECT {cols}, fetched FROM src.doc")
    # Trạng thái queue phải theo nội dung thật, không tin state của máy kia
    conn.execute("UPDATE queue SET state=? WHERE doc_id IN "
                 "(SELECT doc_id FROM doc WHERE length(body)>=200)", (DONE,))
    conn.execute("UPDATE queue SET state=? WHERE state=? AND doc_id IN "
                 "(SELECT doc_id FROM doc WHERE length(body)<200)", (FAILED, PENDING))
    conn.commit()
    after, = conn.execute("SELECT count(*) FROM doc").fetchone()
    conn.execute("DETACH DATABASE src")
    print(f"Gộp {other_path}: {before:,} -> {after:,} doc (+{after-before:,})")


def acquire_instance_lock(db_path):
    """Khoá `<db>.crawl.lock`: MỘT crawler cho MỘT store, hoặc thoát ngay với thông báo rõ.

    05/10: lần restart không dừng được tiến trình cũ nên HAI crawler cùng chạy trên một store và
    cùng phần `--shard-ids 0/5`. Chúng làm trùng việc, gấp đôi tải lên mỗi server từ cùng một IP
    (cnkang tới ~12 req/s thay vì 6), tranh quyền ghi SQLite (doc dồn thành cục, lỗi `another
    row available`), và làm hỏng mọi số đo rate - mà không có dấu hiệu nào báo lỗi. Giao script
    cho đồng đội thì chuyện chạy hai lần còn dễ xảy ra hơn. Trả về file đã khoá: PHẢI giữ tham
    chiếu suốt đời tiến trình, đóng file là nhả khoá.
    """
    path = db_path + ".crawl.lock"
    f = open(path, "a+")
    try:
        if os.name == "nt":
            import msvcrt
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        # PID nằm ở file RIÊNG: trên Windows vùng đang khoá không đọc được, đọc là văng lỗi
        try:
            with open(db_path + ".crawl.pid") as pf:
                other = pf.read().strip() or "?"
        except OSError:
            other = "?"
        sys.exit(f"DUNG: da co mot crawler khac (PID {other}) dang dung store {db_path}.\n"
                 f"Hai crawler cung store lam trung viec, gap doi tai len server va hong so do.\n"
                 f"Dung cai cu truoc (pkill -f crawler.py), kiem tra pgrep -f crawler.py, roi chay lai.")
    with open(db_path + ".crawl.pid", "w") as pf:
        pf.write(f"{os.getpid()}\n")
    return f


def open_db(path=DB):
    conn = sqlite3.connect(path, check_same_thread=False, timeout=60)
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def seed_queue(conn, prio_path=None):
    """Nạp 4,39M URL vào queue. Điểm ưu tiên lấy từ slug_bm25 (đã có, không cần crawl)."""
    n = conn.execute("SELECT count(*) FROM queue").fetchone()[0]
    if n:
        print(f"Queue đã có {n:,} URL, bỏ qua bước nạp")
        return
    import pandas as pd
    from huggingface_hub import hf_hub_download
    links = pd.read_parquet(hf_hub_download("AIGuruTinix/ViBioMIR", "links_corpus.parquet",
                                            repo_type="dataset"))
    prio = {}
    if prio_path:
        # Điểm cao nhất mà URL này đạt được trên bất kỳ câu hỏi nào
        for line in open(prio_path, encoding="utf-8"):
            for c in json.loads(line)["candidates"]:
                d = str(c["doc_id"])
                prio[d] = max(prio.get(d, 0.0), float(c.get("score", 0)))
        print(f"Nạp điểm ưu tiên cho {len(prio):,} URL từ {prio_path}")
    rows = []
    for doc_id, url in zip(links["id"].astype(str), links["url"]):
        dom = domain_of(url)
        state = BLOCKED_ST if dom in BLOCKED else PENDING
        rows.append((doc_id, url, dom, prio.get(doc_id, 0.0), state))
    conn.executemany("INSERT OR IGNORE INTO queue VALUES (?,?,?,?,?)", rows)
    conn.commit()
    blocked = sum(1 for r in rows if r[4] == BLOCKED_ST)
    print(f"Queue: {len(rows):,} URL | đánh dấu BLOCKED ngay: {blocked:,} "
          f"({blocked/len(rows)*100:.1f}%, không tốn request)")


def interleave(items):
    """Trộn xen kẽ theo domain, giữ thứ tự ưu tiên trong từng domain.

    Batch lấy theo `ORDER BY prio DESC` có thể toàn một domain -> cả trăm thread xếp hàng
    sau một rate limiter, phần lớn thread ngồi không. Round-robin giữa các domain cho phép
    chạy song song thật: throughput ≈ tổng rate của các domain đang hoạt động, thay vì
    rate của một domain.
    """
    by = collections.OrderedDict()
    for it in items:
        by.setdefault(it[2], []).append(it)
    out, queues = [], list(by.values())
    while queues:
        for qq in list(queues):
            out.append(qq.pop(0))
            if not qq:
                queues.remove(qq)
    return out


def take_batch(conn, n, retry_failed=False, retry_blocked=False, domains=None,
               rates=None, shard_ids=None):
    """Lấy n URL, CHIA HẠN MỨC THEO DOMAIN để mọi domain tiến song song.

    `ORDER BY prio DESC LIMIT n` toàn cục có thể cho batch dồn vào một domain - đã gặp:
    `bachmai.gov.vn` chiếm 1555/2000 URL đầu, nên throughput tụt về rate của đúng domain
    đó (**0,6 trang/s** trong khi tổng rate của 38 domain trong batch là 262 req/s).
    `interleave()` không cứu được: nó chỉ trộn những gì batch đã chứa.

    Lấy theo từng domain thì throughput ≈ TỔNG rate các domain đang hoạt động.

    Hạn mức phải TỈ LỆ VỚI TỐC ĐỘ, không chia đều: domain bị `AdaptiveLimiter` hạ xuống
    0,03 req/s mà vẫn nhận 40 URL thì cần 22 PHÚT cho phần của nó, và `ex.map` chờ hết
    batch - nó giữ cả batch làm con tin (đã gặp: throughput đứng ở 6,1 trang/s dù tổng
    rate các domain là 262 req/s). Chia theo tỉ lệ thì mọi domain xong phần của mình
    cùng lúc.

    `rates`: {domain: req/s hiện tại}. Thiếu thì chia đều (hành vi cũ).
    """
    states = [PENDING] + ([FAILED] if retry_failed else []) + \
             ([BLOCKED_ST] if retry_blocked else [])
    qs = ",".join("?" * len(states))

    # Domain nào còn việc. Giới hạn để batch không phình khi có hàng trăm domain.
    cond, cargs = "", []
    if domains:
        cond = f" AND domain IN ({','.join('?' * len(domains))})"
        cargs = list(domains)
    # Chia TRONG domain theo doc_id: mỗi IP/máy giữ một phần `doc_id % N == I`. Cần thiết vì
    # trần của crawl là domain chậm nhất (cnkang.com: 940k URL ở 4 req/s = 65 giờ), mà chia
    # theo domain thì ai giữ domain đó vẫn mất 65 giờ. Rate limit thường theo IP nên N máy
    # = N lần thông lượng trên CÙNG domain.
    shard_sql, shard_args = "", ()
    if shard_ids:
        si, sn = shard_ids
        shard_sql, shard_args = " AND CAST(doc_id AS INTEGER) % ? = ?", (sn, si)
    cond += shard_sql
    cargs += list(shard_args)
    active = [d for d, in conn.execute(
        f"SELECT DISTINCT domain FROM queue WHERE state IN ({qs}){cond}",
        (*states, *cargs))]
    if not active:
        return []

    if rates:
        rr = {d: max(rates.get(d, DEFAULT_RATE), 1e-6) for d in active}
        tot = sum(rr.values())
        # Tối thiểu 1 để domain chậm vẫn tiến dần, không bị bỏ hẳn
        quota = {d: max(1, int(n * rr[d] / tot)) for d in active}
    else:
        quota = {d: max(1, n // len(active)) for d in active}

    rows = []
    for dom in active:
        rows += conn.execute(
            f"SELECT doc_id, url, domain FROM queue "
            f"WHERE domain=? AND state IN ({qs}){shard_sql} ORDER BY prio DESC LIMIT ?",
            (dom, *states, *shard_args, quota[dom])).fetchall()
    return interleave(rows)


# ---------------------------------------------------------------- fetch

# Trang chặn bot trả HTTP **200** kèm màn CAPTCHA, nên nó VÔ HÌNH với backoff: crawler coi
# là thành công, `AdaptiveLimiter` không chậm lại, càng đập càng bị chặn. Đo trên *.39.net
# (03/10): tỉ lệ dùng được tụt 46,0% -> 37,0% TRONG một đợt, body còn 11 ký tự, HTML 2.287 B,
# và cả 8 biến thể TLS/cookie đều không vượt được. Coi như 403 thì limiter tự chậm lại và
# URL ở lại FAILED để `--retry-failed` quét sau.
CAPTCHA_SIGNS = ("滑动拼图验证", "滑动验证", "验证码", "加载中…",
                 "slide to verify", "请完成验证")


def looks_captcha(text, raw_len):
    """True nếu trang là màn xác thực chống bot chứ không phải nội dung thật.

    Hai điều kiện cùng lúc: HTML nhỏ (trang thật của các site này đều > 20 KB) VÀ có dấu
    hiệu xác thực. Chỉ xét dấu hiệu thì sẽ nhận lầm bài viết NÓI VỀ captcha.
    """
    return raw_len < 8000 and any(sg in text for sg in CAPTCHA_SIGNS)


def cookie_challenge(body):
    """Trả (tên, giá trị) nếu phản hồi là thách đố cookie, ngược lại None.

    Chỉ xét phản hồi rất nhỏ: trang nội dung thật luôn lớn hơn CHALLENGE_MAX_BYTES, nên
    không có nguy cơ nhận lầm một trang bình thường có chứa `document.cookie`.
    """
    if not body or len(body) > CHALLENGE_MAX_BYTES:
        return None
    m = COOKIE_CHALLENGE.search(body)
    if not m:
        return None
    return m.group(1).decode("latin-1"), m.group(2).decode("latin-1")


# Profile TLS cho từng domain khi `chrome` bị chặn. ĐO 03/10 trên URL thật:
# vov.vn trả 403 với MỌI profile chrome* (chrome/chrome131/chrome124) nhưng 200 với
# safari17_0, firefox133 và edge101 → WAF của nó lọc đúng fingerprint Chrome.
# `nhathuoclongchau.com.vn`: `requests` luôn 403 (Cloudflare), `chrome` vượt được 33/33 mẫu.
# Để nó ngoài bảng này thì mỗi URL tốn HAI lượt `limiter.wait()` (403 rồi mới curl_cffi),
# tức rate hiệu dụng chỉ còn một nửa: đo được 1,5 trang/s ở mức cấu hình 3 req/s.
WAF_PROFILE = {"vov.vn": "firefox133", "nhathuoclongchau.com.vn": "chrome"}

# Domain chỉ trả 200 khi có cookie lấy từ trang chủ TRƯỚC: youmed.vn gọi thẳng trang bài
# thì 403 với cả 6 profile, nhưng home 200 → page 200. Hâm nóng một lần rồi dùng lại.
WAF_WARMUP = {"youmed.vn"}

_local = threading.local()      # Session không chia sẻ giữa thread: mỗi thread một bộ


def raise_fd_limit():
    """Nâng giới hạn file descriptor MỀM lên, trả (cũ, mới) nếu có đổi.

    Đo 04/10 trên máy GPU: `OSError(24, "Too many open files")` làm **83,2%** request thất bại
    (ConnectionError/SSLError trên 2.079/2.500 doc) và throughput tụt 46,6 -> 1,9 trang/s.
    Giới hạn mềm mặc định 1024, trong khi 80 thread × pool kết nối vượt số đó rất nhanh.
    Giới hạn CỨNG là 1.048.576 nên nâng được mà không cần quyền root.
    """
    try:
        import resource
    except ImportError:
        return None                      # Windows không có `resource`
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    want = min(hard, 65536)
    if soft >= want:
        return None
    try:
        resource.setrlimit(resource.RLIMIT_NOFILE, (want, hard))
    except (ValueError, OSError):
        return None
    return soft, want


def http_session():
    """`requests.Session` riêng mỗi thread, giữ keep-alive.

    `requests.get()` mở kết nối MỚI mỗi lần -> tra DNS lại mỗi URL. Với 200 thread đã làm
    ngập resolver của máy GPU: `Temporary failure in name resolution` cho cả `huggingface.co`,
    và 4.340 doc mang `status=None` (lỗi mạng) nên tỉ lệ dùng được tụt còn 41,6%. Session
    tái dùng kết nối theo host nên bỏ được phần lớn lượt tra DNS lẫn TLS handshake.
    """
    s = getattr(_local, "http", None)
    if s is None:
        import requests
        from requests.adapters import HTTPAdapter
        s = _local.http = requests.Session()
        # Pool NHỎ: mỗi thread chỉ chạy một request tại một thời điểm, nên `pool_maxsize`
        # lớn chỉ đốt file descriptor. Pool 32 × 80 thread = 2.560 socket -> vượt ulimit 1024
        # và 83,2% request chết với "Too many open files" (đo 04/10).
        ad = HTTPAdapter(pool_connections=6, pool_maxsize=2, max_retries=0)
        s.mount("http://", ad)
        s.mount("https://", ad)
    return s


def waf_session(domain, limiter):
    """curl_cffi Session cho `domain`, đúng profile và đã hâm nóng nếu domain cần cookie."""
    cache = getattr(_local, "waf", None)
    if cache is None:
        cache = _local.waf = {}
    s = cache.get(domain)
    if s is None:
        from curl_cffi import requests as creq
        s = cache[domain] = creq.Session(
            impersonate=WAF_PROFILE.get(domain, "chrome"))
        if domain in WAF_WARMUP:
            limiter.wait()
            try:
                s.get(f"https://{domain}/", headers=HEADERS, timeout=TIMEOUT)
            except Exception:
                pass                        # hâm nóng thất bại thì vẫn thử trang chính
    return s


def fetch(url, limiter):
    """requests trước; gặp status kiểu WAF thì thử lại bằng curl_cffi (giả TLS trình duyệt).

    Đo được: profile `chrome` mặc định vượt được Cloudflare của nhathuoclongchau.com.vn
    (33/33 mẫu), còn chrome116/chrome110/edge101 thì không. Nhưng `chrome` KHÔNG phải lựa
    chọn đúng cho mọi domain - xem `WAF_PROFILE`/`WAF_WARMUP`.
    """
    http = http_session()
    dom = domain_of(url)
    # Domain đã biết chắc chặn `requests` → đi thẳng curl_cffi, khỏi tốn 1 request vô ích
    # cho mỗi URL (vov.vn/youmed.vn: 403 chắc chắn ở lượt này, đo trên URL thật).
    if dom in WAF_PROFILE or dom in WAF_WARMUP:
        sess = waf_session(dom, limiter)
        limiter.wait()
        r2 = sess.get(url, headers={**HEADERS, "Referer": f"https://{dom}/"},
                      timeout=TIMEOUT, allow_redirects=True)
        return r2.status_code, r2.content, "curl_cffi"
    limiter.wait()
    r = http.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
    # Thách đố cookie (HTTP 200 nhưng thân rỗng + JS đặt cookie): set lại rồi gọi lần hai
    ch = cookie_challenge(r.content) if r.status_code == 200 else None
    if ch:
        limiter.wait()
        r2 = http.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True,
                      cookies={ch[0]: ch[1]})
        if r2.status_code == 200 and not cookie_challenge(r2.content):
            return r2.status_code, r2.content, "requests+cookie"
    if r.status_code in WAF_STATUS:
        sess = waf_session(dom, limiter)
        limiter.wait()
        r2 = sess.get(url, headers={**HEADERS, "Referer": f"https://{dom}/"},
                      timeout=TIMEOUT, allow_redirects=True)
        return r2.status_code, r2.content, "curl_cffi"
    return r.status_code, r.content, "requests"


_META_CHARSET = re.compile(rb"(?i)<meta[^>]+charset\s*=\s*[\"']?\s*([A-Za-z0-9_\-]+)")


def decode_html(raw, domain):
    """bytes -> str đã giải mã ĐÚNG bảng mã; không chắc thì trả nguyên `raw` (hành vi cũ).

    Đưa byte thô cho trafilatura thì nó tự đoán bảng mã, và với trang GBK mà header chỉ ghi
    `text/html` (không có charset) nó có thể đoán sai: đo 05/10, **7.229 doc (0,68%)** thành
    mojibake Cyrillic (`非物质文化遗产` -> `ЗЧЮяжЪЮФЛЏвХВњ`, tức byte GBK đọc bằng ISO-8859-5), gần hết
    ở `wujue.com` (14,4% doc của nó). Sửa sau khi đã trích thì KHÔNG khôi phục chính xác được: lúc
    trích nó đã chuẩn hoá NBSP và ký tự điều khiển C1 nên chuỗi byte GBK gốc không còn nguyên
    (chỉ 43/7.229 doc sửa được). Phải sửa ở đây.

    Thứ tự: (1) UTF-8 nghiêm ngặt (đa số trang); (2) charset khai báo trong <meta>, và nếu là
    gb2312/gbk thì dùng gb18030 (tập cha, không rớt ký tự hiếm); (3) domain tiếng Trung thì thử
    gb18030 nghiêm ngặt. Các bảng mã đơn byte (ISO-8859-x, cp125x) "giải mã được" mọi chuỗi byte
    nên KHÔNG được để chúng quyết định.
    """
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        pass
    m = _META_CHARSET.search(raw[:6000])
    if m:
        enc = m.group(1).decode("ascii", "ignore").lower()
        if enc in ("gb2312", "gbk", "gb18030"):
            return raw.decode("gb18030", "replace")       # trang tự khai là GBK thì tin nó
        try:
            return raw.decode(enc)
        except (LookupError, UnicodeDecodeError):
            pass
    if is_zh_domain(domain):
        try:
            return raw.decode("gb18030")
        except UnicodeDecodeError:
            pass
        # Cả hai đều lỗi nghiêm ngặt: trang hỏng nhẹ (vd. zydcd.com khai báo utf-8 nhưng thật ra
        # là GBK, lại có byte bị cắt dở trước thẻ đóng). Chọn bảng mã ÍT ký tự lỗi hơn; chỉ tin
        # khi tỉ lệ lỗi rất thấp, nếu không thì để trafilatura tự đoán như cũ.
        best = None
        for enc in ("utf-8", "gb18030"):
            t = raw.decode(enc, "replace")
            bad = t.count("�")
            if best is None or bad < best[0]:
                best = (bad, t)
        if best[0] <= max(5, len(raw) // 500):
            return best[1]
    return raw


def extract_doc(raw, url, domain):
    """Trích + chuẩn hoá + simhash. CHẠY TRONG PROCESS RIÊNG.

    Đo được: trafilatura tốn ~59 ms CPU mỗi trang (max 2.025 ms). Làm trong thread thì GIL
    hoá tuần tự → trần ~17 trang/s bất kể có bao nhiêu thread, và đó chính là nghẽn thật
    (rate limit của 45 domain cho trần 225 trang/s, nhưng đo được 7,8). Process pool thoát
    GIL: 8 core → ~137 trang/s lý thuyết.
    """
    import trafilatura
    out = {"title": "", "descr": "", "tags": None, "pub_date": None, "body": "",
           "raw_html": None, "simhash": 0, "extra_via": ""}
    src = decode_html(raw, domain)       # tự giải mã đúng bảng mã, xem decode_html
    try:
        d = trafilatura.bare_extraction(src, url=url, with_metadata=True, include_tables=True,
                                        include_comments=False)
        d = (d if isinstance(d, dict) else d.as_dict()) if d else {}
    except Exception:
        d = {}
    body = d.get("text") or ""
    if len(body.strip()) < 200:                     # trafilatura trượt -> thử fallback
        fb = extract_fallback(src.encode("utf-8") if isinstance(src, str) else src)
        if fb and len(fb.strip()) > len(body.strip()):
            body = fb
            out["extra_via"] = "+fallback"

    out["title"] = (d.get("title") or "").strip()
    out["descr"] = (d.get("description") or "").strip()
    tags = (d.get("tags") or []) + (d.get("categories") or [])
    out["tags"] = json.dumps(tags, ensure_ascii=False) if tags else None
    out["pub_date"] = d.get("date")
    out["body"] = normalize(body)
    out["lang"] = detect_lang(out["body"] or out["title"], domain)
    if len(out["body"]) >= 200:
        out["simhash"] = simhash64(out["body"])
    else:
        # Trích thất bại dù HTTP 200 -> giữ HTML để viết parser, KHÔNG crawl lại 20 giờ
        out["raw_html"] = raw[:400_000].decode("utf-8", "replace")
    return out


def crawl_one(item, limiters, pool=None):
    """Trả về bản ghi doc đã sẵn sàng ghi vào DB. Mọi lỗi là dữ liệu, không phải crash.

    Phần mạng chạy ở thread này; phần trích (CPU) đẩy sang `pool` để thoát GIL.
    `pool=None` thì trích ngay tại đây - dùng cho self-check và chạy nhỏ.
    """
    doc_id, url, dom = item
    rec = {"doc_id": doc_id, "url": url, "domain": dom, "lang": None, "status": None,
           "err": None, "via": None, "title": "", "descr": "", "tags": None,
           "pub_date": None, "body": "", "raw_html": None, "simhash": 0}
    try:
        status, raw, via = fetch(url, limiters[dom])
        rec["status"], rec["via"] = status, via
    except Deferred:
        rec["deferred"] = True          # không ghi, không đếm: URL quay lại hàng đợi lô sau
        return rec
    except Exception as e:
        rec["err"] = f"{type(e).__name__}: {e}"[:200]
        return rec
    if status != 200 or not raw:
        return rec

    try:
        got = pool.submit(extract_doc, raw, url, dom).result() if pool \
            else extract_doc(raw, url, dom)
    except Exception as e:                  # worker chết thì ghi lỗi, không kéo cả run xuống
        rec["err"] = f"extract {type(e).__name__}: {e}"[:200]
        return rec
    rec["via"] = (rec["via"] or "") + got.pop("extra_via", "")
    rec.update(got)
    # CAPTCHA đến dưới dạng 200 -> đổi thành 403 để `AdaptiveLimiter` phạt domain và URL
    # ở lại FAILED, thay vì ghi 11 ký tự rác rồi tiếp tục đập vào server
    if looks_captcha((rec.get("title") or "") + (rec.get("body") or ""), len(raw)):
        rec["status"], rec["err"] = 403, "captcha"
        rec["body"], rec["title"], rec["descr"] = "", "", ""
    return rec


# ---------------------------------------------------------------- vòng chính

def write_one(conn, rec, tries=6):
    """Ghi một doc, chịu được `database is locked`. Trả True nếu ghi được.

    HAI crawler ghi chung một store là có thật (một chạy `--lang zh`, một chạy
    `--domains nhathuoclongchau.com.vn`), và `timeout=60` ở `connect` KHÔNG đủ: đo 04/10,
    `writer_loop` ăn `OperationalError: database is locked`, thread ghi CHẾT HẲN vì không bắt
    exception, nên crawler vẫn fetch mà store đứng ở 500 doc suốt 35 phút. Lùi theo hàm mũ
    rồi bỏ qua doc đó - URL vẫn ở PENDING nên lần sau crawl lại, không mất gì.
    """
    for i in range(tries):
        try:
            conn.execute(
                f"INSERT OR REPLACE INTO doc ({','.join(COLS)}, fetched) "
                f"VALUES ({','.join('?' * len(COLS))}, datetime('now'))",
                tuple(rec.get(c) for c in COLS))
            state = DONE if len(rec.get("body") or "") >= 200 else FAILED
            conn.execute("UPDATE queue SET state=? WHERE doc_id=?", (state, rec["doc_id"]))
            return True
        except sqlite3.OperationalError as e:
            if "locked" not in str(e).lower() and "busy" not in str(e).lower():
                raise
            time.sleep(0.2 * 2 ** i)
    return False


# Commit NGẮN để hai crawler ghi chung store được. Ở 200 doc và 3 trang/s, một transaction
# giữ write-lock gần 67 GIÂY - crawler kia chờ hết `timeout=60` rồi bỏ sạch doc, nên store
# đứng im dù cả hai vẫn fetch (đo 04/10). 25 doc ≈ 8 giây lock, vừa trong hạn chờ.
# `synchronous=NORMAL` nên commit thường xuyên hơn gần như không tốn thêm.
COMMIT_EVERY = 25


def writer_loop(conn, q, commit_every=COMMIT_EVERY):
    """Một thread ghi duy nhất: SQLite không thích nhiều writer.

    Thread này KHÔNG được phép chết: nó là nơi duy nhất ghi vào store, nên một exception
    không bắt là crawler chạy không tải - fetch bình thường, lưu được 0 doc.
    """
    n = skipped = 0
    while True:
        rec = q.get()
        if rec is None:
            break
        try:
            if write_one(conn, rec):
                n += 1
            else:
                skipped += 1
                if skipped in (1, 10, 100, 1000):
                    print(f"  ⚠️ store bị khoá, đã bỏ qua {skipped} doc "
                          f"(URL vẫn PENDING, sẽ crawl lại)")
        except Exception as e:                  # không để thread ghi chết vì bất cứ gì
            skipped += 1
            print(f"  ⚠️ lỗi ghi {type(e).__name__}: {str(e)[:120]}")
        if n and n % commit_every == 0:
            try:
                conn.commit()
            except sqlite3.OperationalError:
                pass                            # commit sau sẽ gộp luôn phần này
    try:
        conn.commit()
    except sqlite3.OperationalError:
        pass


def penalty_kind(rec):
    """Lý do phạt limiter của domain, hoặc None nếu KHÔNG nên phạt.

    Phạt khi server phản đối TỐC ĐỘ: 403/429/503 (status), lỗi kết nối bị từ chối/ngắt
    (`NewConnectionError`, reset), và CAPTCHA (đã đổi thành 403). KHÔNG phạt `ReadTimeout`:
    đo 05/10 trên `cnkang.com`, timeout là server chậm ngẫu nhiên chứ không do ta gửi nhanh -
    ở 0,5 req/s vẫn timeout 51%, ở rate 6 chỉ 19%, và tải lại từng URL timeout với 1 yêu cầu mỗi
    1,5 giây thì 4/8 vẫn treo. Phạt timeout làm hạ `cnkang` từ 6 xuống 0,75 req/s (mất gấp 8 lần
    thông lượng) mà timeout không giảm chút nào.
    """
    st, err = rec.get("status"), rec.get("err") or ""
    if st in BACKOFF_STATUS:
        return str(st)
    if st is None and err and "ReadTimeout" not in err:
        return "lỗi mạng"
    return None


def run(conn, workers, batch, limit, retry_failed, retry_blocked, procs=None,
        domains=None, shard_ids=None):
    limiters = collections.defaultdict(lambda: AdaptiveLimiter(DEFAULT_RATE))
    for dom, rate in RATES.items():
        limiters[dom] = AdaptiveLimiter(rate)

    bumped = raise_fd_limit()
    if bumped:
        print(f"Giới hạn file descriptor: {bumped[0]} -> {bumped[1]}")

    q = queue.Queue(maxsize=2000)
    wt = threading.Thread(target=writer_loop, args=(conn, q), daemon=True)
    wt.start()

    done = ok = 0
    t0 = time.monotonic()
    nproc = procs if procs is not None else max(1, (os.cpu_count() or 4) - 1)
    pool = ProcessPoolExecutor(nproc) if nproc > 1 else None
    print(f"{workers} thread mạng + {nproc} process trích nội dung")
    try:
        with ThreadPoolExecutor(workers) as ex:
            while limit is None or done < limit:
                n = batch if limit is None else min(batch, limit - done)
                # Rate HIỆN TẠI (đã tính backoff) để chia hạn mức theo tỉ lệ
                cur_rates = {d: 1.0 / lim.interval for d, lim in limiters.items()
                             if getattr(lim, "interval", 0) > 0}
                items = take_batch(conn, n, retry_failed, retry_blocked, domains,
                                   cur_rates or None, shard_ids)
                if not items:
                    print("Hết URL cần crawl.")
                    break
                # `as_completed`, KHÔNG `ex.map`: map trả kết quả theo thứ tự GỬI, nên một
                # request mắc kẹt (socket CloseWait sau khi đổi mạng, timeout không nổ) làm
                # đứng cả crawl - 79 thread xong rồi mà vòng lặp vẫn chờ item đầu. Đã gặp:
                # 48 phút không ghi doc nào, CPU gần 0, trong khi mạng hoàn toàn bình thường.
                done_at_start = done
                futs = [ex.submit(crawl_one, it, limiters, pool) for it in items]
                pending = set(futs)
                stuck = 0
                while pending:
                    got, pending = wait(pending, timeout=BATCH_STALL_SEC,
                                        return_when=FIRST_COMPLETED)
                    if not got:
                        # Không cái nào xong trong BATCH_STALL_SEC -> bỏ phần còn lại.
                        # URL bị bỏ vẫn ở state PENDING nên lần sau crawl lại, không mất.
                        stuck = len(pending)
                        print(f"  ⚠️ {stuck} request mắc kẹt > {BATCH_STALL_SEC}s → bỏ qua "
                              f"batch này, URL vẫn PENDING và sẽ crawl lại")
                        for f in pending:
                            f.cancel()
                        break
                    for fut in got:
                        try:
                            rec = fut.result()
                        except Exception as e:
                            print(f"  ⚠️ lỗi worker: {type(e).__name__}: {e}")
                            continue
                        if rec.get("deferred"):
                            continue                # hoãn: không ghi, không tính vào `done`
                        q.put(rec)
                        done += 1
                        ok += len(rec.get("body") or "") >= 200
                        # Thành công -> cho domain nới dần về mức gốc (xem AIMD)
                        if rec.get("status") == 200:
                            lim = limiters[rec["domain"]]
                            if hasattr(lim, "reward") and lim.reward():
                                pass        # nới âm thầm, không spam log
                        # Server phản đối -> chậm domain đó lại ngay. LỖI MẠNG CŨNG TÍNH:
                        # nhiều server zh không trả 429 mà DROP kết nối, nên `status` là None
                        # và limiter không bao giờ phạt -> crawler đập mãi ở 12 req/s. Đo
                        # 04/10: NewConnectionError chiếm 59,5% doc zh (1.709/2.870) đúng ở ba
                        # domain LỚN nhất (cnkang 963k, 120ask 918k, ask.39.net 337k), trong
                        # khi longchau cùng lúc vẫn 99,9% -> mạng không hỏng, là bị chặn.
                        why = penalty_kind(rec)
                        if why:
                            lim = limiters[rec["domain"]]
                            if hasattr(lim, "penalize"):
                                before = lim.interval
                                n_str, iv = lim.penalize(soft=(why == "lỗi mạng"))
                                if iv != before and n_str in (1, 5, 20, 100):
                                    print(f"  ⚠️ {rec['domain']} {why} "
                                          f"({n_str} lần) → hạ xuống {1/iv:.2f} req/s")
                        if done % 500 == 0:
                            rate = done / (time.monotonic() - t0)
                            left = (f" | còn lại ~{(limit - done) / rate / 3600:.1f}h"
                                    if limit else "")
                            print(f"  {done:,} xong | dùng được {ok/done*100:.1f}% | "
                                  f"{rate:.1f} trang/s{left}")
                if done == done_at_start:
                    time.sleep(1.0)         # cả lô bị hoãn: đừng quay vòng nóng lấy lại URL cũ
    finally:
        q.put(None)
        wt.join()
        if pool:
            pool.shutdown()
    el = time.monotonic() - t0
    print(f"\nXong {done:,} URL trong {el/60:.1f} phút | dùng được {ok:,} "
          f"({ok/max(done,1)*100:.1f}%) | {done/max(el,1):.1f} trang/s")


def stats(conn):
    print("--- Queue ---")
    names = {PENDING: "chờ", DONE: "xong", FAILED: "thất bại", BLOCKED_ST: "bị chặn"}
    tot = 0
    for st, n in conn.execute("SELECT state, count(*) FROM queue GROUP BY state"):
        print(f"  {names.get(st, st):10} {n:>10,}")
        tot += n
    print(f"  {'tổng':10} {tot:>10,}")
    nd = conn.execute("SELECT count(*) FROM doc WHERE length(body)>=200").fetchone()[0]
    if nd:
        row = conn.execute("SELECT avg(length(body)), sum(length(body)), "
                           "sum(title!=''), sum(descr!=''), sum(tags IS NOT NULL) "
                           "FROM doc WHERE length(body)>=200").fetchone()
        print(f"\n--- Doc dùng được: {nd:,} ---")
        print(f"  body trung bình {row[0]:.0f} ký tự | tổng {row[1]/1024**3:.2f} GB")
        print(f"  title {row[2]/nd*100:.0f}% | descr {row[3]/nd*100:.0f}% | "
              f"tags {row[4]/nd*100:.0f}%")
        print("\n--- 12 domain yếu nhất (có ≥20 lượt thử) ---")
        for dom, n, good in conn.execute(
                "SELECT domain, count(*), sum(length(body)>=200) FROM doc "
                "GROUP BY domain HAVING count(*)>=20 ORDER BY 1.0*sum(length(body)>=200)/count(*) "
                "LIMIT 12"):
            print(f"  {good/n*100:5.0f}%  {good:>6,}/{n:<6,}  {dom}")


# ---------------------------------------------------------------- self-check

def demo():
    HTML = b"""<html><head><title>Viem da day trot xung huyet man tinh</title>
    <meta name="description" content="Tom tat benh"></head><body>
    <nav>Trang chu | Lien he</nav>
    <article><p>Viem da day trot xung huyet man tinh la tinh trang niem mac da day bi viem
    va tron keo dai nhieu thang o nguoi lon tuoi.</p>
    <p>Dieu tri bang thuoc uc che bom proton ket hop khang sinh neu co vi khuan HP, thoi gian
    thuong tu bon den tam tuan tuy muc do ton thuong.</p></article>
    <footer>Copyright 2026</footer></body></html>"""

    import trafilatura
    d = trafilatura.bare_extraction(HTML, with_metadata=True)
    d = d if isinstance(d, dict) else d.as_dict()
    body = normalize(d["text"])
    assert "niem mac da day" in body
    assert "Copyright" not in body and "Trang chu" not in body, body

    # normalize: giữ '\n', gộp khoảng trắng ngang, không phá nội dung
    assert normalize("a  \t b\n\n\n c ") == "a b\n\nc"
    assert normalize("dòng1\ndòng2") == "dòng1\ndòng2"
    # CRLF và CR đơn lẻ phải thành '\n' (ca thật từ baotayninh.vn)
    assert normalize("COVID-19.\r\n\r\nTiêm vaccine") == "COVID-19.\n\nTiêm vaccine"
    assert normalize("a\rb") == "a\nb"
    assert "\r" not in normalize("x\r\n \r\n y")
    # Khoảng trắng Unicode khác cũng phải gộp
    assert normalize("a\u2003\u2003b") == "a b"

    # fallback phải lấy được nội dung khi trafilatura bó tay
    NOART = b"<html><body><div id=x>" + b"Noi dung that rat dai. " * 20 + \
            b"</div><div>ngan</div><script>var a=1</script></body></html>"
    fb = extract_fallback(NOART)
    assert fb and "Noi dung that" in fb and "var a" not in fb, fb
    assert extract_fallback(b"<html><body><div>qua ngan</div></body></html>") is None

    # AdaptiveLimiter: phạt phải giãn gấp đôi, có chặn trên, và giữ nguyên hành vi chờ
    al = AdaptiveLimiter(10)                 # interval 0,1 s
    assert abs(al.interval - 0.1) < 1e-9
    n1, i1 = al.penalize()
    assert n1 == 1 and abs(i1 - 0.2) < 1e-9, (n1, i1)
    n2, i2 = al.penalize()
    assert n2 == 2 and abs(i2 - 0.4) < 1e-9, (n2, i2)
    for _ in range(50):
        al.penalize()
    assert al.interval == AdaptiveLimiter.MAX_INTERVAL, al.interval
    assert al.base == 0.1, "phải giữ mức gốc để biết đã hạ bao nhiêu"
    # Vẫn phải chờ được (kế thừa RateLimiter), không làm hỏng hành vi cũ
    AdaptiveLimiter(1000).wait()
    # 429 phải nằm trong danh sách phạt, 404 thì không
    assert 429 in BACKOFF_STATUS and 403 in BACKOFF_STATUS
    assert 404 not in BACKOFF_STATUS and 200 not in BACKOFF_STATUS

    # Nâng ulimit: không được crash trên máy đã ở mức cao, cũng không crash trên Windows
    raise_fd_limit()

    # Giải mã HTML: trang GBK không khai báo charset ở header KHÔNG được thành mojibake Cyrillic
    zh_txt = "非物质文化遗产是指各族人民世代相传并视为其文化遗产组成部分的各种传统文化表现形式。" * 6
    gbk_page = (f"<html><head><meta http-equiv=\"Content-Type\" content=\"text/html; "
                f"charset=gb2312\"><title>非物质文化遗产</title></head><body><p>{zh_txt}</p>"
                f"</body></html>").encode("gb18030")
    assert decode_html(gbk_page, "wujue.com").count("非物质") >= 6, "meta gb2312 phải giải mã đúng"
    nometa = f"<html><body><p>{zh_txt}</p></body></html>".encode("gb18030")
    assert "非物质" in decode_html(nometa, "cnkang.com"), "domain zh, không meta, GBK phải đúng"
    utf = f"<html><body><p>{zh_txt}</p></body></html>".encode("utf-8")
    assert "非物质" in decode_html(utf, "cnkang.com"), "UTF-8 phải giữ nguyên"
    vi = "<html><body><p>Viêm dạ dày trợt xung huyết</p></body></html>".encode("utf-8")
    assert "Viêm" in decode_html(vi, "vinmec.com")
    # trang khai báo utf-8 nhưng thật ra là GBK và có byte bị cắt dở (đúng ca zydcd.com, 05/10)
    lying = (f"<html><head><meta charset=\"utf-8\"></head><body><p>{zh_txt}</p>"
             .encode("gb18030") + b"\xb8</p></body></html>")
    got_l = decode_html(lying, "zydcd.com")
    assert isinstance(got_l, str) and got_l.count("非物质") >= 6, "GBK khai báo sai utf-8 phải ra Hán"
    odd = b"<html><body>\xff\xfe\xfd</body></html>"
    assert decode_html(odd, "vinmec.com") == odd, "domain không phải zh, không rõ bảng mã: giữ raw"
    got = extract_doc(gbk_page, "http://wujue.com/x.html", "wujue.com")
    assert "非物质" in got["body"], f"extract_doc ra mojibake: {got['body'][:40]!r}"
    assert not any("Ѐ" <= ch <= "ӿ" for ch in got["body"]), "body còn ký tự Cyrillic"

    # Khoá một-crawler-một-store: cái thứ hai PHẢI bị từ chối, và nhả khoá khi cái đầu thoát
    import subprocess, tempfile
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as _d:
        _db = os.path.join(_d, "x.sqlite")
        _lk = acquire_instance_lock(_db)
        _probe = [sys.executable, "-c",
                  "import sys; sys.path.insert(0, %r); import crawler; "
                  "crawler.acquire_instance_lock(%r)" % (os.path.dirname(os.path.abspath(__file__)), _db)]
        _r = subprocess.run(_probe, capture_output=True, text=True)
        assert _r.returncode != 0 and "DUNG" in (_r.stderr + _r.stdout),             "crawler thứ hai phải bị từ chối khi store đang có crawler khác"
        _lk.close()
        _r2 = subprocess.run(_probe, capture_output=True, text=True)
        assert _r2.returncode == 0, f"đóng khoá xong thì crawler khác phải chạy được: {_r2.stderr[-200:]}"

    # Phân loại phạt: server phản đối tốc độ thì phạt, timeout (server chậm) thì KHÔNG
    assert penalty_kind({"status": 429}) == "429" and penalty_kind({"status": 403}) == "403"
    assert penalty_kind({"status": None, "err": "ConnectionError: NewConnectionError"}) == "lỗi mạng"
    assert penalty_kind({"status": None, "err": "ReadTimeout: HTTPSConnectionPool"}) is None,         "ReadTimeout không do rate, phạt nó chỉ làm mất thông lượng"
    assert penalty_kind({"status": 200, "err": None}) is None
    assert penalty_kind({"status": 404, "err": None}) is None

    # Hàng đợi domain quá dài thì HOÃN, không ngủ giữ luồng (05/10: cả 160 luồng ngủ chờ một domain)
    dl = AdaptiveLimiter(4.0)
    dl.interval = 30.0                           # 0,033 req/s
    dl.wait()                                    # lượt đầu không phải chờ, đặt next_t = +30s
    nt = dl.next_t
    t_d = time.monotonic()
    try:
        dl.wait()                                # slot ở +30s > MAX_QUEUE_WAIT -> phải hoãn NGAY
        raise AssertionError("phải raise Deferred khi hàng đợi quá MAX_QUEUE_WAIT")
    except Deferred:
        pass
    assert time.monotonic() - t_d < 0.5, "hoãn phải tức thì, không được ngủ"
    assert dl.next_t == nt, "hoãn KHÔNG được đặt chỗ (next_t không đổi)"
    got_d = crawl_one(("1", "http://invalid.invalid/x", "d.vn"),
                      collections.defaultdict(lambda: dl), None)
    assert got_d.get("deferred") is True and got_d["err"] is None and got_d["status"] is None, \
        "URL bị hoãn không được ghi lỗi/FAILED"

    # Luồng chính KHÔNG được bị chặn bởi luồng đang ngủ trong wait(): penalize()/reward() phải trả
    # về ngay dù có luồng khác đang chờ lượt ở rate rất thấp (đã làm crawler đứng 15 phút)
    import threading
    slow = AdaptiveLimiter(4.0)
    slow.interval = 1.5
    slow.wait()                                  # lượt đầu: không phải chờ
    sleeper = threading.Thread(target=slow.wait)
    sleeper.start()                              # lượt hai: ngủ ~1,5 giây
    time.sleep(0.2)
    t0 = time.monotonic()
    slow.penalize(); slow.reward()
    held = time.monotonic() - t0
    sleeper.join()
    assert held < 0.3, f"penalize/reward bị chặn {held:.2f}s bởi luồng đang ngủ trong wait()"
    # và nhịp request vẫn đúng: hai lượt liên tiếp cách nhau >= interval
    gap = AdaptiveLimiter(10.0)
    gap.wait(); t1 = time.monotonic(); gap.wait()
    assert time.monotonic() - t1 >= 0.09, "wait() phải giữ khoảng cách tối thiểu giữa hai request"

    # Nới theo THỜI GIAN: limiter bị hạ sát đáy phải TỰ về lại base sau một lúc, không kẹt vĩnh
    # viễn chờ chuỗi thắng liên tiếp (đã làm crawl đứng hàng giờ ở CPU 2%, 04/10)
    rl = AdaptiveLimiter(4.0)                    # base = 0,25 s
    for _ in range(12):
        rl.penalize()                            # xuống sát MAX_INTERVAL
    assert rl.interval > 10, "phải đã bị hạ sát đáy"
    t0 = rl.last_penalty
    assert rl.recover(t0 + 10) is False, "chưa đủ RECOVER_AFTER thì không được nới"
    before = rl.interval
    assert rl.recover(t0 + AdaptiveLimiter.RECOVER_AFTER + 1) is True
    assert abs(rl.interval - before / AdaptiveLimiter.EASE) < 1e-9, "mỗi lần nới đúng một bậc"
    assert rl.recover(rl.last_penalty + 10) is False, "bậc kế phải đợi thêm RECOVER_AFTER"
    now = rl.last_penalty
    for _ in range(100):                         # nới mãi phải dừng ĐÚNG ở base
        now += AdaptiveLimiter.RECOVER_AFTER + 1
        rl.recover(now)
    assert rl.interval == rl.base, "nới phải dừng ở base, không nhanh hơn"
    rl.penalize()                                # bị phạt lại thì đồng hồ phải reset
    assert rl.recover(rl.last_penalty + 10) is False

    # writer_loop phải SỐNG khi store bị khoá. Giả một conn luôn báo locked: thread ghi
    # không được thoát, và doc bị bỏ qua phải để URL ở PENDING cho lần crawl sau.
    class LockedConn:
        def execute(self, *a):
            raise sqlite3.OperationalError("database is locked")

        def commit(self):
            pass

    assert write_one(LockedConn(), {"doc_id": "1", "body": "x" * 300}, tries=2) is False
    lq = queue.Queue()
    lq.put({"doc_id": "1", "body": "x" * 300})
    lq.put(None)
    writer_loop(LockedConn(), lq)            # phải trả về bình thường, không raise

    # CAPTCHA: phải bắt được trang xác thực, và KHÔNG nhận lầm bài viết nói về captcha
    assert looks_captcha("39健康 滑动拼图验证 加载中…", 2287)
    assert not looks_captcha("39健康 滑动拼图验证 加载中…", 50000),         "HTML lớn là trang thật, dù có chữ xác thực trong nội dung"
    assert not looks_captcha("Bài viết bàn về cách vượt captcha của website", 3000)

    # Session WAF: đúng profile theo domain, cache lại (không tạo mới mỗi request), và
    # chỉ hâm nóng domain nằm trong WAF_WARMUP. `chrome` là mặc định cho domain khác.
    # AIMD: phạt rồi thưởng phải quay dần về base, và KHÔNG được vượt base
    al2 = AdaptiveLimiter(10.0)                 # base = 0,1 s
    al2.penalize(); al2.penalize()              # 0,1 -> 0,4
    assert abs(al2.interval - 0.4) < 1e-9

    # Lỗi mạng LẺ TẺ không được phạt: 9 lỗi trong cửa sổ giữ nguyên rate, lỗi thứ 10 mới phạt.
    # (cnkang: ~1 lỗi/70 giây vẫn bị kéo về sàn khi mỗi lỗi đều phạt, 05/10)
    lone = AdaptiveLimiter(6.0)
    iv0 = lone.interval
    for _ in range(AdaptiveLimiter.SOFT_BURST - 1):
        lone.penalize(soft=True)
    assert lone.interval == iv0 and lone.strikes == 0, "lỗi lẻ không được phạt"
    lone.penalize(soft=True)
    assert lone.interval > iv0 and lone.strikes == 1, "đủ một loạt thì phải phạt"
    # lỗi rải rác (mỗi lỗi cách nhau > cửa sổ) KHÔNG BAO GIỜ gộp thành một loạt
    spread = AdaptiveLimiter(6.0)
    for k in range(40):
        spread.penalize(soft=True, now=1000.0 + k * (AdaptiveLimiter.SOFT_WINDOW + 5))
    assert spread.interval == spread.base, "40 lỗi rải rác không được hạ rate"
    # 1 lỗi mỗi 70 giây (đúng nhịp đo được ở cnkang) cũng không bao giờ thành một loạt
    cn = AdaptiveLimiter(6.0)
    for k in range(60):
        cn.penalize(soft=True, now=5000.0 + k * 70)
    assert cn.interval == cn.base and cn.strikes == 0, "cnkang 1 lỗi/70s không được bị phạt"

    # Phạt MỀM (lỗi mạng) phải nhẹ hơn và có chặn dưới: một LOẠT lỗi không được làm chậm ×32
    al3 = AdaptiveLimiter(4.0)                  # base = 0,25 s
    for _ in range(5 * AdaptiveLimiter.SOFT_BURST):
        al3.penalize(soft=True)
    assert al3.interval <= al3.base * AdaptiveLimiter.SOFT_CAP + 1e-9,         f"phạt mềm vượt chặn dưới: {1/al3.interval:.2f} req/s"
    assert 1 / al3.interval >= 0.5, f"5 lỗi mạng không được hạ dưới 0,5 req/s, đang {1/al3.interval:.2f}"
    al4 = AdaptiveLimiter(4.0)
    for _ in range(5):
        al4.penalize()                          # phạt CỨNG vẫn phải gắt như cũ
    assert al4.interval > al3.interval, "429/403 phải bị phạt nặng hơn lỗi mạng"
    for _ in range(AdaptiveLimiter.WIN_STREAK - 1):
        assert al2.reward() is None, "chưa đủ chuỗi thắng thì không được nới"
    assert abs(al2.reward() - 0.4 / AdaptiveLimiter.EASE) < 1e-9
    for _ in range(AdaptiveLimiter.WIN_STREAK * 10):
        al2.reward()
    assert al2.interval == al2.base, "nới phải dừng đúng ở base, không nhanh hơn"
    assert al2.reward() is None
    al2.penalize()                              # phạt lại phải reset chuỗi thắng
    assert al2.wins == 0

    assert WAF_PROFILE["vov.vn"] == "firefox133", "vov.vn chặn mọi profile chrome*"
    assert "youmed.vn" in WAF_WARMUP and "vov.vn" not in WAF_WARMUP
    _local.waf = None
    s1 = waf_session("khong-ton-tai.invalid", AdaptiveLimiter(1000))
    assert waf_session("khong-ton-tai.invalid", AdaptiveLimiter(1000)) is s1,         "phải dùng lại Session đã có, nếu không thì mất cookie và tốn handshake"
    assert waf_session("vov.vn", AdaptiveLimiter(1000)) is not s1, "mỗi domain một Session"
    _local.waf = None

    # Thách đố cookie: phải bắt được, và KHÔNG nhận lầm trang thật
    CH = (b'<html><body><script>document.cookie="D1N=af1d42e1fd6ed5396337f3234bdd576a"'
          b'+"; expires=Fri, 31 Dec 2099 23:59:59 GMT; path=/";'
          b'window.location.reload(true);</script></body></html>')
    assert cookie_challenge(CH) == ("D1N", "af1d42e1fd6ed5396337f3234bdd576a"), \
        cookie_challenge(CH)
    assert cookie_challenge(b"<html><body>noi dung that</body></html>") is None
    # Trang THẬT có chứa document.cookie nhưng lớn -> không được nhận lầm
    assert cookie_challenge(b'x' * 5000 + b'document.cookie="a=b"') is None
    assert cookie_challenge(b"") is None and cookie_challenge(None) is None

    # lang
    assert detect_lang("2型糖尿病空腹血糖10点高吗，需要注意饮食和运动管理", "ask.39.net") == "zh"
    assert detect_lang("viêm dạ dày trợt xung huyết mạn tính", "suckhoedoisong.vn") == "vi"
    assert detect_lang("", "familydoctor.com.cn") == "zh"

    # simhash: gần trùng phải gần nhau, khác hẳn phải xa; và vừa int64 của SQLite
    a = simhash64("mot hai ba bon nam sau bay tam chin muoi " * 5)
    b = simhash64("mot hai ba bon nam sau bay tam chin muoi mot " * 5)
    c = simhash64("hoan toan khac biet khong lien quan gi ca het " * 5)
    d64 = lambda x, y: bin((x ^ y) & 0xFFFFFFFFFFFFFFFF).count("1")
    assert d64(a, b) < d64(a, c), (d64(a, b), d64(a, c))
    assert -(2**63) <= a < 2**63 and simhash64("") == 0

    # store: ghi, resume, và đếm trạng thái
    conn = open_db(":memory:")
    conn.executemany("INSERT INTO queue VALUES (?,?,?,?,?)", [
        ("1", "http://a.vn/x", "a.vn", 9.0, PENDING),
        ("2", "http://a.vn/y", "a.vn", 1.0, PENDING),
        ("3", "http://familydoctor.com.cn/z", "familydoctor.com.cn", 5.0, BLOCKED_ST)])
    conn.commit()
    got = take_batch(conn, 10)
    assert [r[0] for r in got] == ["1", "2"], "BLOCKED không được lấy ra, và phải theo prio"
    assert sorted(r[0] for r in take_batch(conn, 10, retry_blocked=True)) == ["1", "2", "3"]

    # interleave: xen kẽ domain, nhưng trong cùng domain phải giữ thứ tự ưu tiên
    items = [("a1", "u", "A"), ("a2", "u", "A"), ("a3", "u", "A"),
             ("b1", "u", "B"), ("c1", "u", "C")]
    mixed = [i[0] for i in interleave(items)]
    assert mixed == ["a1", "b1", "c1", "a2", "a3"], mixed
    assert len(mixed) == len(items) and set(mixed) == {i[0] for i in items}
    assert interleave([]) == []

    # bộ lọc domain
    assert [r[0] for r in take_batch(conn, 10, domains=["a.vn"])] == ["1", "2"]
    # --shard-ids: N phần phải KHÔNG chồng lấn và HỢP LẠI đủ tập, nếu không thì hoặc crawl
    # trùng (phí rate limit) hoặc bỏ sót URL (mất dữ liệu mà không ai biết)
    for N in (2, 3):
        parts = [{r[0] for r in take_batch(conn, 100, shard_ids=(i, N))} for i in range(N)]
        allp = {r[0] for r in take_batch(conn, 100)}
        assert sum(len(p) for p in parts) == len(allp), f"chồng lấn/sót với N={N}: {parts}"
        assert set().union(*parts) == allp, f"không phủ đủ với N={N}"
    assert take_batch(conn, 10, domains=["khong-ton-tai.vn"]) == []

    # HẠN MỨC THEO DOMAIN: một domain đông không được chiếm hết batch
    bc = open_db(":memory:")
    bc.executemany("INSERT INTO queue VALUES (?,?,?,?,?)",
                   [(f"big{i}", "u", "dong.vn", 100.0 - i, PENDING) for i in range(500)]
                   + [(f"s{i}", "u", f"it{i}.vn", 0.0, PENDING) for i in range(4)])
    bc.commit()
    got = take_batch(bc, 50)
    doms = collections.Counter(r[2] for r in got)
    assert doms["dong.vn"] <= 12, f"domain đông chiếm {doms['dong.vn']}/50 - vẫn dồn batch"
    assert len(doms) == 5, f"phải có cả 5 domain trong batch: {doms}"
    assert all(n >= 1 for n in doms.values()), doms
    # Trong cùng domain vẫn phải theo thứ tự ưu tiên
    big = [r[0] for r in got if r[2] == "dong.vn"]
    assert big == sorted(big, key=lambda x: int(x[3:])), big

    # HẠN MỨC TỈ LỆ TỐC ĐỘ: domain bị hạ rate phải nhận ÍT URL hơn hẳn
    rc = open_db(":memory:")
    rc.executemany("INSERT INTO queue VALUES (?,?,?,?,?)",
                   [(f"f{i}", "u", "nhanh.vn", 0.0, PENDING) for i in range(400)]
                   + [(f"s{i}", "u", "cham.vn", 0.0, PENDING) for i in range(400)])
    rc.commit()
    got2 = collections.Counter(
        r[2] for r in take_batch(rc, 100, rates={"nhanh.vn": 12.0, "cham.vn": 0.03}))
    assert got2["nhanh.vn"] > 50, got2
    assert got2["cham.vn"] <= 2, f"domain chậm phải nhận rất ít: {got2}"
    assert got2["cham.vn"] >= 1, "nhưng không được bỏ hẳn, phải tiến dần"
    # Không truyền rates -> chia đều như cũ
    even = collections.Counter(r[2] for r in take_batch(rc, 100))
    assert abs(even["nhanh.vn"] - even["cham.vn"]) <= 1, even

    # Phân loại ngôn ngữ theo domain
    for d in ("cnkang.com", "120ask.com", "familydoctor.com.cn", "tnb.39.net",
              "ask.39.net", "bingli.iiyi.com", "msdmanuals.cn"):
        assert is_zh_domain(d), d
    for d in ("suckhoedoisong.vn", "nhathuoclongchau.com.vn", "thanhnien.vn",
              "medlatec.vn", "vinmec.com", "laodong.vn"):
        assert not is_zh_domain(d), d

    lc = open_db(":memory:")
    lc.executemany("INSERT INTO queue VALUES (?,?,?,?,?)", [
        ("1", "u", "suckhoedoisong.vn", 0.0, PENDING),
        ("2", "u", "cnkang.com", 0.0, PENDING),
        ("3", "u", "tnb.39.net", 0.0, PENDING),
        ("4", "u", "familydoctor.com.cn", 0.0, BLOCKED_ST)])
    lc.commit()
    assert lang_domains(lc, "vi") == ["suckhoedoisong.vn"]
    assert sorted(lang_domains(lc, "zh")) == ["cnkang.com", "tnb.39.net"], \
        lang_domains(lc, "zh")
    # Domain đã chặn không được vào bất kỳ ngôn ngữ nào
    assert "familydoctor.com.cn" not in lang_domains(lc, "zh")

    # shard: dùng DB riêng để không làm bẩn các assertion phía sau
    sc = open_db(":memory:")
    sc.executemany("INSERT INTO queue VALUES (?,?,?,?,?)",
                   [(str(i), "u", f"d{i}.vn", 0.0, PENDING) for i in range(7)]
                   + [("99", "u", "familydoctor.com.cn", 0.0, BLOCKED_ST)])
    sc.commit()
    parts = [set(shard_domains(sc, i, 3)) for i in range(3)]
    allp = set().union(*parts)
    assert sum(len(x) for x in parts) == len(allp), "một domain bị chia cho 2 phần"
    assert "familydoctor.com.cn" not in allp, "domain đã chặn không được vào shard"
    assert allp == {f"d{i}.vn" for i in range(7)}, allp
    assert all(parts), "không phần nào được rỗng"

    q = queue.Queue()
    t = threading.Thread(target=writer_loop, args=(conn, q, 1), daemon=True)
    t.start()
    q.put({"doc_id": "1", "url": "http://a.vn/x", "domain": "a.vn", "lang": "vi",
           "status": 200, "err": None, "via": "requests", "title": "T", "descr": "",
           "tags": None, "pub_date": None, "body": "x" * 300, "raw_html": None,
           "simhash": 123})
    q.put(None)
    t.join()
    assert conn.execute("SELECT state FROM queue WHERE doc_id='1'").fetchone()[0] == DONE
    assert [r[0] for r in take_batch(conn, 10)] == ["2"], "đã xong thì không lấy lại"
    assert conn.execute("SELECT length(body) FROM doc WHERE doc_id='1'").fetchone()[0] == 300
    print("demo OK")


def main():
    global TIMEOUT
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DB)
    ap.add_argument("--prio", default=None, help="JSONL slug_rank để xếp thứ tự hàng đợi")
    ap.add_argument("--limit", type=int, default=None, help="chỉ crawl N URL rồi dừng")
    ap.add_argument("--workers", type=int, default=100,
                    help="đo được độ trễ mạng 338 ms → rate limit mới là nút cổ chai, "
                         "~100 thread chỉ cần đủ phủ 97 domain song song")
    ap.add_argument("--batch", type=int, default=2000)
    ap.add_argument("--procs", type=int, default=None,
                    help="số process trích nội dung (mặc định: số core - 1). "
                         "Trích tốn ~59 ms CPU/trang và bị GIL → đây mới là nút cổ chai")
    ap.add_argument("--retry-failed", action="store_true")
    ap.add_argument("--domains", default=None,
                    help="chỉ crawl các domain này (phân tách bằng dấu phẩy)")
    ap.add_argument("--lang", choices=["vi", "zh"], default=None,
                    help="chỉ crawl domain của một ngôn ngữ. Dùng để chia việc hai máy: "
                         "máy A --lang vi, máy B --lang zh. Ghép lại bằng --merge")
    ap.add_argument("--shard", default=None, metavar="I/N",
                    help="crawl phần I của N (vd. 0/3). Chia theo DOMAIN để mỗi domain "
                         "do đúng một máy phụ trách, giữ nguyên rate limit")
    ap.add_argument("--shard-ids", default=None, metavar="I/N",
                    help="chia TRONG domain: chỉ lấy URL có doc_id %% N == I. Dùng khi nhiều "
                         "máy/IP cùng crawl MỘT domain lớn (cnkang, 120ask): mỗi IP giữ rate "
                         "limit riêng nên N máy = N lần thông lượng. Khác --shard (chia theo "
                         "domain, không tăng tốc được domain chậm nhất)")
    ap.add_argument("--timeout", type=float, default=None, metavar="GIÂY",
                    help="timeout mỗi request (mặc định 25). Hạ xuống ~10-12 khi server trả lời "
                         "lưỡng cực (về trong vài giây hoặc treo hẳn): giải phóng luồng sớm hơn")
    ap.add_argument("--rate", action="append", default=[], metavar="DOMAIN=REQ/S",
                    help="ghi đè rate của MỘT domain cho lần chạy này (vd. --rate cnkang.com=6), "
                         "không đổi mặc định. Dùng để thử riêng từng domain: lần thử nâng rate "
                         "cả cụm cùng lúc cho kết quả nhiễu, không biết domain nào gây chặn")
    ap.add_argument("--merge", default=None, metavar="FILE.sqlite",
                    help="gộp store của máy khác vào store này rồi thoát")
    ap.add_argument("--retry-blocked", action="store_true",
                    help="chạy lại domain bị chặn - dùng khi đã có IP/proxy khác")
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--demo", action="store_true")
    args = ap.parse_args()
    if args.demo:
        return demo()
    demo()

    conn = open_db(args.db)
    if args.merge:
        merge_shard(conn, args.merge)
        return stats(conn)
    if args.stats:
        return stats(conn)
    seed_queue(conn, args.prio)
    doms = [d.strip() for d in args.domains.split(",")] if args.domains else None
    if args.lang:
        sel = lang_domains(conn, args.lang)
        doms = [d for d in doms if d in sel] if doms else sel
    if args.shard:
        i, n = (int(x) for x in args.shard.split("/"))
        doms = shard_domains(conn, i, n)
        print(f"Phần {i}/{n}: {len(doms)} domain")
    if args.timeout:
        assert args.timeout >= 3, "--timeout < 3 giây sẽ cắt cả request bình thường"
        TIMEOUT = args.timeout
        print(f"Timeout mỗi request: {TIMEOUT:g}s")
    for item in args.rate:
        dom, _, r = item.partition("=")
        assert dom and r and float(r) > 0, f"--rate {item!r}: cần dạng domain=số_dương"
        old = RATES.get(dom, DEFAULT_RATE)
        RATES[dom] = float(r)
        print(f"Rate ghi đè: {dom} {old} -> {float(r)} req/s")
    shard_ids = None
    if args.shard_ids:
        si, sn = (int(x) for x in args.shard_ids.split("/"))
        assert sn >= 1 and 0 <= si < sn, f"--shard-ids {args.shard_ids}: cần 0 <= I < N"
        shard_ids = (si, sn)
        print(f"Chia trong domain: doc_id % {sn} == {si}")
    instance_lock = acquire_instance_lock(args.db)      # giữ tham chiếu đến hết tiến trình
    run(conn, args.workers, args.batch, args.limit, args.retry_failed,
        args.retry_blocked, args.procs, doms, shard_ids)
    stats(conn)
    instance_lock.close()


if __name__ == "__main__":
    sys.exit(main())
