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
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

from pubmed_module.http import RateLimiter      # dùng lại, không viết lại

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

# Thách đố cookie: server trả HTTP 200 với một mẩu JS đặt cookie rồi reload. Giá trị cookie
# nằm SẴN trong phản hồi nên không cần chạy JS - chỉ cần set lại rồi gọi lần hai.
#   laodong.vn (31.282 URL): document.cookie="D1N=af1d42e1..."; window.location.reload(true);
COOKIE_CHALLENGE = re.compile(rb"""document\.cookie\s*=\s*["']([^"'=;]{1,64})=([^"';]{1,256})["']""")
CHALLENGE_MAX_BYTES = 4096        # trang thật không bao giờ nhỏ thế này

# Rate limit req/s theo từng domain. Đo được: cnkang/120ask/ask.39.net chịu tải tốt
# (99-100% thành công), a-hospital trả 502 ở 28/65 mẫu nên phải hạ hẳn.
RATES = {"cnkang.com": 10, "120ask.com": 10, "ask.39.net": 8, "a-hospital.com": 1.5}
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
CREATE INDEX IF NOT EXISTS d_domain ON doc(domain);
"""


# ---------------------------------------------------------------- tiện ích

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


def take_batch(conn, n, retry_failed=False, retry_blocked=False, domains=None):
    states = [PENDING] + ([FAILED] if retry_failed else []) + \
             ([BLOCKED_ST] if retry_blocked else [])
    args = [*states]
    where = f"state IN ({','.join('?' * len(states))})"
    if domains:                 # lọc domain: để crawl lại một domain sau khi viết parser
        where += f" AND domain IN ({','.join('?' * len(domains))})"
        args += list(domains)
    rows = conn.execute(
        f"SELECT doc_id, url, domain FROM queue WHERE {where} "
        f"ORDER BY prio DESC LIMIT ?", (*args, n)).fetchall()
    return interleave(rows)


# ---------------------------------------------------------------- fetch

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


def fetch(url, limiter):
    """requests trước; gặp status kiểu WAF thì thử lại bằng curl_cffi (giả TLS Chrome).

    Đo được: profile `chrome` mặc định vượt được Cloudflare của nhathuoclongchau.com.vn
    (33/33 mẫu), còn chrome116/chrome110/edge101 thì không - nên để mặc định.
    """
    import requests
    limiter.wait()
    r = requests.get(url, headers=HEADERS, timeout=25, allow_redirects=True)
    # Thách đố cookie (HTTP 200 nhưng thân rỗng + JS đặt cookie): set lại rồi gọi lần hai
    ch = cookie_challenge(r.content) if r.status_code == 200 else None
    if ch:
        limiter.wait()
        r2 = requests.get(url, headers=HEADERS, timeout=25, allow_redirects=True,
                          cookies={ch[0]: ch[1]})
        if r2.status_code == 200 and not cookie_challenge(r2.content):
            return r2.status_code, r2.content, "requests+cookie"
    if r.status_code in WAF_STATUS:
        from curl_cffi import requests as creq
        limiter.wait()
        r2 = creq.get(url, headers=HEADERS, timeout=25, impersonate="chrome",
                      allow_redirects=True)
        if r2.status_code == 200:
            return r2.status_code, r2.content, "curl_cffi"
        return r2.status_code, r2.content, "curl_cffi"
    return r.status_code, r.content, "requests"


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
    try:
        d = trafilatura.bare_extraction(raw, url=url, with_metadata=True, include_tables=True,
                                        include_comments=False)
        d = (d if isinstance(d, dict) else d.as_dict()) if d else {}
    except Exception:
        d = {}
    body = d.get("text") or ""
    if len(body.strip()) < 200:                     # trafilatura trượt -> thử fallback
        fb = extract_fallback(raw)
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
    return rec


# ---------------------------------------------------------------- vòng chính

def writer_loop(conn, q, commit_every=200):
    """Một thread ghi duy nhất: SQLite không thích nhiều writer."""
    n = 0
    while True:
        rec = q.get()
        if rec is None:
            conn.commit()
            return
        conn.execute(
            f"INSERT OR REPLACE INTO doc ({','.join(COLS)}, fetched) "
            f"VALUES ({','.join('?' * len(COLS))}, datetime('now'))",
            tuple(rec.get(c) for c in COLS))
        state = DONE if len(rec.get("body") or "") >= 200 else FAILED
        conn.execute("UPDATE queue SET state=? WHERE doc_id=?", (state, rec["doc_id"]))
        n += 1
        if n % commit_every == 0:
            conn.commit()


def run(conn, workers, batch, limit, retry_failed, retry_blocked, procs=None,
        domains=None):
    limiters = collections.defaultdict(lambda: RateLimiter(DEFAULT_RATE))
    for dom, rate in RATES.items():
        limiters[dom] = RateLimiter(rate)

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
                items = take_batch(conn, n, retry_failed, retry_blocked, domains)
                if not items:
                    print("Hết URL cần crawl.")
                    break
                for rec in ex.map(lambda it: crawl_one(it, limiters, pool), items):
                    q.put(rec)
                    done += 1
                    ok += len(rec.get("body") or "") >= 200
                    if done % 500 == 0:
                        rate = done / (time.monotonic() - t0)
                        left = f" | còn lại ~{(limit - done) / rate / 3600:.1f}h" if limit \
                            else ""
                        print(f"  {done:,} xong | dùng được {ok/done*100:.1f}% | "
                              f"{rate:.1f} trang/s{left}")
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
    assert take_batch(conn, 10, domains=["khong-ton-tai.vn"]) == []

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
    ap.add_argument("--shard", default=None, metavar="I/N",
                    help="crawl phần I của N (vd. 0/3). Chia theo DOMAIN để mỗi domain "
                         "do đúng một máy phụ trách, giữ nguyên rate limit")
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
    if args.shard:
        i, n = (int(x) for x in args.shard.split("/"))
        doms = shard_domains(conn, i, n)
        print(f"Phần {i}/{n}: {len(doms)} domain")
    run(conn, args.workers, args.batch, args.limit, args.retry_failed,
        args.retry_blocked, args.procs, doms)
    stats(conn)


if __name__ == "__main__":
    sys.exit(main())
