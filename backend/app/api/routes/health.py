"""
Health check endpoint for application monitoring.

2026 Best Practices:
- /health: Liveness (lightweight, fast)
- /readyz: Readiness (checks dependencies)

For Kubernetes/load balancers to route traffic safely.
"""

from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, status
from pydantic import Field

from app.core.logging import get_logger
from app.schemas.chat import HealthCheckResponse

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["health"])

# Application version - update with each release
__version__ = "0.1.0"


async def check_services() -> Dict[str, str]:
    """Check status of individual services."""
    services = {
        "api": "healthy",
        # These will be expanded as services are implemented
        # "database": "unknown",
        # "vector_store": "unknown",
        # "llm": "unknown",
        # "embeddings": "unknown",
    }
    return services


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Health Check",
    description="System health and status information",
    status_code=200,
)
async def health() -> HealthCheckResponse:
    """
    Health check endpoint.

    Returns the overall health status and status of individual services.

    Returns:
        HealthCheckResponse: Contains overall status and per-service status
    """
    logger.debug("Health check requested")

    services = await check_services()

    # Determine overall status
    if all(status == "healthy" for status in services.values()):
        overall_status = "healthy"
    elif all(status in ("healthy", "degraded") for status in services.values()):
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"

    response = HealthCheckResponse(
        status=overall_status,
        services=services,
        version=__version__,
        timestamp=datetime.utcnow().isoformat(),
    )

    logger.debug(f"Health check result: {overall_status}")
    return response


@router.get(
    "/readyz",
    summary="Readiness Probe",
    description="Check if service is ready to handle traffic",
    status_code=200,
)
async def readiness() -> Dict[str, Any]:
    """
    Readiness probe endpoint (checks dependencies).

    For Kubernetes/load balancers to determine if service can handle traffic.
    Checks:
    - Configuration loaded
    - Critical services operational
    - Database connected (when implemented)

    Returns:
        200: Ready to serve
        503: Not ready (dependencies down)

    Raises:
        HTTPException: 503 if not ready
    """
    try:
        logger.debug("Readiness check requested")

        # Check configuration
        from app.core.config import settings
        _ = settings

        # Check services
        services = await check_services()

        # All services must be healthy for readiness
        if not all(status == "healthy" for status in services.values()):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Services not ready",
            )

        return {
            "ready": True,
            "services": services,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready",
        )
