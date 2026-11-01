"""
Rate limiting middleware for FastAPI.

Limits requests per client (by IP address) to prevent abuse.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.core.logging import get_logger
from app.core.rate_limiter import get_rate_limiter

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware for FastAPI."""

    async def dispatch(self, request: Request, call_next):
        """
        Rate limiting middleware.

        Enforces per-client rate limits. Returns 429 Too Many Requests if exceeded.

        Args:
            request: FastAPI request
            call_next: Next middleware/route handler

        Returns:
            Response or 429 if rate limited
        """
        try:
            # Skip rate limiting for certain endpoints
            if request.url.path in ["/api/v1/health", "/docs", "/openapi.json", "/redoc"]:
                return await call_next(request)

            # Get client IP
            client_ip = request.client.host if request.client else "unknown"

            # Get endpoint path
            endpoint = request.url.path

            # Get rate limiter
            rate_limiter = get_rate_limiter()

            # Check if request is allowed
            if not rate_limiter.allow_request(client_ip, endpoint):
                # Get reset time
                reset_after = rate_limiter.get_reset_after(client_ip, endpoint)

                logger.warning(f"Rate limit exceeded for {client_ip} on {endpoint}")

                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "rate_limit_exceeded",
                        "message": "Too many requests. Please try again later.",
                        "retry_after": int(reset_after) + 1,
                    },
                    headers={"Retry-After": str(int(reset_after) + 1)},
                )

            # Add rate limit headers to response
            response = await call_next(request)

            remaining = rate_limiter.get_remaining(client_ip, endpoint)
            response.headers["X-RateLimit-Remaining"] = str(remaining)

            return response

        except Exception as e:
            # Fail open - if rate limiting fails, allow the request
            logger.error(f"Rate limiting error: {e}", exc_info=True)
            return await call_next(request)


# For backwards compatibility with app.add_middleware()
async def rate_limit_middleware(request: Request, call_next):
    """Wrapper function for middleware compatibility."""
    middleware = RateLimitMiddleware(app=None)
    return await middleware.dispatch(request, call_next)
