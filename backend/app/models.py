"""SQLAlchemy ORM models."""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Boolean, Float, Index, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector
import enum

from app.database import Base


class Intent(str, enum.Enum):
    """Message intent types."""
    APPOINTMENT_REQUEST = "appointment_request"
    OFFICE_HOURS = "office_hours"
    FEE_QUESTION = "fee_question"
    SERVICE_INFORMATION = "service_information"
    DOCUMENT_SUBMISSION = "document_submission"
    LEGAL_QUESTION = "legal_question"
    OTHER = "other"


class MessageSender(str, enum.Enum):
    """Message sender types."""
    CLIENT = "client"
    PROFESSIONAL = "professional"
    AI = "ai"


class Conversation(Base):
    """Conversation between client and professional."""
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, index=True)
    client_phone = Column(String(20), nullable=False, index=True)
    status = Column(String(50), default="active", index=True)  # active, closed, escalated
    detected_language = Column(String(10), default="en", index=True)  # ISO 639-1 code (en, ru, it)
    language_confidence = Column(Float, nullable=True)  # 0-1 confidence in language detection
    last_client_message_at = Column(DateTime, nullable=True)
    last_professional_message_at = Column(DateTime, nullable=True)
    last_ai_message_at = Column(DateTime, nullable=True)
    custom_data = Column(JSONB, nullable=True)  # Store custom data
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_conversations_phone_created", "client_phone", "created_at"),
    )


class Message(Base):
    """Individual message in a conversation."""
    __tablename__ = "messages"

    id = Column(String, primary_key=True, index=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False, index=True)
    sender = Column(SQLEnum(MessageSender), nullable=False, index=True)
    content = Column(Text, nullable=False)
    detected_language = Column(String(10), nullable=True)  # ISO 639-1 code (en, ru, it)
    language_confidence = Column(Float, nullable=True)  # 0-1 confidence in detection
    media_type = Column(String(50), nullable=True)  # audio, image, document, etc.
    media_url = Column(String(500), nullable=True)
    transcript = Column(Text, nullable=True)  # For audio messages
    detected_intent = Column(SQLEnum(Intent), nullable=True)
    is_auto_reply = Column(Boolean, default=False, index=True)
    custom_data = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    __table_args__ = (
        Index("ix_messages_conversation_created", "conversation_id", "created_at"),
        Index("ix_messages_sender_intent", "sender", "detected_intent"),
    )


class KnowledgeDocument(Base):
    """Knowledge base documents for RAG."""
    __tablename__ = "knowledge_documents"

    id = Column(String, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, docx, txt
    file_size_bytes = Column(Integer)
    section_title = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    """Chunks of knowledge documents with embeddings for vector search."""
    __tablename__ = "document_chunks"

    id = Column(String, primary_key=True, index=True)
    document_id = Column(String, ForeignKey("knowledge_documents.id"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    detected_language = Column(String(10), nullable=True)  # ISO 639-1 code for chunk language
    embedding = Column(Vector(1536), nullable=True)  # OpenAI embedding dimension
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    document = relationship("KnowledgeDocument", back_populates="chunks")

    __table_args__ = (
        Index("ix_document_chunks_document", "document_id"),
    )


class AuditLog(Base):
    """Audit trail for all AI actions."""
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, index=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=True)
    action = Column(String(255), nullable=False)
    details = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("ix_audit_logs_created", "created_at"),
    )
