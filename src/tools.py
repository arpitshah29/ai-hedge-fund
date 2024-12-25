import os
import logging
import pandas as pd
from typing import Dict, Any, List, Tuple
import aiohttp


from src.providers.crypto_market_provider import CryptoMarketProvider


logging.getLogger("httpcore").setLevel(logging.WARNING)


async def get_market_data(symbol: str) -> Dict[str, Any]:
    """Get current market data for a cryptocurrency."""
    try:
        if os.getenv('COINMARKETCAP_API_KEY'):
            provider = CryptoMarketProvider()

        return await provider.get_market_data(symbol)
    except Exception as e:
        raise Exception(f"Failed to get market data: {str(e)}")


async def get_price_data(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Get historical price data for a cryptocurrency."""
    try:
        if os.getenv('COINMARKETCAP_API_KEY'):
            provider = CryptoMarketProvider()

        # Convert async generator to list
        prices = []
        async for chunk in provider.get_historical_prices(symbol, start_date, end_date):
            prices.append(chunk)
        
        # Combine chunks and convert to DataFrame
        return prices_to_df({'data': prices})
    except Exception as e:
        raise Exception(f"Failed to get price data: {str(e)}")


def prices_to_df(price_data: Dict[str, Any]) -> pd.DataFrame:
    """Convert price data to DataFrame format."""
    try:
        if not isinstance(price_data, dict):
            raise ValueError("Price data must be a dictionary")

        if isinstance(price_data, dict) and 'price_data' in price_data:
            df = price_data['price_data']
            if isinstance(df, pd.DataFrame):
                return df.copy()

        if isinstance(price_data, dict) and 'data' in price_data:
            rows = []
            for quote_data in price_data['data']['quotes']:
                if 'quote' in quote_data:
                    usd_data = quote_data['quote']['USD']
                    row = {
                        'timestamp': usd_data['timestamp'],
                        'open': usd_data.get('open', usd_data['close']),
                        'high': usd_data.get('high', usd_data['close']),
                        'low': usd_data.get('low', usd_data['close']),
                        'close': usd_data['close'],
                        'volume': usd_data['volume'],
                        'market_cap': usd_data.get('market_cap', 0)
                    }
                    rows.append(row)
            df = pd.DataFrame(rows)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)
            return df

        raise ValueError("Unsupported price data format")
    except Exception as e:
        raise Exception(f"Error converting prices to DataFrame: {str(e)}")


async def get_supported_cryptocurrencies(session: aiohttp.ClientSession = None) -> List[Dict[str, str]]:
    """Get list of supported cryptocurrencies."""
    try:
        if os.getenv('COINMARKETCAP_API_KEY'):
            provider = CryptoMarketProvider(session=session)

        cryptos = await provider.get_supported_cryptocurrencies()
        return cryptos['data']
    except Exception as e:
        raise Exception(f"Failed to get supported cryptocurrencies: {str(e)}")


def calculate_confidence_level(df: pd.DataFrame) -> float:
    """Calculate confidence level based on technical indicators."""
    try:
        rsi = calculate_rsi(df)
        macd_line, signal_line = calculate_macd(df)
        return float(rsi.iloc[-1])
    except Exception as e:
        raise Exception(f"Error calculating confidence level: {str(e)}")


def calculate_macd(df: pd.DataFrame, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> Tuple[pd.Series, pd.Series]:
    """Calculate MACD (Moving Average Convergence Divergence)."""
    try:
        fast_ema = df['close'].ewm(span=fast_period, adjust=False).mean()
        slow_ema = df['close'].ewm(span=slow_period, adjust=False).mean()
        macd_line = fast_ema - slow_ema
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        return macd_line, signal_line
    except Exception as e:
        raise Exception(f"Error calculating MACD: {str(e)}")


def calculate_rsi(df: pd.DataFrame, periods: int = 14) -> pd.Series:
    """Calculate RSI (Relative Strength Index)."""
    try:
        close_delta = df['close'].diff()
        gains = close_delta.where(close_delta > 0, 0.0)
        losses = -close_delta.where(close_delta < 0, 0.0)
        avg_gains = gains.rolling(window=periods, min_periods=1).mean()
        avg_losses = losses.rolling(window=periods, min_periods=1).mean()
        rs = avg_gains / avg_losses
        rsi = 100.0 - (100.0 / (1.0 + rs))
        return rsi.fillna(50.0)
    except Exception as e:
        raise Exception(f"Error calculating RSI: {str(e)}")


def calculate_bollinger_bands(df: pd.DataFrame, window: int = 20) -> Tuple[pd.Series, pd.Series]:
    """Calculate Bollinger Bands."""
    try:
        sma = df['close'].rolling(window=window).mean()
        std = df['close'].rolling(window=window).std()
        upper_band = sma + (std * 2)
        lower_band = sma - (std * 2)
        return upper_band.fillna(method='bfill'), lower_band.fillna(method='bfill')
    except Exception as e:
        raise Exception(f"Error calculating Bollinger Bands: {str(e)}")


def calculate_obv(df: pd.DataFrame) -> pd.Series:
    """Calculate On-Balance Volume (OBV)."""
    try:
        obv = pd.Series(index=df.index, dtype=float)
        obv.iloc[0] = 0
        for i in range(1, len(df)):
            if df['close'].iloc[i] > df['close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + df['volume'].iloc[i]
            elif df['close'].iloc[i] < df['close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - df['volume'].iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        return obv
    except Exception as e:
        raise Exception(f"Error calculating OBV: {str(e)}")


def calculate_technical_indicators(df: pd.DataFrame) -> Dict[str, pd.Series]:
    """Calculate all technical indicators in one pass"""
    results = {}
    
    # Calculate EMAs once and reuse
    fast_ema = df['close'].ewm(span=12, adjust=False).mean()
    slow_ema = df['close'].ewm(span=26, adjust=False).mean()
    
    # MACD
    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    results['macd'] = (macd_line, signal_line)
    
    # RSI and other indicators
    # ... optimize other calculations
    
    return results
