"""
Health check endpoint for application monitoring.

Verifies that the application and its dependencies are operational.
"""

from datetime import datetime

from fastapi import APIRouter
from pydantic import Field

from app.core.logging import get_logger
from app.schemas.chat import HealthCheckResponse

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["health"])

# Application version - update with each release
__version__ = "0.1.0"


async def check_services() -> dict:
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
    description="Check application and service status",
    status_code=200,
)
async def health_check() -> HealthCheckResponse:
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
