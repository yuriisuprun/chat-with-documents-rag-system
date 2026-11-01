"""
Utility functions for the Streamlit frontend.
"""

import re
from typing import Any

import streamlit as st


def format_file_size(size_bytes: int) -> str:
    """
    Format bytes to human-readable file size.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string
    """
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text to maximum length with ellipsis.

    Args:
        text: Text to truncate
        max_length: Maximum length

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def extract_text_preview(text: str, max_length: int = 200) -> str:
    """
    Extract a preview of text, removing excess whitespace.

    Args:
        text: Text to preview
        max_length: Maximum length

    Returns:
        Text preview
    """
    # Remove excess whitespace
    text = " ".join(text.split())
    return truncate_text(text, max_length)


def format_similarity_score(score: float) -> str:
    """
    Format similarity score as percentage.

    Args:
        score: Similarity score (0-1)

    Returns:
        Formatted percentage string
    """
    return f"{score:.1%}"


def safe_get(data: dict, key: str, default: Any = None) -> Any:
    """
    Safely get value from dictionary with default.

    Args:
        data: Dictionary
        key: Key to get
        default: Default value if key not found

    Returns:
        Value or default
    """
    return data.get(key, default)


def highlight_code(code: str, language: str = "python") -> str:
    """
    Highlight code for display.

    Args:
        code: Code string
        language: Programming language

    Returns:
        HTML highlighted code
    """
    return f"```{language}\n{code}\n```"


def create_badge(
    label: str,
    background_color: str = "#1f77b4",
    text_color: str = "white",
) -> str:
    """
    Create HTML badge.

    Args:
        label: Badge label
        background_color: Background color
        text_color: Text color

    Returns:
        HTML badge string
    """
    return (
        f'<span style="background-color: {background_color}; '
        f'color: {text_color}; padding: 0.25rem 0.75rem; '
        f'border-radius: 1rem; font-size: 0.85rem; font-weight: bold;">'
        f"{label}</span>"
    )


def validate_query(query: str) -> tuple[bool, str]:
    """
    Validate user query.

    Args:
        query: User query string

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not query or not query.strip():
        return False, "Query cannot be empty"

    if len(query) < 3:
        return False, "Query must be at least 3 characters"

    if len(query) > 2000:
        return False, "Query cannot exceed 2000 characters"

    return True, ""


@st.cache_data
def get_placeholder_queries() -> list[str]:
    """
    Get placeholder queries for user guidance.

    Returns:
        List of example queries
    """
    return [
        "What is machine learning?",
        "How does the system work?",
        "What are the main concepts?",
        "Summarize the key points",
        "What examples are provided?",
    ]


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
