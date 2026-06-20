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
    TENANT_BUSINESS_NAME: str = "My Professional Services"
    TENANT_PROFESSIONAL_NAME: str = "John Doe"
    TENANT_WHATSAPP_NUMBER: str = "+1234567890"
    
    # Auto-Reply Configuration
    TENANT_AUTO_REPLY_DELAY_MINUTES: int = 30
    
    # Booking & Info
    TENANT_BOOKING_URL: Optional[str] = None  # e.g., https://calendly.com/john
    TENANT_OFFICE_HOURS: Optional[str] = None  # e.g., "Mon-Fri 9AM-5PM EST"
    
    # Legal Compliance
    TENANT_DISCLAIMER: str = "This is an automated assistant. This message is not professional advice."
    
    # ============ APPOINTMENT AUTOMATION FEATURE ============
    # Feature flag for automatic appointment scheduling
    TENANT_ENABLE_AUTO_APPOINTMENT: bool = False
    
    # Calendar Integration (optional - when auto-appointment enabled)
    TENANT_APPOINTMENT_API_TYPE: Optional[str] = None  # "calendly", "google_calendar", "custom"
    TENANT_APPOINTMENT_API_KEY: Optional[str] = None   # API key for calendar service
    TENANT_APPOINTMENT_API_URL: Optional[str] = None   # Custom API endpoint
    TENANT_APPOINTMENT_DEFAULT_DURATION: int = 30      # Minutes
    TENANT_APPOINTMENT_CONFIRMATION_MESSAGE: Optional[str] = None  # Custom confirmation message
    
    # ============ MULTI-LANGUAGE SUPPORT ============
    # Supported languages for the assistant (ISO 639-1 codes)
    SUPPORTED_LANGUAGES: list = ["en", "ru", "it"]  # English, Russian, Italian
    
    # Language-specific disclaimers and messages
    TENANT_DISCLAIMER_EN: str = "This is an automated assistant. This message is not professional advice."
    TENANT_DISCLAIMER_RU: str = "Это автоматический помощник. Это сообщение не является профессиональной консультацией."
    TENANT_DISCLAIMER_IT: str = "Questo è un assistente automatico. Questo messaggio non è una consulenza professionale."
    
    # Language-specific office hours formats
    TENANT_OFFICE_HOURS_EN: Optional[str] = None  # e.g., "Mon-Fri 9AM-5PM EST"
    TENANT_OFFICE_HOURS_RU: Optional[str] = None  # e.g., "Пн-Пт 9:00-17:00 МСК"
    TENANT_OFFICE_HOURS_IT: Optional[str] = None  # e.g., "Lun-Ven 9:00-17:00 CET"
    
    # Default language for the tenant
    TENANT_DEFAULT_LANGUAGE: str = "en"
    
    # =====================================================
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
