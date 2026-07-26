import logging
import ccxt.async_support as ccxt
from brokers.base import BaseBroker
from typing import Dict, Any, Optional

logger = logging.getLogger("AlpacaBroker")

class AlpacaBroker(BaseBroker):
    """
    Execution adapter for Alpaca (stocks/ETFs) via CCXT.

    Purpose:
    - Provide a minimal, consistent broker interface for stock trading similar to crypto brokers.
    - Return balances/positions in a shape compatible with OmniRouter and higher-level services.
    - Keep failure handling non-fatal for the caller (return 0.0 / None on missing data).
    """
    def __init__(self, api_key: str, secret_key: str, paper: Optional[bool] = None):
        # Alpaca requires 'paper' hostname for simulation endpoint
        from config.settings import get_settings
        settings = get_settings()
        
        # Priority: 1. Constructor arg, 2. Settings, 3. True (Default)
        is_paper = paper if paper is not None else getattr(settings, "ALPACA_PAPER", True)
        
        # SANITIZE KEYS (Handle SecretStr from Pydantic)
        _key = api_key.get_secret_value() if hasattr(api_key, "get_secret_value") else str(api_key)
        _secret = secret_key.get_secret_value() if hasattr(secret_key, "get_secret_value") else str(secret_key)
        
        config = {
            'apiKey': _key,
            'secret': _secret,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',
                'fetchBalance': {
                    'params': {
                        'asset_class': 'us_equity'  # CRITICAL: Prevent 403 by avoiding crypto probing
                    }
                }
            }
        }
        if is_paper:
            config['hostname'] = 'paper-api.alpaca.markets'
            
        self.client = ccxt.alpaca(config)
        # Disable automatic market loading for crypto to avoid 401/403 on startup
        self.client.options['fetchMarkets'] = ['us_equity']
        self.client.options['fetchBalance'] = {'params': {'asset_class': 'us_equity'}}
        
        self.is_paper = is_paper # Persist state for raw calls
        logger.info(f"[BROKER] Alpaca Connector Initialized (STOCKS ONLY) | Mode: {'PAPER' if is_paper else 'LIVE'}")

    async def get_balance(self, asset: str) -> float:
        try:
            # Force asset_class to avoid crypto probing
            balance = await self.client.fetch_balance({'asset_class': 'us_equity'})
            info = balance.get('info', []) # Alpaca returns list for /account or dict for unified? CCXT varies.
            
            # If info is a list (standard Alpaca /account), it's likely empty or handled differently
            if isinstance(info, list) and len(info) > 0:
                info = info[0]
            elif not isinstance(info, dict):
                info = {}

            # For USD, return CASH (not equity) so wallet shows available trading capital.
            if asset == 'USD':
                return float(info.get('cash', 0.0))
            
            bal = balance.get(asset, {})
            return bal.get('total', bal.get('free', 0.0))
        except Exception as e:
            logger.error(f"[BROKER] Alpaca Balance Error: {e}")
            return 0.0

    async def get_position(self, symbol: str) -> float:
        try:
            # CCXT unify
            positions = await self.client.fetch_positions([symbol])
            if positions:
                return float(positions[0]['info'].get('qty', 0.0))
            return 0.0
        except Exception as e:
            # Symbol might not be found if no position
            return 0.0

    async def _raw_submit_order(self, symbol: str, side: str, qty: float, order_type: str = "market", time_in_force: str = "day") -> Any:
        """
        Fallback: Submits order directly to Alpaca API via aiohttp, bypassing CCXT validation.
        Used when CCXT filters out tradeable assets (broken market cache).
        """
        try:
            import aiohttp
            from config.settings import get_settings
            settings = get_settings()
            
            # Determine URL
            # Determine URL
            # USE INSTANCE STATE (Correct)
            is_paper = getattr(self, "is_paper", getattr(settings, "ALPACA_PAPER", True))
            base_url = "https://paper-api.alpaca.markets" if is_paper else "https://api.alpaca.markets"
            endpoint = f"{base_url}/v2/orders"
            
            key_id = self.client.apiKey
            secret = self.client.secret
            
            # DIAGNOSTIC: Check Key Type vs Endpoint
            if key_id:
                is_paper_key = key_id.startswith("PK")
                if is_paper and not is_paper_key:
                     logger.critical(f"[BROKER] [CRITICAL] CONFIG MISMATCH: Paper Mode enabled but Key ({key_id[:4]}...) does NOT start with PK!")
                elif not is_paper and is_paper_key:
                     logger.critical(f"[BROKER] [CRITICAL] CONFIG MISMATCH: Live Mode enabled but Key ({key_id[:4]}...) looks like a Paper Key!")

            # Headers
            headers = {
                "APCA-API-KEY-ID": key_id,
                "APCA-API-SECRET-KEY": secret,
                "Content-Type": "application/json"
            }
            
            # Payload
            payload = {
                "symbol": symbol,
                "qty": str(qty), # Send as string to preserve precision
                "side": side.lower(),
                "type": order_type.lower(),
                "time_in_force": time_in_force.lower()
            }
            
            logger.info(f"[BROKER] [EXECUTION] RAW FALLBACK: Sending {side} {qty} {symbol} to {endpoint} (Key: {key_id[:4]}...)")
            
            async with aiohttp.ClientSession() as session:
                # [STATIC IP UPGRADE] Removed proxy=settings.EGRESS_PROXY_URL
                async with session.post(endpoint, json=payload, headers=headers) as resp:
                    if resp.status == 200 or resp.status == 201:
                        data = await resp.json()
                        logger.info(f"[BROKER] RAW FILLED: {data['id']}")
                        return data
                    else:
                        text = await resp.text()
                        logger.critical(f"[BROKER] RAW EXECUTION FAILED ({resp.status}): {text} | KeyPrefix: {key_id[:4] if key_id else 'None'}")
                        return None
                        
        except Exception as e:
             logger.critical(f"[BROKER] RAW EXCEPTION: {e}")
             return None

    async def place_order(self, symbol: str, side: str, order_type: str, quantity: float, price: float = None, params: Dict = {}) -> Any:
        target_symbol = symbol
        try:
            # MAP GLOBAL ASSETS TO ALPA-COMPATIBLE ETFs
            from config.settings import get_settings
            settings = get_settings()
            mapping = getattr(settings, 'ALPACA_SYMBOL_MAP', {})
            
            if symbol in mapping:
                target_symbol = mapping[symbol]
                logger.info(f"[BROKER] [INFO] MAPPED {symbol} -> {target_symbol} for Alpaca Execution")
            
            logger.info(f"[BROKER] [EXECUTION] WALL ST: {side} {quantity} {target_symbol}")
            # Alpaca expects specific params sometimes, but CCXT handles mapping.
            # create_order signature: (symbol, type, side, amount, price=None, params={})
            order = await self.client.create_order(target_symbol, order_type, side, quantity, price, params)
            logger.info(f"[BROKER] FILLED: {order['id']}")
            return order
        except Exception as e:
            error_msg = str(e).lower()
            # If CCXT says "market symbol not found", but we suspect it exists -> TRY RAW
            # Also catch "asset_class" errors (likely CCXT checking crypto on stock account)
            if "does not have market symbol" in error_msg or "symbol not found" in error_msg or "asset_class" in error_msg:
                 logger.warning(f"[BROKER] CCXT Glitch Detected ({error_msg[:50]}...). Attempting Raw API Override for {target_symbol}...")
                 return await self._raw_submit_order(target_symbol, side, quantity, order_type)
            
            logger.critical(f"[BROKER] ALPACA EXECUTION FAILED: {e}")
            return None

    async def cancel_all_orders(self, symbol: str) -> bool:
        try:
            await self.client.cancel_all_orders(symbol)
            return True
        except Exception as e:
            logger.error(f"[BROKER] Alpaca Cancel Error: {e}")
            return False

    async def get_all_positions(self) -> list:
        """
        Returns all open positions from Alpaca via Raw API (CCXT missing fetchPositions).
        Format: [{'symbol': 'NFLX', 'qty': 1.0, 'current_price': 100.0, ...}, ...]
        """
        try:
            # CCXT 'fetch_positions' often fails on Alpaca.
            # Use Direct API call.
            import aiohttp
            from config.settings import get_settings
            settings = get_settings()
            
            # USE INSTANCE STATE (Correct)
            is_paper = getattr(self, "is_paper", getattr(settings, "ALPACA_PAPER", True))
            base_url = "https://paper-api.alpaca.markets" if is_paper else "https://api.alpaca.markets"
            endpoint = f"{base_url}/v2/positions"
            
            headers = {
                "APCA-API-KEY-ID": self.client.apiKey,
                "APCA-API-SECRET-KEY": self.client.secret,
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                # [STATIC IP UPGRADE] Removed proxy=settings.EGRESS_PROXY_URL
                async with session.get(endpoint, headers=headers) as resp:
                    if resp.status == 200:
                        positions = await resp.json()
                        clean_positions = []
                        for p in positions:
                            clean_positions.append({
                                'symbol': p['symbol'],
                                'qty': float(p['qty']),
                                'current_price': float(p['current_price']),
                                'entry_price': float(p['avg_entry_price']),
                                'side': p['side'], # 'long' or 'short'
                                'unrealized_pnl': float(p['unrealized_pl'])
                            })
                        return clean_positions
                    else:
                        logger.error(f"[BROKER] Alpaca Positions Fetch Failed ({resp.status}): {await resp.text()}")
                        return []

        except Exception as e:
            logger.error(f"[BROKER] Alpaca Batch Position Error: {e}")
            return []

    async def close(self):
        await self.client.close()
