"""
Cryptocurrency Market Data Provider

This module provides cryptocurrency market data using multiple data sources.
Specializes in historical cryptocurrency price and volume data retrieval with support
for major cryptocurrencies like BTC, ETH, and others.

Features:
- Historical cryptocurrency price and volume data
- Automatic USD pair handling for crypto assets
- Built-in error handling and logging
- CoinMarketCap-compatible data format
"""
from datetime import datetime, timedelta
import logging
from typing import Dict, Any, List
from functools import lru_cache
from asyncio import Lock
from circuitbreaker import circuit
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
import aiohttp
import os

from src.providers.cmc_client import CMCClient
from .base import BaseProvider


class CryptoMarketProvider(BaseProvider):
    """
    Provider for historical cryptocurrency market data.
    """

    def __init__(self, session: aiohttp.ClientSession = None):
        """Initialize the cryptocurrency data provider."""
        self.logger = logging.getLogger(__name__)
        self._cache_lock = Lock()
        self.client = CMCClient()  # Initialize CMC client here
        self.api_key = os.getenv('COINMARKETCAP_API_KEY')
        self.session = session
        super().__init__()

    async def _initialize_provider(self) -> None:
        """Initialize the cryptocurrency data provider."""
        self.logger.info("Initialized cryptocurrency market data provider")

    @lru_cache(maxsize=100)
    async def get_market_data(self, symbol: str) -> Dict[str, Any]:
        """Get current market data for a cryptocurrency."""
        async with self._cache_lock:
            try:
                response = await self.client.get_market_data(symbol)
                if not response or 'data' not in response:
                    raise ValueError(f"Invalid response format from CoinMarketCap API for {symbol}")
                return response
            except Exception as e:
                self.logger.error(f"Error fetching market data: {e}")
                raise

    @circuit(failure_threshold=5, recovery_timeout=60)
    async def get_historical_prices(self, symbol: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Get historical price data for a cryptocurrency."""
        try:
            response = await self.client.get_historical_prices(symbol, start_date, end_date)
            
            if not response or 'data' not in response:
                raise ValueError(f"Invalid response from CoinMarketCap API for {symbol}")
                
            return response
            
        except Exception as e:
            self.logger.error(f"Error fetching historical prices: {e}")
            raise

    async def get_supported_cryptocurrencies(self) -> Dict[str, str]:
        """Get list of supported cryptocurrencies."""
        if not self.session:
            async with aiohttp.ClientSession() as session:
                return await self._fetch_cryptocurrencies(session)
        else:
            return await self._fetch_cryptocurrencies(self.session)

    async def _fetch_cryptocurrencies(self, session: aiohttp.ClientSession) -> Dict[str, str]:
        try:
            response = await self.client.get_available_cryptocurrencies()
            if not response or 'data' not in response:
                raise ValueError("Invalid response format from CoinMarketCap API")

            # Create a more structured format with unique symbols
            seen_symbols = set()
            cryptos = []
            
            for crypto in response['data']:
                symbol = crypto['symbol']
                # Handle duplicate symbols by appending platform/chain info
                if symbol in seen_symbols:
                    # If duplicate, add platform/chain identifier
                    platform = crypto.get('platform')
                    if platform and isinstance(platform, dict):
                        symbol = f"{symbol}-{platform.get('symbol', '')}"
                
                if symbol not in seen_symbols:
                    seen_symbols.add(symbol)
                    # Safely handle platform information
                    platform = crypto.get('platform')
                    platform_name = platform.get('name') if platform and isinstance(platform, dict) else 'Native'
                    
                    cryptos.append({
                        'symbol': symbol,
                        'name': crypto['name'],
                        'rank': crypto.get('rank', 9999),  # Use high rank for those without
                        'platform': platform_name
                    })

            # Sort by rank to prioritize major tokens
            cryptos.sort(key=lambda x: x['rank'])
            return {'data': cryptos[:5000]}  # Limit to top 5000 cryptocurrencies
            
        except Exception as e:
            self.logger.error(f"Error fetching supported cryptocurrencies: {e}")
            raise
