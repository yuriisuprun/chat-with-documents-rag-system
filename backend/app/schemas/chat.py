"""
Pydantic schemas for chat-related API requests and responses.
"""

from typing import Optional

from pydantic import BaseModel, Field


class SourceReference(BaseModel):
    """Reference to a source chunk in a document."""

    document_id: str = Field(..., description="ID of the source document")
    filename: str = Field(..., description="Name of the source document")
    page_number: int = Field(..., description="Page number in the document")
    chunk_index: int = Field(..., description="Index of the chunk")
    similarity_score: float = Field(
        ..., description="Similarity score (0-1) of this chunk to query"
    )
    text_preview: str = Field(..., description="First 200 characters of the chunk")


class ChatRequest(BaseModel):
    """Request for chat endpoint."""

    query: str = Field(..., min_length=1, max_length=2000, description="User question")
    document_ids: Optional[list[str]] = Field(
        None, description="List of document IDs to search in (optional)"
    )
    include_sources: bool = Field(
        True, description="Whether to include source references in response"
    )


class ChatResponse(BaseModel):
    """Response from chat endpoint."""

    query: str = Field(..., description="The user's question")
    answer: str = Field(..., description="LLM-generated answer")
    sources: list[SourceReference] = Field(
        ..., description="Source chunks used to generate answer"
    )
    context_sufficient: bool = Field(
        ..., description="Whether context was sufficient to answer"
    )
    error: Optional[str] = Field(
        None, description="Error message if generation failed"
    )


class HealthCheckResponse(BaseModel):
    """Response from health check endpoint."""

    status: str = Field(..., description="Overall health status (healthy, degraded, unhealthy)")
    services: dict = Field(..., description="Status of individual services")
    version: str = Field(..., description="Application version")
    timestamp: str = Field(..., description="Timestamp of health check")


class ErrorResponse(BaseModel):
    """Standard error response."""

    error_code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[dict] = Field(
        None, description="Additional error details"
    )
