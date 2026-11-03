"""
Prometheus metrics middleware for FastAPI (ASGI-compliant).

Tracks:
- Request count (per endpoint, method, status)
- Request latency (histogram by endpoint)
- In-flight requests (gauge)
"""

import time
from typing import Any

from prometheus_client import Counter, Gauge, Histogram

# Metrics (2026 standard)
request_count = Counter(
    "fastapi_requests_total",
    "Total requests",
    ["method", "endpoint", "status"],
)

request_duration = Histogram(
    "fastapi_request_duration_seconds",
    "Request latency in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

in_flight_requests = Gauge(
    "fastapi_requests_in_flight",
    "Number of in-flight requests",
)


class PrometheusMiddleware:
    """Middleware for Prometheus metrics collection (ASGI-compliant)."""

    def __init__(self, app: Any):
        """Initialize middleware."""
        self.app = app

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        """
        Process ASGI scope and collect metrics.
        
        This is the proper ASGI middleware signature.
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "UNKNOWN")
        path = scope.get("path", "/")

        # Skip metrics endpoint
        if path == "/metrics":
            await self.app(scope, receive, send)
            return

        in_flight_requests.inc()
        start_time = time.time()
        status_code = 500

        async def send_with_metrics(message: dict) -> None:
            """Track response metrics."""
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 500)
            await send(message)

        try:
            await self.app(scope, receive, send_with_metrics)
        finally:
            duration = time.time() - start_time
            request_duration.labels(method=method, endpoint=path).observe(duration)
            request_count.labels(
                method=method,
                endpoint=path,
                status=status_code,
            ).inc()
            in_flight_requests.dec()
