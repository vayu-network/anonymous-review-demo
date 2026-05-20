import pytest
from backoff_scheduler import BackoffScheduler


# ---------------------------------------------------------------------------
# Construction – valid inputs
# ---------------------------------------------------------------------------

def test_construction_basic() -> None:
    sched = BackoffScheduler(base_ms=100.0, factor=2.0, cap_ms=1000.0)
    assert sched.base_ms == 100.0
    assert sched.factor == 2.0
    assert sched.cap_ms == 1000.0


def test_construction_factor_exactly_one() -> None:
    sched = BackoffScheduler(base_ms=50.0, factor=1.0, cap_ms=50.0)
    assert sched.factor == 1.0


def test_construction_base_equals_cap() -> None:
    sched = BackoffScheduler(base_ms=200.0, factor=1.5, cap_ms=200.0)
    assert sched.base_ms == sched.cap_ms


def test_construction_fractional_values() -> None:
    sched = BackoffScheduler(base_ms=0.5, factor=1.5, cap_ms=100.0)
    assert sched.base_ms == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# Construction – invalid inputs (raises)
# ---------------------------------------------------------------------------

def test_raises_invalid_base_ms_zero() -> None:
    with pytest.raises(ValueError, match="base_ms"):
        BackoffScheduler(base_ms=0.0, factor=2.0, cap_ms=1000.0)


def test_raises_invalid_base_ms_negative() -> None:
    with pytest.raises(ValueError, match="base_ms"):
        BackoffScheduler(base_ms=-1.0, factor=2.0, cap_ms=1000.0)


def test_raises_invalid_factor_zero() -> None:
    with pytest.raises(ValueError, match="factor"):
        BackoffScheduler(base_ms=100.0, factor=0.0, cap_ms=1000.0)


def test_raises_invalid_factor_negative() -> None:
    with pytest.raises(ValueError, match="factor"):
        BackoffScheduler(base_ms=100.0, factor=-1.0, cap_ms=1000.0)


def test_raises_invalid_factor_less_than_one() -> None:
    with pytest.raises(ValueError, match="factor"):
        BackoffScheduler(base_ms=100.0, factor=0.9, cap_ms=1000.0)


def test_raises_invalid_cap_ms_zero() -> None:
    with pytest.raises(ValueError, match="cap_ms"):
        BackoffScheduler(base_ms=100.0, factor=2.0, cap_ms=0.0)


def test_raises_invalid_cap_ms_negative() -> None:
    with pytest.raises(ValueError, match="cap_ms"):
        BackoffScheduler(base_ms=100.0, factor=2.0, cap_ms=-5.0)


def test_raises_cap_ms_less_than_base_ms() -> None:
    with pytest.raises(ValueError, match="cap_ms"):
        BackoffScheduler(base_ms=200.0, factor=2.0, cap_ms=100.0)


# ---------------------------------------------------------------------------
# delay – requirement 4: delay(0) == base_ms exactly
# ---------------------------------------------------------------------------

def test_delay_attempt_zero_equals_base_ms() -> None:
    sched = BackoffScheduler(base_ms=100.0, factor=2.0, cap_ms=1000.0)
    assert sched.delay(0) == pytest.approx(100.0)


def test_delay_attempt_zero_fractional_base() -> None:
    sched = BackoffScheduler(base_ms=0.5, factor=3.0, cap_ms=50.0)
    assert sched.delay(0) == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# delay – requirement 2: formula min(base * factor**n, cap)
# ---------------------------------------------------------------------------

def test_delay_formula_below_cap() -> None:
    sched = BackoffScheduler(base_ms=100.0, factor=2.0, cap_ms=10000.0)
    assert sched.delay(1) == pytest.approx(200.0)
    assert sched.delay(2) == pytest.approx(400.0)
    assert sched.delay(3) == pytest.approx(800.0)


def test_delay_formula_at_cap() -> None:
    sched = BackoffScheduler(base_ms=100.0, factor=2.0, cap_ms=400.0)
    assert sched.delay(2) == pytest.approx(400.0)


def test_delay_formula_above_cap_is_capped() -> None:
    sched = BackoffScheduler(base_ms=100.0, factor=2.0, cap_ms=400.0)
    assert sched.delay(3) == pytest.approx(400.0)
    assert sched.delay(10) == pytest.approx(400.0)


def test_delay_factor_one_constant() -> None:
    sched = BackoffScheduler(base_ms=150.0, factor=1.0, cap_ms=500.0)
    for attempt in range(5):
        assert sched.delay(attempt) == pytest.approx(150.0)


# ---------------------------------------------------------------------------
# delay – requirement 5: delay(n) <= cap_ms
# ---------------------------------------------------------------------------

def test_delay_never_exceeds_cap() -> None:
    sched = BackoffScheduler(base_ms=100.0, factor=3.0, cap_ms=1000.0)
    for attempt in range(20):
        assert sched.delay(attempt) <= sched.cap_ms + 1e-9


# ---------------------------------------------------------------------------
# delay – requirement 6: delay(n) >= base_ms
# ---------------------------------------------------------------------------

def test_delay_always_at_least_base_ms() -> None:
    sched = BackoffScheduler(base_ms=100.0, factor=2.0, cap_ms=1000.0)
    for attempt in range(20):
        assert sched.delay(attempt) >= sched.base_ms - 1e-9


# ---------------------------------------------------------------------------
# delay – requirement 3: non-decreasing sequence
# ---------------------------------------------------------------------------

def test_delay_non_decreasing_factor_gt_one() -> None:
    sched = BackoffScheduler(base_ms=100.0, factor=2.0, cap_ms=10000.0)
    delays = [sched.delay(n) for n in range(15)]
    for i in range(len(delays) - 1):
        assert delays[i + 1] >= delays[i]


def test_delay_non_decreasing_with_cap() -> None:
    sched = BackoffScheduler(base_ms=100.0, factor=2.0, cap_ms=500.0)
    delays = [sched.delay(n) for n in range(15)]
    for i in range(len(delays) - 1):
        assert delays[i + 1] >= delays[i]


def test_delay_non_decreasing_factor_one() -> None:
    sched = BackoffScheduler(base_ms=100.0, factor=1.0, cap_ms=100.0)
    delays = [sched.delay(n) for n in range(10)]
    for i in range(len(delays) - 1):
        assert delays[i + 1] >= delays[i]


# ---------------------------------------------------------------------------
# delay – invalid attempt (raises)
# ---------------------------------------------------------------------------

def test_raises_negative_attempt() -> None:
    sched = BackoffScheduler(base_ms=100.0, factor=2.0, cap_ms=1000.0)
    with pytest.raises(ValueError, match="attempt"):
        sched.delay(-1)


def test_raises_negative_attempt_large() -> None:
    sched = BackoffScheduler(base_ms=100.0, factor=2.0, cap_ms=1000.0)
    with pytest.raises(ValueError):
        sched.delay(-100)
