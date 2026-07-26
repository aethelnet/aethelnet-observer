import logging
import asyncio
import ccxt.async_support as ccxt
from brokers.base import BaseBroker
from typing import Dict, Any

logger = logging.getLogger("BinanceBroker")

class BinanceBroker(BaseBroker):
    """
    Execution adapter for Binance (Spot / Futures / Margin).

    Provides a thin, defensive wrapper over CCXT's Binance client with:
    - Mode detection (spot/future/margin) and optional forced mode.
    - Safety seals (leverage/margin mode enforcement for futures).
    - Quantity/price sanitization using exchange precision helpers.
    - Specific CCXT exception handling to categorize and persist last error for diagnostics.
    - Best-effort compat shims for different CCXT/client versions.

    This class aims to expose a consistent async broker API for the OmniRouter while
    surfacing actionable logs on failure.
    """
    def __init__(self, api_key: str, secret_key: str, auto_detect: bool = True, force_mode: str = None):
        from config import get_settings
        settings = get_settings()
        
        self.api_key = api_key
        self.secret_key = secret_key
        
        # Default from Settings or Force Mode
        initial_mode = 'spot'
        if force_mode:
            initial_mode = force_mode.lower()
            auto_detect = False # disable auto-detect if forced
        elif settings.TRADING_MODE.upper() == 'FUTURES':
            initial_mode = 'future'
        elif settings.TRADING_MODE.upper() == 'MARGIN':
            initial_mode = 'margin'

        # Configure client base settings
        client_config = {
            'apiKey': api_key,
            'secret': secret_key,
            'enableRateLimit': True,
            'options': {
                'defaultType': initial_mode,
                'adjustForTimeDifference': True, # Automatically sync clock (Phase 13 Fix)
            } 
        }
        
        # Add testnet configuration if BINANCE_TESTNET is enabled
        if settings.BINANCE_TESTNET:
            client_config['sandbox'] = True
            client_config['urls'] = {
                'api': {
                    'public': 'https://testnet.binance.vision/api/v3',
                    'private': 'https://testnet.binance.vision/api/v3',
                },
                'test': {
                    'public': 'https://testnet.binance.vision/api/v3',
                    'private': 'https://testnet.binance.vision/api/v3',
                }
            }
            logger.info("[BROKER] 🧪 Testnet mode enabled - using testnet.binance.vision")
        
        # Inject Proxy for stable IP (Oracle Gateway)
        if settings.EGRESS_PROXY_URL:
            logger.info(f"[BROKER] 🛡️ Routing through Execution Gateway: {settings.EGRESS_PROXY_URL}")
            client_config['proxies'] = {
                'http': settings.EGRESS_PROXY_URL,
                'https': settings.EGRESS_PROXY_URL,
            }

        # --- SOVEREIGN UPGRADE: Inert Constructor ---
        self.auto_detect = auto_detect
        self.force_mode = force_mode
        self.initial_mode = initial_mode
        self.client_config = client_config
        self.client = None
        self.mode = initial_mode
        self._last_error = None
        logger.info(f"[BROKER] Binance Connector Created (Mode: {initial_mode.upper()}). Call connect() to hydrate.")

    async def connect(self):
        """
        Async entry point for Binance initialization.
        Handles auto-discovery and network-sensitive client setup.
        """
        logger.info("[BROKER] Binance: Connecting to Exchange...")
        try:
            # 1. AUTO-DISCOVERY (Network Probe)
            if self.auto_detect:
                try:
                    # Run the synchronous probe in a thread to keep the event loop alive
                    detected_mode = await asyncio.to_thread(self._probe_permissions)
                    logger.info(f"[BROKER] ✅ Auto-Discovery Success! Mode: {detected_mode.upper()}")
                    self.mode = detected_mode
                    self.client_config['options']['defaultType'] = detected_mode
                except Exception as e:
                    logger.warning(f"[BROKER] ⚠️ Auto-Discovery Failed ({e}). Falling back to: {self.mode.upper()}")

            # 2. Instantiate CCXT Client
            import ccxt.async_support as ccxt_async
            self.client = ccxt_async.binance(self.client_config)
            
            logger.info(f"[BROKER] 🟢 Binance Connection Ready ({self.mode.upper()}).")
            return True
        except Exception as e:
            logger.error(f"[BROKER] Binance Connection Critical Failure: {e}")
            return False

    def _probe_permissions(self) -> str:
        """
        Probes the API Key to see if it allows Futures or Spot.
        Returns 'future' or 'spot'.
        
        Uses raw HMAC-signed REST requests instead of a CCXT client to avoid
        any possible coroutine leakage (RuntimeWarning: coroutine never awaited).
        """
        import hashlib
        import hmac
        import time
        import requests as _req
        from config import get_settings
        settings = get_settings()

        proxies = {}
        if settings.EGRESS_PROXY_URL:
            proxies = {
                'http': settings.EGRESS_PROXY_URL,
                'https': settings.EGRESS_PROXY_URL,
            }

        def _signed_get(base_url: str, path: str) -> int:
            """Returns HTTP status code for a signed weight-1 balance check."""
            ts = int(time.time() * 1000)
            query = f"timestamp={ts}"
            sig = hmac.new(self.secret_key.encode(), query.encode(), hashlib.sha256).hexdigest()
            url = f"{base_url}{path}?{query}&signature={sig}"
            try:
                resp = _req.get(
                    url,
                    headers={"X-MBX-APIKEY": self.api_key},
                    timeout=5,
                    proxies=proxies,
                )
                return resp.status_code
            except Exception:
                return 0

        # 1. Try Futures (USD-M)
        try:
            code = _signed_get("https://fapi.binance.com", "/fapi/v2/account")
            if code == 200:
                return 'future'
        except Exception:
            pass

        # 2. Try Spot
        try:
            code = _signed_get("https://api.binance.com", "/api/v3/account")
            if code == 200:
                return 'spot'
        except Exception:
            pass

        raise Exception("Invalid API Key (Neither Futures nor Spot responded with 200)")


    async def get_balance(self, asset: str) -> float:
        try:
            balance = await self.client.fetch_balance()
            return balance.get(asset, {}).get('free', 0.0)
        except Exception as e:
            error_str = str(e)
            if "-2015" in error_str:
                logger.warning("[BROKER] 🛑 Legacy Binance Spot API Permission Error (-2015) - Consider disabling BINANCE_API_KEY if not in use.")
                # Muted: Not an action required if user is on Hyperliquid
                # return 0.0 to let it sail past gracefully
            elif "-1021" in error_str:
                logger.warning("[SYSTEM] ⏳ Timestamp Drift Detected. Syncing Clock...")
            else:
                logger.error(f"[BROKER] Binance Balance Error: {e}")
            return 0.0

    async def get_all_balances(self) -> Dict[str, Dict[str, float]]:
        """
        Returns ALL assets with > 0 balance.
        Format: {'EUR': {'free': 50.0, 'locked': 0.0}, 'BTC': ...}
        """
        try:
            # fetch_balance returns a huge dict. We need to parse 'total' or 'free'/'locked'.
            # CCXT structure: {'free': {'BTC': 0.1, ...}, 'locked': {...}, 'total': {...}, 'info': {...}}
            full_bals = await self.client.fetch_balance()
            
            # PROBE: Print Raw Data
            logger.info(f"[PROBE] RAW WALLET DUMP: {full_bals.get('total', 'NO_TOTAL_KEY')}")
            
            result = {}
            # Iterate over 'total' to find non-zero assets
            if 'total' in full_bals:
                for asset, total_amount in full_bals['total'].items():
                    # Relaxed Filter: Show anything > 0.0 (even tiny amounts)
                    if total_amount > 0.0:
                        free = full_bals.get('free', {}).get(asset, 0.0)
                        locked = full_bals.get('locked', {}).get(asset, 0.0)
                        result[asset] = {'free': float(free), 'locked': float(locked)}
                        
            logger.info(f"[PROBE] Filtered Result: {result}")
            return result
        except Exception as e:
            error_str = str(e)
            if "-2015" in error_str:
                logger.warning("[BROKER] 🛑 Legacy Binance Spot API Permission Error (-2015). Skipping full balance sync.")
                # Muted: Handled as non-fatal warning for decommissioned Spot keys
                return {}
            elif "-1021" in error_str:
                logger.warning("[SYSTEM] ⏳ Timestamp Drift Detected. Syncing Clock...")
            else:
                logger.error(f"[BROKER] Failed to fetch full balances: {e}")
            return {}

    async def get_funding_rate(self, symbol: str) -> float:
        """
        Fetches the current funding rate for a symbol (Futures only).
        Returns float (e.g. 0.0001 for 0.01%).
        """
        if self.mode != 'future':
            return 0.0
            
        try:
            # CCXT fetchFundingRate
            # symbol needs to be formatted? CCXT handles it usually if we passed it correctly.
            # We assume symbol is like "BTC/USDT" or "BTCUSDT" depending on how it was initialized.
            # Our system uses "BTCUSDT" mostly. CCXT might need "BTC/USDT".
            # However, self.client is initialized with options.
            
            # Try raw symbol first, if fail, try slash
            try:
                funding = await self.client.fetch_funding_rate(symbol)
            except:
                # Try adding slash
                if "USDT" in symbol and "/" not in symbol:
                    slash_sym = symbol.replace("USDT", "/USDT")
                    funding = await self.client.fetch_funding_rate(slash_sym)
                else:
                    return 0.0
            
            return float(funding.get('fundingRate', 0.0))
        except Exception as e:
            # logger.warning(f"[BROKER] Funding Rate Fetch Failed: {e}")
            return 0.0

    async def get_position(self, symbol: str) -> float:
        try:
            # SPOT MODE HANDLING
            if self.mode == 'spot':
                # Parse Base Asset (e.g. BTCUSDT -> BTC)
                base_asset = symbol.replace("USDT", "").replace("USDC", "").replace("BUSD", "")
                # Handle edge cases if needed, but for now standard pairs work
                bal = await self.client.fetch_balance()
                asset_bal = bal.get(base_asset, {})
                return float(asset_bal.get('free', 0.0)) + float(asset_bal.get('locked', 0.0))

            # FUTURES HANDLING
            positions = await self.client.fetch_positions([symbol])
            if positions:
                # CCXT usually returns a list
                return float(positions[0]['contracts']) 
            return 0.0
        except Exception as e:
            logger.error(f"[BROKER] Binance Position Error: {e}")
            return None # CRITICAL: Return None to signal "Uncertainty". Returning 0.0 causes Blind Buys.

    async def get_trades(self, symbol: str, limit: int = 5) -> list:
        """
        Fetch recent trades for a symbol.
        """
        try:
            # CCXT normalize
            trades = await self.client.fetch_my_trades(symbol, limit=limit)
            return trades
        except Exception as e:
            logger.warning(f"[Binance] Get Trades failed for {symbol}: {e}")
            return []



    async def _ensure_safety(self, symbol: str):
        """
        SAFETY SEAL: Enforces Isolated Margin and Low Leverage (3x) for Futures.
        """
        if self.mode != 'future':
            return
            
        # Check cache to avoid rate limit spam
        if not hasattr(self, '_safe_symbols'):
            self._safe_symbols = set()
            
        if symbol in self._safe_symbols:
            return

        try:
            # 1. Set Leverage (Safe Default: 3x)
            # This prevents accidental 20x/50x liquidation cascades
            try:
                await self.client.set_leverage(3, symbol)
                logger.info(f"[SAFETY] Leverage capped at 3x for {symbol}")
            except Exception as lev_err:
                # Often fails if already set, or if open orders exist.
                # proceed anyway, as Margin Mode is the critical one.
                logger.debug(f"[SAFETY] Leverage set skipped: {lev_err}")

            # 2. Set Margin Mode (ISOLATED)
            # This prevents Cross-Wallet Draining
            try:
                await self.client.set_margin_mode('ISOLATED', symbol)
                logger.info(f"[SAFETY] ISOLATED Margin enforced for {symbol}")
            except Exception as mm_err:
                # Code -4046: "No need to change margin type" -> Safe to ignore
                if "No need to change" not in str(mm_err):
                    logger.warning(f"[SAFETY] [WARN] Could not enforce ISOLATED Margin: {mm_err}")
                
            self._safe_symbols.add(symbol)
            
        except Exception as e:
            logger.error(f"[SAFETY] Failed to apply Safety Seal on {symbol}: {e}")
    
    async def get_margin_state(self) -> Dict[str, float]:
        """
        Query Binance margin state.
        
        For Futures mode: Returns actual margin utilization from account.
        For Spot mode: Returns simple balance (no margin concept).
        
        Returns:
            Dict with keys:
                - 'account_value': Total account equity
                - 'margin_used': Margin currently locked in positions
                - 'available_margin': Free margin for new positions  
                - 'utilization': Margin usage ratio (0.0 to 1.0)
        """
        try:
            if self.mode == 'future':
                # Futures: Query margin usage
                balance = await self.client.fetch_balance()
                info = balance.get('info', {})
                
                # Binance Futures structure
                total_wallet_balance = float(info.get('totalWalletBalance', 0.0))
                total_margin_balance = float(info.get('totalMarginBalance', 0.0))
                available_balance = float(info.get('availableBalance', 0.0))
                
                # Calculate margin used
                margin_used = total_margin_balance - available_balance
                
                # Calculate utilization
                utilization = (margin_used / total_wallet_balance) if total_wallet_balance > 0 else 0.0
                
                return {
                    'account_value': total_wallet_balance,
                    'margin_used': max(0.0, margin_used),
                    'available_margin': max(0.0, available_balance),
                    'utilization': utilization
                }
            else:
                # Spot/Margin mode: Just return free balance
                # No margin concept in spot trading
                balance = await self.get_balance('USDT')
                
                return {
                    'account_value': balance,
                    'margin_used': 0.0,
                    'available_margin': balance,
                    'utilization': 0.0
                }
                
        except Exception as e:
            logger.error(f"[Binance] Failed to get margin state: {e}")
            # Return safe defaults on error
            return {
                'account_value': 0.0,
                'margin_used': 0.0,
                'available_margin': 0.0,
                'utilization': 0.0
            }


    async def place_order(self, symbol: str, side: str, order_type: str, quantity: float, price: float = None, params: Dict = {}) -> Any:
        try:
            # 0. SAFETY SEAL (Futures Only)
            if self.mode == 'future':
                await self._ensure_safety(symbol)

            # [NEW] MARGIN AUTO-PILOT (The "Rat" Upgrade)
            if self.mode == 'margin':
                # This magic flag handles borrowing (for Shorts) and repaying (for Covers) automatically.
                if 'sideEffectType' not in params:
                    params['sideEffectType'] = 'AUTO_BORROW_REPAY'

            # 1. Ensure Markets Loaded (for Precision Info)
            if not self.client.markets:
                await self.client.load_markets()
            
            # 2. Sanitize Quantity (LOT_SIZE Filter)
            # This handles stepSize (e.g. 0.00001) and minQty
            # We use float(sanitized_qty) because create_order often prefers numeric types over strings 
            # while respecting the precision string CCXT provides.
            sanitized_qty = self.client.amount_to_precision(symbol, quantity)
            
            # [FIX] Force integer if precision is 0 decimals (amount precision == 1.0)
            market = self.client.market(symbol)
            if market['precision'].get('amount') == 1.0:
                sanitized_qty = str(int(float(sanitized_qty)))
            
            # Log the before/after for debugging
            logger.info(f"[BROKER] Sanitized {symbol} quantity: {quantity} -> {sanitized_qty}")
            
            # Sanitize Price if provided
            sanitized_price = price
            if price:
                sanitized_price = self.client.price_to_precision(symbol, price)

            # --- DEEP SANITIZATION (PHASE 9) ---
            # Manually sanitize prices inside params (stopPrice, takeProfitPrice)
            # CCXT does NOT auto-sanitize params.
            for key in ['stopPrice', 'takeProfitPrice', 'price']: 
                if key in params:
                    params[key] = self.client.price_to_precision(symbol, params[key])
 
            # Inject TimeInForce for Limit Orders if missing
            if order_type and isinstance(order_type, str) and order_type.upper() in ['LIMIT', 'STOP_LOSS_LIMIT', 'TAKE_PROFIT_LIMIT']:
                if 'timeInForce' not in params:
                     params['timeInForce'] = 'GTC' # Good Till Cancelled
            
            logger.info(f"[BROKER] [EXECUTION] {side} {sanitized_qty} {symbol} @ {price or 'MARKET'} (Raw: {quantity})")
            
            # 3. Execute
            # NOTE: Do NOT inject recvWindow into params — Binance Spot counts it as an extra
            # parameter and throws -1104. Clock drift is already handled by adjustForTimeDifference=True
            # in the client config (set at init time).
            # CCXT Signature: create_order(symbol, type, side, amount, price=None, params={})
            # PASS STRINGS TO PRESERVE PRECISION (Phase 11)
            order = await self.client.create_order(symbol, order_type, side, sanitized_qty, sanitized_price, params)
            logger.info(f"[BROKER] [SUCCESS] ORDER FILLED: {order['id']}")
            return order

        except ccxt.InsufficientFunds as e:
            error_msg = str(e)
            self._last_error = error_msg
            logger.error(f"[BROKER] [FAIL] INSUFFICIENT FUNDS: {error_msg} | symbol={symbol} | side={side} | required={quantity}")
            return None
        except ccxt.InvalidOrder as e:
            error_msg = str(e)
            self._last_error = error_msg
            logger.error(f"[BROKER] [FAIL] INVALID ORDER: {error_msg} | symbol={symbol} | side={side} | check symbol format/availability")
            return None
        except ccxt.NetworkError as e:
            error_msg = str(e)
            self._last_error = error_msg
            logger.error(f"[BROKER] [FAIL] NETWORK ERROR: {error_msg} | symbol={symbol} | side={side} | retrying may help")
            return None
        except ccxt.ExchangeError as e:
            error_msg = str(e)
            self._last_error = error_msg
            
            # [AUTO-FIX] LOT_SIZE / Filter Failure -> Reload Markets & Retry
            if ("-2010" in error_msg or "LOT_SIZE" in error_msg) and not params.get('_retried'):
                 logger.warning(f"[BROKER] [WARN] LOT_SIZE/Filter Error ({error_msg}). Reloading Markets & Retrying...")
                 try:
                     await self.client.load_markets(reload=True)
                     params['_retried'] = True
                     # Recursive Retry
                     return await self.place_order(symbol, side, order_type, quantity, price, params)
                 except Exception as retry_err:
                     logger.error(f"[BROKER] Retry Failed: {retry_err}")

            # Check for specific Binance error codes
            if "-2015" in error_msg:
                logger.critical(f"[BROKER] [CRITICAL] API PERMISSION ERROR (-2015): {error_msg} | symbol={symbol} | Check Binance API settings and IP whitelist")
            elif "-1013" in error_msg or "filter failure" in error_msg.lower():
                logger.error(f"[BROKER] [FAIL] ORDER FILTER FAILURE: {error_msg} | symbol={symbol} | check quantity/price precision")
            else:
                logger.critical(f"[BROKER] [FAIL] EXCHANGE ERROR: {error_msg} | symbol={symbol} | side={side} | qty={quantity}")
            return None
        except Exception as e:
            error_msg = str(e)
            self._last_error = error_msg
            logger.critical(f"[BROKER] [FAIL] UNEXPECTED ERROR: {type(e).__name__}: {error_msg} | symbol={symbol} | side={side} | qty={quantity}")
            return None

    async def cancel_all_orders(self, symbol: str) -> bool:
        try:
            await self.client.cancel_all_orders(symbol)
            return True
        except Exception as e:
            logger.error(f"[BROKER] Cancel Error: {e}")
            return False

    async def close(self):
        await self.client.close()
