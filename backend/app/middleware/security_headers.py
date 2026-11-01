"""
Security headers middleware for FastAPI.

Adds security headers to all responses to protect against common attacks:
- XSS (X-XSS-Protection, Content-Security-Policy)
- Clickjacking (X-Frame-Options)
- MIME sniffing (X-Content-Type-Options)
- HTTPS enforcement (Strict-Transport-Security)
"""

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Security headers middleware for FastAPI."""

    async def dispatch(self, request: Request, call_next):
        """
        Add security headers to response.

        Args:
            request: FastAPI request
            call_next: Next middleware/route handler

        Returns:
            Response with security headers added
        """
        try:
            response = await call_next(request)

            # Content-Security-Policy: Prevent inline scripts and external script loading
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; "
                "font-src 'self' data:; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )

            # X-Frame-Options: Prevent clickjacking
            response.headers["X-Frame-Options"] = "DENY"

            # X-Content-Type-Options: Prevent MIME sniffing
            response.headers["X-Content-Type-Options"] = "nosniff"

            # X-XSS-Protection: Additional XSS protection in older browsers
            response.headers["X-XSS-Protection"] = "1; mode=block"

            # Referrer-Policy: Control referrer information
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

            # Permissions-Policy: Disable unnecessary features
            response.headers["Permissions-Policy"] = (
                "accelerometer=(), camera=(), microphone=(), "
                "geolocation=(), magnetometer=(), gyroscope=()"
            )

            # Remove server header to avoid fingerprinting
            if "server" in response.headers:
                del response.headers["server"]

            # HSTS: Enforce HTTPS (only in production)
            if settings.is_production:
                response.headers["Strict-Transport-Security"] = (
                    "max-age=31536000; includeSubDomains; preload"
                )
                logger.debug("Added HSTS header for production")

            return response

        except Exception as e:
            logger.error(f"Security headers middleware error: {e}", exc_info=True)
            # Fail open - if security headers fail, still return response
            return await call_next(request)


# For backwards compatibility with app.add_middleware()
async def security_headers_middleware(request: Request, call_next):
    """Wrapper function for middleware compatibility."""
    middleware = SecurityHeadersMiddleware(app=None)
    return await middleware.dispatch(request, call_next)
