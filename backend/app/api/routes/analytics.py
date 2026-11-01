"""
Analytics endpoints for database statistics and insights.

Provides endpoints for accessing historical data and analytics.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.logging import get_logger
from app.db.database import get_db_session
from app.schemas.db_models import (
    DocumentStats,
    QueryStats,
    SessionStats,
    DatabaseStats,
)
from app.services.database_service import DatabaseService

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get(
    "/documents",
    response_model=DocumentStats,
    summary="Get Document Statistics",
)
async def get_document_stats(db_session = Depends(get_db_session)):
    """
    Get document collection statistics.

    Returns counts of total, indexed, and failed documents plus total chunks.

    Returns:
        DocumentStats with document metrics
    """
    try:
        db_service = DatabaseService(db_session)
        stats = db_service.get_document_stats()
        
        return DocumentStats(
            total_documents=stats.get("total_documents", 0),
            indexed_documents=stats.get("indexed_documents", 0),
            failed_documents=stats.get("failed_documents", 0),
            total_chunks=stats.get("total_chunks", 0),
        )
    except Exception as e:
        logger.error(f"Error getting document stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document statistics",
        )


@router.get(
    "/queries",
    response_model=QueryStats,
    summary="Get Query Statistics",
)
async def get_query_stats(db_session = Depends(get_db_session)):
    """
    Get query execution statistics.

    Returns metrics on query performance and context sufficiency.

    Returns:
        QueryStats with query metrics
    """
    try:
        db_service = DatabaseService(db_session)
        stats = db_service.get_query_stats()
        
        return QueryStats(
            total_queries=stats.get("total_queries", 0),
            avg_retrieval_time_ms=stats.get("avg_retrieval_time_ms", 0),
            avg_generation_time_ms=stats.get("avg_generation_time_ms", 0),
            avg_total_time_ms=stats.get("avg_total_time_ms", 0),
            context_sufficient_percentage=stats.get("context_sufficient_percentage", 0),
        )
    except Exception as e:
        logger.error(f"Error getting query stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve query statistics",
        )


@router.get(
    "/sessions",
    response_model=SessionStats,
    summary="Get Session Statistics",
)
async def get_session_stats(db_session = Depends(get_db_session)):
    """
    Get user session statistics.

    Returns metrics on user sessions and interaction patterns.

    Returns:
        SessionStats with session metrics
    """
    try:
        db_service = DatabaseService(db_session)
        stats = db_service.get_session_stats()
        
        return SessionStats(
            total_sessions=stats.get("total_sessions", 0),
            avg_queries_per_session=stats.get("avg_queries_per_session", 0),
        )
    except Exception as e:
        logger.error(f"Error getting session stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve session statistics",
        )


@router.get(
    "/overview",
    response_model=DatabaseStats,
    summary="Get Overall Database Statistics",
)
async def get_overall_stats(db_session = Depends(get_db_session)):
    """
    Get overall system statistics from database.

    Combines document, query, and session statistics for comprehensive view.

    Returns:
        DatabaseStats with all metrics
    """
    try:
        db_service = DatabaseService(db_session)
        stats = db_service.get_overall_stats()
        
        docs = stats["documents"]
        queries = stats["queries"]
        sessions = stats["sessions"]
        
        return DatabaseStats(
            total_documents=docs.get("total_documents", 0),
            indexed_documents=docs.get("indexed_documents", 0),
            failed_documents=docs.get("failed_documents", 0),
            total_chunks=docs.get("total_chunks", 0),
            total_queries=queries.get("total_queries", 0),
            avg_query_time_ms=queries.get("avg_total_time_ms", 0),
            total_sessions=sessions.get("total_sessions", 0),
        )
    except Exception as e:
        logger.error(f"Error getting overall stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve overall statistics",
        )
