"""Token-bucket rate limiter."""
import time
from collections import defaultdict
from dataclasses import dataclass


@dataclass
class Bucket:
    tokens: float
    last_refill: float


class RateLimiter:
    def __init__(self, rate: float, burst: int) -> None:
        self.rate = rate
        self.burst = burst
        self._buckets: dict[str, Bucket] = defaultdict(
            lambda: Bucket(tokens=burst, last_refill=time.monotonic())
        )

    def allow(self, key: str, cost: float = 1.0) -> bool:
        now = time.monotonic()
        b = self._buckets[key]
        elapsed = now - b.last_refill
        b.tokens = min(self.burst, b.tokens + elapsed * self.rate)
        b.last_refill = now
        if b.tokens >= cost:
            b.tokens -= cost
            return True
        return False
