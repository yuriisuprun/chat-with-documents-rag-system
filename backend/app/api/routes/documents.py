"""
Document management endpoints.

Handles document upload, listing, retrieval, and deletion.
To be implemented in Phase 5.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

# Placeholder - will be implemented in Phase 5


@router.post("/upload")
async def upload_document():
    """Upload a PDF document. (Phase 5)"""
    pass


@router.get("")
async def list_documents():
    """List all indexed documents. (Phase 5)"""
    pass


@router.get("/{document_id}")
async def get_document(document_id: str):
    """Get details about a specific document. (Phase 5)"""
    pass


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and its embeddings. (Phase 5)"""
    pass
