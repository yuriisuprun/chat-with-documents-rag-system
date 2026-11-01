"""
Ollama LLM provider for local model inference.

Supports all Ollama models for on-device generation.
"""

from app.core.config import settings
from app.core.exceptions import LLMTimeoutException, LLMUnavailableException
from app.core.logging import get_logger
from app.infrastructure.llm.base import LLMProvider

logger = get_logger(__name__)


class OllamaProvider(LLMProvider):
    """LLM provider using Ollama for local inference."""

    def __init__(self, model_name: str | None = None):
        """
        Initialize Ollama provider.

        Args:
            model_name: Model to use (default from settings)
        """
        self.model_name = model_name or settings.ollama_model
        self.base_url = settings.ollama_base_url
        self.default_temperature = settings.ollama_temperature
        self.timeout = settings.ollama_timeout

        logger.debug(
            f"OllamaProvider initialized: model={self.model_name}, "
            f"url={self.base_url}, timeout={self.timeout}s"
        )

    def generate(
        self, prompt: str, temperature: float | None = None, timeout: int | None = None
    ) -> str:
        """
        Generate text using Ollama.

        Args:
            prompt: Input prompt
            temperature: Response temperature (default from settings)
            timeout: Request timeout in seconds (default from settings)

        Returns:
            Generated text response

        Raises:
            LLMUnavailableException: If Ollama service unreachable
            LLMTimeoutException: If request times out
        """
        try:
            import requests

            temp = temperature if temperature is not None else self.default_temperature
            timeout_val = timeout if timeout is not None else self.timeout

            logger.debug(f"Calling Ollama model '{self.model_name}' with temperature={temp}")

            # Prepare request
            url = f"{self.base_url}/api/generate"
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "temperature": temp,
                "stream": False,
            }

            # Make request
            try:
                response = requests.post(
                    url,
                    json=payload,
                    timeout=timeout_val,
                )
                response.raise_for_status()
            except requests.Timeout:
                logger.error(f"Ollama request timed out after {timeout_val}s")
                raise LLMTimeoutException(timeout_val)
            except requests.ConnectionError as e:
                logger.error(f"Failed to connect to Ollama at {self.base_url}: {e}")
                raise LLMUnavailableException("ollama", str(e))
            except requests.RequestException as e:
                logger.error(f"Ollama request failed: {e}")
                raise LLMUnavailableException("ollama", str(e))

            # Parse response
            result = response.json()
            generated_text = result.get("response", "")

            if not generated_text:
                logger.warning("Ollama returned empty response")
                return ""

            logger.debug(f"Generated {len(generated_text)} characters")
            return generated_text

        except (LLMTimeoutException, LLMUnavailableException):
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling Ollama: {e}")
            raise LLMUnavailableException("ollama", str(e))

    def get_model_name(self) -> str:
        """
        Get the name of the LLM model.

        Returns:
            Model name
        """
        return self.model_name
