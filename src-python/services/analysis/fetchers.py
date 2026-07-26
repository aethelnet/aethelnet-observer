
import logging
import aiohttp
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger("Analysis.Fetchers")

class DataFetcher:
    async def fetch_symbol_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch current price and 24h stats for any symbol from appropriate data source.
        Supports crypto (Binance), forex/stocks/commodities (Yahoo Finance), and CCXT exchanges.
        """
        try:
            from services.symbol_resolver import get_symbol_resolver
            resolver = get_symbol_resolver()
            
            symbol_upper = symbol.upper()
            symbol_type = resolver.detect_symbol_type(symbol_upper)
            data_source, normalized_symbol = resolver.get_data_source(symbol_upper)
            
            # Route to appropriate data source with fallbacks
            if data_source == 'binance':
                result = await self._fetch_from_binance(normalized_symbol)
                if result: return result
                return await self._fetch_from_yahoo(normalized_symbol, symbol_upper)
            elif data_source == 'yahoo':
                result = await self._fetch_from_yahoo(normalized_symbol, symbol_upper)
                if result: return result
                if symbol_upper == "XAUUSD":
                    result = await self._fetch_from_yahoo("XAUUSD=X", symbol_upper)
                    if result: return result
                    result = await self._fetch_from_yahoo("GC=F", symbol_upper)
                    if result: return result
                return None
            elif data_source == 'ccxt':
                return await self._fetch_from_ccxt(normalized_symbol, symbol_upper)
            else:
                # Fallback: try all sources
                result = await self._fetch_from_binance(normalized_symbol)
                if result: return result
                result = await self._fetch_from_yahoo(normalized_symbol, symbol_upper)
                if result: return result
                return await self._fetch_from_ccxt(normalized_symbol, symbol_upper)
        except Exception as e:
            logger.error(f"Fetch logic failed: {e}")
            return None
    
    async def _fetch_from_binance(self, symbol: str) -> Optional[Dict[str, Any]]:
        symbol_upper = symbol.upper()
        try:
            url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol_upper}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        data = await response.json()
                        price = float(data.get('lastPrice', 0))
                        volume = float(data.get('volume', 0))
                        change_24h = float(data.get('priceChangePercent', 0))
                        if price > 0:
                            return {
                                "symbol": symbol_upper, "price": price,
                                "volume": volume, "change_24h": change_24h,
                                "source": "binance_api"
                            }
        except Exception:
             pass
        # Fallback to historical (simplified for new module)
        try:
            from services.data_manager import get_data_manager
            dm = get_data_manager()
            historical = dm.get_data(symbol_upper, "1h", start=datetime.now() - timedelta(hours=24))
            if historical:
                latest = historical[-1]
                cols = [h['close'] for h in historical if 'close' in h]
                if cols:
                    current = latest.get('close', 0)
                    first = cols[0]
                    change = ((current - first)/first * 100) if first > 0 else 0
                    return {
                        "symbol": symbol_upper, "price": current,
                        "volume": sum(h.get('volume',0) for h in historical),
                        "change_24h": change, "source": "historical"
                    }
        except Exception:
            pass
        return None
    
    async def _fetch_from_yahoo(self, symbol: str, original_symbol: str) -> Optional[Dict[str, Any]]:
        try:
            from services.yahoo_connector import YahooConnector
            yahoo = YahooConnector()
            price = yahoo.get_latest_price(symbol)
            if price <= 0: return None
            
            end = datetime.now()
            start = end - timedelta(days=1)
            hist = yahoo.get_historical_klines(symbol, '1h', start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))
            
            change = 0.0
            vol = 0.0
            if hist and len(hist) >= 2:
                first = float(hist[0][4]) if len(hist[0]) > 4 else price
                last = float(hist[-1][4]) if len(hist[-1]) > 4 else price
                if first > 0: change = ((last - first)/first) * 100
                vol = sum(float(h[5]) for h in hist if len(h) > 5)
                
            return {
                "symbol": original_symbol.upper(), "price": price,
                "volume": vol, "change_24h": change, "source": "yahoo"
            }
        except Exception:
            return None

    async def _fetch_from_ccxt(self, symbol: str, original_symbol: str) -> Optional[Dict[str, Any]]:
        try:
            from services.watchtower import get_watchtower
            wt = get_watchtower()
            await wt.fetch_price(original_symbol)
            consensus = wt.consensus_price
            if consensus > 0:
                return {
                    "symbol": original_symbol.upper(), "price": consensus,
                    "volume": 0.0, "change_24h": 0.0, "source": "ccxt"
                }
        except Exception:
            pass
        return None
