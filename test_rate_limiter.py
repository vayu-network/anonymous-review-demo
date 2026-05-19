import time
import threading
import pytest
from rate_limiter import RateLimiter


def test_allow_returns_true_when_tokens_available() -> None:
    rl = RateLimiter(capacity=5, refill_rate=1.0)
    assert rl.allow() is True


def test_allow_returns_false_when_empty() -> None:
    rl = RateLimiter(capacity=3, refill_rate=0.0)
    # Exhaust all tokens
    for _ in range(3):
        assert rl.allow() is True
    # Bucket is now empty
    assert rl.allow() is False


def test_allow_returns_true_after_refill() -> None:
    rl = RateLimiter(capacity=1, refill_rate=10.0)
    # Exhaust the single token
    assert rl.allow() is True
    assert rl.allow() is False
    # Wait long enough for at least one token to be refilled (0.15s for 10 tokens/s)
    time.sleep(0.15)
    assert rl.allow() is True


def test_capacity_not_exceeded_after_long_wait() -> None:
    capacity = 4
    rl = RateLimiter(capacity=capacity, refill_rate=100.0)
    # Exhaust all tokens
    for _ in range(capacity):
        rl.allow()
    # Wait long enough that many tokens would be added without capping
    time.sleep(0.2)
    # Bucket should be capped at capacity
    successes = sum(1 for _ in range(capacity + 5) if rl.allow())
    assert successes == capacity


def test_zero_capacity_always_returns_false() -> None:
    rl = RateLimiter(capacity=0, refill_rate=100.0)
    for _ in range(5):
        assert rl.allow() is False


def test_thread_safety() -> None:
    capacity = 50
    rl = RateLimiter(capacity=capacity, refill_rate=0.0)
    results: list[bool] = []
    lock = threading.Lock()

    def worker() -> None:
        result = rl.allow()
        with lock:
            results.append(result)

    threads = [threading.Thread(target=worker) for _ in range(100)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    true_count = sum(1 for r in results if r)
    false_count = sum(1 for r in results if not r)
    assert true_count == capacity
    assert false_count == 100 - capacity


def test_refill_rate_zero_no_refill() -> None:
    rl = RateLimiter(capacity=2, refill_rate=0.0)
    assert rl.allow() is True
    assert rl.allow() is True
    assert rl.allow() is False
    time.sleep(0.1)
    # No refill should happen
    assert rl.allow() is False


def test_multiple_refills_respect_capacity() -> None:
    rl = RateLimiter(capacity=2, refill_rate=10.0)
    # Drain the bucket
    rl.allow()
    rl.allow()
    assert rl.allow() is False
    # Wait for more than enough time to fill beyond capacity
    time.sleep(0.5)
    # Should only have capacity tokens available
    assert rl.allow() is True
    assert rl.allow() is True
    assert rl.allow() is False
