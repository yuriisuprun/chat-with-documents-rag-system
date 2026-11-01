"""
PDF file validation and security checks.

Implements comprehensive validation to prevent malicious or corrupted PDFs.
"""

import hashlib
from pathlib import Path

from app.core.config import settings
from app.core.exceptions import (
    FileSizeException,
    InvalidFileTypeException,
    InvalidPDFException,
)


def validate_pdf_signature(file_path: Path) -> bool:
    """
    Validate PDF file signature (magic bytes).

    PDFs must start with '%PDF-' magic bytes.

    Args:
        file_path: Path to file to validate

    Returns:
        True if valid PDF signature

    Raises:
        InvalidFileTypeException: If file doesn't start with PDF magic bytes
    """
    try:
        with open(file_path, "rb") as f:
            header = f.read(5)
            if header != b"%PDF-":
                raise InvalidFileTypeException(file_path.name)
        return True
    except (IOError, OSError) as e:
        raise InvalidFileTypeException(f"{file_path.name}: {str(e)}")


def validate_file_size(file_path: Path) -> bool:
    """
    Validate file size is within limits.

    Args:
        file_path: Path to file

    Returns:
        True if file size is acceptable

    Raises:
        FileSizeException: If file exceeds max upload size
    """
    file_size = file_path.stat().st_size
    if file_size > settings.max_upload_size:
        raise FileSizeException(file_size, settings.max_upload_size)
    return True


def calculate_file_hash(file_path: Path) -> str:
    """
    Calculate SHA-256 hash of file content.

    Used for duplicate detection and integrity verification.

    Args:
        file_path: Path to file

    Returns:
        Hex-encoded SHA-256 hash
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def validate_pdf_file(file_path: Path) -> dict:
    """
    Perform comprehensive validation of uploaded PDF.

    Args:
        file_path: Path to uploaded PDF file

    Returns:
        Dictionary with validation results containing:
        - is_valid: bool
        - file_size: int
        - file_hash: str
        - filename: str

    Raises:
        InvalidFileTypeException: If not a valid PDF
        FileSizeException: If file too large
    """
    # Validate file exists
    if not file_path.exists():
        raise InvalidFileTypeException(f"File not found: {file_path.name}")

    # Validate file is readable
    if not file_path.is_file():
        raise InvalidFileTypeException(f"Path is not a file: {file_path.name}")

    # Validate file size
    validate_file_size(file_path)

    # Validate PDF signature
    validate_pdf_signature(file_path)

    # Calculate file hash
    file_hash = calculate_file_hash(file_path)

    return {
        "is_valid": True,
        "file_size": file_path.stat().st_size,
        "file_hash": file_hash,
        "filename": file_path.name,
    }
