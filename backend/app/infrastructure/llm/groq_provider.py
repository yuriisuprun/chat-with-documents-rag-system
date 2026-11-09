"""
Groq LLM provider for fast cloud-based inference.

Supports Groq's fast LLM API with various open-source models.
"""

from app.core.config import settings
from app.core.exceptions import LLMTimeoutException, LLMUnavailableException
from app.core.logging import get_logger
from app.infrastructure.llm.base import LLMProvider

logger = get_logger(__name__)


class GroqProvider(LLMProvider):
    """LLM provider using Groq for fast cloud-based inference."""

    def __init__(self, model_name: str | None = None, api_key: str | None = None):
        """
        Initialize Groq provider.

        Args:
            model_name: Model to use (default from settings)
            api_key: Groq API key (default from settings)
        """
        self.model_name = model_name or settings.groq_model
        self.api_key = api_key or settings.groq_api_key
        self.default_temperature = settings.groq_temperature
        self.timeout = settings.groq_timeout

        if not self.api_key:
            raise LLMUnavailableException(
                "groq", "GROQ_API_KEY environment variable not set"
            )

        logger.debug(
            f"GroqProvider initialized: model={self.model_name}, "
            f"timeout={self.timeout}s"
        )

    def generate(
        self, prompt: str, temperature: float | None = None, timeout: int | None = None
    ) -> str:
        """
        Generate text using Groq API.

        Args:
            prompt: Input prompt
            temperature: Response temperature (default from settings)
            timeout: Request timeout in seconds (default from settings)

        Returns:
            Generated text response

        Raises:
            LLMUnavailableException: If Groq API unreachable or returns error
            LLMTimeoutException: If request times out
        """
        try:
            temp = temperature if temperature is not None else self.default_temperature
            timeout_val = timeout if timeout is not None else self.timeout

            logger.debug(f"Calling Groq model '{self.model_name}' with temperature={temp}")

            # Import here to get fresh instance
            from groq import Groq
            
            # Initialize Groq client with proper configuration
            client = Groq(
                api_key=self.api_key,
                timeout=timeout_val,
            )

            logger.debug(f"Groq client created successfully")

            # Make request using correct Groq API
            try:
                logger.debug(f"Calling chat.completions.create with model={self.model_name}")
                
                response = client.chat.completions.create(
                    model=self.model_name,
                    max_tokens=1024,
                    temperature=temp,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                )

                logger.debug(f"Response received: {type(response)}")

                # Extract response
                generated_text = response.choices[0].message.content

                if not generated_text:
                    logger.warning("Groq returned empty response")
                    return ""

                logger.debug(f"Generated {len(generated_text)} characters")
                return generated_text

            except AttributeError as e:
                error_msg = str(e)
                logger.error(f"AttributeError - Groq client issue: {error_msg}")
                logger.error(f"Client type: {type(client)}")
                logger.error(f"Client dir: {[x for x in dir(client) if not x.startswith('_')]}")
                raise LLMUnavailableException("groq", f"Groq API error: {error_msg}")
            except Exception as e:
                error_msg = str(e)
                if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                    logger.error(f"Groq request timed out after {timeout_val}s")
                    raise LLMTimeoutException(timeout_val)
                elif "authentication" in error_msg.lower() or "invalid api key" in error_msg.lower() or "401" in error_msg:
                    logger.error(f"Groq authentication failed: {error_msg}")
                    raise LLMUnavailableException("groq", "Invalid API key or authentication failed")
                else:
                    logger.error(f"Groq request failed: {e}")
                    raise LLMUnavailableException("groq", error_msg)

        except (LLMTimeoutException, LLMUnavailableException):
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling Groq: {e}")
            raise LLMUnavailableException("groq", str(e))

    def get_model_name(self) -> str:
        """
        Get the name of the LLM model.

        Returns:
            Model name
        """
        return self.model_name
