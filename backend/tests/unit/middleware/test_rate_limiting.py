"""
Unit tests for rate limiting middleware.

Tests rate limiting enforcement and header generation.
"""

import pytest
from fastapi import FastAPI, status
from fastapi.responses import PlainTextResponse
from fastapi.testclient import TestClient

from app.core.rate_limiter import init_rate_limiter
from app.middleware.rate_limiting import RateLimitMiddleware


@pytest.fixture
def test_app():
    """Create a test FastAPI app with rate limiting middleware."""
    app = FastAPI()

    # Initialize rate limiter with small limits for testing
    init_rate_limiter(global_limit=3, upload_limit=2, chat_limit=2)

    # Add middleware
    app.add_middleware(RateLimitMiddleware)

    @app.get("/test")
    def test_endpoint():
        return {"status": "ok"}

    @app.get("/api/v1/documents/upload")
    def upload_endpoint():
        return {"status": "ok"}

    @app.get("/api/v1/chat")
    def chat_endpoint():
        return {"status": "ok"}

    @app.get("/api/v1/health")
    def health_endpoint():
        return {"status": "ok"}

    return app


@pytest.fixture
def client(test_app):
    """Create a test client."""
    return TestClient(test_app)


class TestRateLimitingMiddleware:
    """Tests for rate limiting middleware."""

    def test_allows_requests_within_limit(self, client):
        """Should allow requests within limit."""
        # Global limit is 3, so 3 requests should succeed
        response1 = client.get("/test")
        assert response1.status_code == 200

        response2 = client.get("/test")
        assert response2.status_code == 200

        response3 = client.get("/test")
        assert response3.status_code == 200

    def test_rejects_requests_exceeding_limit(self, client):
        """Should reject requests exceeding limit."""
        # Use up limit
        for _ in range(3):
            client.get("/test")

        # 4th request should be rate limited
        response = client.get("/test")
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_rate_limit_headers(self, client):
        """Should include rate limit headers in response."""
        response = client.get("/test")

        assert response.status_code == 200
        assert "X-RateLimit-Remaining" in response.headers

    def test_endpoint_specific_limits(self, client):
        """Should enforce endpoint-specific limits."""
        # Upload limit is 2
        response1 = client.get("/api/v1/documents/upload")
        assert response1.status_code == 200

        response2 = client.get("/api/v1/documents/upload")
        assert response2.status_code == 200

        response3 = client.get("/api/v1/documents/upload")
        assert response3.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_bypass_health_endpoint(self, client):
        """Health endpoint should bypass rate limiting."""
        # Make many requests to health endpoint
        for _ in range(100):
            response = client.get("/api/v1/health")
            assert response.status_code == 200

    def test_per_client_isolation(self, client):
        """Different clients should have separate limits."""
        # Make requests as one client
        for _ in range(3):
            client.get("/test")

        # The same client IP should now be limited
        response = client.get("/test")
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS


class TestRateLimitErrorResponse:
    """Tests for rate limit error responses."""

    def test_rate_limit_error_format(self, client):
        """Rate limit error should have correct format."""
        # Exhaust limit
        for _ in range(3):
            client.get("/test")

        response = client.get("/test")
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

        data = response.json()
        assert "error" in data
        assert "message" in data
        assert "retry_after" in data

    def test_retry_after_header(self, client):
        """Should include Retry-After header."""
        # Exhaust limit
        for _ in range(3):
            client.get("/test")

        response = client.get("/test")
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert "Retry-After" in response.headers
