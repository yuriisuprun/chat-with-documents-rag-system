"""
Pydantic schemas for document-related API requests and responses.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    """Metadata about a document."""

    id: str = Field(..., description="Unique document identifier (UUID)")
    filename: str = Field(..., description="Original filename")
    sha256: str = Field(..., description="SHA-256 hash of file content")
    status: str = Field(
        ...,
        description="Document status (pending, processing, indexed, failed, deleting)",
    )
    page_count: int = Field(..., description="Number of pages in PDF")
    chunk_count: int = Field(..., description="Number of text chunks created")
    embedding_model: str = Field(..., description="Embedding model used")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class DocumentUploadResponse(BaseModel):
    """Response for successful document upload."""

    document_id: str = Field(..., description="Unique identifier for uploaded document")
    filename: str = Field(..., description="Filename of uploaded document")
    status: str = Field(..., description="Current processing status")
    message: str = Field(..., description="Status message")


class DocumentListResponse(BaseModel):
    """Response containing list of documents."""

    documents: list[DocumentMetadata] = Field(
        ..., description="List of indexed documents"
    )
    count: int = Field(..., description="Total number of documents")


class DocumentDetailResponse(BaseModel):
    """Response with detailed document information."""

    metadata: DocumentMetadata = Field(..., description="Document metadata")
    chunks_sample: list[str] = Field(
        ..., description="Sample of indexed chunks (first 3)"
    )


class DocumentDeleteResponse(BaseModel):
    """Response for document deletion."""

    document_id: str = Field(..., description="ID of deleted document")
    message: str = Field(..., description="Status message")


class DocumentStatusResponse(BaseModel):
    """Response for document status check."""

    document_id: str = Field(..., description="Document ID")
    status: str = Field(..., description="Current status")
    page_count: Optional[int] = Field(None, description="Number of pages")
    chunk_count: Optional[int] = Field(None, description="Number of chunks")
    error_message: Optional[str] = Field(None, description="Error message if status is failed")
