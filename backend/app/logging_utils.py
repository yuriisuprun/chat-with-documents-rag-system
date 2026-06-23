"""Logging utilities and decorators for structured logging."""

import functools
import time
from typing import Any, Callable, Dict, Optional

import structlog


logger = structlog.get_logger(__name__)


def log_operation(operation_name: str, include_args: bool = False):
    """
    Decorator to log operation execution with timing and error handling.
    
    Args:
        operation_name: Name of the operation for logging
        include_args: Whether to log function arguments (set False for sensitive operations)
        
    Example:
        @log_operation("user_authentication", include_args=False)
        def authenticate_user(username: str, password: str) -> bool:
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            log_context = {
                "operation": operation_name,
                "function": func.__name__,
            }
            
            if include_args:
                log_context["args_count"] = len(args)
                log_context["kwargs_keys"] = list(kwargs.keys())
            
            logger.info(f"{operation_name}_started", **log_context)
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(
                    f"{operation_name}_completed",
                    duration_ms=round(duration * 1000, 2),
                    **log_context
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"{operation_name}_error",
                    error=str(e),
                    duration_ms=round(duration * 1000, 2),
                    exc_info=True,
                    **log_context
                )
                raise
        
        return wrapper
    return decorator


def log_database_operation(operation_type: str, entity: str):
    """
    Decorator to log database operations (create, read, update, delete).
    
    Args:
        operation_type: Type of operation (create, read, update, delete)
        entity: Entity name (e.g., "conversation", "message")
        
    Example:
        @log_database_operation("create", "conversation")
        def create_conversation(phone_number: str) -> Conversation:
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            log_context = {
                "db_operation": operation_type,
                "entity": entity,
            }
            
            logger.info(
                f"db_{operation_type}_{entity}_started",
                **log_context
            )
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(
                    f"db_{operation_type}_{entity}_completed",
                    duration_ms=round(duration * 1000, 2),
                    **log_context
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"db_{operation_type}_{entity}_error",
                    error=str(e),
                    duration_ms=round(duration * 1000, 2),
                    exc_info=True,
                    **log_context
                )
                raise
        
        return wrapper
    return decorator


def log_external_api_call(api_name: str, endpoint: Optional[str] = None):
    """
    Decorator to log external API calls with timing and error tracking.
    
    Args:
        api_name: Name of the external API (e.g., "openai", "whatsapp", "google_calendar")
        endpoint: Optional endpoint being called
        
    Example:
        @log_external_api_call("openai", "/chat/completions")
        def generate_response(prompt: str) -> str:
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            log_context = {
                "api": api_name,
                "endpoint": endpoint,
            }
            
            logger.info(
                f"{api_name}_api_call_started",
                **log_context
            )
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(
                    f"{api_name}_api_call_completed",
                    duration_ms=round(duration * 1000, 2),
                    **log_context
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"{api_name}_api_call_error",
                    error=str(e),
                    duration_ms=round(duration * 1000, 2),
                    exc_info=True,
                    **log_context
                )
                raise
        
        return wrapper
    return decorator


def log_task_execution(task_name: str):
    """
    Decorator to log Celery task execution.
    
    Args:
        task_name: Name of the Celery task
        
    Example:
        @log_task_execution("send_email")
        def send_email_task(email: str, subject: str) -> dict:
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            log_context = {
                "task": task_name,
            }
            
            logger.info(
                f"task_{task_name}_started",
                **log_context
            )
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(
                    f"task_{task_name}_completed",
                    duration_ms=round(duration * 1000, 2),
                    result_status=result.get("status") if isinstance(result, dict) else None,
                    **log_context
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"task_{task_name}_error",
                    error=str(e),
                    duration_ms=round(duration * 1000, 2),
                    exc_info=True,
                    **log_context
                )
                raise
        
        return wrapper
    return decorator


def add_request_context(request_id: str, user_id: Optional[str] = None, 
                       tenant_id: Optional[str] = None) -> Dict[str, str]:
    """
    Create a context dictionary for request tracing.
    
    Args:
        request_id: Unique request identifier
        user_id: Optional user ID
        tenant_id: Optional tenant ID
        
    Returns:
        Dictionary with context for logging
    """
    context = {"request_id": request_id}
    if user_id:
        context["user_id"] = user_id
    if tenant_id:
        context["tenant_id"] = tenant_id
    return context


class OperationContext:
    """Context manager for logging complex operations."""
    
    def __init__(self, operation_name: str, **kwargs):
        """
        Initialize operation context.
        
        Args:
            operation_name: Name of the operation
            **kwargs: Additional context fields
        """
        self.operation_name = operation_name
        self.context = kwargs
        self.start_time = None
    
    def __enter__(self):
        """Start operation logging."""
        self.start_time = time.time()
        logger.info(
            f"{self.operation_name}_started",
            **self.context
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End operation logging."""
        duration = time.time() - self.start_time
        
        if exc_type is None:
            logger.info(
                f"{self.operation_name}_completed",
                duration_ms=round(duration * 1000, 2),
                **self.context
            )
        else:
            logger.error(
                f"{self.operation_name}_error",
                error=str(exc_val),
                duration_ms=round(duration * 1000, 2),
                exc_info=(exc_type, exc_val, exc_tb),
                **self.context
            )
        
        return False
    
    def log_step(self, step_name: str, **kwargs):
        """Log a step within the operation."""
        context = {**self.context, **kwargs}
        logger.info(
            f"{self.operation_name}_{step_name}",
            **context
        )
    
    def log_checkpoint(self, checkpoint_name: str, **kwargs):
        """Log a checkpoint within the operation."""
        elapsed = time.time() - self.start_time
        context = {
            **self.context,
            "elapsed_ms": round(elapsed * 1000, 2),
            **kwargs
        }
        logger.debug(
            f"{self.operation_name}_{checkpoint_name}",
            **context
        )
