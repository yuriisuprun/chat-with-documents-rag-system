"""
Structured logging configuration.

Provides production-grade logging with JSON output and sensitive data filtering.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

from .config import settings


class SensitiveDataFilter(logging.Filter):
    """Filter to prevent logging of sensitive information."""

    SENSITIVE_KEYS = {
        "password",
        "token",
        "api_key",
        "secret",
        "authorization",
        "api-key",
    }

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter record to remove sensitive data."""
        # Don't log sensitive messages
        if hasattr(record, "msg") and isinstance(record.msg, str):
            msg_lower = record.msg.lower()
            for key in self.SENSITIVE_KEYS:
                if key in msg_lower:
                    record.msg = "[REDACTED: SENSITIVE DATA]"
                    return True
        return True


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "extra"):
            log_data.update(record.extra)

        return json.dumps(log_data)


def configure_logging() -> None:
    """Configure logging for the application."""
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level)

    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create formatters
    if settings.log_json:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            fmt=(
                "%(asctime)s - %(name)s - %(levelname)s - "
                "%(funcName)s:%(lineno)d - %(message)s"
            ),
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    # Add sensitive data filter
    sensitive_filter = SensitiveDataFilter()

    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(settings.log_level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(sensitive_filter)
    root_logger.addHandler(console_handler)

    # File handler (for all logs)
    file_handler = logging.FileHandler(log_dir / "app.log")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(sensitive_filter)
    root_logger.addHandler(file_handler)

    # File handler for errors only
    error_handler = logging.FileHandler(log_dir / "error.log")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    error_handler.addFilter(sensitive_filter)
    root_logger.addHandler(error_handler)

    # Suppress noisy third-party loggers
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("langchain").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a given name."""
    return logging.getLogger(name)
