import pytest
from backoff_scheduler import BackoffScheduler


# ---------------------------------------------------------------------------
# Construction validation
# ---------------------------------------------------------------------------

class TestConstructorValidation:
    def test_valid_construction(self) -> None:
        s = BackoffScheduler(100.0, 2.0, 1000.0)
        assert s.base_ms == 100.0
        assert s.factor == 2.0
        assert s.cap_ms == 1000.0

    def test_base_ms_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="base_ms"):
            BackoffScheduler(0.0, 2.0, 1000.0)

    def test_base_ms_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="base_ms"):
            BackoffScheduler(-1.0, 2.0, 1000.0)

    def test_factor_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="factor"):
            BackoffScheduler(100.0, 0.0, 1000.0)

    def test_factor_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="factor"):
            BackoffScheduler(100.0, -2.0, 1000.0)

    def test_factor_less_than_one_raises(self) -> None:
        with pytest.raises(ValueError, match="factor"):
            BackoffScheduler(100.0, 0.5, 1000.0)

    def test_cap_ms_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="cap_ms"):
            BackoffScheduler(100.0, 2.0, 0.0)

    def test_cap_ms_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="cap_ms"):
            BackoffScheduler(100.0, 2.0, -500.0)

    def test_cap_ms_less_than_base_ms_raises(self) -> None:
        with pytest.raises(ValueError, match="cap_ms"):
            BackoffScheduler(100.0, 2.0, 50.0)

    def test_factor_exactly_one_is_valid(self) -> None:
        s = BackoffScheduler(100.0, 1.0, 100.0)
        assert s.factor == 1.0

    def test_cap_ms_equals_base_ms_is_valid(self) -> None:
        s = BackoffScheduler(100.0, 2.0, 100.0)
        assert s.cap_ms == s.base_ms


# ---------------------------------------------------------------------------
# delay() validation
# ---------------------------------------------------------------------------

class TestDelayValidation:
    def test_negative_attempt_raises(self) -> None:
        s = BackoffScheduler(100.0, 2.0, 1000.0)
        with pytest.raises(ValueError, match="attempt"):
            s.delay(-1)

    def test_attempt_zero_equals_base_ms(self) -> None:
        """Requirement 4: delay(0) == base_ms exactly."""
        s = BackoffScheduler(100.0, 2.0, 1000.0)
        assert s.delay(0) == 100.0

    def test_attempt_zero_equals_base_ms_various(self) -> None:
        for base in [1.0, 50.0, 250.5, 999.9]:
            s = BackoffScheduler(base, 2.0, base * 100)
            assert s.delay(0) == base

    def test_exponential_growth(self) -> None:
        s = BackoffScheduler(100.0, 2.0, 10_000.0)
        assert s.delay(0) == 100.0
        assert s.delay(1) == 200.0
        assert s.delay(2) == 400.0
        assert s.delay(3) == 800.0

    def test_cap_applied(self) -> None:
        """Requirement 5: delay(n) <= cap_ms."""
        s = BackoffScheduler(100.0, 2.0, 500.0)
        assert s.delay(10) == 500.0
        assert s.delay(100) == 500.0

    def test_delay_never_exceeds_cap(self) -> None:
        s = BackoffScheduler(100.0, 3.0, 1000.0)
        for n in range(20):
            assert s.delay(n) <= s.cap_ms

    def test_delay_never_below_base(self) -> None:
        """Requirement 6: delay(n) >= base_ms."""
        s = BackoffScheduler(100.0, 2.0, 1000.0)
        for n in range(20):
            assert s.delay(n) >= s.base_ms

    def test_non_decreasing_sequence(self) -> None:
        """Requirement 3: delay(n+1) >= delay(n)."""
        s = BackoffScheduler(100.0, 2.0, 800.0)
        delays = [s.delay(n) for n in range(15)]
        for i in range(len(delays) - 1):
            assert delays[i + 1] >= delays[i], (
                f"delay({i+1})={delays[i+1]} < delay({i})={delays[i]}"
            )

    def test_non_decreasing_with_factor_one(self) -> None:
        """Factor=1 means constant sequence (still non-decreasing)."""
        s = BackoffScheduler(100.0, 1.0, 500.0)
        delays = [s.delay(n) for n in range(10)]
        for i in range(len(delays) - 1):
            assert delays[i + 1] >= delays[i]
        # All should equal base_ms since factor==1
        assert all(d == 100.0 for d in delays)

    def test_formula_correctness(self) -> None:
        """Verify formula: min(base * factor**attempt, cap)."""
        s = BackoffScheduler(50.0, 3.0, 5000.0)
        for n in range(10):
            expected = min(50.0 * (3.0 ** n), 5000.0)
            assert s.delay(n) == pytest.approx(expected)

    def test_large_attempt_number(self) -> None:
        s = BackoffScheduler(1.0, 2.0, 1000.0)
        assert s.delay(1000) == 1000.0  # capped

    def test_attempt_zero_is_int_zero(self) -> None:
        s = BackoffScheduler(200.0, 1.5, 10_000.0)
        assert s.delay(0) == 200.0
