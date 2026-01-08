"""Tests for rate limiter utility.

TDD RED Phase: Write failing tests first.
Token bucket algorithm implementation for rate limiting.
"""

import time
import threading


class TestRateLimiterBasic:
    """Test cases for basic rate limiter functionality."""

    def test_rate_limiter_allows_within_limit(self):
        """Test that requests within rate limit are allowed."""
        from app.utils.rate_limiter import RateLimiter

        limiter = RateLimiter(rate=10, per_seconds=1)

        # Should allow 10 requests immediately
        for _ in range(10):
            assert limiter.acquire() is True

    def test_rate_limiter_blocks_over_limit(self):
        """Test that requests over rate limit are blocked."""
        from app.utils.rate_limiter import RateLimiter

        limiter = RateLimiter(rate=5, per_seconds=1)

        # Use up all tokens
        for _ in range(5):
            limiter.acquire()

        # 6th request should fail
        assert limiter.acquire() is False

    def test_rate_limiter_refills_tokens(self):
        """Test that tokens are refilled over time."""
        from app.utils.rate_limiter import RateLimiter

        limiter = RateLimiter(rate=10, per_seconds=1)

        # Use all tokens
        for _ in range(10):
            limiter.acquire()

        # Wait for refill
        time.sleep(0.15)

        # Should have at least 1 token now
        assert limiter.acquire() is True

    def test_rate_limiter_default_50_per_second(self):
        """Test default rate limiter configuration (50 req/sec)."""
        from app.utils.rate_limiter import RateLimiter

        limiter = RateLimiter()

        # Default should be 50 per second
        assert limiter.rate == 50
        assert limiter.per_seconds == 1

    def test_rate_limiter_custom_configuration(self):
        """Test rate limiter with custom configuration."""
        from app.utils.rate_limiter import RateLimiter

        limiter = RateLimiter(rate=100, per_seconds=2)

        assert limiter.rate == 100
        assert limiter.per_seconds == 2


class TestRateLimiterTokenBucket:
    """Test cases for token bucket algorithm."""

    def test_token_bucket_initial_tokens(self):
        """Test that bucket starts with full tokens."""
        from app.utils.rate_limiter import RateLimiter

        limiter = RateLimiter(rate=10, per_seconds=1)

        # Should start with 10 tokens
        assert limiter.tokens == 10

    def test_token_bucket_consumes_tokens(self):
        """Test that acquire consumes tokens."""
        from app.utils.rate_limiter import RateLimiter

        limiter = RateLimiter(rate=10, per_seconds=1)

        limiter.acquire()
        # Allow small float tolerance due to time-based refill
        assert 8.9 <= limiter.tokens <= 9.1

        limiter.acquire()
        assert 7.9 <= limiter.tokens <= 8.1

    def test_token_bucket_max_tokens(self):
        """Test that tokens don't exceed maximum."""
        from app.utils.rate_limiter import RateLimiter

        limiter = RateLimiter(rate=10, per_seconds=1)

        # Wait for potential over-refill
        time.sleep(0.2)

        # Tokens should not exceed rate
        assert limiter.tokens <= 10

    def test_token_bucket_partial_refill(self):
        """Test partial token refill based on elapsed time."""
        from app.utils.rate_limiter import RateLimiter

        limiter = RateLimiter(rate=10, per_seconds=1)

        # Use 5 tokens
        for _ in range(5):
            limiter.acquire()

        # Wait for partial refill (0.1 sec = 1 token at 10/sec)
        time.sleep(0.15)

        # Force token check
        limiter.acquire()

        # Should have around 5-6 tokens (5 remaining + ~1 refilled - 1 just used)
        assert 4 <= limiter.tokens <= 6


class TestRateLimiterThreadSafety:
    """Test cases for thread-safe rate limiting."""

    def test_thread_safety_concurrent_acquire(self):
        """Test rate limiter is thread-safe with concurrent access."""
        from app.utils.rate_limiter import RateLimiter

        limiter = RateLimiter(rate=100, per_seconds=1)
        successes = []
        failures = []
        lock = threading.Lock()

        def worker():
            result = limiter.acquire()
            with lock:
                if result:
                    successes.append(1)
                else:
                    failures.append(1)

        # Create 150 threads trying to acquire
        threads = [threading.Thread(target=worker) for _ in range(150)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Should have approximately 100 successes (allow small tolerance for time-based refill)
        assert 100 <= len(successes) <= 105
        assert len(failures) >= 45

    def test_thread_safety_no_race_condition(self):
        """Test that no tokens are lost due to race conditions."""
        from app.utils.rate_limiter import RateLimiter

        limiter = RateLimiter(rate=50, per_seconds=1)
        results = []
        lock = threading.Lock()

        def worker():
            result = limiter.acquire()
            with lock:
                results.append(result)

        # Create exactly 50 threads
        threads = [threading.Thread(target=worker) for _ in range(50)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # All 50 should succeed
        assert sum(results) == 50


class TestRateLimiterWait:
    """Test cases for blocking wait functionality."""

    def test_acquire_with_wait(self):
        """Test acquire with blocking wait."""
        from app.utils.rate_limiter import RateLimiter

        limiter = RateLimiter(rate=10, per_seconds=1)

        # Use all tokens
        for _ in range(10):
            limiter.acquire()

        # Acquire with wait should eventually succeed
        start = time.time()
        result = limiter.acquire(wait=True, timeout=1.0)
        elapsed = time.time() - start

        assert result is True
        assert elapsed < 1.0  # Should not take full second

    def test_acquire_with_wait_timeout(self):
        """Test acquire with wait times out."""
        from app.utils.rate_limiter import RateLimiter

        # Very slow refill rate
        limiter = RateLimiter(rate=1, per_seconds=10)

        # Use the only token
        limiter.acquire()

        # Should timeout waiting for token
        start = time.time()
        result = limiter.acquire(wait=True, timeout=0.1)
        elapsed = time.time() - start

        assert result is False
        assert elapsed >= 0.1


class TestRateLimiterReset:
    """Test cases for rate limiter reset functionality."""

    def test_reset_restores_tokens(self):
        """Test that reset restores all tokens."""
        from app.utils.rate_limiter import RateLimiter

        limiter = RateLimiter(rate=10, per_seconds=1)

        # Use all tokens
        for _ in range(10):
            limiter.acquire()

        # Allow small float tolerance due to time-based refill
        assert limiter.tokens < 1

        # Reset
        limiter.reset()

        assert limiter.tokens == 10

    def test_reset_allows_new_requests(self):
        """Test that reset allows new requests."""
        from app.utils.rate_limiter import RateLimiter

        limiter = RateLimiter(rate=5, per_seconds=1)

        # Use all tokens
        for _ in range(5):
            limiter.acquire()

        # Should fail
        assert limiter.acquire() is False

        # Reset and try again
        limiter.reset()
        assert limiter.acquire() is True
