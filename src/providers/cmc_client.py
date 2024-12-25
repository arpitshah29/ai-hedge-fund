import os
import logging
import aiohttp
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv

class CMCClient:
    """CoinMarketCap API client."""

    def __init__(self):
        load_dotenv()  # Load environment variables
        self.api_key = os.getenv('COINMARKETCAP_API_KEY')
        if not self.api_key:
            raise ValueError("COINMARKETCAP_API_KEY not found in environment variables")
        self.base_url = "https://pro-api.coinmarketcap.com/v1"
        self.headers = {
            'X-CMC_PRO_API_KEY': self.api_key,
            'Accept': 'application/json'
        }
        self._session = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self._get_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def _get_session(self):
        """Get or create an aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(headers=self.headers)
        return self._session

    async def get_market_data(self, symbol: str) -> Dict[str, Any]:
        """Get current market data for a cryptocurrency."""
        session = await self._get_session()
        url = f"{self.base_url}/cryptocurrency/quotes/latest"
        params = {'symbol': symbol, 'convert': 'USD'}
        
        async with session.get(url, params=params) as response:
            response.raise_for_status()
            return await response.json()

    async def get_historical_prices(self, symbol: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Get historical price data for a cryptocurrency."""
        session = await self._get_session()
        url = f"{self.base_url}/cryptocurrency/quotes/historical"
        
        # Convert dates to timestamps if they're not already
        start_timestamp = int(datetime.fromisoformat(start_date.replace('Z', '')).timestamp())
        end_timestamp = int(datetime.fromisoformat(end_date.replace('Z', '')).timestamp())
        
        params = {
            'symbol': symbol,
            'convert': 'USD',
            'time_start': start_timestamp,
            'time_end': end_timestamp
        }
        
        async with session.get(url, params=params) as response:
            response.raise_for_status()
            return await response.json()

    async def get_available_cryptocurrencies(self) -> Dict[str, Any]:
        """Get list of all available cryptocurrencies.
        
        Returns top 500 cryptocurrencies sorted by CMC rank.
        """
        session = await self._get_session()
        url = f"{self.base_url}/cryptocurrency/map"
        
        params = {
            'sort': 'cmc_rank',
            'limit': 5000,
            'start': 1
        }
        
        async with session.get(url, params=params) as response:
            response.raise_for_status()
            return await response.json()

    async def close(self):
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
