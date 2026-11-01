"""
Chat endpoint for RAG question answering.

To be implemented in Phase 5.
"""

from fastapi import APIRouter

from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/api/v1", tags=["chat"])

# Placeholder - will be implemented in Phase 5


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Ask a question about indexed documents. (Phase 5)

    Returns an answer based on retrieved context with source references.
    """
    pass
