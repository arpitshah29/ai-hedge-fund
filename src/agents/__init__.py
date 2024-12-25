"""
AI-powered trading agents package.
"""

from typing import Dict, Any
import asyncio
import os
from dotenv import load_dotenv

from .base import BaseAgent
from .specialized import (
    MarketDataAgent,
    SentimentAgent,
    TechnicalAgent,
    RiskManagementAgent,
    PortfolioAgent
)
from ..config.model_config import get_model_provider, ModelConfig

__all__ = ['BaseAgent', 'analyze_market']

async def analyze_market(
    symbol: str,
    market_data: Dict[str, Any],
    price_data: Dict[str, Any],
    show_reasoning: bool = False,
    provider_map: Dict[str, Any] = None,
    agent_type: str = None
) -> Dict[str, str]:
    """
    Analyze market data using all available agents or a specific agent type.
    
    Args:
        symbol: Trading symbol
        market_data: Market data dictionary
        price_data: Price data dictionary
        show_reasoning: Whether to show agent reasoning
        provider_map: Provider configuration
        agent_type: Optional specific agent type to run ("market", "sentiment", "technical", "risk", "portfolio")
    """
    
    # Get config for providers
    config = ModelConfig()
    
    # Initialize provider configurations
    provider_configs = {}
    api_keys = {}
    
    # If provider_map is provided, use those providers
    if provider_map:
        # Convert single provider string to a list
        providers = [provider_map] if isinstance(provider_map, str) else provider_map
        
        for provider in providers:
            # Get provider-specific config
            provider_config = config.get_provider_config(provider)
            provider_configs[provider] = provider_config['default_model']
            
            # Get corresponding API keys from environment
            if provider == 'anthropic':
                api_key = os.getenv('ANTHROPIC_API_KEY')
                if not api_key:
                    raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
                api_keys[provider] = api_key
            elif provider == 'openai':
                api_key = os.getenv('OPENAI_API_KEY')
                if not api_key:
                    raise ValueError("OPENAI_API_KEY not found in environment variables")
                api_keys[provider] = api_key

    # Define agent mapping
    agent_mapping = {
        "market": ("market_data_agent", MarketDataAgent),
        "sentiment": ("sentiment_agent", SentimentAgent),
        "technical": ("technical_agent", TechnicalAgent),
        "risk": ("risk_management_agent", RiskManagementAgent),
        "portfolio": ("portfolio_agent", PortfolioAgent)
    }

    # Initialize requested agents
    agents = {}
    provider_list = list(provider_configs.keys())
    
    if agent_type:
        # Initialize single agent if agent_type is specified
        if agent_type not in agent_mapping:
            raise ValueError(f"Invalid agent_type: {agent_type}")
        
        agent_name, agent_class = agent_mapping[agent_type]
        provider = provider_list[0]  # Use first provider for single agent
        agents[agent_name] = agent_class(
            model_name=provider_configs[provider],
            api_key=api_keys[provider],
            provider_name=provider
        )
    else:
        # Initialize all agents with round-robin assignment
        for i, (_, (agent_name, agent_class)) in enumerate(agent_mapping.items()):
            provider = provider_list[i % len(provider_list)]
            agents[agent_name] = agent_class(
                model_name=provider_configs[provider],
                api_key=api_keys[provider],
                provider_name=provider
            )

    # Run agent analyses
    tasks = {
        name: asyncio.create_task(agent.analyze(symbol=symbol, 
                                              price_data=price_data, 
                                              market_data=market_data, 
                                              show_reasoning=show_reasoning))
        for name, agent in agents.items()
    }
    results = await asyncio.gather(*tasks.values(), return_exceptions=True)
    return dict(zip(tasks.keys(), results))
