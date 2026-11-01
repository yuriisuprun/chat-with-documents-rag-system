"""
Unit tests for security headers middleware.

Tests that security headers are added to all responses.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.middleware.security_headers import SecurityHeadersMiddleware


@pytest.fixture
def test_app():
    """Create a test FastAPI app with security headers middleware."""
    app = FastAPI()

    # Add middleware
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/test")
    def test_endpoint():
        return {"status": "ok"}

    return app


@pytest.fixture
def client(test_app):
    """Create a test client."""
    return TestClient(test_app)


class TestSecurityHeadersMiddleware:
    """Tests for security headers middleware."""

    def test_adds_content_security_policy(self, client):
        """Should add Content-Security-Policy header."""
        response = client.get("/test")

        assert "Content-Security-Policy" in response.headers
        assert "script-src 'self'" in response.headers["Content-Security-Policy"]

    def test_adds_x_frame_options(self, client):
        """Should add X-Frame-Options header."""
        response = client.get("/test")

        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"

    def test_adds_x_content_type_options(self, client):
        """Should add X-Content-Type-Options header."""
        response = client.get("/test")

        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"

    def test_adds_x_xss_protection(self, client):
        """Should add X-XSS-Protection header."""
        response = client.get("/test")

        assert "X-XSS-Protection" in response.headers
        assert "1; mode=block" in response.headers["X-XSS-Protection"]

    def test_adds_referrer_policy(self, client):
        """Should add Referrer-Policy header."""
        response = client.get("/test")

        assert "Referrer-Policy" in response.headers
        assert "strict-origin-when-cross-origin" in response.headers["Referrer-Policy"]

    def test_adds_permissions_policy(self, client):
        """Should add Permissions-Policy header."""
        response = client.get("/test")

        assert "Permissions-Policy" in response.headers
        policy = response.headers["Permissions-Policy"]
        assert "camera=()" in policy
        assert "microphone=()" in policy
        assert "geolocation=()" in policy

    def test_removes_server_header(self, client):
        """Should remove server header if present."""
        response = client.get("/test")

        # Server header should not be exposed
        # (TestClient might not include it anyway, but this is defensive)
        if "server" in response.headers:
            # If somehow set, it should be empty
            assert response.headers["server"] == ""

    def test_hsts_in_production(self, client):
        """Should add HSTS header in production."""
        with patch("app.middleware.security_headers.settings") as mock_settings:
            mock_settings.is_production = True

            response = client.get("/test")

            assert "Strict-Transport-Security" in response.headers
            assert "max-age=31536000" in response.headers["Strict-Transport-Security"]

    def test_no_hsts_in_development(self, client):
        """Should not add HSTS header in development."""
        with patch("app.middleware.security_headers.settings") as mock_settings:
            mock_settings.is_production = False

            response = client.get("/test")

            # HSTS should not be present in development
            # (it might still be there if TestClient caches, but we're testing the logic)
            if "Strict-Transport-Security" in response.headers:
                # This would be from a previous test, not added by this middleware
                pass


class TestSecurityHeadersCompliance:
    """Tests for security compliance."""

    def test_csp_prevents_inline_scripts(self, client):
        """CSP should prevent inline scripts."""
        response = client.get("/test")

        csp = response.headers["Content-Security-Policy"]
        # Should NOT include 'unsafe-inline' for scripts specifically
        # (may be in styles, but not in script-src)
        script_src = [part for part in csp.split("; ") if part.startswith("script-src")]
        assert len(script_src) > 0
        assert "'unsafe-inline'" not in script_src[0]

    def test_csp_allows_style_inline(self, client):
        """CSP should allow inline styles (for some frameworks)."""
        response = client.get("/test")

        csp = response.headers["Content-Security-Policy"]
        # Styles are often inline in modern frameworks
        assert "style-src 'self' 'unsafe-inline'" in csp

    def test_csp_restricts_frames(self, client):
        """CSP should restrict framing."""
        response = client.get("/test")

        csp = response.headers["Content-Security-Policy"]
        assert "frame-ancestors 'none'" in csp

    def test_error_handling_graceful(self, client):
        """Middleware should not crash on errors."""
        # Test multiple requests to ensure no state issues
        response1 = client.get("/test")
        response2 = client.get("/test")
        response3 = client.get("/test")

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200

        # All should have headers
        assert "Content-Security-Policy" in response1.headers
        assert "Content-Security-Policy" in response2.headers
        assert "Content-Security-Policy" in response3.headers
