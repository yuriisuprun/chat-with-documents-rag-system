"""
Prompt injection defense utilities.

Detects and defends against prompt injection attempts through queries.
Provides detection and logging, not blocking (to avoid false positives).
"""

import re
from enum import Enum
from typing import Dict, List, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


class PromptInjectionLevel(str, Enum):
    """Severity levels for prompt injection detection."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class InjectionPattern:
    """Represents a prompt injection pattern."""

    def __init__(
        self,
        name: str,
        pattern: str,
        level: PromptInjectionLevel,
        description: str
    ):
        """
        Initialize injection pattern.

        Args:
            name: Pattern identifier
            pattern: Regex pattern to match
            level: Severity level
            description: Human-readable description
        """
        self.name = name
        self.pattern = re.compile(pattern, re.IGNORECASE)
        self.level = level
        self.description = description

    def match(self, text: str) -> bool:
        """Check if pattern matches text."""
        return bool(self.pattern.search(text))


# Define common injection patterns
INJECTION_PATTERNS = [
    # Instruction override attempts
    InjectionPattern(
        "ignore_instructions",
        r"ignore.*(?:previous\s+)?instructions?|forget.*(?:previous\s+)?instructions?",
        PromptInjectionLevel.CRITICAL,
        "Attempts to override system instructions"
    ),
    InjectionPattern(
        "system_prompt_leak",
        r"(?:what|show|reveal|print|output|display).{0,20}(?:system\s+)?prompt|reveal.*system|system.*prompt",
        PromptInjectionLevel.HIGH,
        "Attempts to extract system prompt"
    ),
    InjectionPattern(
        "role_play",
        r"(?:pretend|act|roleplay|play\s+the\s+role).{0,20}(?:as|like)|you\s+are\s+(?:now|no\s+longer).*assistant",
        PromptInjectionLevel.MEDIUM,
        "Attempts to change AI role/behavior"
    ),
    InjectionPattern(
        "context_escape",
        r"(?:this\s+)?(?:instruction|context)\s+no\s+longer\s+applies|rule\s+(?:has\s+)?changed|from\s+now\s+on|ignore.*context",
        PromptInjectionLevel.HIGH,
        "Attempts to escape the RAG context"
    ),
    InjectionPattern(
        "jailbreak",
        r"(?:jailbreak|bypass|crack|exploit|vulnerability|weakness|loophole).*(?:system|safety|filter|protection)",
        PromptInjectionLevel.CRITICAL,
        "Explicit jailbreak attempt"
    ),
    InjectionPattern(
        "prompt_injection",
        r"prompt\s+(?:injection|attack|exploit|jailbreak)",
        PromptInjectionLevel.HIGH,
        "Direct mention of prompt injection"
    ),
    InjectionPattern(
        "hidden_instruction",
        r"hidden\s+instruction|secret\s+command|easter\s+egg",
        PromptInjectionLevel.MEDIUM,
        "Attempts to access hidden functionality"
    ),
    InjectionPattern(
        "reverse_psychology",
        r"you\s+(?:must|have\s+to|should|must\s+not|cannot)\s+(?:refuse|deny|decline|reject)",
        PromptInjectionLevel.LOW,
        "Attempts to use reverse psychology"
    ),
    InjectionPattern(
        "token_smuggling",
        r"\\u[0-9a-f]{4}|encoded:|base64:|hex:|ROT13:",
        PromptInjectionLevel.MEDIUM,
        "Attempts to smuggle encoded instructions"
    ),
    InjectionPattern(
        "multilingual_bypass",
        r"(?:say\s+this\s+in|translate\s+this|speak\s+in|use\s+the\s+language\s+of).*(?:instruction|command|order)",
        PromptInjectionLevel.LOW,
        "Attempts to bypass through language switching"
    ),
]


class DetectionResult:
    """Result of prompt injection detection."""

    def __init__(
        self,
        is_suspicious: bool,
        level: Optional[PromptInjectionLevel] = None,
        patterns_matched: Optional[List[str]] = None,
        severity_score: float = 0.0
    ):
        """
        Initialize detection result.

        Args:
            is_suspicious: True if suspicious patterns detected
            level: Highest severity level detected
            patterns_matched: List of pattern names that matched
            severity_score: Score 0-1 indicating severity
        """
        self.is_suspicious = is_suspicious
        self.level = level
        self.patterns_matched = patterns_matched or []
        self.severity_score = severity_score

    def __str__(self) -> str:
        """String representation."""
        if not self.is_suspicious:
            return "Clean - no suspicious patterns detected"

        return (
            f"Suspicious - Level: {self.level}, "
            f"Score: {self.severity_score:.2f}, "
            f"Patterns: {', '.join(self.patterns_matched)}"
        )


class PromptDefense:
    """Prompt injection defense service."""

    def __init__(self, block_on_detection: bool = False):
        """
        Initialize prompt defense.

        Args:
            block_on_detection: If True, block requests with suspicious patterns
                              If False, log and allow (default)
        """
        self.block_on_detection = block_on_detection
        self.patterns = INJECTION_PATTERNS

    def detect(self, text: str) -> DetectionResult:
        """
        Detect prompt injection attempts in text.

        Args:
            text: Text to analyze

        Returns:
            DetectionResult with findings
        """
        if not text:
            return DetectionResult(is_suspicious=False)

        matched_patterns = []
        max_level = None
        level_values = {"low": 1, "medium": 2, "high": 3, "critical": 4}

        # Check each pattern
        for pattern in self.patterns:
            if pattern.match(text):
                matched_patterns.append(pattern.name)

                # Track highest severity
                if max_level is None:
                    max_level = pattern.level
                elif level_values[pattern.level.value] > level_values[max_level.value]:
                    max_level = pattern.level

        # Calculate severity score
        if matched_patterns:
            # Score is number of matches normalized to 0-1
            severity_score = min(1.0, len(matched_patterns) / len(self.patterns))

            logger.warning(
                f"Prompt injection detected: patterns={matched_patterns}, "
                f"level={max_level}, score={severity_score:.2f}"
            )

            return DetectionResult(
                is_suspicious=True,
                level=max_level,
                patterns_matched=matched_patterns,
                severity_score=severity_score
            )

        return DetectionResult(is_suspicious=False)

    def sanitize_query(self, query: str) -> str:
        """
        Sanitize query to remove potential injection markers.

        Removes encoded instructions and suspicious markers while
        preserving legitimate query content.

        Args:
            query: Query text to sanitize

        Returns:
            Sanitized query
        """
        # Remove encoded sequences
        sanitized = re.sub(r'\\u[0-9a-f]{4}', '', query, flags=re.IGNORECASE)
        sanitized = re.sub(r'encoded:|base64:|hex:|ROT13:', '', sanitized, flags=re.IGNORECASE)

        # Remove multiple spaces
        sanitized = ' '.join(sanitized.split())

        return sanitized

    def create_safe_context(
        self,
        query: str,
        retrieved_chunks: List[str],
        system_prompt: str
    ) -> str:
        """
        Create a safe context assembly resistant to injection.

        Ensures clear separation between query, context, and system prompt
        to prevent injection attacks from bleeding into instructions.

        Args:
            query: User query
            retrieved_chunks: Retrieved document chunks
            system_prompt: System instructions

        Returns:
            Safe context with proper boundaries
        """
        # Use clear delimiters and structure to prevent bleeding
        context_parts = [
            "=== SYSTEM INSTRUCTIONS ===",
            system_prompt,
            "",
            "=== RETRIEVED CONTEXT ===",
            "\n".join(f"[{i+1}] {chunk}" for i, chunk in enumerate(retrieved_chunks)),
            "",
            "=== USER QUERY ===",
            f"Question: {query}",
            "",
            "=== RESPONSE ===",
        ]

        return "\n".join(context_parts)


# Global prompt defense instance
_prompt_defense: Optional[PromptDefense] = None


def get_prompt_defense() -> PromptDefense:
    """
    Get global prompt defense instance.

    Returns:
        PromptDefense instance
    """
    global _prompt_defense
    if _prompt_defense is None:
        _prompt_defense = PromptDefense(block_on_detection=False)
    return _prompt_defense


def init_prompt_defense(block_on_detection: bool = False) -> None:
    """
    Initialize prompt defense service.

    Args:
        block_on_detection: Whether to block on detection (default: False)
    """
    global _prompt_defense
    _prompt_defense = PromptDefense(block_on_detection=block_on_detection)
    logger.info(f"Prompt defense initialized (block_on_detection={block_on_detection})")
