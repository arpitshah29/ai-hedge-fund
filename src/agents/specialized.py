"""
Specialized cryptocurrency trading agent implementations.
"""

# Standard library imports
import json
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Dict, Any
import logging
import pandas as pd

# Local imports
from .base import BaseAgent
from ..providers import PROVIDER_MAP
from ..tools import (
    calculate_bollinger_bands,
    calculate_macd,
    calculate_obv,
    calculate_rsi,
    get_market_data,
    get_price_data,
    prices_to_df
)
import aioredis

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("httpcore").setLevel(logging.WARNING)

class MarketDataAgent(BaseAgent):
    """Analyzes current market data and trends for any cryptocurrency using Claude."""

    def __init__(self, model_name: str, api_key: str, provider_name: str = 'anthropic', redis_url: str = 'redis://localhost'):
        super().__init__(
            model_name=model_name,
            api_key=api_key,
            provider_name=provider_name
        )
        # Initialize Redis client
        self.redis_client = None
        self.redis_url = redis_url

    async def _init_redis(self):
        """Initialize Redis client if not already initialized"""
        if self.redis_client is None:
            self.redis_client = await aioredis.from_url(self.redis_url)

    async def analyze(self, price_data, market_data, show_reasoning=True, symbol=None):
        # Initialize Redis client
        await self._init_redis()
        
        # Create a cache key using only hashable components
        try:
            symbol = next(iter(market_data['data'].keys()))
            quote = market_data['data'][symbol]['quote']['USD']
            cache_key = f"{symbol}:{quote['price']}:{quote['percent_change_24h']}:{datetime.now().strftime('%Y-%m-%d-%H')}"
            
            # Check Redis cache
            cached_result = await self.redis_client.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            # Validate market_data input
            if not isinstance(market_data, dict) or 'data' not in market_data:
                return "Error: Invalid or missing market data"

            # Get the first cryptocurrency data
            crypto_data = next(iter(market_data['data'].values()), None)
            if not crypto_data or 'quote' not in crypto_data or 'USD' not in crypto_data['quote']:
                return "Error: Invalid cryptocurrency data structure"

            quote = crypto_data['quote']['USD']

            # Format basic market data with clear section breaks
            market_stats = (
                "=== MARKET STATISTICS ===\n"
                f"Current Price:    ${quote['price']:.2f}\n"
                f"24h Change:       {quote['percent_change_24h']:.2f}%\n"
                f"Volume:          ${quote['volume_24h']/1e6:.1f}M\n"
                f"Market Cap:      ${quote['market_cap']/1e9:.2f}B"
            )

            if self.provider:
                # Add reasoning request to the prompt when show_reasoning is True
                reasoning_request = """
                For each point, please explain your reasoning by:
                - Citing specific data points that support your conclusion
                - Explaining the significance of these indicators
                - Describing how you arrived at your assessment
                """ if show_reasoning else ""

                prompt = f"""Analyze the following cryptocurrency market data and provide insights:
                {market_stats}
                
                Please provide:
                1. Market strength assessment
                2. Notable patterns or concerns
                3. Key factors to watch
                {reasoning_request}
                """
                
                print(f"MarketDataAgent Prompt:\n{prompt}")
                response = await self.provider.create_message(prompt)
                
                # If show_reasoning is False, try to extract just the conclusions
                if not show_reasoning:
                    # Split response into lines and filter out lines that look like reasoning
                    lines = response.split('\n')
                    analysis_lines = [
                        line for line in lines 
                        if not line.strip().startswith(('Because', 'This is based on', 'Given that', 'Considering'))
                    ]
                    analysis = '\n'.join(analysis_lines)
                else:
                    analysis = response
            else:
                analysis = market_stats

            await self.redis_client.set(cache_key, json.dumps(analysis), ex=3600)
            return analysis
        except Exception as e:
            return f"Error analyzing market data: {str(e)}"

class SentimentAgent(BaseAgent):
    """Analyzes market sentiment for any cryptocurrency using AI."""

    def __init__(self, model_name: str, api_key: str, provider_name: str = 'anthropic'):
        super().__init__(
            model_name=model_name,
            api_key=api_key, 
            provider_name=provider_name
        )

    async def analyze(self, price_data, market_data, show_reasoning=False, symbol=None):
        try:
            quote = list(market_data['data'].values())[0]['quote']['USD']
            
            market_stats = (
                "=== MARKET TRENDS ===\n"
                f"24h Change: {quote['percent_change_24h']:.2f}%\n"
                f"7d Change: {quote['percent_change_7d']:.2f}%\n"
                f"30d Change: {quote['percent_change_30d']:.2f}%\n"
                f"Volume Change 24h: {quote['volume_change_24h']:.2f}%"
            )

            if self.provider:
                prompt = f"""Analyze the market sentiment based on the following cryptocurrency data:
                {market_stats}
                
                Please provide:
                1. Overall market sentiment (bullish/bearish/neutral)
                2. Key sentiment indicators
                3. Sentiment outlook for next 24-48 hours
                """
                
                print(f"SentimentAgent Prompt:\n{prompt}")
                response = await self.provider.create_message(prompt)
                analysis = f"{response}"
            else:
                sentiment = "bullish" if quote['percent_change_24h'] > 0 else "bearish"
                analysis = (
                    f"Market Sentiment: {sentiment.upper()}\n"
                    f"24h Trend: {quote['percent_change_24h']:.2f}%\n"
                    f"7d Trend: {quote['percent_change_7d']:.2f}%"
                )
            
            return analysis
        except Exception as e:
            return f"Error analyzing sentiment: {str(e)}"

class TechnicalAgent(BaseAgent):
    """Analyzes technical indicators for any cryptocurrency using AI."""

    def __init__(self, model_name: str, api_key: str, provider_name: str = 'anthropic'):
        super().__init__(
            model_name=model_name,
            api_key=api_key,
            provider_name=provider_name
        )

    async def analyze(self, price_data, market_data, show_reasoning=False, symbol=None):
        try:
           
            # Convert price_data to DataFrame if it's a dictionary
            if isinstance(price_data, dict):
                try:
                    # Handle the nested structure from data.json
                    if 'data' in price_data and 'quotes' in price_data['data']:
                        quotes = price_data['data']['quotes']
                        data_list = []
                        for quote in quotes:
                            data_list.append({
                                'timestamp': quote['timestamp'],
                                'close': quote['quote']['USD']['price'],
                                'volume': quote['quote']['USD']['volume_24h'],
                                'market_cap': quote['quote']['USD']['market_cap']
                            })
                        df = pd.DataFrame(data_list)
                        df['timestamp'] = pd.to_datetime(df['timestamp'])
                        df.set_index('timestamp', inplace=True)
                    # Keep the existing logic for other data formats
                    elif 'prices' in price_data:
                        df = pd.DataFrame(price_data['prices'])
                        df['close'] = df['price']  # Rename 'price' to 'close'
                        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                        df.set_index('timestamp', inplace=True)
                    else:
                        # Try direct conversion if data is already in correct format
                        df = pd.DataFrame(price_data)
                    
                    logging.debug(f"Converted DataFrame columns: {df.columns.tolist()}")
                    
                    # Ensure required columns exist
                    required_columns = ['close']
                    missing_columns = [col for col in required_columns if col not in df.columns]
                    if missing_columns:
                        raise ValueError(f"Missing required columns: {missing_columns}")
                        
                except Exception as e:
                    logging.error(f"DataFrame conversion error: {str(e)}")
                    raise ValueError(f"Error converting prices to DataFrame: {str(e)}")
            else:
                df = price_data

            if df.empty:
                return "Error: No price data available for technical analysis"

            # Calculate technical indicators
            rsi = calculate_rsi(df)
            macd_line, signal_line = calculate_macd(df)
            upper_band, lower_band = calculate_bollinger_bands(df)
            
            # Get latest values
            latest_rsi = float(rsi.iloc[-1])
            latest_macd = float(macd_line.iloc[-1])
            latest_signal = float(signal_line.iloc[-1])
            latest_close = float(df['close'].iloc[-1])
            latest_upper = float(upper_band.iloc[-1])
            latest_lower = float(lower_band.iloc[-1])

            technical_data = (
                "=== TECHNICAL INDICATORS ===\n"
                f"RSI (14): {latest_rsi:.2f}\n"
                f"MACD: {latest_macd:.2f}\n"
                f"Signal Line: {latest_signal:.2f}\n"
                f"Current Price: {latest_close:.2f}\n"
                f"Upper BB: {latest_upper:.2f}\n"
                f"Lower BB: {latest_lower:.2f}"
            )

            if self.provider:
                prompt = f"""Analyze these technical indicators and provide trading insights:
                {technical_data}
                
                Please provide:
                1. Overall technical analysis summary
                2. Key indicator signals (RSI, MACD, Bollinger Bands)
                3. Potential price action scenarios
                4. Trading recommendations based on technical analysis
                """
                
                print(f"TechnicalAgent Prompt:\n{prompt}")
                response = await self.provider.create_message(prompt)
                analysis = f"{response}"
            else:
                # Fallback to original logic
                rsi_signal = "Overbought" if latest_rsi > 70 else "Oversold" if latest_rsi < 30 else "Neutral"
                macd_signal = "Bullish" if latest_macd > latest_signal else "Bearish"
                bb_signal = "Overbought" if latest_close > latest_upper else "Oversold" if latest_close < latest_lower else "Neutral"
                
                analysis = (
                    f"Technical Analysis:\n"
                    f"RSI (14): {latest_rsi:.2f} - {rsi_signal}\n"
                    f"MACD Signal: {macd_signal} (MACD: {latest_macd:.2f}, Signal: {latest_signal:.2f})\n"
                    f"Bollinger Bands: {bb_signal} (Price: {latest_close:.2f}, Upper: {latest_upper:.2f}, Lower: {latest_lower:.2f})"
                )

            return analysis
        except Exception as e:
            return f"Error analyzing technical indicators: {str(e)}"

class RiskManagementAgent(BaseAgent):
    """Analyzes market risks for any cryptocurrency using AI."""

    def __init__(self, model_name: str, api_key: str, provider_name: str = 'anthropic'):
        super().__init__(
            model_name=model_name,
            api_key=api_key,
            provider_name=provider_name
        )

    async def analyze(self, price_data, market_data, show_reasoning=False, symbol=None):
        try:
            quote = list(market_data['data'].values())[0]['quote']['USD']
            volatility = abs(quote['percent_change_24h'])
            
            risk_data = (
                "=== RISK METRICS ===\n"
                f"24h Volatility: {volatility:.2f}%\n"
                f"Volume Change: {quote['volume_change_24h']:.2f}%\n"
                f"Market Cap: ${quote['market_cap']/1e9:.2f}B\n"
                f"24h Volume: ${quote['volume_24h']/1e6:.2f}M"
            )

            if self.provider:
                prompt = f"""Analyze the following risk metrics for this cryptocurrency:
                {risk_data}
                
                Please provide:
                1. Overall risk assessment
                2. Key risk factors
                3. Risk mitigation recommendations
                4. Position sizing suggestions
                """
                
                print(f"RiskManagementAgent Prompt:\n{prompt}")
                response = await self.provider.create_message(prompt)
                analysis = f"{response}"
            else:
                risk_level = "HIGH" if volatility > 10 else "MEDIUM" if volatility > 5 else "LOW"
                analysis = (
                    f"Risk Level: {risk_level}\n"
                    f"Volatility: {volatility:.2f}%\n"
                    f"Volume Change: {quote['volume_change_24h']:.2f}%"
                )

            return analysis
        except Exception as e:
            return f"Error analyzing risks: {str(e)}"

class PortfolioAgent(BaseAgent):
    """Provides portfolio recommendations for any cryptocurrency using AI."""

    def __init__(self, model_name: str, api_key: str, provider_name: str = 'anthropic'):
        super().__init__(
            model_name=model_name,
            api_key=api_key,
            provider_name=provider_name
        )

    async def analyze(self, price_data, market_data, show_reasoning=False, symbol=None):
        try:
            quote = list(market_data['data'].values())[0]['quote']['USD']
            
            portfolio_data = (
                "=== PORTFOLIO METRICS ===\n"
                f"Current Price: ${quote['price']:.2f}\n"
                f"24h Change: {quote['percent_change_24h']:.2f}%\n"
                f"7d Change: {quote['percent_change_7d']:.2f}%\n"
                f"Market Cap: ${quote['market_cap']/1e9:.2f}B\n"
                f"Volume: ${quote['volume_24h']/1e6:.2f}M"
            )

            if self.provider:
                prompt = f"""Analyze these portfolio metrics and provide investment recommendations:
                {portfolio_data}
                
                Please provide:
                1. Recommended portfolio action (buy/sell/hold)
                2. Position sizing recommendation
                3. Risk management considerations
                4. Short-term and long-term outlook
                """
                
                print(f"PortfolioAgent Prompt:\n{prompt}")
                response = await self.provider.create_message(prompt)
                analysis = f"{response}"
            else:
                trend = quote['percent_change_24h']
                action = "TAKE PROFIT" if trend > 5 else "BUY DIP" if trend < -5 else "HOLD"
                analysis = (
                    f"Recommended Action: {action}\n"
                    f"Price Trend: {trend:.2f}%\n"
                    f"Market Direction: {'Upward' if trend > 0 else 'Downward'}"
                )

            return analysis
        except Exception as e:
            return f"Error generating portfolio advice: {str(e)}"
