from threading import Lock
import time


class TokenBucket:
    """
    A thread-safe token-bucket rate limiter.

    Tokens accumulate at `rate` tokens per second up to `capacity`.
    A call to `consume(tokens)` returns True if enough tokens are
    available (and deducts them), or False otherwise.
    """

    def __init__(self, capacity: float, rate: float) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if rate <= 0:
            raise ValueError("rate must be positive")

        self._capacity: float = capacity
        self._rate: float = rate          # tokens per second
        self._tokens: float = capacity    # start full
        self._last_refill: float = time.monotonic()
        self._lock: Lock = Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def capacity(self) -> float:
        return self._capacity

    @property
    def rate(self) -> float:
        return self._rate

    @property
    def tokens(self) -> float:
        """Current token count (after a refill)."""
        with self._lock:
            self._refill()
            return self._tokens

    def consume(self, tokens: float = 1.0) -> bool:
        """
        Attempt to consume `tokens` from the bucket.

        Returns True and deducts the tokens if sufficient tokens exist,
        otherwise returns False without modifying the bucket.
        """
        if tokens <= 0:
            raise ValueError("tokens to consume must be positive")
        with self._lock:
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    def reset(self) -> None:
        """Refill the bucket to capacity immediately."""
        with self._lock:
            self._tokens = self._capacity
            self._last_refill = time.monotonic()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _refill(self) -> None:
        """Add tokens proportional to elapsed time (must hold lock)."""
        now = time.monotonic()
        elapsed = now - self._last_refill
        if elapsed > 0:
            self._tokens = min(
                self._capacity,
                self._tokens + elapsed * self._rate,
            )
            self._last_refill = now
