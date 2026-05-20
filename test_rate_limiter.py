import time
import pytest
from rate_limiter import TokenBucket


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

class TestConstruction:
    def test_defaults_to_full_bucket(self) -> None:
        tb = TokenBucket(capacity=10, rate=1)
        assert tb.tokens == pytest.approx(10, abs=0.05)

    def test_invalid_capacity_raises(self) -> None:
        with pytest.raises(ValueError):
            TokenBucket(capacity=0, rate=1)
        with pytest.raises(ValueError):
            TokenBucket(capacity=-5, rate=1)

    def test_invalid_rate_raises(self) -> None:
        with pytest.raises(ValueError):
            TokenBucket(capacity=10, rate=0)
        with pytest.raises(ValueError):
            TokenBucket(capacity=10, rate=-1)

    def test_properties_accessible(self) -> None:
        tb = TokenBucket(capacity=5.0, rate=2.0)
        assert tb.capacity == 5.0
        assert tb.rate == 2.0


# ---------------------------------------------------------------------------
# Consume
# ---------------------------------------------------------------------------

class TestConsume:
    def test_consume_within_capacity_returns_true(self) -> None:
        tb = TokenBucket(capacity=10, rate=1)
        assert tb.consume(5) is True

    def test_consume_deducts_tokens(self) -> None:
        tb = TokenBucket(capacity=10, rate=1)
        tb.consume(4)
        assert tb.tokens == pytest.approx(6, abs=0.05)

    def test_consume_exact_capacity(self) -> None:
        tb = TokenBucket(capacity=10, rate=1)
        assert tb.consume(10) is True
        assert tb.tokens == pytest.approx(0, abs=0.05)

    def test_consume_exceeds_tokens_returns_false(self) -> None:
        tb = TokenBucket(capacity=5, rate=1)
        tb.consume(5)          # drain
        assert tb.consume(1) is False

    def test_consume_does_not_deduct_on_failure(self) -> None:
        tb = TokenBucket(capacity=5, rate=1)
        tb.consume(5)
        before = tb.tokens
        tb.consume(1)
        assert tb.tokens == pytest.approx(before, abs=0.05)

    def test_consume_invalid_amount_raises(self) -> None:
        tb = TokenBucket(capacity=10, rate=1)
        with pytest.raises(ValueError):
            tb.consume(0)
        with pytest.raises(ValueError):
            tb.consume(-1)

    def test_tokens_never_go_negative(self) -> None:
        tb = TokenBucket(capacity=3, rate=0.1)
        for _ in range(10):
            tb.consume(1)
        assert tb.tokens >= 0


# ---------------------------------------------------------------------------
# Refill
# ---------------------------------------------------------------------------

class TestRefill:
    def test_tokens_increase_over_time(self) -> None:
        tb = TokenBucket(capacity=10, rate=5)   # 5 tok/s
        tb.consume(5)                            # leave 5
        time.sleep(0.2)                          # expect ~1 token added
        assert tb.tokens > 5

    def test_tokens_capped_at_capacity(self) -> None:
        tb = TokenBucket(capacity=5, rate=100)  # very fast refill
        time.sleep(0.1)
        assert tb.tokens <= pytest.approx(5, abs=0.05)

    def test_refill_rate_respected(self) -> None:
        tb = TokenBucket(capacity=100, rate=10)  # 10 tok/s
        tb.consume(10)                            # leave 90
        time.sleep(0.5)                           # expect ~5 tokens added
        expected = 90 + 10 * 0.5
        assert tb.tokens == pytest.approx(expected, abs=1.0)


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------

class TestReset:
    def test_reset_refills_to_capacity(self) -> None:
        tb = TokenBucket(capacity=10, rate=1)
        tb.consume(10)
        tb.reset()
        assert tb.tokens == pytest.approx(10, abs=0.05)

    def test_reset_allows_immediate_consume(self) -> None:
        tb = TokenBucket(capacity=10, rate=1)
        tb.consume(10)
        tb.reset()
        assert tb.consume(10) is True


# ---------------------------------------------------------------------------
# Thread safety (light smoke test)
# ---------------------------------------------------------------------------

class TestThreadSafety:
    def test_concurrent_consume_never_exceeds_capacity(self) -> None:
        import threading

        tb = TokenBucket(capacity=100, rate=0)   # rate=0 not valid, use tiny
        tb = TokenBucket(capacity=100, rate=0.001)
        successes: list[bool] = []
        lock = threading.Lock()

        def worker() -> None:
            result = tb.consume(1)
            with lock:
                successes.append(result)

        threads = [threading.Thread(target=worker) for _ in range(200)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # At most 100 consumes should succeed (bucket started with 100)
        assert sum(successes) <= 100
