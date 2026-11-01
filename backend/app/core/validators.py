"""
Input validation utilities for request data.

Provides validators for common input types to prevent injection attacks,
malformed data, and resource exhaustion.
"""

import re
import string
from typing import Optional

from app.core.exceptions import ValidationException
from app.core.logging import get_logger

logger = get_logger(__name__)

# Safe filename characters (alphanumeric + common safe chars)
SAFE_FILENAME_CHARS = set(string.ascii_letters + string.digits + "._- ")

# UUID v4 pattern
UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$', re.IGNORECASE)

# Document ID pattern (UUID or fallback to alphanumeric)
DOCUMENT_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{1,36}$')

# SQL injection patterns (basic detection)
SQL_INJECTION_PATTERNS = [
    r"(\b(UNION|SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|SCRIPT)\b)",
    r"(--|;|\||\"|\*)",
]

# Jailbreak/prompt injection patterns
PROMPT_INJECTION_PATTERNS = [
    r"ignore.*instructions?",
    r"forget.*previous",
    r"pretend.*you.*are",
    r"role.*play",
    r"act.*as.*if",
    r"system.*prompt",
    r"hidden.*instruction",
]


def validate_query_length(query: str, max_length: int = 500) -> None:
    """
    Validate query doesn't exceed maximum length.

    Args:
        query: Query text to validate
        max_length: Maximum allowed length (default: 500)

    Raises:
        ValidationException: If query exceeds maximum length
    """
    if not query:
        raise ValidationException("Query cannot be empty")

    if len(query) > max_length:
        raise ValidationException(
            f"Query exceeds maximum length of {max_length} characters "
            f"(provided: {len(query)})"
        )


def validate_document_id(document_id: str, max_length: int = 36) -> None:
    """
    Validate document ID format.

    Args:
        document_id: Document ID to validate
        max_length: Maximum allowed length (default: 36 for UUID)

    Raises:
        ValidationException: If document_id is invalid
    """
    if not document_id:
        raise ValidationException("Document ID cannot be empty")

    if len(document_id) > max_length:
        raise ValidationException(
            f"Document ID exceeds maximum length of {max_length} characters"
        )

    if not DOCUMENT_ID_PATTERN.match(document_id):
        raise ValidationException(
            "Document ID contains invalid characters (alphanumeric, dash, underscore only)"
        )


def validate_filename(filename: str, max_length: int = 255) -> str:
    """
    Validate and sanitize filename.

    - Rejects files with path traversal attempts
    - Ensures safe characters only
    - Trims to maximum length

    Args:
        filename: Filename to validate
        max_length: Maximum allowed length (default: 255)

    Returns:
        Sanitized filename

    Raises:
        ValidationException: If filename is invalid
    """
    if not filename:
        raise ValidationException("Filename cannot be empty")

    # Reject path traversal attempts
    if ".." in filename or "/" in filename or "\\" in filename:
        raise ValidationException("Filename contains invalid path characters")

    # Only allow safe characters
    unsafe_chars = [c for c in filename if c not in SAFE_FILENAME_CHARS]
    if unsafe_chars:
        logger.warning(f"Filename contains unsafe characters: {unsafe_chars}")
        # Replace unsafe chars with underscore instead of rejecting
        filename = "".join(c if c in SAFE_FILENAME_CHARS else "_" for c in filename)

    # Trim to maximum length
    if len(filename) > max_length:
        logger.warning(f"Filename truncated from {len(filename)} to {max_length} chars")
        filename = filename[:max_length]

    return filename


def sanitize_text(text: str, strip_whitespace: bool = True) -> str:
    """
    Sanitize user-provided text.

    - Optionally strips leading/trailing whitespace
    - Removes null bytes
    - Normalizes newlines

    Args:
        text: Text to sanitize
        strip_whitespace: Whether to strip whitespace (default: True)

    Returns:
        Sanitized text
    """
    if not text:
        return ""

    # Remove null bytes
    text = text.replace("\x00", "")

    # Normalize newlines (CRLF -> LF)
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Strip whitespace if requested
    if strip_whitespace:
        text = text.strip()

    return text


def detect_sql_injection(text: str, raise_error: bool = False) -> bool:
    """
    Detect potential SQL injection patterns.

    Uses simple regex patterns for detection. Does NOT prevent SQL injection
    (that's handled by parameterized queries in ORM), but flags suspicious input.

    Args:
        text: Text to check for SQL injection patterns
        raise_error: If True, raise ValidationException on detection

    Returns:
        True if suspicious patterns detected, False otherwise

    Raises:
        ValidationException: If raise_error=True and injection detected
    """
    if not text:
        return False

    # Check each pattern
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            msg = f"Potential SQL injection detected: {pattern}"
            logger.warning(msg)

            if raise_error:
                raise ValidationException(msg)

            return True

    return False


def detect_prompt_injection(text: str, raise_error: bool = False) -> bool:
    """
    Detect potential prompt injection attempts.

    Flags suspicious queries that attempt to override instructions or escape
    the RAG context. Does NOT block execution, only detects for logging.

    Args:
        text: Text to check for prompt injection patterns
        raise_error: If True, raise ValidationException on detection (rarely used)

    Returns:
        True if suspicious patterns detected, False otherwise

    Raises:
        ValidationException: If raise_error=True and injection detected
    """
    if not text:
        return False

    # Check each pattern
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            msg = f"Potential prompt injection detected: {pattern}"
            logger.warning(msg)

            if raise_error:
                raise ValidationException(msg)

            return True

    return False


def validate_json_safe(data: str, max_length: int = 10000) -> None:
    """
    Validate JSON string for safety.

    Checks for:
    - Reasonable length
    - No embedded scripts

    Args:
        data: JSON string to validate
        max_length: Maximum allowed length (default: 10000)

    Raises:
        ValidationException: If JSON is invalid or too large
    """
    if not data:
        raise ValidationException("JSON data cannot be empty")

    if len(data) > max_length:
        raise ValidationException(
            f"JSON data exceeds maximum size of {max_length} bytes"
        )

    # Basic check for script tags
    if "<script" in data.lower():
        raise ValidationException("JSON contains script tags (XSS attempt)")


def validate_email(email: str) -> bool:
    """
    Basic email validation.

    Args:
        email: Email to validate

    Returns:
        True if email format is valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_url(url: str) -> bool:
    """
    Basic URL validation.

    Args:
        url: URL to validate

    Returns:
        True if URL format is valid, False otherwise
    """
    pattern = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$'
    return bool(re.match(pattern, url))
