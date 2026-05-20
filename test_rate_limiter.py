import pytest
from rate_limiter import RateLimiter


# --- Construction ---

def test_starts_at_full_capacity():
    """Invariant 5: A newly constructed RateLimiter always starts at full capacity."""
    rl = RateLimiter(capacity=10, refill_rate=1.0)
    assert rl.available() == 10


def test_starts_at_full_capacity_various():
    for cap in [1, 5, 100]:
        rl = RateLimiter(capacity=cap, refill_rate=0.5)
        assert rl.available() == cap


def test_invalid_capacity_zero():
    with pytest.raises(ValueError):
        RateLimiter(capacity=0, refill_rate=1.0)


def test_invalid_capacity_negative():
    with pytest.raises(ValueError):
        RateLimiter(capacity=-1, refill_rate=1.0)


def test_invalid_refill_rate_zero():
    with pytest.raises(ValueError):
        RateLimiter(capacity=5, refill_rate=0.0)


def test_invalid_refill_rate_negative():
    with pytest.raises(ValueError):
        RateLimiter(capacity=5, refill_rate=-1.0)


# --- consume() ---

def test_consume_success_returns_true():
    rl = RateLimiter(capacity=5, refill_rate=1.0)
    assert rl.consume(1) is True


def test_consume_deducts_tokens():
    rl = RateLimiter(capacity=5, refill_rate=1.0)
    rl.consume(3)
    assert rl.available() == 2


def test_consume_fails_when_insufficient():
    rl = RateLimiter(capacity=5, refill_rate=1.0)
    assert rl.consume(6) is False


def test_consume_does_not_deduct_on_failure():
    rl = RateLimiter(capacity=5, refill_rate=1.0)
    rl.consume(6)
    assert rl.available() == 5


def test_consume_never_goes_below_zero():
    """Invariant 2: consume() never reduces tokens below 0."""
    rl = RateLimiter(capacity=3, refill_rate=1.0)
    rl.consume(3)
    assert rl.available() == 0
    result = rl.consume(1)
    assert result is False
    assert rl.available() == 0


def test_consume_exact_capacity():
    rl = RateLimiter(capacity=5, refill_rate=1.0)
    assert rl.consume(5) is True
    assert rl.available() == 0


def test_consume_invalid_tokens():
    rl = RateLimiter(capacity=5, refill_rate=1.0)
    with pytest.raises(ValueError):
        rl.consume(0)
    with pytest.raises(ValueError):
        rl.consume(-1)


def test_two_consecutive_consume_both_succeed_requires_two_tokens():
    """Invariant 4: Two consecutive consume(1) can only both succeed if available() >= 2."""
    # Exactly 2 tokens → both succeed
    rl = RateLimiter(capacity=2, refill_rate=1.0)
    assert rl.available() >= 2
    assert rl.consume(1) is True
    assert rl.consume(1) is True

    # Only 1 token → second fails
    rl2 = RateLimiter(capacity=5, refill_rate=1.0)
    rl2.consume(4)  # leave 1 token
    assert rl2.available() == 1
    assert rl2.consume(1) is True
    assert rl2.consume(1) is False


def test_two_consecutive_consume_zero_tokens():
    """If available() < 2, the two consecutive consume(1) cannot both succeed."""
    rl = RateLimiter(capacity=5, refill_rate=1.0)
    rl.consume(5)  # drain completely
    assert rl.available() == 0
    assert rl.consume(1) is False
    assert rl.consume(1) is False


# --- refill() ---

def test_refill_adds_tokens():
    rl = RateLimiter(capacity=10, refill_rate=2.0)
    rl.consume(6)
    assert rl.available() == 4
    rl.refill(2.0)  # adds 4 tokens
    assert rl.available() == 8


def test_refill_clamped_to_capacity():
    """Invariant 3: refill() never increases tokens above capacity."""
    rl = RateLimiter(capacity=10, refill_rate=5.0)
    rl.consume(2)
    rl.refill(100.0)  # would add 500 tokens
    assert rl.available() == 10


def test_refill_zero_elapsed():
    rl = RateLimiter(capacity=10, refill_rate=2.0)
    rl.consume(5)
    rl.refill(0.0)
    assert rl.available() == 5


def test_refill_invalid_negative():
    rl = RateLimiter(capacity=10, refill_rate=1.0)
    with pytest.raises(ValueError):
        rl.refill(-1.0)


def test_refill_partial():
    rl = RateLimiter(capacity=10, refill_rate=1.0)
    rl.consume(10)
    rl.refill(0.5)  # adds 0.5 tokens → available() = floor(0.5) = 0
    assert rl.available() == 0
    rl.refill(0.6)  # total = 1.1 → available() = 1
    assert rl.available() == 1


# --- available() ---

def test_available_returns_floor():
    rl = RateLimiter(capacity=10, refill_rate=1.0)
    rl.consume(10)
    rl.refill(0.9)  # 0.9 tokens
    assert rl.available() == 0
    rl.refill(0.2)  # 1.1 tokens
    assert rl.available() == 1


# --- Invariant 1: tokens always in [0, capacity] ---

def test_tokens_always_in_range():
    """Invariant 1: Token count is always in [0, capacity]."""
    rl = RateLimiter(capacity=5, refill_rate=2.0)
    for _ in range(10):
        rl.consume(1)
        assert 0 <= rl.available() <= 5
    rl.refill(10.0)
    assert 0 <= rl.available() <= 5
