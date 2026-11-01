"""
Unit tests for rate limiting service.

Tests token bucket algorithm, per-client limits, and endpoint-specific limits.
"""

import time
from unittest.mock import patch

import pytest

from app.core.rate_limiter import (
    RateLimitConfig,
    RateLimiter,
    TokenBucket,
    get_rate_limiter,
    init_rate_limiter,
)


class TestTokenBucket:
    """Tests for TokenBucket class."""

    def test_token_bucket_allows_requests_within_limit(self):
        """Token bucket should allow requests within limit."""
        config = RateLimitConfig(max_tokens=10, refill_rate=1)
        bucket = TokenBucket(config)

        # Should allow 10 requests
        for _ in range(10):
            assert bucket.allow_request() is True

        # 11th request should fail
        assert bucket.allow_request() is False

    def test_token_bucket_refills_over_time(self):
        """Token bucket should refill tokens over time."""
        config = RateLimitConfig(max_tokens=5, refill_rate=1)  # 1 token/sec
        bucket = TokenBucket(config)

        # Consume all tokens
        for _ in range(5):
            bucket.allow_request()

        # Next request should fail
        assert bucket.allow_request() is False

        # Wait for 1 second to get 1 token back
        time.sleep(1.1)

        # Should allow 1 request
        assert bucket.allow_request() is True

    def test_token_bucket_get_remaining(self):
        """Token bucket should report remaining tokens correctly."""
        config = RateLimitConfig(max_tokens=10, refill_rate=1)
        bucket = TokenBucket(config)

        # Initially should have 10 tokens
        assert bucket.get_remaining() == 10

        # After consuming 3
        bucket.allow_request()
        bucket.allow_request()
        bucket.allow_request()
        assert bucket.get_remaining() == 7


class TestRateLimiter:
    """Tests for RateLimiter class."""

    def test_rate_limiter_default_limit(self):
        """Rate limiter should enforce default global limit."""
        config = RateLimitConfig(max_tokens=5, refill_rate=1)
        limiter = RateLimiter(config)

        # Should allow 5 requests per client
        for _ in range(5):
            assert limiter.allow_request("client1") is True

        # 6th should fail
        assert limiter.allow_request("client1") is False

    def test_rate_limiter_per_client_isolation(self):
        """Rate limiter should isolate limits per client."""
        config = RateLimitConfig(max_tokens=5, refill_rate=1)
        limiter = RateLimiter(config)

        # Client 1 uses 5 requests
        for _ in range(5):
            limiter.allow_request("client1")

        # Client 1 should be limited
        assert limiter.allow_request("client1") is False

        # Client 2 should get fresh quota
        for _ in range(5):
            assert limiter.allow_request("client2") is True

    def test_rate_limiter_endpoint_limits(self):
        """Rate limiter should enforce endpoint-specific limits."""
        global_config = RateLimitConfig(max_tokens=10, refill_rate=1)
        upload_config = RateLimitConfig(max_tokens=2, refill_rate=1)

        limiter = RateLimiter(global_config)
        limiter.set_endpoint_limit("/upload", upload_config)

        client = "client1"

        # Upload endpoint should allow only 2 requests
        assert limiter.allow_request(client, "/upload") is True
        assert limiter.allow_request(client, "/upload") is True
        assert limiter.allow_request(client, "/upload") is False

        # Global limit should still allow other endpoints
        for _ in range(10):
            assert limiter.allow_request(client, "/global") is True

    def test_rate_limiter_get_remaining(self):
        """Rate limiter should return correct remaining count."""
        config = RateLimitConfig(max_tokens=5, refill_rate=1)
        limiter = RateLimiter(config)

        client = "client1"
        assert limiter.get_remaining(client) == 5

        limiter.allow_request(client)
        assert limiter.get_remaining(client) == 4

    def test_rate_limiter_get_reset_after(self):
        """Rate limiter should calculate reset time."""
        config = RateLimitConfig(max_tokens=1, refill_rate=1)  # 1 token/sec
        limiter = RateLimiter(config)

        client = "client1"

        # Use the token
        limiter.allow_request(client)

        # Should be rate limited
        assert limiter.allow_request(client) is False

        # Reset time should be approximately 1 second
        reset_time = limiter.get_reset_after(client)
        assert 0.9 < reset_time < 1.2

    def test_rate_limiter_cleanup_old_buckets(self):
        """Rate limiter should clean up old unused buckets."""
        config = RateLimitConfig(max_tokens=10, refill_rate=1)
        limiter = RateLimiter(config)

        # Create buckets
        limiter.allow_request("client1")
        limiter.allow_request("client2")
        assert len(limiter.buckets) == 2

        # Cleanup with 0 second max age should remove old buckets
        with patch("time.time", return_value=time.time() + 3600):
            removed = limiter.cleanup_old_buckets(max_age_seconds=3600)

        assert removed == 2
        assert len(limiter.buckets) == 0


class TestRateLimiterGlobal:
    """Tests for global rate limiter initialization."""

    def test_init_rate_limiter_with_custom_limits(self):
        """Initializing rate limiter should set custom limits."""
        init_rate_limiter(global_limit=50, upload_limit=5, chat_limit=15)
        limiter = get_rate_limiter()

        # Test upload limit (lower than chat)
        for _ in range(5):
            assert limiter.allow_request("client", "/api/v1/documents/upload") is True

        assert limiter.allow_request("client", "/api/v1/documents/upload") is False

        # Test chat limit (different client)
        for _ in range(15):
            assert limiter.allow_request("client2", "/api/v1/chat") is True

        assert limiter.allow_request("client2", "/api/v1/chat") is False


class TestRateLimiterEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_rate_limiter_zero_max_tokens(self):
        """Rate limiter should handle zero max tokens."""
        config = RateLimitConfig(max_tokens=0, refill_rate=0)
        bucket = TokenBucket(config)

        # Should not allow any requests
        assert bucket.allow_request() is False

    def test_rate_limiter_very_high_refill_rate(self):
        """Rate limiter should handle very high refill rates."""
        config = RateLimitConfig(max_tokens=1000000, refill_rate=1000000)
        bucket = TokenBucket(config)

        # Should have many tokens
        for _ in range(1000):
            assert bucket.allow_request() is True

    def test_rate_limiter_many_clients(self):
        """Rate limiter should handle many clients."""
        config = RateLimitConfig(max_tokens=10, refill_rate=1)
        limiter = RateLimiter(config)

        # Create 100 clients
        for i in range(100):
            client_id = f"client_{i}"
            assert limiter.allow_request(client_id) is True

        # Each should have 9 remaining
        for i in range(100):
            client_id = f"client_{i}"
            assert limiter.get_remaining(client_id) == 9
