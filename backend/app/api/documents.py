"""Knowledge document management endpoints."""

import uuid
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import KnowledgeDocument
from app.schemas import DocumentResponse, DocumentUploadRequest
from app.services.rag_service import RAGService
from app.tasks import generate_embeddings_for_document
import os
import shutil

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])

UPLOAD_DIR = "uploads"
ALLOWED_TYPES = {"pdf", "docx", "txt"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def ensure_upload_dir():
    """Ensure upload directory exists."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    section_title: Optional[str] = Form(None),
    db: Session = Depends(get_db)
) -> DocumentResponse:
    """Upload knowledge document."""
    
    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided"
        )
    
    # Get file extension
    file_ext = file.filename.rsplit(".", 1)[-1].lower()
    if file_ext not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {ALLOWED_TYPES}"
        )
    
    try:
        # Read file
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size exceeds limit"
            )
        
        # Save file
        doc_id = f"doc_{uuid.uuid4().hex[:12]}"
        file_path = os.path.join(UPLOAD_DIR, f"{doc_id}_{file.filename}")
        
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Extract text
        rag_service = RAGService()
        content = rag_service.extract_text(file_path, file_ext)
        
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not extract text from file"
            )
        
        # Create document record
        document = KnowledgeDocument(
            id=doc_id,
            tenant_id=tenant_id,
            filename=file.filename,
            content=content,
            file_type=file_ext,
            file_size_bytes=len(contents),
            section_title=section_title,
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        logger.info(f"Created document {doc_id} for tenant {tenant_id}")
        
        # Schedule embedding generation
        generate_embeddings_for_document.delay(doc_id)
        
        return DocumentResponse.from_orm(document)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error uploading document"
        )


@router.get("", response_model=list[DocumentResponse])
def list_documents(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
) -> list[DocumentResponse]:
    """List all documents."""
    documents = db.query(KnowledgeDocument).order_by(
        KnowledgeDocument.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return [DocumentResponse.from_orm(d) for d in documents]


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: str,
    db: Session = Depends(get_db)
) -> DocumentResponse:
    """Get document details."""
    document = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.id == document_id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return DocumentResponse.from_orm(document)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: str,
    db: Session = Depends(get_db)
) -> None:
    """Delete document."""
    document = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.id == document_id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Delete file
    for file in os.listdir(UPLOAD_DIR):
        if file.startswith(document_id):
            try:
                os.remove(os.path.join(UPLOAD_DIR, file))
            except Exception as e:
                logger.error(f"Error deleting file: {str(e)}")
    
    # Delete from database
    db.delete(document)
    db.commit()
    
    logger.info(f"Deleted document {document_id}")


@router.patch("/{document_id}", response_model=DocumentResponse)
def update_document_status(
    document_id: str,
    is_active: bool,
    db: Session = Depends(get_db)
) -> DocumentResponse:
    """Enable/disable document."""
    document = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.id == document_id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    document.is_active = is_active
    db.commit()
    db.refresh(document)
    
    return DocumentResponse.from_orm(document)
