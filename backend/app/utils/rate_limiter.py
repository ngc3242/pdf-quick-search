"""Rate limiter using token bucket algorithm.

Thread-safe rate limiter for controlling API request rates.
Default configuration: 50 requests per second (CrossRef Polite Pool limit).
"""

import threading
import time
from typing import Optional


class RateLimiter:
    """Thread-safe rate limiter using token bucket algorithm.

    The token bucket algorithm allows bursts up to the bucket size
    while maintaining an average rate over time.

    Attributes:
        rate: Maximum number of tokens (requests) per time period
        per_seconds: Time period in seconds for rate calculation
        tokens: Current number of available tokens
    """

    def __init__(self, rate: int = 50, per_seconds: float = 1.0):
        """Initialize rate limiter.

        Args:
            rate: Maximum requests per time period (default 50)
            per_seconds: Time period in seconds (default 1.0)
        """
        self.rate = rate
        self.per_seconds = per_seconds
        self._tokens = float(rate)
        self._last_update = time.monotonic()
        self._lock = threading.Lock()

    @property
    def tokens(self) -> float:
        """Get current token count after refill calculation."""
        self._refill()
        return self._tokens

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self._last_update

        # Calculate tokens to add based on elapsed time
        tokens_to_add = elapsed * (self.rate / self.per_seconds)
        self._tokens = min(self.rate, self._tokens + tokens_to_add)
        self._last_update = now

    def acquire(self, wait: bool = False, timeout: Optional[float] = None) -> bool:
        """Attempt to acquire a token.

        Args:
            wait: If True, block until token is available or timeout
            timeout: Maximum time to wait in seconds (only used if wait=True)

        Returns:
            True if token was acquired, False otherwise
        """
        if wait:
            return self._acquire_with_wait(timeout)
        return self._try_acquire()

    def _try_acquire(self) -> bool:
        """Try to acquire a token without waiting."""
        with self._lock:
            self._refill()

            if self._tokens >= 1:
                self._tokens -= 1
                return True

            return False

    def _acquire_with_wait(self, timeout: Optional[float]) -> bool:
        """Acquire a token, waiting if necessary.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            True if token was acquired, False if timeout exceeded
        """
        start_time = time.monotonic()
        poll_interval = 0.01  # 10ms polling interval

        while True:
            if self._try_acquire():
                return True

            # Check timeout
            if timeout is not None:
                elapsed = time.monotonic() - start_time
                if elapsed >= timeout:
                    return False

            # Small sleep to avoid busy waiting
            time.sleep(poll_interval)

    def reset(self) -> None:
        """Reset the rate limiter to full capacity."""
        with self._lock:
            self._tokens = float(self.rate)
            self._last_update = time.monotonic()
