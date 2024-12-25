from typing import Any, Dict, Optional, List
from langchain_anthropic import ChatAnthropic
from .base import (
    BaseProvider,
    ModelProviderError,
    ProviderAuthenticationError,
    ProviderQuotaError,
    ProviderConnectionError
)

class AnthropicProvider(BaseProvider):
    """Provider implementation for Anthropic's Claude models."""

    def __init__(self, model_name: str, api_key: Optional[str] = None, settings: Dict[str, Any] = None):
        """Initialize Anthropic provider with model and settings.

        Args:
            model_name: Name of the Claude model to use
            api_key: API key for authentication
            settings: Additional settings (temperature, max_tokens, etc.)
        """
        self.api_key = api_key
        super().__init__(model_name=model_name, settings=settings or {})
        self._initialize_provider()

    def _initialize_provider(self) -> None:
        """Initialize the Anthropic client with model settings."""
        try:
            # Set max_tokens based on model version, but with lower defaults to avoid rate limits
            default_max_tokens = 4096 if '-3-5-' in self.model_name else 2048
            max_tokens = self.settings.get('max_tokens', default_max_tokens)

            # Cap max tokens to avoid rate limits
            max_tokens = min(max_tokens, 4096)  # Conservative limit

            self.client = ChatAnthropic(
                model=self.model_name,
                temperature=self.settings.get('temperature', 0.3),
                max_tokens=max_tokens,
                top_p=self.settings.get('top_p', 1.0),
                api_key=self.api_key
            )
        except Exception as e:
            if "authentication" in str(e).lower():
                raise ProviderAuthenticationError(str(e), provider="Anthropic")
            elif "rate limit" in str(e).lower():
                raise ProviderQuotaError(str(e), provider="Anthropic")
            elif "connection" in str(e).lower():
                raise ProviderConnectionError(str(e), provider="Anthropic")
            else:
                raise ModelProviderError(str(e), provider="Anthropic")

    async def create_message(self, messages: List[Dict[str, str]], model: str = None) -> str:
        """Create a message using the Anthropic model.

        Args:
            messages: List of message dictionaries with role and content
            model: Optional model override

        Returns:
            Generated text response

        Raises:
            ModelProviderError: If API call fails or other errors occur
        """
        try:
            # Instead of trying to parse roles, just use the string directly
            user_prompt = messages
            system_prompt = ""  # Or some default system prompt if needed

            # Use ainvoke for async operation instead of invoke
            response = await self.client.ainvoke(f"{system_prompt}\n\n{user_prompt}")
            return response.content
        except Exception as e:
            if "authentication" in str(e).lower():
                raise ProviderAuthenticationError(str(e), provider="Anthropic")
            elif "rate limit" in str(e).lower():
                raise ProviderQuotaError(str(e), provider="Anthropic")
            elif "connection" in str(e).lower():
                raise ProviderConnectionError(str(e), provider="Anthropic")
            else:
                raise ModelProviderError(str(e), provider="Anthropic")

    def generate_response(self, system_prompt: str, user_prompt: str) -> str:
        """Generate a response using the Claude model.

        Args:
            system_prompt: System context for the model
            user_prompt: User input to generate response from

        Returns:
            Generated text response

        Raises:
            ModelProviderError: If API call fails or other errors occur
        """
        try:
            response = self.client.invoke(f"{system_prompt}\n\n{user_prompt}")
            return response.content
        except Exception as e:
            if "authentication" in str(e).lower():
                raise ProviderAuthenticationError(str(e), provider="Anthropic")
            elif "rate limit" in str(e).lower():
                raise ProviderQuotaError(str(e), provider="Anthropic")
            elif "connection" in str(e).lower():
                raise ProviderConnectionError(str(e), provider="Anthropic")
            else:
                raise ModelProviderError(str(e), provider="Anthropic")
