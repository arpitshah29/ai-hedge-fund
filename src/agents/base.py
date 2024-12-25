"""
Base agent class for cryptocurrency market analysis.
"""

from typing import Dict, Any, Optional
from ..providers import PROVIDER_MAP
import os

class BaseAgent:
    """Base class for AI trading agents."""

    def __init__(self, model_name: str, api_key: str, provider_name: str = 'anthropic'):
        """Initialize the agent with a model provider.
        
        Args:
            model_name: Name of the model to use
            api_key: API key for authentication
            provider_name: Name of the provider (default: 'anthropic')
        """
        provider_class = PROVIDER_MAP[provider_name]
        # Pass the api_key to the provider initialization
        self.provider = provider_class(model_name=model_name, api_key=api_key)

    async def analyze(self, price_data, market_data, show_reasoning=False):
        """Analyze market data and return insights."""
        raise NotImplementedError("Agents must implement analyze method")
