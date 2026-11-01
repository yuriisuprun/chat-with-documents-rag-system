"""
Document management endpoints.

Handles document upload, listing, retrieval, and deletion.
Includes input validation and security checks (Phase 8).
"""

import os
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.core.config import settings
from app.core.exceptions import (
    DuplicateDocumentException,
    EmptyDocumentException,
    FileSizeException,
    InvalidFileTypeException,
    InvalidPDFException,
    PDFPageCountException,
    ValidationException,
)
from app.core.logging import get_logger
from app.core.validators import validate_filename, validate_document_id
from app.schemas.document import (
    DocumentDeleteResponse,
    DocumentDetailResponse,
    DocumentListResponse,
    DocumentUploadResponse,
)
from app.services.ingestion_service import IngestionService
from app.services.retrieval_service import RetrievalService

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

# Lazy-loaded services (initialized on first use)
_ingestion_service = None
_retrieval_service = None


def get_ingestion_service():
    """Get or create ingestion service."""
    global _ingestion_service
    if _ingestion_service is None:
        _ingestion_service = IngestionService()
    return _ingestion_service


def get_retrieval_service():
    """Get or create retrieval service."""
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = RetrievalService()
    return _retrieval_service


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    summary="Upload PDF Document",
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a PDF document for processing.

    Validates the PDF, extracts text, creates chunks, and indexes embeddings.

    Args:
        file: PDF file to upload

    Returns:
        DocumentUploadResponse with document ID and status

    Raises:
        400: Invalid file (size, type, corruption, empty)
        413: File too large
        422: PDF page count exceeded
        500: Processing error
    """
    try:
        logger.info(f"Document upload started: {file.filename}")

        # Validate filename (Phase 8)
        if not file.filename:
            logger.warning("Upload attempted with empty filename")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required",
            )

        # Sanitize filename
        try:
            safe_filename = validate_filename(file.filename)
        except ValidationException as e:
            logger.warning(f"Filename validation failed: {e.message}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e.message),
            )

        # Save uploaded file temporarily
        temp_dir = settings.upload_directory
        temp_dir.mkdir(parents=True, exist_ok=True)

        temp_filename = f"temp_{uuid4()}_{file.filename}"
        temp_path = temp_dir / temp_filename

        try:
            # Write file
            content = await file.read()
            if not content:
                raise InvalidFileTypeException(file.filename or "unknown")

            temp_path.write_bytes(content)

            # Ingest document
            result = get_ingestion_service().ingest_pdf(temp_path)

            # Index in vector store
            try:
                indexed_count = get_retrieval_service().index_document(
                    result["chunks"],
                    result["document_metadata"].embedding_model or "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                )
                logger.info(
                    f"Document indexed: {result['document_id']}, "
                    f"{indexed_count} chunks"
                )
            except Exception as e:
                logger.error(f"Indexing failed: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to index document",
                )

            return DocumentUploadResponse(
                document_id=result["document_id"],
                filename=result["filename"],
                status="indexed",
                message=f"Document successfully uploaded and indexed "
                f"({result['page_count']} pages, {result['chunk_count']} chunks)",
            )

        except (
            FileSizeException,
            InvalidFileTypeException,
            InvalidPDFException,
            PDFPageCountException,
            EmptyDocumentException,
        ) as e:
            logger.warning(f"Validation error: {e.error_code}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e.message),
            )
        finally:
            # Clean up temp file
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception as e:
                    logger.warning(f"Failed to clean up temp file: {e}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during upload: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List Documents",
)
async def list_documents():
    """
    List all indexed documents.

    Returns statistics about indexed documents and vector store status.

    Returns:
        DocumentListResponse with list of documents and count
    """
    try:
        logger.debug("Listing documents")

        # Get collection stats
        stats = get_retrieval_service().get_collection_stats()

        # For now, return empty list when no chunks (Phase 7 will add database integration)
        documents = []
        chunk_count = stats.get("chunk_count", 0)

        return DocumentListResponse(
            documents=documents,
            count=chunk_count,
        )

    except Exception as e:
        logger.error(f"Error listing documents: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list documents",
        )


@router.get(
    "/{document_id}",
    response_model=DocumentDetailResponse,
    summary="Get Document Details",
)
async def get_document(document_id: str):
    """
    Get details about a specific document.

    Returns document metadata and sample chunks (Phase 7: database integration).

    Args:
        document_id: Document ID

    Returns:
        DocumentDetailResponse with metadata and sample chunks

    Raises:
        400: Invalid document ID format
        404: Document not found
    """
    try:
        # Validate document ID format (Phase 8)
        try:
            validate_document_id(document_id, max_length=settings.max_document_id_length)
        except ValidationException as e:
            logger.warning(f"Invalid document ID: {e.message}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e.message),
            )

        logger.debug(f"Getting document: {document_id}")

        # Phase 7 will add database lookup
        # For now, return placeholder
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document details not yet available (Phase 7)",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get document",
        )


@router.delete(
    "/{document_id}",
    response_model=DocumentDeleteResponse,
    summary="Delete Document",
)
async def delete_document(document_id: str):
    """
    Delete a document and all its chunks from the vector store.

    Args:
        document_id: Document ID to delete

    Returns:
        DocumentDeleteResponse with deletion confirmation

    Raises:
        400: Invalid document ID format
        404: Document not found
    """
    try:
        # Validate document ID format (Phase 8)
        try:
            validate_document_id(document_id, max_length=settings.max_document_id_length)
        except ValidationException as e:
            logger.warning(f"Invalid document ID: {e.message}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e.message),
            )

        logger.info(f"Deleting document: {document_id}")

        # Delete from vector store
        try:
            deleted_count = get_retrieval_service().delete_document_chunks(document_id)
            logger.info(f"Deleted {deleted_count} chunks for document {document_id}")
        except Exception as e:
            logger.error(f"Deletion failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete document",
            )

        return DocumentDeleteResponse(
            document_id=document_id,
            message=f"Document deleted ({deleted_count} chunks removed)",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during deletion: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document",
        )
