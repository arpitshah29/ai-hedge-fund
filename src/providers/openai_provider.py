"""
OpenAI model provider implementation.
Supports GPT-4 and other OpenAI models through LangChain integration.
"""

from typing import Dict, Any, Optional, List
from langchain_openai import ChatOpenAI

from .base import (
    BaseProvider,
    ModelProviderError,
    ResponseValidationError,
    ProviderConnectionError,
    ProviderAuthenticationError,
    ProviderQuotaError
)

class OpenAIProvider(BaseProvider):
    """OpenAI model provider implementation."""

    def __init__(self, model_name: str, api_key: Optional[str] = None, settings: Dict[str, Any] = None):
        """Initialize OpenAI provider with model and settings.

        Args:
            model_name: Name of the model to use
            api_key: API key for authentication
            settings: Additional settings (temperature, max_tokens, etc.)
        """
        self.api_key = api_key
        super().__init__(model_name=model_name, settings=settings or {})
        self._initialize_provider()

    def _initialize_provider(self) -> None:
        """Initialize the OpenAI client."""
        try:
            self.client = ChatOpenAI(
                model_name=self.model_name,
                temperature=self.settings.get('temperature', 1.0),
                max_tokens=self.settings.get('max_tokens', 4096),
                top_p=self.settings.get('top_p', 1.0),
                api_key=self.api_key
            )
        except Exception as e:
            raise ModelProviderError(
                f"Failed to initialize OpenAI provider: {str(e)}",
                provider="OpenAI"
            )

    async def create_message(self, messages: List[Dict[str, str]], model: str = None) -> str:
        """Create a message using the OpenAI model.

        Args:
            messages: List of message dictionaries with role and content
            model: Optional model override

        Returns:
            Generated text response

        Raises:
            ModelProviderError: If API call fails or other errors occur
        """
        try:
            # Use ainvoke for async operation
            response = await self.client.ainvoke(messages)
            return response.content
        except Exception as e:
            if "authentication" in str(e).lower():
                raise ProviderAuthenticationError(
                    "OpenAI authentication failed",
                    provider="OpenAI"
                )
            elif "rate" in str(e).lower():
                raise ProviderQuotaError(
                    "OpenAI rate limit exceeded",
                    provider="OpenAI"
                )
            elif "connection" in str(e).lower():
                raise ProviderConnectionError(
                    "OpenAI connection failed",
                    provider="OpenAI"
                )
            else:
                raise ModelProviderError(
                    f"OpenAI response generation failed: {str(e)}",
                    provider="OpenAI"
                )

    def generate_response(self, system_prompt: str, user_prompt: str) -> str:
        """Generate response using OpenAI model."""
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            response = self.client.invoke(messages)
            return response.content
        except Exception as e:
            if "authentication" in str(e).lower():
                raise ProviderAuthenticationError(
                    "OpenAI authentication failed",
                    provider="OpenAI"
                )
            elif "rate" in str(e).lower():
                raise ProviderQuotaError(
                    "OpenAI rate limit exceeded",
                    provider="OpenAI"
                )
            elif "connection" in str(e).lower():
                raise ProviderConnectionError(
                    "OpenAI connection failed",
                    provider="OpenAI"
                )
            else:
                raise ModelProviderError(
                    f"OpenAI response generation failed: {str(e)}",
                    provider="OpenAI"
                )

    def validate_response(self, response: str) -> Dict[str, Any]:
        """Validate OpenAI response format."""
        if not isinstance(response, str):
            raise ResponseValidationError(
                "Response must be a string",
                provider="OpenAI",
                response=response
            )
        if not response.strip():
            raise ResponseValidationError(
                "Response cannot be empty",
                provider="OpenAI",
                response=response
            )
        return super().validate_response(response)
