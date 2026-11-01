"""
Rate limiting service using token bucket algorithm.

Provides in-memory rate limiting for API endpoints. Can be extended to use
Redis for distributed deployments.
"""

import time
from dataclasses import dataclass
from typing import Dict, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    max_tokens: int
    refill_rate: float  # tokens per second


class TokenBucket:
    """Token bucket for rate limiting."""

    def __init__(self, config: RateLimitConfig):
        """
        Initialize token bucket.

        Args:
            config: Rate limit configuration
        """
        self.config = config
        self.tokens = float(config.max_tokens)
        self.last_refill = time.time()

    def allow_request(self) -> bool:
        """
        Check if request is allowed and consume token if allowed.

        Returns:
            True if request is allowed, False if rate limited
        """
        self._refill()

        if self.tokens >= 1:
            self.tokens -= 1
            return True

        return False

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(
            self.config.max_tokens,
            self.tokens + elapsed * self.config.refill_rate
        )
        self.last_refill = now

    def get_remaining(self) -> int:
        """Get current remaining tokens."""
        self._refill()
        return int(self.tokens)


class RateLimiter:
    """In-memory rate limiter for multiple clients."""

    def __init__(self, default_config: RateLimitConfig):
        """
        Initialize rate limiter.

        Args:
            default_config: Default rate limit configuration
        """
        self.default_config = default_config
        self.buckets: Dict[str, TokenBucket] = {}
        self.endpoint_configs: Dict[str, RateLimitConfig] = {}

    def set_endpoint_limit(self, endpoint: str, config: RateLimitConfig) -> None:
        """
        Set rate limit for specific endpoint.

        Args:
            endpoint: Endpoint path (e.g., "/api/v1/documents/upload")
            config: Rate limit configuration for this endpoint
        """
        self.endpoint_configs[endpoint] = config
        logger.debug(f"Set rate limit for {endpoint}: {config.max_tokens} tokens")

    def allow_request(self, client_id: str, endpoint: str = "global") -> bool:
        """
        Check if request is allowed for client.

        Args:
            client_id: Unique client identifier (IP, API key, etc.)
            endpoint: Endpoint path (default: "global" for global limit)

        Returns:
            True if request is allowed, False if rate limited
        """
        # Get config for this endpoint
        config = self.endpoint_configs.get(endpoint, self.default_config)

        # Create bucket key
        bucket_key = f"{client_id}:{endpoint}"

        # Get or create bucket
        if bucket_key not in self.buckets:
            self.buckets[bucket_key] = TokenBucket(config)

        bucket = self.buckets[bucket_key]
        allowed = bucket.allow_request()

        if not allowed:
            logger.warning(f"Rate limit exceeded for {client_id} on {endpoint}")

        return allowed

    def get_remaining(self, client_id: str, endpoint: str = "global") -> int:
        """
        Get remaining requests for client.

        Args:
            client_id: Unique client identifier
            endpoint: Endpoint path (default: "global")

        Returns:
            Number of remaining requests
        """
        bucket_key = f"{client_id}:{endpoint}"

        if bucket_key not in self.buckets:
            config = self.endpoint_configs.get(endpoint, self.default_config)
            return config.max_tokens

        return self.buckets[bucket_key].get_remaining()

    def get_reset_after(self, client_id: str, endpoint: str = "global") -> float:
        """
        Get seconds until next token is available.

        Args:
            client_id: Unique client identifier
            endpoint: Endpoint path (default: "global")

        Returns:
            Seconds until next token, or 0 if token available now
        """
        bucket_key = f"{client_id}:{endpoint}"

        if bucket_key not in self.buckets:
            return 0

        bucket = self.buckets[bucket_key]
        if bucket.tokens >= 1:
            return 0

        # Calculate seconds until next token
        tokens_needed = 1 - bucket.tokens
        return tokens_needed / bucket.config.refill_rate

    def cleanup_old_buckets(self, max_age_seconds: int = 3600) -> int:
        """
        Clean up unused buckets (for long-running servers).

        Args:
            max_age_seconds: Remove buckets not used in this many seconds

        Returns:
            Number of buckets removed
        """
        now = time.time()
        to_remove = []

        for bucket_key, bucket in self.buckets.items():
            age = now - bucket.last_refill
            if age > max_age_seconds:
                to_remove.append(bucket_key)

        for bucket_key in to_remove:
            del self.buckets[bucket_key]

        if to_remove:
            logger.debug(f"Cleaned up {len(to_remove)} rate limit buckets")

        return len(to_remove)


# Global rate limiter instance (initialized in main.py)
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """
    Get global rate limiter instance.

    Returns:
        RateLimiter instance
    """
    global _rate_limiter
    if _rate_limiter is None:
        # Create with 100 req/min default
        config = RateLimitConfig(max_tokens=100, refill_rate=100 / 60)
        _rate_limiter = RateLimiter(config)
    return _rate_limiter


def init_rate_limiter(global_limit: int = 100, upload_limit: int = 10, chat_limit: int = 30) -> None:
    """
    Initialize rate limiter with custom limits.

    Args:
        global_limit: Global requests per minute
        upload_limit: Document upload requests per minute
        chat_limit: Chat requests per minute
    """
    global _rate_limiter

    # Create rate limiter with global limit
    config = RateLimitConfig(
        max_tokens=global_limit,
        refill_rate=global_limit / 60
    )
    _rate_limiter = RateLimiter(config)

    # Set endpoint-specific limits
    upload_config = RateLimitConfig(
        max_tokens=upload_limit,
        refill_rate=upload_limit / 60
    )
    _rate_limiter.set_endpoint_limit("/api/v1/documents/upload", upload_config)

    chat_config = RateLimitConfig(
        max_tokens=chat_limit,
        refill_rate=chat_limit / 60
    )
    _rate_limiter.set_endpoint_limit("/api/v1/chat", chat_config)

    logger.info(
        f"Rate limiter initialized: "
        f"global={global_limit}/min, "
        f"upload={upload_limit}/min, "
        f"chat={chat_limit}/min"
    )
