from fastapi import FastAPI, HTTPException, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional
import asyncio
from datetime import datetime, timedelta
from fastapi.middleware.gzip import GZipMiddleware
from redis import Redis
from contextlib import asynccontextmanager
from functools import partial
from fastapi_cache.decorator import cache
import time
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from contextlib import asynccontextmanager
from src.providers.cmc_client import CMCClient

from src.tools import get_supported_cryptocurrencies, get_market_data, get_price_data
from src.agents import analyze_market
from src.providers.crypto_market_provider import CryptoMarketProvider

import logging
import aiohttp

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

redis_client = None
cmc_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup
    redis = Redis(
        host="localhost",
        port=6379,
        encoding="utf8",
        decode_responses=True
    )
    # Make redis globally available
    global redis_client
    redis_client = redis
    
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
    global cmc_client
    cmc_client = CMCClient()
    await cmc_client._get_session()  # Initialize the session
    
    yield
    
    # Cleanup (if needed)
    if cmc_client:
        await cmc_client.close()

# Initialize tracing before creating the app
trace.set_tracer_provider(TracerProvider())

app = FastAPI(lifespan=lifespan)
FastAPIInstrumentor.instrument_app(app)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Frontend dev server
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add response caching
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache

def cache_key_builder(
    func,
    *args,
    **kwargs
) -> str:
    """Build cache key from function name and arguments"""
    # Extract relevant parameters
    symbol = kwargs.get('symbol', '')
    provider = kwargs.get('provider', 'openai')
    start_date = kwargs.get('start_date', '')
    end_date = kwargs.get('end_date', '')
    
    # Create a unique key combining all parameters
    return f"{func.__name__}:{symbol}:{provider}:{start_date}:{end_date}:{int(time.time() / 300)}"

@app.get("/api/cryptocurrencies")
async def list_cryptocurrencies():
    """Get list of supported cryptocurrencies."""
    try:
        async with aiohttp.ClientSession() as session:  # Create a session
            cryptocurrencies = await get_supported_cryptocurrencies(session)  # Pass session as parameter
            return {"data": cryptocurrencies}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/market-data/{symbol}")
@cache(
    expire=60,
    key_builder=cache_key_builder
)
async def get_crypto_market_data(symbol: str):
    try:
        # Convert symbol to uppercase before accessing market data
        symbol = symbol.upper()
        market_data = await get_market_data(symbol)
        if not market_data:
            raise HTTPException(status_code=404, detail=f"No market data found for {symbol}")

        quote = market_data['data'][symbol]['quote']['USD']
        return {
            "price": quote['price'],
            "change24h": quote['percent_change_24h'],
            "volume": quote['volume_24h'],
            "marketcap": quote['market_cap']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analysis/{symbol}")
@cache(
    expire=300,  # Cache results for 5 minutes
    key_builder=cache_key_builder
)
async def get_crypto_analysis(
    symbol: str,
    provider: str = "openai",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get AI agent analysis for a specific cryptocurrency."""
    try:
        # Use current date range if not specified
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        # Validate provider
        if provider not in ["openai", "anthropic"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid provider: {provider}. Supported providers are: openai, anthropic"
            )

        # Create provider instance
        crypto_provider = CryptoMarketProvider()

        try:
            # Concurrent fetching of market and price data
            market_data_task = asyncio.create_task(crypto_provider.get_market_data(symbol))
            price_data_task = asyncio.create_task(crypto_provider.get_historical_prices(symbol, start_date, end_date))
            
            market_data, price_data = await asyncio.gather(market_data_task, price_data_task)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch market or price data: {str(e)}")

        try:
            # Run agents concurrently for both providers
            symbol = symbol.upper()
            
            agent_tasks = []
            agent_functions = {
                "market_data_agent": partial(analyze_market, agent_type="market"),
                "sentiment_agent": partial(analyze_market, agent_type="sentiment"),
                "technical_agent": partial(analyze_market, agent_type="technical"),
                "risk_management_agent": partial(analyze_market, agent_type="risk"),
                "portfolio_agent": partial(analyze_market, agent_type="portfolio")
            }
            
            for agent_name, agent_func in agent_functions.items():
                task = asyncio.create_task(agent_func(
                    symbol=symbol,  # Now using normalized symbol
                    market_data=market_data,
                    price_data=price_data,
                    show_reasoning=True,
                    provider_map=provider
                ))
                agent_tasks.append((agent_name, task))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create agent tasks: {str(e)}")

        try:
            # Wait for all agent tasks to complete
            analysis_results = {}
            for agent_name, task in agent_tasks:
                try:
                    result = await task
                    logging.info(f"Agent {agent_name} completed successfully")
                    analysis_results[agent_name] = result[agent_name]
                except TypeError as te:
                    logging.error(f"Type error in {agent_name}: {str(te)}")
                    logging.error(f"Result that caused error: {result}")
                    raise HTTPException(
                        status_code=500, 
                        detail=f"Type error in {agent_name}: {str(te)}. This might be due to unhashable dictionary values."
                    )
                except Exception as e:
                    logging.error(f"Error in {agent_name}: {str(e)}", exc_info=True)
                    raise HTTPException(status_code=500, detail=f"Failed during {agent_name} analysis: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed during agent analysis: {str(e)}")

        # Format results for frontend
        agents = [
            {"title": "Market Data Agent", "content": analysis_results["market_data_agent"]},
            {"title": "Sentiment Agent", "content": analysis_results["sentiment_agent"]},
            {"title": "Technical Agent", "content": analysis_results["technical_agent"]},
            {"title": "Risk Agent", "content": analysis_results["risk_management_agent"]},
            {"title": "Portfolio Agent", "content": analysis_results["portfolio_agent"]}
        ]

        return {"agents": agents}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error during analysis: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
