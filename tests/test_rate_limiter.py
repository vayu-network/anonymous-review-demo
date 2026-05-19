import time
from src.rate_limiter import RateLimiter


def test_burst_then_throttle():
    rl = RateLimiter(rate=10.0, burst=5)
    for _ in range(5):
        assert rl.allow("user-1")
    assert not rl.allow("user-1")


def test_refill_after_wait():
    rl = RateLimiter(rate=10.0, burst=5)
    for _ in range(5):
        rl.allow("user-1")
    time.sleep(0.25)
    assert rl.allow("user-1")


def test_buckets_isolated_per_key():
    rl = RateLimiter(rate=1.0, burst=2)
    assert rl.allow("alice")
    assert rl.allow("alice")
    assert not rl.allow("alice")
    assert rl.allow("bob")
