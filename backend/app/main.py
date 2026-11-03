import logging
import uvicorn
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

# from prometheus_client import generate_latest, REGISTRY

from app.api.routes import chat, documents, health
from app.core.config import settings
from app.core.exceptions import ApplicationException
from app.core.logging import configure_logging, get_logger
# from app.core.rate_limiter import init_rate_limiter
# from app.core.prompt_defense import init_prompt_defense
# from app.middleware.prometheus import PrometheusMiddleware
# from app.middleware.rate_limiting import RateLimitMiddleware
# from app.middleware.api_key_auth import APIKeyAuthMiddleware
# from app.middleware.security_headers import SecurityHeadersMiddleware

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown events.

    Startup:
    - Configure logging
    - Create necessary directories
    - Log startup information

    Shutdown:
    - Log shutdown information
    - Cleanup resources (will be expanded)
    """
    # ========================================================================
    # STARTUP
    # ========================================================================
    logger.info("=" * 80)
    logger.info("Chat With Documents – RAG System Starting Up")
    logger.info("=" * 80)

    # Configure logging
    configure_logging()

    # Create required directories
    try:
        settings.upload_directory.mkdir(parents=True, exist_ok=True)
        settings.chroma_directory.mkdir(parents=True, exist_ok=True)
        Path("logs").mkdir(exist_ok=True)
        Path("data").mkdir(exist_ok=True)
        logger.debug(f"Created directories: {settings.upload_directory}, {settings.chroma_directory}")
    except Exception as e:
        logger.error(f"Failed to create directories: {e}")
        raise

    # Initialize database
    try:
        from app.db.database import init_db
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    # # Initialize rate limiter (Phase 8)
    # try:
    #     init_rate_limiter(
    #         global_limit=settings.rate_limit_global,
    #         upload_limit=settings.rate_limit_upload,
    #         chat_limit=settings.rate_limit_chat,
    #     )
    #     logger.info("Rate limiter initialized")
    # except Exception as e:
    #     logger.error(f"Failed to initialize rate limiter: {e}")
    #     raise

    # # Initialize prompt defense (Phase 8)
    # try:
    #     init_prompt_defense(block_on_detection=False)
    #     logger.info("Prompt defense initialized")
    # except Exception as e:
    #     logger.error(f"Failed to initialize prompt defense: {e}")
    #     raise

    # Log configuration (without sensitive values)
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"API: {settings.api_host}:{settings.api_port}")
    logger.info(f"LLM Provider: {settings.llm_provider} ({settings.ollama_model})")
    logger.info(f"Embedding Model: {settings.embedding_model}")
    logger.info(f"Database: {settings.database_url}")
    logger.info(f"Debug Mode: {settings.debug}")
    logger.info("Startup complete.")

    yield

    # ========================================================================
    # SHUTDOWN
    # ========================================================================
    logger.info("=" * 80)
    logger.info("Chat With Documents – RAG System Shutting Down")
    logger.info("=" * 80)
    logger.info("Shutdown complete.")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured application instance
    """
    app = FastAPI(
        title="Chat With Documents – RAG System",
        description="AI-powered PDF question answering system using Retrieval-Augmented Generation",
        version="0.1.0",
        lifespan=lifespan,
    )

    # ========================================================================
    # CORS Middleware
    # ========================================================================
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ========================================================================
    # Security Middleware (Phase 8) - TEMPORARILY DISABLED
    # ========================================================================
    # Add middleware in reverse order (first middleware added is last to execute)
    
    # # 1. Prometheus metrics (added first to track all requests)
    # app.add_middleware(PrometheusMiddleware)
    # logger.debug("Added Prometheus metrics middleware")
    
    # # 2. Security headers (applied to all responses)
    # if settings.enable_security_headers:
    #     app.add_middleware(SecurityHeadersMiddleware)
    #     logger.debug("Added security headers middleware")
    
    # # 3. API key authentication (before rate limiting)
    # if settings.api_key_enabled:
    #     app.add_middleware(APIKeyAuthMiddleware)
    #     logger.debug("Added API key authentication middleware")
    
    # # 4. Rate limiting (applied to all routes)
    # if settings.rate_limit_enabled:
    #     app.add_middleware(RateLimitMiddleware)
    #     logger.debug("Added rate limiting middleware")

    # ========================================================================
    # Exception Handlers
    # ========================================================================

    @app.exception_handler(ApplicationException)
    async def application_exception_handler(
        request: Request, exc: ApplicationException
    ) -> JSONResponse:
        """Handle application exceptions."""
        logger.error(f"Application error: {exc.error_code} - {exc.message}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error_code": exc.error_code,
                "message": exc.message,
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle unexpected exceptions."""
        logger.error(f"Unexpected error: {type(exc).__name__} - {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
            },
        )

    # ========================================================================
    # Include Routers
    # ========================================================================
    app.include_router(health.router)
    app.include_router(documents.router)
    app.include_router(chat.router)
    
    # # Phase 7: Analytics endpoints
    # from app.api.routes import analytics
    # app.include_router(analytics.router)

    # ========================================================================
    # Root Endpoint
    # ========================================================================

    @app.get(
        "/",
        summary="API Root",
        description="Information about the API",
    )
    async def root():
        """Root endpoint with API information."""
        return {
            "name": "Chat With Documents – RAG System",
            "version": "0.1.0",
            "docs": "/docs",
            "api_version": "v1",
            "metrics": "/metrics",
        }

    # @app.get(
    #     "/metrics",
    #     tags=["monitoring"],
    #     summary="Prometheus Metrics",
    #     description="Prometheus metrics endpoint for monitoring",
    # )
    # async def metrics():
    #     """Export metrics in Prometheus format."""
    #     return Response(
    #         generate_latest(REGISTRY),
    #         media_type="text/plain; charset=utf-8",
    #     )

    return app


# Create the application instance
app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
    )
