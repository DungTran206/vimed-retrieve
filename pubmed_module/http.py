"""HTTP client cho API PubMed: retry và cache SQLite."""
import hashlib
import json
import sqlite3
import threading

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from utils.rate_limit import RateLimiter


class KVStore:
    """Key-value store trên SQLite, an toàn khi dùng từ nhiều thread."""

    def __init__(self, path: str):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.lock = threading.Lock()
        with self.lock:
            self.conn.execute("CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT)")
            self.conn.commit()

    def get(self, key: str):
        with self.lock:
            row = self.conn.execute("SELECT v FROM kv WHERE k = ?", (key,)).fetchone()
        return row[0] if row else None

    def set(self, key: str, value: str):
        with self.lock:
            self.conn.execute("INSERT OR REPLACE INTO kv (k, v) VALUES (?, ?)", (key, value))
            self.conn.commit()


class HttpClient:
    # Tham số không đưa vào khoá cache (không ảnh hưởng nội dung trả về)
    _IGNORED_PARAMS = {"api_key", "email", "tool"}

    def __init__(self, cache_path: str, timeout: int = 30):
        self.timeout = timeout
        self.cache = KVStore(cache_path)
        self.limiters: dict[str, RateLimiter] = {}
        self.session = requests.Session()
        retry = Retry(
            total=5,
            backoff_factor=1.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
            respect_retry_after_header=True,
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retry))
        self.session.headers["User-Agent"] = "vimed-retrieval/0.1 (research; competition)"

    def add_limiter(self, name: str, rate_per_sec: float):
        self.limiters[name] = RateLimiter(rate_per_sec)

    def _key(self, url: str, params: dict) -> str:
        clean = {k: v for k, v in sorted(params.items()) if k not in self._IGNORED_PARAMS}
        raw = url + "?" + json.dumps(clean, ensure_ascii=False, sort_keys=True)
        return "http:" + hashlib.sha1(raw.encode("utf-8")).hexdigest()

    def get_text(self, url: str, params: dict, limiter: str, use_cache: bool = True) -> str:
        key = self._key(url, params)
        if use_cache:
            cached = self.cache.get(key)
            if cached is not None:
                return cached
        self.limiters[limiter].wait()
        resp = self.session.get(url, params=params, timeout=self.timeout)
        resp.raise_for_status()
        text = resp.text
        if use_cache and text.strip():
            self.cache.set(key, text)
        return text
