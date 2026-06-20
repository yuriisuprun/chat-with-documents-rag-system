"""Tenant management endpoints."""

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Tenant
from app.schemas import TenantCreate, TenantUpdate, TenantResponse

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
def create_tenant(
    request: TenantCreate,
    db: Session = Depends(get_db)
) -> TenantResponse:
    """Create a new tenant."""
    # Check if phone number already exists
    existing = db.query(Tenant).filter(
        Tenant.whatsapp_number == request.whatsapp_number
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="WhatsApp number already registered"
        )
    
    # Create tenant
    tenant = Tenant(
        id=f"tenant_{uuid.uuid4().hex[:12]}",
        business_name=request.business_name,
        professional_name=request.professional_name,
        whatsapp_number=request.whatsapp_number,
        auto_reply_delay_minutes=request.auto_reply_delay_minutes,
        booking_url=request.booking_url,
        office_hours=request.office_hours,
        disclaimer=request.disclaimer,
    )
    
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    
    return TenantResponse.from_orm(tenant)


@router.get("/{tenant_id}", response_model=TenantResponse)
def get_tenant(
    tenant_id: str,
    db: Session = Depends(get_db)
) -> TenantResponse:
    """Get tenant by ID."""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    return TenantResponse.from_orm(tenant)


@router.put("/{tenant_id}", response_model=TenantResponse)
def update_tenant(
    tenant_id: str,
    request: TenantUpdate,
    db: Session = Depends(get_db)
) -> TenantResponse:
    """Update tenant."""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    # Update fields
    if request.professional_name is not None:
        tenant.professional_name = request.professional_name
    if request.auto_reply_delay_minutes is not None:
        tenant.auto_reply_delay_minutes = request.auto_reply_delay_minutes
    if request.booking_url is not None:
        tenant.booking_url = request.booking_url
    if request.office_hours is not None:
        tenant.office_hours = request.office_hours
    if request.disclaimer is not None:
        tenant.disclaimer = request.disclaimer
    if request.is_active is not None:
        tenant.is_active = request.is_active
    
    db.commit()
    db.refresh(tenant)
    
    return TenantResponse.from_orm(tenant)


@router.get("", response_model=list[TenantResponse])
def list_tenants(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> list[TenantResponse]:
    """List all tenants."""
    tenants = db.query(Tenant).offset(skip).limit(limit).all()
    return [TenantResponse.from_orm(t) for t in tenants]


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tenant(
    tenant_id: str,
    db: Session = Depends(get_db)
) -> None:
    """Delete tenant and all associated data."""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    db.delete(tenant)
    db.commit()
