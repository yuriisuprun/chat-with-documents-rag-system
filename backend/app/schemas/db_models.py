"""
Pydantic schemas for database models.

API-facing schemas for document, query, and session data.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DocumentDB(BaseModel):
    """Document metadata from database."""

    id: str = Field(..., description="Document ID")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    page_count: int = Field(..., description="Number of pages")
    chunk_count: int = Field(..., description="Number of chunks")
    status: str = Field(..., description="Processing status")
    embedding_model: str = Field(..., description="Embedding model used")
    query_count: int = Field(..., description="Number of queries")
    access_count: int = Field(..., description="Access count")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Update timestamp")


class QueryDB(BaseModel):
    """Query record from database."""

    id: str = Field(..., description="Query ID")
    query_text: str = Field(..., description="Question asked")
    answer_text: str = Field(..., description="Answer generated")
    retrieval_time_ms: float = Field(..., description="Retrieval time")
    generation_time_ms: float = Field(..., description="Generation time")
    total_time_ms: float = Field(..., description="Total time")
    context_sufficient: bool = Field(..., description="Context sufficient flag")
    retrieval_count: int = Field(..., description="Number of chunks retrieved")
    average_similarity_score: float = Field(..., description="Average similarity")
    user_feedback: Optional[str] = Field(None, description="User feedback")
    created_at: datetime = Field(..., description="Creation timestamp")


class SessionDB(BaseModel):
    """Session record from database."""

    id: str = Field(..., description="Session ID")
    session_name: Optional[str] = Field(None, description="Session name")
    query_count: int = Field(..., description="Number of queries")
    document_upload_count: int = Field(..., description="Uploads in session")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Update timestamp")


class DatabaseStats(BaseModel):
    """Overall database statistics."""

    total_documents: int = Field(..., description="Total documents")
    indexed_documents: int = Field(..., description="Successfully indexed")
    failed_documents: int = Field(..., description="Failed to process")
    total_chunks: int = Field(..., description="Total chunks created")
    total_queries: int = Field(..., description="Total queries executed")
    avg_query_time_ms: float = Field(..., description="Average query time")
    total_sessions: int = Field(..., description="Total user sessions")


class QueryFeedback(BaseModel):
    """User feedback for a query."""

    query_id: str = Field(..., description="Query ID")
    feedback: str = Field(..., description="Feedback: helpful, not_helpful, neutral")


class DocumentStats(BaseModel):
    """Document statistics."""

    total_documents: int
    indexed_documents: int
    failed_documents: int
    total_chunks: int


class QueryStats(BaseModel):
    """Query statistics."""

    total_queries: int
    avg_retrieval_time_ms: float
    avg_generation_time_ms: float
    avg_total_time_ms: float
    context_sufficient_percentage: float


class SessionStats(BaseModel):
    """Session statistics."""

    total_sessions: int
    avg_queries_per_session: float
