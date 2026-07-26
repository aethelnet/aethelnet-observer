import logging
import asyncio
import ccxt.async_support as ccxt
from typing import Dict, Any, Optional
import re

logger = logging.getLogger("CCXTBroker")

class CCXTBroker:
    """
    Universal Crypto Adapter (Phase 21).
    Powered by CCXT (Async).
    """
    def __init__(self, exchange_id: str, api_key: str = None, secret: str = None, sandbox: bool = False):
        self.exchange_id = exchange_id
        self.exchange = None
        
        try:
            exchange_class = getattr(ccxt, exchange_id)
            config = {
                'apiKey': api_key,
                'secret': secret,
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'}
            }
            
            # Add testnet URLs for Binance
            if exchange_id == 'binance' and sandbox:
                config['sandbox'] = True
                config['urls'] = {
                    'api': {
                        'public': 'https://testnet.binance.vision/api/v3',
                        'private': 'https://testnet.binance.vision/api/v3',
                    },
                    'test': {
                        'public': 'https://testnet.binance.vision/api/v3',
                        'private': 'https://testnet.binance.vision/api/v3',
                    }
                }
            
            self.exchange = exchange_class(config)
            
            if sandbox:
                self.exchange.set_sandbox_mode(True)
                logger.info(f"[CCXT] ⏳ Sandbox Mode Enabled for {exchange_id}")
                
        except Exception as e:
            logger.critical(f"[CCXT] ❌ Failed to initialize {exchange_id}: {e}")

    async def close(self):
        if self.exchange:
            await self.exchange.close()

    async def fetch_balance(self) -> Dict[str, float]:
        if not self.exchange: return {}
        try:
            balance = await self.exchange.fetch_balance()
            # Normalize to simple dict {ASSET: FREE}
            total = balance.get('total', {})
            return total
        except Exception as e:
            logger.error(f"[CCXT] Balance Fetch Error: {e}")
            return {}

    async def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        if not self.exchange: return {}
        try:
            ticker = await self.exchange.fetch_ticker(symbol)
            return ticker
        except Exception as e:
            logger.error(f"[CCXT] Ticker Fetch Error: {e}")
            return {}

    def _normalize_symbol(self, symbol: str) -> str:
        """
        Convert internal symbol format (BTCUSDT) to CCXT format (BTC/USDT)
        """
        if "/" in symbol:
            return symbol  # Already in CCXT format
            
        # Common quote currencies in order of preference
        quote_currencies = ['USDT', 'USDC', 'BUSD', 'BTC', 'ETH', 'BNB']
        
        for quote in quote_currencies:
            if symbol.endswith(quote):
                base = symbol[:-len(quote)]
                return f"{base}/{quote}"
        
        # Fallback: assume USDT
        if len(symbol) > 3:
            base = symbol[:-4] if len(symbol) > 6 else symbol[:3]
            quote = symbol[-4:] if len(symbol) > 6 else 'USDT'
            return f"{base}/{quote}"
            
        return symbol

    async def create_order(self, symbol: str, type: str, side: str, amount: float, price: float = None):
        """
        Executes a Trade.
        type: 'limit' or 'market'
        side: 'buy' or 'sell'
        """
        if not self.exchange: 
            logger.error("[CCXT] ❌ Exchange not initialized")
            return None
        
        try:
            # Convert symbol format
            ccxt_symbol = self._normalize_symbol(symbol.upper())
            
            logger.info(f"[CCXT] 🚀 Executing {side.upper()} {type.upper()} {amount} {ccxt_symbol} @ {price}")
            
            # Validate inputs
            if amount <= 0:
                logger.error(f"[CCXT] ❌ Invalid amount: {amount}")
                return None
                
            if type == 'limit' and (price is None or price <= 0):
                logger.error(f"[CCXT] ❌ Invalid price for limit order: {price}")
                return None
            
            response = await self.exchange.create_order(ccxt_symbol, type, side, amount, price)
            logger.info(f"[CCXT] ✅ Order Success: {response.get('id')} | Status: {response.get('status')}")
            return response
            
        except Exception as e:
            logger.critical(f"[CCXT] ❌ Order Failed: {e}")
            return None
