"""
Chat endpoint for RAG question answering.

Handles question answering using the RAG pipeline with source references.
Includes input validation and prompt injection defense (Phase 8).
"""

from fastapi import APIRouter, HTTPException, status, Depends

from app.api.dependencies import get_rag_service
from app.core.config import settings
from app.core.exceptions import RAGException, ValidationException, LLMUnavailableException
from app.core.logging import get_logger
from app.core.prompt_defense import get_prompt_defense
from app.core.validators import (
    detect_prompt_injection,
    sanitize_text,
    validate_query_length,
)
from app.schemas.chat import ChatRequest, ChatResponse, SourceReference
from app.services.rag_service import RAGService

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["chat"])


@router.options("/chat", include_in_schema=False)
async def options_chat():
    """Handle CORS preflight for chat endpoint."""
    return None


@router.options("/chat/history", include_in_schema=False)
async def options_chat_history():
    """Handle CORS preflight for chat history endpoint."""
    return None


@router.get(
    "/chat/history",
    response_model=list,
    summary="Get Chat History",
    status_code=status.HTTP_200_OK,
)
async def get_chat_history() -> list:
    """
    Get chat history for the current session.

    Returns:
        List of chat messages (empty for now - Phase 7 will add persistence)
    """
    try:
        logger.debug("Getting chat history")
        # Phase 7 will add database integration to persist chat history
        return []
    except Exception as e:
        logger.error(f"Error getting chat history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get chat history",
        )


@router.delete(
    "/chat/history",
    summary="Clear Chat History",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def clear_chat_history():
    """
    Clear chat history for the current session.

    Returns:
        204 No Content
    """
    try:
        logger.debug("Clearing chat history")
        # Phase 7 will add database integration
        return None
    except Exception as e:
        logger.error(f"Error clearing chat history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear chat history",
        )


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Ask Question About Documents",
    status_code=status.HTTP_200_OK,
)
async def chat(
    request: ChatRequest,
    rag_service: RAGService = Depends(get_rag_service),
) -> ChatResponse:
    """
    Ask a question about indexed documents.

    Uses RAG pipeline to retrieve relevant context and generate an answer
    with source references.

    Args:
        request: ChatRequest with query and optional document_ids
        rag_service: RAG service (injected)

    Returns:
        ChatResponse with generated answer and source references

    Raises:
        400: Invalid query or no documents indexed
        500: RAG pipeline error
    """
    try:
        # ====================================================================
        # Input Validation (Phase 8)
        # ====================================================================
        
        # Sanitize query
        query = sanitize_text(request.query)
        logger.info(f"Chat request: '{query[:50]}...'")

        # Validate query length
        try:
            validate_query_length(query, max_length=settings.max_query_length)
        except ValidationException as e:
            logger.warning(f"Query validation failed: {e.message}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e.message),
            )

        # ====================================================================
        # Prompt Injection Defense (Phase 8)
        # ====================================================================
        
        prompt_defense = get_prompt_defense()
        detection_result = prompt_defense.detect(query)

        if detection_result.is_suspicious:
            logger.warning(
                f"Prompt injection detected: {detection_result}"
            )
            # Log but don't block (detection-only mode by default)
            # In production, could set block_on_detection=True to reject

        # ====================================================================
        # RAG Pipeline
        # ====================================================================
        
        try:
            result = rag_service.answer_question(
                question=query,
                document_ids=request.document_ids,
                top_k=8,  # Increased from 4 to get better results
            )
        except LLMUnavailableException as e:
            logger.warning(f"LLM unavailable: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"LLM service temporarily unavailable. To use this feature, ensure your LLM provider ({settings.llm_provider}) is properly configured and accessible.",
            )
        except RAGException as e:
            logger.error(f"RAG pipeline failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e.message),
            )

        # Build source references
        sources = []
        if request.include_sources:
            for source in result.get("sources", []):
                logger.debug(
                    f"Building source ref: filename={source.get('filename')}, "
                    f"page={source.get('page_number')}, "
                    f"similarity={source.get('similarity_score', 0.0)}"
                )
                source_ref = SourceReference(
                    document_id=source.get("document_id", "unknown"),
                    filename=source.get("filename", "Unknown"),
                    page_number=source.get("page_number", 0),
                    chunk_index=source.get("chunk_index", 0),
                    similarity_score=source.get("similarity_score", 0.0),
                    text_preview=source.get("text_preview", ""),
                )
                logger.debug(f"Created source_ref: similarity_score={source_ref.similarity_score}")
                sources.append(source_ref)

        return ChatResponse(
            query=request.query,
            answer=result.get("answer", ""),
            sources=sources,
            context_sufficient=result.get("context_sufficient", False),
            error=None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat request",
        )
