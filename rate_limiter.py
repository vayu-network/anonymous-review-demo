import math


class RateLimiter:
    def __init__(self, capacity: int, refill_rate: float) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be a positive integer")
        if refill_rate <= 0:
            raise ValueError("refill_rate must be a positive float")
        self._capacity: int = capacity
        self._refill_rate: float = refill_rate
        self._tokens: float = float(capacity)

    def consume(self, tokens: int = 1) -> bool:
        if tokens < 1:
            raise ValueError("tokens must be >= 1")
        if self._tokens >= tokens:
            self._tokens -= tokens
            return True
        return False

    def refill(self, elapsed_seconds: float) -> None:
        if elapsed_seconds < 0:
            raise ValueError("elapsed_seconds must be >= 0")
        self._tokens = min(
            float(self._capacity),
            self._tokens + self._refill_rate * elapsed_seconds,
        )

    def available(self) -> int:
        return math.floor(self._tokens)
