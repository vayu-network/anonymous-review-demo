from typing import Final


class BackoffScheduler:
    """Exponential back-off scheduler."""

    def __init__(self, base_ms: float, factor: float, cap_ms: float) -> None:
        if base_ms <= 0:
            raise ValueError(f"base_ms must be strictly positive, got {base_ms}")
        if factor <= 0:
            raise ValueError(f"factor must be strictly positive, got {factor}")
        if factor < 1.0:
            raise ValueError(f"factor must be >= 1.0, got {factor}")
        if cap_ms <= 0:
            raise ValueError(f"cap_ms must be strictly positive, got {cap_ms}")
        if cap_ms < base_ms:
            raise ValueError(
                f"cap_ms must be >= base_ms, got cap_ms={cap_ms}, base_ms={base_ms}"
            )

        self.base_ms: Final[float] = base_ms
        self.factor: Final[float] = factor
        self.cap_ms: Final[float] = cap_ms

    def delay(self, attempt: int) -> float:
        """Return the delay in milliseconds for the given attempt number."""
        if attempt < 0:
            raise ValueError(f"attempt must be >= 0, got {attempt}")
        return min(self.base_ms * (self.factor ** attempt), self.cap_ms)
