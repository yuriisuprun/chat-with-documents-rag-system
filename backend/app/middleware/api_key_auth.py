"""
API key authentication middleware for FastAPI.

Validates API key in Authorization header when enabled.
Bypass for health check and documentation endpoints.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Endpoints that bypass API key authentication
BYPASS_ENDPOINTS = {
    "/api/v1/health",
    "/docs",
    "/redoc",
    "/openapi.json",
}


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """API key authentication middleware for FastAPI."""

    async def dispatch(self, request: Request, call_next):
        """
        API key authentication middleware.

        Validates Authorization header when API_KEY_ENABLED is true.
        Format: "Authorization: Bearer <api_key>"

        Args:
            request: FastAPI request
            call_next: Next middleware/route handler

        Returns:
            Response or 401 Unauthorized if auth fails
        """
        try:
            # Skip authentication if disabled
            if not settings.api_key_enabled:
                return await call_next(request)

            # Skip certain endpoints
            if request.url.path in BYPASS_ENDPOINTS:
                return await call_next(request)

            # Get Authorization header
            auth_header = request.headers.get("Authorization", "")

            if not auth_header:
                logger.warning(f"Missing Authorization header for {request.url.path}")
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "error": "missing_authorization",
                        "message": "Authorization header is required",
                    },
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Parse Bearer token
            parts = auth_header.split()
            if len(parts) != 2 or parts[0].lower() != "bearer":
                logger.warning(f"Invalid Authorization header format for {request.url.path}")
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "error": "invalid_authorization_format",
                        "message": "Authorization header must be 'Bearer <token>'",
                    },
                    headers={"WWW-Authenticate": "Bearer"},
                )

            api_key = parts[1]

            # Validate API key
            if not api_key or api_key != settings.api_key:
                logger.warning(f"Invalid API key attempt for {request.url.path}")
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "error": "invalid_api_key",
                        "message": "Invalid API key",
                    },
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # API key is valid, proceed
            logger.debug(f"Valid API key for {request.url.path}")
            return await call_next(request)

        except Exception as e:
            logger.error(f"API key authentication error: {e}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "authentication_error",
                    "message": "Authentication error",
                },
            )


# For backwards compatibility with app.add_middleware()
async def api_key_auth_middleware(request: Request, call_next):
    """Wrapper function for middleware compatibility."""
    middleware = APIKeyAuthMiddleware(app=None)
    return await middleware.dispatch(request, call_next)
