"""
Base abstraction for LLM providers.

Defines interface for different LLM implementations.
"""

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate(self, prompt: str, temperature: float = 0.3, timeout: int = 120) -> str:
        """
        Generate text from prompt.

        Args:
            prompt: Input prompt
            temperature: Response temperature (0.0-1.0)
            timeout: Request timeout in seconds

        Returns:
            Generated text response
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """
        Get the name of the LLM model.

        Returns:
            Model name/identifier
        """
        pass
