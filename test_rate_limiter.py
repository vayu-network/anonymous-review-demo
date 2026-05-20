import pytest
from rate_limiter import RateLimiter


# --- Construction ---

def test_starts_at_full_capacity():
    rl = RateLimiter(10, 1.0)
    assert rl.available() == 10


def test_starts_at_full_capacity_various():
    for cap in [1, 5, 100]:
        rl = RateLimiter(cap, 2.0)
        assert rl.available() == cap


def test_invalid_capacity_zero():
    with pytest.raises(ValueError):
        RateLimiter(0, 1.0)


def test_invalid_capacity_negative():
    with pytest.raises(ValueError):
        RateLimiter(-5, 1.0)


def test_invalid_refill_rate_zero():
    with pytest.raises(ValueError):
        RateLimiter(10, 0.0)


def test_invalid_refill_rate_negative():
    with pytest.raises(ValueError):
        RateLimiter(10, -1.0)


# --- consume() ---

def test_consume_returns_true_when_tokens_available():
    rl = RateLimiter(5, 1.0)
    assert rl.consume(1) is True


def test_consume_deducts_tokens():
    rl = RateLimiter(5, 1.0)
    rl.consume(3)
    assert rl.available() == 2


def test_consume_returns_false_when_insufficient():
    rl = RateLimiter(3, 1.0)
    rl.consume(3)
    assert rl.consume(1) is False


def test_consume_does_not_go_below_zero():
    rl = RateLimiter(3, 1.0)
    rl.consume(3)
    rl.consume(1)  # should fail
    assert rl.available() >= 0


def test_consume_exact_capacity():
    rl = RateLimiter(5, 1.0)
    assert rl.consume(5) is True
    assert rl.available() == 0


def test_consume_more_than_capacity_fails():
    rl = RateLimiter(5, 1.0)
    assert rl.consume(6) is False
    assert rl.available() == 5  # unchanged


def test_consume_invalid_tokens():
    rl = RateLimiter(5, 1.0)
    with pytest.raises(ValueError):
        rl.consume(0)
    with pytest.raises(ValueError):
        rl.consume(-1)


# --- Invariant 4: two consecutive consume(1) ---

def test_two_consecutive_consume_both_succeed_requires_two_tokens():
    rl = RateLimiter(10, 1.0)
    # Drain to exactly 2
    rl.consume(8)
    assert rl.available() == 2
    assert rl.consume(1) is True
    assert rl.consume(1) is True


def test_two_consecutive_consume_fail_when_less_than_two():
    rl = RateLimiter(10, 1.0)
    rl.consume(9)
    assert rl.available() == 1
    first = rl.consume(1)
    second = rl.consume(1)
    assert not (first and second), "Both cannot succeed with only 1 token"


def test_two_consecutive_consume_fail_when_zero():
    rl = RateLimiter(5, 1.0)
    rl.consume(5)
    assert rl.available() == 0
    assert rl.consume(1) is False
    assert rl.consume(1) is False


# --- refill() ---

def test_refill_adds_tokens():
    rl = RateLimiter(10, 2.0)
    rl.consume(6)
    rl.refill(2.0)  # adds 4 tokens
    assert rl.available() == 8


def test_refill_clamped_to_capacity():
    rl = RateLimiter(10, 5.0)
    rl.consume(3)
    rl.refill(10.0)  # would add 50, but capped at 10
    assert rl.available() == 10


def test_refill_zero_seconds_no_change():
    rl = RateLimiter(10, 1.0)
    rl.consume(5)
    rl.refill(0.0)
    assert rl.available() == 5


def test_refill_never_exceeds_capacity():
    rl = RateLimiter(10, 1.0)
    rl.refill(100.0)
    assert rl.available() <= 10


def test_refill_invalid_negative():
    rl = RateLimiter(10, 1.0)
    with pytest.raises(ValueError):
        rl.refill(-1.0)


# --- available() ---

def test_available_returns_floor():
    rl = RateLimiter(10, 0.5)
    rl.consume(10)
    rl.refill(1.0)  # adds 0.5 tokens, floor = 0
    assert rl.available() == 0


def test_available_returns_floor_nonzero():
    rl = RateLimiter(10, 1.5)
    rl.consume(10)
    rl.refill(1.0)  # adds 1.5 tokens, floor = 1
    assert rl.available() == 1


# --- Invariant 1: tokens always in [0, capacity] ---

def test_tokens_always_in_range():
    rl = RateLimiter(5, 2.0)
    for _ in range(10):
        rl.consume(1)
    assert 0 <= rl.available() <= 5
    rl.refill(100.0)
    assert 0 <= rl.available() <= 5
