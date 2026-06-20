"""Pydantic request/response schemas."""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator
from app.models import Intent, MessageSender


class ConversationCreate(BaseModel):
    """Create conversation request."""
    client_phone: str = Field(..., min_length=5, max_length=20, pattern=r"^\+?[\d]{5,20}$")


class ConversationUpdate(BaseModel):
    """Update conversation request."""
    status: Optional[str] = Field(None, pattern="^(active|closed|escalated)$")


class MessageResponse(BaseModel):
    """Message response."""
    id: str
    sender: MessageSender
    content: str
    media_type: Optional[str]
    transcript: Optional[str]
    detected_intent: Optional[Intent]
    is_auto_reply: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    """Conversation response."""
    id: str
    client_phone: str
    status: str
    last_client_message_at: Optional[datetime]
    last_professional_message_at: Optional[datetime]
    last_ai_message_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationDetailResponse(ConversationResponse):
    """Conversation with messages."""
    messages: List[MessageResponse]


class DocumentUploadRequest(BaseModel):
    """Document upload request."""
    section_title: Optional[str] = Field(None, max_length=255)


class DocumentResponse(BaseModel):
    """Document response."""
    id: str
    filename: str
    file_type: str
    file_size_bytes: int
    section_title: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class WhatsAppMessage(BaseModel):
    """Incoming WhatsApp message webhook."""
    messaging_product: str
    metadata: dict
    contacts: list
    messages: list
    statuses: Optional[list] = None


class AIResponseGenerationRequest(BaseModel):
    """Request to generate AI response."""
    conversation_id: str
    message_content: str
    detected_intent: Intent


class AdminLoginRequest(BaseModel):
    """Admin login request."""
    username: str
    password: str


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str = "1.0.0"
    business_name: str = ""  # Current tenant info
    professional_name: str = ""


class TenantInfoResponse(BaseModel):
    """Current tenant information."""
    business_name: str
    professional_name: str
    whatsapp_number: str
    auto_reply_delay_minutes: int
    booking_url: Optional[str]
    office_hours: Optional[str]
    disclaimer: str
    # Appointment automation
    enable_auto_appointment: bool
    appointment_api_type: Optional[str]
    appointment_default_duration: int


class AppointmentRequest(BaseModel):
    """Appointment creation request."""
    client_phone: str
    client_name: Optional[str] = None
    preferred_date: Optional[str] = None  # e.g., "2024-01-15"
    preferred_time: Optional[str] = None  # e.g., "14:00"
    notes: Optional[str] = None


class AppointmentResponse(BaseModel):
    """Appointment creation response."""
    appointment_id: str
    client_phone: str
    scheduled_at: Optional[str]
    confirmation_url: Optional[str]
    status: str  # pending, confirmed, failed
    message: str
