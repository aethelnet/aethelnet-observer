"""
Binance Market Info Service: Caching Exchange Requirements

Caches Binance exchange information including minimum notional values per symbol
to avoid repeated API calls and enable smart resource management.
"""

import logging
import time
from typing import Dict, Optional
from functools import lru_cache

logger = logging.getLogger("BinanceMarketInfo")

class BinanceMarketInfo:
    """
    Singleton service to cache Binance exchange information.
    
    Provides minimum notional values per symbol to enable smart resource allocation.
    """
    _instance: Optional['BinanceMarketInfo'] = None
    _cache: Dict[str, Dict] = {}
    _cache_time: Dict[str, float] = {}
    _cache_ttl: float = 3600.0  # Cache for 1 hour
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BinanceMarketInfo, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        logger.info("[BinanceMarketInfo] Service initialized")
    
    async def get_min_notional(self, symbol: str, broker=None) -> float:
        """
        Get minimum notional value for a symbol from Binance.
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            broker: Optional BinanceBroker instance (if available)
        
        Returns:
            Minimum notional value in quote currency (default: 10.0 if unavailable)
        """
        symbol_upper = symbol.upper()
        
        # Check cache first
        if symbol_upper in self._cache:
            cache_time = self._cache_time.get(symbol_upper, 0)
            if time.time() - cache_time < self._cache_ttl:
                min_notional = self._cache[symbol_upper].get('min_notional', 10.0)
                logger.debug(f"[BinanceMarketInfo] Cache hit for {symbol_upper}: {min_notional}")
                return float(min_notional)
        
        # Try to fetch from broker if provided
        if broker:
            try:
                min_notional = await self._fetch_from_broker(symbol_upper, broker)
                if min_notional:
                    self._cache[symbol_upper] = {'min_notional': min_notional}
                    self._cache_time[symbol_upper] = time.time()
                    return float(min_notional)
            except Exception as e:
                logger.debug(f"[BinanceMarketInfo] Failed to fetch from broker for {symbol_upper}: {e}")
        
        # Try to fetch from router (gets broker automatically)
        try:
            min_notional = await self._fetch_from_router(symbol_upper)
            if min_notional:
                self._cache[symbol_upper] = {'min_notional': min_notional}
                self._cache_time[symbol_upper] = time.time()
                return float(min_notional)
        except Exception as e:
            logger.debug(f"[BinanceMarketInfo] Failed to fetch from router for {symbol_upper}: {e}")
        
        # Safe default: 10.0 USD/EUR (conservative estimate)
        logger.warning(f"[BinanceMarketInfo] Using default min_notional (10.0) for {symbol_upper}")
        return 10.0
    
    async def _fetch_from_broker(self, symbol: str, broker) -> Optional[float]:
        """Fetch min notional from a BinanceBroker instance."""
        try:
            if not hasattr(broker, 'client'):
                return None
            
            # Ensure markets are loaded
            if not broker.client.markets:
                await broker.client.load_markets()
            
            # Get market info
            market = broker.client.market(symbol)
            if not market:
                return None
            
            # Extract min notional from limits
            limits = market.get('limits', {})
            cost_limits = limits.get('cost', {})
            min_notional = cost_limits.get('min')
            
            if min_notional:
                logger.info(f"[BinanceMarketInfo] Fetched min_notional for {symbol}: {min_notional}")
                return float(min_notional)
            
            # Fallback: check filters (Binance-specific)
            filters = market.get('info', {}).get('filters', [])
            for f in filters:
                if f.get('filterType') == 'MIN_NOTIONAL':
                    min_notional = float(f.get('minNotional', 10.0))
                    logger.info(f"[BinanceMarketInfo] Fetched min_notional from filter for {symbol}: {min_notional}")
                    return min_notional
            
            return None
            
        except Exception as e:
            logger.debug(f"[BinanceMarketInfo] Error fetching from broker: {e}")
            return None
    
    async def _fetch_from_router(self, symbol: str) -> Optional[float]:
        """Fetch min notional by routing through OmniRouter."""
        try:
            from brokers.router import OmniRouter
            
            router = OmniRouter()
            broker = router._route(symbol)
            
            if broker:
                return await self._fetch_from_broker(symbol, broker)
            
            return None
            
        except Exception as e:
            logger.debug(f"[BinanceMarketInfo] Error fetching from router: {e}")
            return None
    
    def clear_cache(self, symbol: Optional[str] = None):
        """Clear cache for a specific symbol or all symbols."""
        if symbol:
            symbol_upper = symbol.upper()
            if symbol_upper in self._cache:
                del self._cache[symbol_upper]
                del self._cache_time[symbol_upper]
                logger.debug(f"[BinanceMarketInfo] Cleared cache for {symbol_upper}")
        else:
            self._cache.clear()
            self._cache_time.clear()
            logger.debug("[BinanceMarketInfo] Cleared all cache")
    
    def get_cached_min_notional(self, symbol: str) -> Optional[float]:
        """Get cached min notional without fetching (returns None if not cached)."""
        symbol_upper = symbol.upper()
        if symbol_upper in self._cache:
            cache_time = self._cache_time.get(symbol_upper, 0)
            if time.time() - cache_time < self._cache_ttl:
                return float(self._cache[symbol_upper].get('min_notional', 10.0))
        return None

# Singleton instance
_market_info_instance: Optional[BinanceMarketInfo] = None

def get_binance_market_info() -> BinanceMarketInfo:
    """Get or create the singleton BinanceMarketInfo instance."""
    global _market_info_instance
    if _market_info_instance is None:
        _market_info_instance = BinanceMarketInfo()
    return _market_info_instance

