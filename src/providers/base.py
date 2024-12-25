"""
Base classes and error handling for AI model providers.
"""
from typing import Any, Dict, Optional
from tenacity import retry, stop_after_attempt, wait_exponential


class ModelProviderError(Exception):
    """Base exception class for model provider errors."""
    def __init__(self, message: str, provider: Optional[str] = None):
        self.provider = provider
        super().__init__(f"[{provider or 'Unknown Provider'}] {message}")


class ResponseValidationError(ModelProviderError):
    """Exception raised when provider response validation fails."""
    def __init__(self, message: str, provider: Optional[str] = None, response: Any = None):
        self.response = response
        super().__init__(message, provider)


class ProviderConnectionError(ModelProviderError):
    """Exception raised when connection to provider fails."""
    def __init__(self, message: str, provider: Optional[str] = None, retry_count: int = 0):
        self.retry_count = retry_count
        super().__init__(message, provider)


class ProviderAuthenticationError(ModelProviderError):
    """Exception raised when provider authentication fails."""
    pass


class ProviderQuotaError(ModelProviderError):
    """Exception raised when provider quota is exceeded."""
    def __init__(self, message: str, provider: Optional[str] = None, quota_reset_time: Optional[str] = None):
        self.quota_reset_time = quota_reset_time
        super().__init__(message, provider)


class BaseProvider:
    """Base class for AI model providers."""

    def __init__(self, model_name: str = None, settings: Dict[str, Any] = None):
        self.model_name = model_name
        self.settings = settings or {}

    @classmethod
    async def create(cls, model_name: str = None, settings: Dict[str, Any] = None):
        instance = cls(model_name, settings)
        await instance._initialize_provider()
        return instance

    async def _initialize_provider(self) -> None:
        """Initialize the provider client and validate settings."""
        raise NotImplementedError("Provider must implement _initialize_provider")

    def generate_response(self, system_prompt: str, user_prompt: str) -> str:
        """Generate a response from the model."""
        raise NotImplementedError("Provider must implement generate_response")

    def validate_response(self, response: str) -> Dict[str, Any]:
        """Validate and parse the model's response."""
        try:
            # Basic JSON validation
            import json
            return json.loads(response)
        except json.JSONDecodeError as e:
            raise ResponseValidationError(
                f"Failed to parse response as JSON: {str(e)}",
                provider=self.__class__.__name__,
                response=response
            )

    def _handle_provider_error(self, error: Exception, retry_count: int = 0) -> None:
        """Handle provider-specific errors and implement fallback logic."""
        if isinstance(error, ProviderConnectionError) and retry_count < 3:
            # Implement exponential backoff
            import time
            time.sleep(2 ** retry_count)
            return self.generate_response(
                system_prompt="Retry after connection error",
                user_prompt="Please try again"
            )
        elif isinstance(error, ProviderQuotaError):
            # Try fallback provider if quota exceeded
            from src.config import get_model_provider
            fallback_provider = get_model_provider("openai")  # Default fallback
            return fallback_provider.generate_response(
                system_prompt="Fallback after quota error",
                user_prompt="Please try again"
            )
        else:
            raise error

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def _make_api_request(self, *args, **kwargs):
        # Implement retry logic for API calls
        raise Exception("API request failed")