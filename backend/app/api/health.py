"""Health check endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)) -> HealthResponse:
    """Health check endpoint."""
    # Test database connection
    db.execute("SELECT 1")
    
    return HealthResponse(
        status="ok",
        version="1.0.0"
    )


@router.get("/ready")
def readiness_check(db: Session = Depends(get_db)) -> dict:
    """Readiness check for Kubernetes."""
    return {"ready": True}
