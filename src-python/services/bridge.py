
import logging
import asyncio
import aiohttp
from typing import Dict

logger = logging.getLogger("AuraticBridge")

class BridgeScanner:
    """
    The Bridge (Phase 29).
    Scans for Arbitrage opportunities across chains.
    """
    def __init__(self):
        self.chains = {
            "ETHEREUM": "https://mainnet.infura.io/v3/YOUR_KEY",
            "SOLANA": "https://api.mainnet-beta.solana.com",
            "BINANCE_CEX": "https://api.binance.com"
        }
        self.prices = {}

    async def get_price_solana(self):
        """
        Fetches Real-Time SOL Price from Jupiter Aggregator (Solana DEX).
        """
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        try:
            url = "https://api.jup.ag/price/v2?ids=So11111111111111111111111111111111111111112"
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Jupiter v2 response format
                        return float(data['data']['So11111111111111111111111111111111111111112']['price'])
                    else:
                        logger.warning(f"[BRIDGE] Jupiter Returned: {response.status}")
        except Exception as e:
            logger.error(f"[BRIDGE] Jupiter API Failed: {e}")
        return 0.0

    async def get_price_binance(self, symbol="SOLUSDT"):
        """
        Fetches Real-Time SOL Price from Binance (CEX).
        """
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            url = f"https://api.binance.com/api/v3/avgPrice?symbol={symbol}"
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return float(data['price'])
                    else:
                        logger.warning(f"[BRIDGE] Binance Returned: {response.status}")
        except Exception as e:
            logger.error(f"[BRIDGE] Binance API Failed: {e}")
        return 0.0
        
    async def scan_arb(self, symbol="SOL"):
        """
        Checks CEX vs DEX prices in Real-Time.
        """
        try:
            # 1. Get CEX Price (Binance)
            cex_price = await self.get_price_binance(f"{symbol}USDT")
            
            # 2. Get DEX Price (Solana/Raydium via Jupiter)
            dex_price = await self.get_price_solana()
            
            if cex_price == 0 or dex_price == 0:
                return {"opportunity": False, "reason": "Data Missing"}
            
            # Calculate Spread
            spread = (dex_price - cex_price) / cex_price
            
            logger.info(f"[BRIDGE] 🌉 {symbol} SCAN | CEX: ${cex_price:.2f} | DEX: ${dex_price:.2f} | Spread: {spread*100:.3f}%")
            
            if abs(spread) > 0.005: # 0.5% Arb
                direction = "Buy CEX -> Sell DEX" if spread > 0 else "Buy DEX -> Sell CEX"
                logger.warning(f"[BRIDGE] 🚨 ARB OPPORTUNITY: {direction}")
                return {"opportunity": True, "spread": spread, "direction": direction}
                
            return {"opportunity": False, "spread": spread}
        except Exception as e:
            logger.error(f"[BRIDGE] Scan Failed: {e}")
            return {}

_bridge_instance = None
def get_bridge():
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = BridgeScanner()
    return _bridge_instance
