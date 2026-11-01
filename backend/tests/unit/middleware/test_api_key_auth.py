"""
Unit tests for API key authentication middleware.

Tests API key validation and authorization.
"""

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.middleware.api_key_auth import APIKeyAuthMiddleware


@pytest.fixture
def test_app_with_auth():
    """Create a test FastAPI app with API key auth enabled."""
    app = FastAPI()

    # Add middleware
    app.add_middleware(APIKeyAuthMiddleware)

    @app.get("/test")
    def test_endpoint():
        return {"status": "ok"}

    @app.get("/api/v1/health")
    def health_endpoint():
        return {"status": "ok"}

    @app.get("/docs")
    def docs_endpoint():
        return {"status": "docs"}

    return app


@pytest.fixture
def test_app_without_auth():
    """Create a test FastAPI app with API key auth disabled."""
    app = FastAPI()

    # Add middleware (but with auth disabled via settings)
    app.add_middleware(APIKeyAuthMiddleware)

    @app.get("/test")
    def test_endpoint():
        return {"status": "ok"}

    return app


class TestAPIKeyAuthMiddleware:
    """Tests for API key authentication middleware."""

    def test_bypasses_health_check(self, test_app_with_auth):
        """Should bypass API key check for health endpoint."""
        # Mock settings to enable API key auth
        with patch("app.middleware.api_key_auth.settings") as mock_settings:
            mock_settings.api_key_enabled = True
            mock_settings.api_key = "test-key"

            client = TestClient(test_app_with_auth)
            response = client.get("/api/v1/health")

            assert response.status_code == 200

    def test_bypasses_docs(self, test_app_with_auth):
        """Should bypass API key check for docs."""
        with patch("app.middleware.api_key_auth.settings") as mock_settings:
            mock_settings.api_key_enabled = True
            mock_settings.api_key = "test-key"

            client = TestClient(test_app_with_auth)
            response = client.get("/docs")

            assert response.status_code == 200

    def test_rejects_missing_authorization_header(self, test_app_with_auth):
        """Should reject request without Authorization header."""
        with patch("app.middleware.api_key_auth.settings") as mock_settings:
            mock_settings.api_key_enabled = True
            mock_settings.api_key = "test-key"

            client = TestClient(test_app_with_auth)
            response = client.get("/test")

            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            data = response.json()
            assert data["error"] == "missing_authorization"

    def test_rejects_invalid_authorization_format(self, test_app_with_auth):
        """Should reject invalid Authorization header format."""
        with patch("app.middleware.api_key_auth.settings") as mock_settings:
            mock_settings.api_key_enabled = True
            mock_settings.api_key = "test-key"

            client = TestClient(test_app_with_auth)
            response = client.get(
                "/test",
                headers={"Authorization": "InvalidFormat"}
            )

            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            data = response.json()
            assert data["error"] == "invalid_authorization_format"

    def test_accepts_valid_api_key(self, test_app_with_auth):
        """Should accept request with valid API key."""
        with patch("app.middleware.api_key_auth.settings") as mock_settings:
            mock_settings.api_key_enabled = True
            mock_settings.api_key = "test-key-123"

            client = TestClient(test_app_with_auth)
            response = client.get(
                "/test",
                headers={"Authorization": "Bearer test-key-123"}
            )

            assert response.status_code == 200

    def test_rejects_invalid_api_key(self, test_app_with_auth):
        """Should reject request with invalid API key."""
        with patch("app.middleware.api_key_auth.settings") as mock_settings:
            mock_settings.api_key_enabled = True
            mock_settings.api_key = "test-key-correct"

            client = TestClient(test_app_with_auth)
            response = client.get(
                "/test",
                headers={"Authorization": "Bearer test-key-wrong"}
            )

            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            data = response.json()
            assert data["error"] == "invalid_api_key"

    def test_skips_auth_when_disabled(self, test_app_without_auth):
        """Should skip authentication when disabled."""
        with patch("app.middleware.api_key_auth.settings") as mock_settings:
            mock_settings.api_key_enabled = False

            client = TestClient(test_app_without_auth)
            # Request without API key should succeed
            response = client.get("/test")

            assert response.status_code == 200

    def test_case_sensitive_bearer_token(self, test_app_with_auth):
        """Bearer token should be case-insensitive prefix."""
        with patch("app.middleware.api_key_auth.settings") as mock_settings:
            mock_settings.api_key_enabled = True
            mock_settings.api_key = "test-key"

            client = TestClient(test_app_with_auth)

            # Lowercase bearer should work
            response = client.get(
                "/test",
                headers={"Authorization": "bearer test-key"}
            )
            assert response.status_code == 200

            # Uppercase Bearer should work
            response = client.get(
                "/test",
                headers={"Authorization": "Bearer test-key"}
            )
            assert response.status_code == 200

    def test_www_authenticate_header(self, test_app_with_auth):
        """Should include WWW-Authenticate header on 401."""
        with patch("app.middleware.api_key_auth.settings") as mock_settings:
            mock_settings.api_key_enabled = True
            mock_settings.api_key = "test-key"

            client = TestClient(test_app_with_auth)
            response = client.get("/test")

            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert "WWW-Authenticate" in response.headers
            assert response.headers["WWW-Authenticate"] == "Bearer"
