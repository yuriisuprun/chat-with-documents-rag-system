"""
Document management endpoints.

Handles document upload, listing, retrieval, and deletion.
Includes input validation and security checks (Phase 8).
"""

import asyncio
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status, Depends

from app.api.dependencies import get_ingestion_service, get_retrieval_service
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


@router.options("", include_in_schema=False)
async def options_documents():
    """Handle CORS preflight for documents endpoint."""
    return None


@router.options("/{document_id}", include_in_schema=False)
async def options_document(document_id: str):
    """Handle CORS preflight for document detail endpoint."""
    return None


@router.options("/upload", include_in_schema=False)
async def options_document_upload():
    """Handle CORS preflight for document upload endpoint."""
    return None


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    summary="Upload PDF Document",
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
    ingestion_service: IngestionService = Depends(get_ingestion_service),
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
):
    """
    Upload a PDF document for processing.

    Validates the PDF, extracts text, creates chunks, and indexes embeddings.
    
    Note: This operation can take 30-120 seconds depending on document size.
    The frontend should set an appropriate timeout (suggested: 300s).

    Args:
        file: PDF file to upload
        ingestion_service: Document ingestion service (injected)
        retrieval_service: Retrieval service (injected)

    Returns:
        DocumentUploadResponse with document ID and status

    Raises:
        400: Invalid file (size, type, corruption, empty)
        413: File too large
        422: PDF page count exceeded
        500: Processing error
    """
    upload_timeout = 300  # 5 minutes for large document processing
    
    try:
        logger.info(f"Document upload started: {file.filename}")
        logger.debug(f"File content type: {file.content_type}")
        logger.debug(f"File size: {file.size} bytes")

        # Validate filename (Phase 8)
        if not file.filename:
            logger.warning("Upload attempted with empty filename")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required",
            )

        # Sanitize filename
        try:
            logger.debug(f"Validating filename: {file.filename}")
            safe_filename = validate_filename(file.filename)
            logger.debug(f"Safe filename: {safe_filename}")
        except ValidationException as e:
            logger.warning(f"Filename validation failed: {e.message}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e.message),
            )

        # Save uploaded file temporarily
        temp_dir = settings.upload_directory
        temp_dir.mkdir(parents=True, exist_ok=True)

        file_size = file.size or 0
        temp_filename = f"temp_{uuid4()}_{file.filename}"
        temp_path = temp_dir / temp_filename
        logger.debug(f"Temp file path: {temp_path}")

        try:
            # Write file
            logger.debug("Reading file content...")
            content = await file.read()
            logger.info(f"File read successfully. Content size: {len(content)} bytes")
            
            if not content:
                logger.error(f"File content is empty: {file.filename}")
                raise InvalidFileTypeException(file.filename or "unknown")

            logger.debug("Writing file to temp location...")
            temp_path.write_bytes(content)
            logger.info(f"File written to: {temp_path}")

            # Ingest document with timeout
            logger.debug("Starting PDF ingestion...")
            try:
                result = await asyncio.wait_for(
                    asyncio.to_thread(
                        ingestion_service.ingest_pdf,
                        temp_path,
                        safe_filename
                    ),
                    timeout=upload_timeout
                )
            except asyncio.TimeoutError:
                logger.error(f"PDF ingestion timed out after {upload_timeout}s")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Document processing took too long (>{upload_timeout}s). Try uploading a smaller file.",
                )
            
            logger.info(f"PDF ingestion complete. Document ID: {result['document_id']}")
            logger.debug(f"Ingestion result keys: {result.keys()}")

            # Index in vector store with timeout
            try:
                logger.debug(f"Indexing {len(result['chunks'])} chunks...")
                indexed_count = await asyncio.wait_for(
                    asyncio.to_thread(
                        retrieval_service.index_document,
                        result["chunks"],
                        settings.embedding_model,
                    ),
                    timeout=180  # 3 minutes for indexing (includes model load on first request)
                )
                logger.info(
                    f"Document indexed: {result['document_id']}, "
                    f"{indexed_count} chunks"
                )
            except asyncio.TimeoutError:
                logger.error("Vector indexing timed out after 60s")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Document indexing timed out. The document may still be partially indexed.",
                )
            except Exception as e:
                logger.error(f"Indexing failed: {e}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to index document",
                )

            # Save document metadata to database
            try:
                from app.db.database import db
                from app.db.repositories import DocumentRepository
                
                with db.session_context() as session:
                    repo = DocumentRepository(session)
                    doc_metadata = result.get("document_metadata")
                    repo.create(
                        document_id=result["document_id"],
                        filename=result["filename"],
                        file_path=str(temp_path),
                        file_size=len(content),  # Actual file size
                        sha256_hash=doc_metadata.sha256 if doc_metadata else "",
                        page_count=result["page_count"],
                        chunk_count=result["chunk_count"],
                        embedding_model=settings.embedding_model,
                    )
                    repo.update_status(result["document_id"], "indexed")
                    logger.info(f"Saved document metadata to database: {result['document_id']}")
            except Exception as e:
                logger.warning(f"Failed to save document metadata to database: {e}")
                # Don't fail the upload, just log the warning

            response = DocumentUploadResponse(
                document_id=result["document_id"],
                filename=result["filename"],
                status="indexed",
                message=f"Document successfully uploaded and indexed "
                f"({result['page_count']} pages, {result['chunk_count']} chunks)",
            )
            logger.info(f"Returning successful response: {response}")
            return response

        except (
            FileSizeException,
            InvalidFileTypeException,
            InvalidPDFException,
            PDFPageCountException,
            EmptyDocumentException,
        ) as e:
            logger.warning(f"Validation error: {e.error_code} - {e.message}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e.message),
            )
        finally:
            # Clean up temp file
            if temp_path.exists():
                try:
                    temp_path.unlink()
                    logger.debug(f"Cleaned up temp file: {temp_path}")
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
    summary="List Documents",
)
async def list_documents(
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
):
    """
    List all indexed documents.

    First tries to query the database for documents with actual metadata.
    Falls back to ChromaDB if no database records exist.

    Args:
        retrieval_service: Retrieval service (injected)

    Returns:
        List of documents with metadata
    """
    try:
        from app.db.database import db
        from app.db.repositories import DocumentRepository
        
        logger.debug("Fetching documents from database...")
        
        # Query database for all indexed documents
        with db.session_context() as session:
            repo = DocumentRepository(session)
            documents = repo.get_by_status("indexed")
        
        logger.debug(f"Found {len(documents)} indexed documents in database")
        
        if len(documents) > 0:
            # Format response from database (has real metadata)
            result = []
            for doc in documents:
                result.append({
                    "id": doc.id,
                    "name": doc.filename,
                    "uploaded_at": doc.created_at.isoformat() if doc.created_at else "Unknown",
                    "file_size": doc.file_size,
                    "pages": doc.page_count,
                    "chunk_count": doc.chunk_count,
                })
            
            logger.info(f"Returning {len(result)} documents from database")
            return result
        else:
            # No documents in database, try ChromaDB
            logger.debug("No documents in database, falling back to ChromaDB...")
            raise Exception("No documents in database")

    except Exception as e:
        logger.debug(f"Database query failed: {e}, trying ChromaDB fallback...")
        # Fallback to ChromaDB if database fails or is empty
        try:
            logger.debug("Querying ChromaDB for documents...")
            results = retrieval_service.vector_store.collection.get()
            
            documents_dict = {}
            metadatas = results.get('metadatas', []) or []
            logger.debug(f"Got {len(metadatas)} chunks from ChromaDB")
            
            for metadata in metadatas:
                if not metadata:
                    continue
                doc_id = metadata.get('document_id')
                filename = metadata.get('filename')
                
                if doc_id and filename:
                    clean_filename = filename
                    if filename.startswith('temp_'):
                        parts = filename.split('_', 2)
                        if len(parts) > 2:
                            clean_filename = parts[2]
                    
                    if doc_id not in documents_dict:
                        documents_dict[doc_id] = {
                            'id': doc_id,
                            'name': clean_filename,
                            'uploaded_at': 'Unknown',
                            'file_size': 0,  # ChromaDB doesn't store file size
                            'pages': None,
                            'chunk_count': 0,
                        }
                    documents_dict[doc_id]['chunk_count'] += 1
            
            result = list(documents_dict.values())
            logger.info(f"Returning {len(result)} documents from ChromaDB fallback")
            return result
        except Exception as fallback_error:
            logger.error(f"Both database and ChromaDB failed: {fallback_error}", exc_info=True)
            return []


@router.get(
    "/{document_id}",
    response_model=DocumentDetailResponse,
    summary="Get Document Details",
)
async def get_document(
    document_id: str,
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
):
    """
    Get details about a specific document.

    Returns document metadata and sample chunks (Phase 7: database integration).

    Args:
        document_id: Document ID
        retrieval_service: Retrieval service (injected)

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
async def delete_document(
    document_id: str,
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
):
    """
    Delete a document and all its chunks from the vector store.

    Args:
        document_id: Document ID to delete
        retrieval_service: Retrieval service (injected)

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
        deleted_count = 0
        try:
            deleted_count = retrieval_service.delete_document_chunks(document_id)
            logger.info(f"Deleted {deleted_count} chunks from vector store for document {document_id}")
        except Exception as e:
            logger.error(f"Vector store deletion failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete document from vector store",
            )

        # Delete from database
        try:
            from app.db.database import db
            from app.db.repositories import DocumentRepository
            
            with db.session_context() as session:
                repo = DocumentRepository(session)
                repo.delete(document_id)
                logger.info(f"Deleted document {document_id} from database")
        except Exception as e:
            logger.warning(f"Failed to delete document from database: {e}")
            # Don't fail the request, as vector store deletion was successful

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
