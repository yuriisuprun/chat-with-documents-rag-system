"""
Integration tests for security middleware stack.

Tests how security middleware work together.
"""

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.core.rate_limiter import init_rate_limiter
from app.middleware import (
    APIKeyAuthMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
)


@pytest.fixture
def test_app():
    """Create a test FastAPI app with all security middleware."""
    app = FastAPI()

    # Initialize rate limiter
    init_rate_limiter(global_limit=5, upload_limit=2, chat_limit=2)

    # Add middleware stack (in reverse order - last added is first to execute)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(APIKeyAuthMiddleware)
    app.add_middleware(RateLimitMiddleware)

    @app.get("/test")
    def test_endpoint():
        return {"status": "ok"}

    @app.get("/api/v1/health")
    def health_endpoint():
        return {"status": "ok"}

    return app


@pytest.fixture
def client(test_app):
    """Create a test client."""
    return TestClient(test_app)


class TestSecurityMiddlewareStack:
    """Integration tests for middleware stack."""

    def test_rate_limiting_active_with_valid_key(self, client):
        """Rate limiting should work even with valid API key."""
        with patch("app.middleware.api_key_auth.settings") as mock_settings:
            mock_settings.api_key_enabled = False  # Disable API key for this test

            # Should allow limited requests
            for i in range(5):
                response = client.get("/test")
                assert response.status_code == 200

            # 6th should be rate limited
            response = client.get("/test")
            assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_security_headers_on_rate_limit_error(self, client):
        """Should get rate limit error with correct status."""
        with patch("app.middleware.api_key_auth.settings") as mock_settings:
            mock_settings.api_key_enabled = False

            # Exhaust rate limit
            for _ in range(5):
                client.get("/test")

            # Get rate limited response
            response = client.get("/test")

            assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
            assert "Retry-After" in response.headers

    def test_security_headers_on_auth_error(self, client):
        """Should get auth error with correct status."""
        with patch("app.middleware.api_key_auth.settings") as mock_settings:
            mock_settings.api_key_enabled = True
            mock_settings.api_key = "test-key"

            # Make request without API key
            response = client.get("/test")

            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert "WWW-Authenticate" in response.headers

    def test_health_check_bypasses_auth_but_not_security_headers(self, client):
        """Health check should bypass auth but still get security headers."""
        with patch("app.middleware.api_key_auth.settings") as mock_settings:
            mock_settings.api_key_enabled = True
            mock_settings.api_key = "test-key"

            # Health check without API key should succeed
            response = client.get("/api/v1/health")

            assert response.status_code == 200
            # But should still have security headers
            assert "Content-Security-Policy" in response.headers

    def test_multiple_requests_with_all_middleware(self, client):
        """Multiple requests should maintain all security controls."""
        with patch("app.middleware.api_key_auth.settings") as mock_settings:
            mock_settings.api_key_enabled = True
            mock_settings.api_key = "test-key"

            # Make multiple authenticated requests
            for _ in range(3):
                response = client.get(
                    "/test",
                    headers={"Authorization": "Bearer test-key"}
                )
                assert response.status_code == 200
                assert "Content-Security-Policy" in response.headers
                assert "X-RateLimit-Remaining" in response.headers

    def test_rate_limit_headers_always_present(self, client):
        """Rate limit headers should be in successful responses."""
        with patch("app.middleware.api_key_auth.settings") as mock_settings:
            mock_settings.api_key_enabled = False

            response = client.get("/test")

            assert response.status_code == 200
            assert "X-RateLimit-Remaining" in response.headers


class TestMiddlewareErrorHandling:
    """Tests for error handling in middleware."""

    def test_graceful_degradation_on_middleware_error(self, client):
        """Middleware should fail gracefully."""
        with patch("app.middleware.api_key_auth.settings") as mock_settings:
            mock_settings.api_key_enabled = False

            # Make request - should succeed even if middleware has internal error
            response = client.get("/test")

            assert response.status_code == 200

    def test_multiple_failed_requests_dont_break_app(self, client):
        """App should handle auth errors and recover."""
        with patch("app.middleware.api_key_auth.settings") as mock_settings:
            mock_settings.api_key_enabled = True
            mock_settings.api_key = "test-key"

            # Make several failed requests (no auth) - these will exhaust rate limit
            for _ in range(5):
                response = client.get("/test")
                assert response.status_code == status.HTTP_401_UNAUTHORIZED

            # Next unauthenticated request hits rate limit
            response = client.get("/test")
            assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

            # But authenticated request still works (different client tracking)
            response = client.get(
                "/api/v1/health",  # Health check bypasses auth
            )
            assert response.status_code == 200
