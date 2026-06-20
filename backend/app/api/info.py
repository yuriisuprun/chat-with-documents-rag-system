"""System information endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.config import settings
from app.schemas import HealthResponse, TenantInfoResponse, AppointmentRequest, AppointmentResponse
from app.database import get_db
from app.services.appointment_service import AppointmentService

router = APIRouter(tags=["info"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        version="1.0.0",
        business_name=settings.TENANT_BUSINESS_NAME,
        professional_name=settings.TENANT_PROFESSIONAL_NAME
    )


@router.get("/ready")
def readiness_check() -> dict:
    """Readiness check for Kubernetes."""
    return {"ready": True}


@router.get("/info/tenant", response_model=TenantInfoResponse)
def get_tenant_info() -> TenantInfoResponse:
    """Get configured tenant information."""
    return TenantInfoResponse(
        business_name=settings.TENANT_BUSINESS_NAME,
        professional_name=settings.TENANT_PROFESSIONAL_NAME,
        whatsapp_number=settings.TENANT_WHATSAPP_NUMBER,
        auto_reply_delay_minutes=settings.TENANT_AUTO_REPLY_DELAY_MINUTES,
        booking_url=settings.TENANT_BOOKING_URL,
        office_hours=settings.TENANT_OFFICE_HOURS,
        disclaimer=settings.TENANT_DISCLAIMER,
        enable_auto_appointment=settings.TENANT_ENABLE_AUTO_APPOINTMENT,
        appointment_api_type=settings.TENANT_APPOINTMENT_API_TYPE,
        appointment_default_duration=settings.TENANT_APPOINTMENT_DEFAULT_DURATION
    )


@router.post("/appointments", response_model=AppointmentResponse)
def create_appointment(
    request: AppointmentRequest,
    db: Session = Depends(get_db)
) -> AppointmentResponse:
    """
    Create appointment (if auto-appointment is enabled).
    
    This endpoint allows manual appointment creation when the feature is enabled.
    """
    appointment_service = AppointmentService()
    
    if not appointment_service.is_enabled():
        raise HTTPException(
            status_code=400,
            detail="Appointment automation is not enabled"
        )
    
    result = appointment_service.create_appointment(
        client_phone=request.client_phone,
        client_name=request.client_name,
        preferred_date=request.preferred_date,
        preferred_time=request.preferred_time,
        notes=request.notes
    )
    
    return AppointmentResponse(
        appointment_id=result["appointment_id"],
        client_phone=result["client_phone"],
        scheduled_at=result["scheduled_at"],
        confirmation_url=result["confirmation_url"],
        status=result["status"],
        message=result["message"]
    )
