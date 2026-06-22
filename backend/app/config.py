"""Application configuration."""

from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/whatsapp_assistant"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    MODEL_NAME: str = "gpt-4"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    MAX_CONTEXT_LENGTH: int = 2000
    
    # WhatsApp
    WHATSAPP_ACCESS_TOKEN: Optional[str] = None
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = None
    WHATSAPP_WEBHOOK_VERIFY_TOKEN: str = "webhook_verify_token"
    
    # Admin
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "change_me"
    JWT_SECRET: str = "your_jwt_secret_change_me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # App
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    ALLOWED_HOSTS: list = ["localhost", "127.0.0.1", "0.0.0.0"]
    
    # Auto-reply settings
    AUTO_REPLY_DELAY_MINUTES: int = 30
    MAX_AUTO_REPLY_DELAY_MINUTES: int = 120
    
    # File upload
    MAX_UPLOAD_SIZE_MB: int = 10
    UPLOAD_DIR: str = "uploads"
    
    # AI behavior
    TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 500
    
    # ============ SINGLE TENANT CONFIGURATION ============
    # Configure your professional/business details here
    
    # Tenant Identity
    TENANT_BUSINESS_NAME: str = "Legal Services"
    TENANT_PROFESSIONAL_NAME: str = "Your Name"
    TENANT_WHATSAPP_NUMBER: str = "+1234567890"
    
    # Auto-Reply Configuration
    TENANT_AUTO_REPLY_DELAY_MINUTES: int = 30
    
    # ============ APPOINTMENT AUTOMATION FEATURE ============
    # Feature flag for automatic appointment scheduling via Google Calendar
    # Set to True to enable automatic appointment creation when clients request via WhatsApp
    # Requires: Google Cloud service account credentials (TENANT_APPOINTMENT_API_KEY)
    TENANT_ENABLE_AUTO_APPOINTMENT: bool = False
    
    # Calendar Integration (required when auto-appointment enabled)
    # Options: "google_calendar", "custom"
    # Default: "google_calendar" (Recommended)
    TENANT_APPOINTMENT_API_TYPE: Optional[str] = "google_calendar"
    
    # Google Calendar Configuration (REQUIRED for google_calendar type)
    # Service account JSON credentials from Google Cloud Console
    # Example format:
    # {
    #   "type": "service_account",
    #   "project_id": "...",
    #   "private_key_id": "...",
    #   "private_key": "...",
    #   "client_email": "...",
    #   "client_id": "...",
    #   "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    #   "token_uri": "https://oauth2.googleapis.com/token",
    #   "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    #   "client_x509_cert_url": "..."
    # }
    TENANT_APPOINTMENT_API_KEY: Optional[str] = None
    
    # Custom API endpoint (only for custom type)
    TENANT_APPOINTMENT_API_URL: Optional[str] = None
    
    # Appointment Settings
    # Default duration for consultations (60 minutes for legal consultations)
    TENANT_APPOINTMENT_DEFAULT_DURATION: int = 60      # Minutes
    # Working hours define when appointments can be automatically scheduled
    TENANT_APPOINTMENT_WORKING_HOURS_START: int = 9    # 9 AM (24-hour format)
    TENANT_APPOINTMENT_WORKING_HOURS_END: int = 17     # 5 PM (24-hour format)
    TENANT_APPOINTMENT_CONFIRMATION_MESSAGE: Optional[str] = None  # Custom confirmation message
    
    # Booking URL (shown as fallback if appointment fails, can be Google Calendar link)
    TENANT_BOOKING_URL: Optional[str] = None  # e.g., https://calendar.google.com
    # Office hours display (shown to clients in WhatsApp responses)
    TENANT_OFFICE_HOURS: Optional[str] = None  # e.g., "Mon-Fri 9:00-17:00, Sat 10:00-14:00"
    
    # Legal Compliance
    TENANT_DISCLAIMER: str = "This is an automated assistant. This message is not professional advice."
    
    # ============ MULTI-LANGUAGE SUPPORT ============
    # Supported languages for the assistant (ISO 639-1 codes)
    SUPPORTED_LANGUAGES: list = ["en", "ru", "it"]  # English, Russian, Italian
    
    # Language-specific disclaimers and messages
    TENANT_DISCLAIMER_EN: str = "This is an automated assistant. This message is not professional advice."
    TENANT_DISCLAIMER_RU: str = "Это автоматический помощник. Это сообщение не является профессиональной консультацией."
    TENANT_DISCLAIMER_IT: str = "Questo è un assistente automatico. Questo messaggio non è una consulenza professionale."
    
    # Language-specific office hours formats
    TENANT_OFFICE_HOURS_EN: Optional[str] = None  # e.g., "Mon-Fri 9:00-17:00 CET"
    TENANT_OFFICE_HOURS_RU: Optional[str] = None  # e.g., "Пн-Пт 9:00-17:00 CET"
    TENANT_OFFICE_HOURS_IT: Optional[str] = None  # e.g., "Lun-Ven 9:00-17:00 CET"
    
    # Default language for the tenant
    TENANT_DEFAULT_LANGUAGE: str = "en"
    
    # =====================================================
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
