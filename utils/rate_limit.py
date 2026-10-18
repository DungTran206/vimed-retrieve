"""Giới hạn tốc độ request dùng chung giữa các dịch vụ."""
import threading
import time


class RateLimiter:
    """Đảm bảo khoảng cách tối thiểu giữa hai request tới cùng một dịch vụ."""

    def __init__(self, rate_per_sec: float):
        self.interval = 1.0 / rate_per_sec
        self.lock = threading.Lock()
        self.next_t = 0.0

    def wait(self):
        with self.lock:
            now = time.monotonic()
            if now < self.next_t:
                time.sleep(self.next_t - now)
                now = self.next_t
            self.next_t = now + self.interval
