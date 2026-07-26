
import logging
import asyncio
import time
import math
from decimal import Decimal, Context, ROUND_HALF_UP
import requests.adapters
from typing import Dict, Any, List, Optional
from brokers.base import BaseBroker

# FORENSIC OPTIMIZATION: Increase global connection pool for parallel execution
# The default pool size of 10 is too small for our 51-symbol parallel engine.
_original_adapter_init = requests.adapters.HTTPAdapter.__init__
def _patched_adapter_init(self, *args, **kwargs):
    kwargs['pool_connections'] = kwargs.get('pool_connections', 50)
    kwargs['pool_maxsize'] = kwargs.get('pool_maxsize', 50)
    _original_adapter_init(self, *args, **kwargs)
requests.adapters.HTTPAdapter.__init__ = _patched_adapter_init

# [FAILSAFE] Global Timeout for all requests
_original_request = requests.Session.request
def _patched_request(self, method, url, **kwargs):
    if 'timeout' not in kwargs:
        kwargs['timeout'] = 15.0 # [STABILITY] 15s default for all HL SDK calls
    return _original_request(self, method, url, **kwargs)
requests.Session.request = _patched_request

logger = logging.getLogger("HyperliquidBroker")

# Conditional import to avoid crashing if dependencies aren't installed yet
try:
    from eth_account import Account
    from hyperliquid.info import Info
    from hyperliquid.exchange import Exchange
    from hyperliquid.utils import constants
    HAS_HYPERLIQUID = True
except ImportError:
    HAS_HYPERLIQUID = False

logger = logging.getLogger("HyperliquidBroker")

# Rate limiting configuration
RATE_LIMIT_DELAY = 0.5  # [FIX] 500ms between API calls (was 200ms)
CACHE_DURATION = {
    'user_state': 2.0,    # [FIX] 2.0s for health (was 0.5s)
    'meta': 600.0,        # 10 minutes for universe data
    'open_orders': 2.0,   # [FIX] 2.0s (was 0.5s)
    'l2_snapshot': 0.5    # [OPTIMIZATION] Reduced to 0.5s for fresh order book prices
}

# Rate limit error patterns
RATE_LIMIT_ERRORS = [
    '429',
    'too many requests',
    'rate limit',
    'exceeded',
    'throttled'
]

# Additional error patterns that need retry
RETRYABLE_ERRORS = [
    '422',  # JSON deserialization error
    'Failed to deserialize',
    'timeout',
    'connection',
    'network',
    'server error',
    'internal server error',
    '504',
    'gateway timeout'
]

class HyperliquidBroker(BaseBroker):
    """
    DeFi Adapter for Hyperliquid (On-Chain Perp DEX).
    
    Features:
    - No KYC, Region-Free.
    - Uses EVM Private Key for signing.
    - US Data Center (usually) but accessed via public API.
    """
    def __init__(self, private_key: str, check_permissions: bool = True):
        if not HAS_HYPERLIQUID:
            logger.error("[BROKER] ❌ Hyperliquid SDK not installed. Add 'hyperliquid-python-sdk' to requirements.")
            return

        from config import get_settings
        settings = get_settings()

        import threading

        # Initialize error tracking (for router error propagation)
        self._last_error = None
        
        # Rate limiting and caching
        self._lock = threading.RLock()
        self._last_api_call = 0
        self._cache = {}
        self._cache_timestamps = {}
        self._rate_limit_backoff = 0  # Dynamic backoff for rate limits
        self._consecutive_errors = 0
        self._startup_time_ms = int(time.time() * 1000)
        self._subscribed = False

        # Sanitize Key
        self._private_key = private_key
        if hasattr(private_key, "get_secret_value"):
             self._private_key = private_key.get_secret_value()
        
        try:
            self.account = Account.from_key(self._private_key)
            # [API AGENT UPGRADE] Support restricted API signers by mapping target address to the Main Wallet
            self.address = getattr(settings, "HYPERLIQUID_WALLET_ADDRESS", None) or self.account.address
            
            if self.address.lower() != self.account.address.lower():
                logger.info(f"[BROKER] 🕵️ Hyperliquid API Agent Active! Agent: {self.account.address[:6]}...{self.account.address[-4:]} | Main Wallet: {self.address[:6]}...{self.address[-4:]}")
            else:
                logger.info(f"[BROKER] Hyperliquid Wallet-Link: {self.address[:6]}...{self.address[-4:]}")
            
            # [SOVEREIGN UPGRADE] Constructor is now INERT.
            # SDK initialization is deferred to async connect() to prevent boot-time hangs.
            self.info = None
            self.exchange = None
            self._leverage_cache = {} # [OPTIMIZATION] Avoid redundant leverage updates
                
        except Exception as e:
            logger.error(f"[BROKER] Hyperliquid Init Failed: {e}")
            self._last_error = str(e)
            raise e

    async def connect(self):
        """
        Async entry point for SDK initialization.
        Ensures the "Silent Wall" (boot-time hang) is bypassed by running
        blocking network calls in a background thread.
        """
        logger.info("[BROKER] Hyperliquid: Connecting to L1...")
        try:
            # We run the synchronous _reinit_sdk in a thread to keep the event loop alive
            await asyncio.to_thread(self._reinit_sdk)
            if self.info and self.exchange:
                logger.info("[BROKER] 🟢 Hyperliquid Connection Established.")
                return True
            else:
                logger.warning("[BROKER] 🟡 Hyperliquid Connection Partial/Failed.")
                return False
        except Exception as e:
            logger.error(f"[BROKER] Hyperliquid Connection Critical Failure: {e}")
            return False

    def _reinit_sdk(self):
        """Force Re-initialization of SDK objects (Fixes Broken Pipe/Bad File Descriptor)."""
        try:
            from hyperliquid.info import Info
            from hyperliquid.exchange import Exchange
            from hyperliquid.utils import constants
            from config import get_settings
            settings = get_settings()
            
            # Clean up old websocket manager if it exists to prevent zombie listeners
            if hasattr(self, 'info') and self.info and hasattr(self.info, 'ws_manager'):
                try:
                    logger.info("[BROKER] Closing old Hyperliquid WebSocket manager...")
                    self.info.ws_manager.stop()
                    self._subscribed = False
                except Exception as e:
                    logger.warning(f"[BROKER] Error stopping old WebSocket: {e}")

            logger.info("[BROKER] Hyperliquid SDK: (Re)Initializing Connection Objects...")
            # [UPGRADE] Enabling WebSockets for real-time fill listening (The "Easy Way")
            base_url = constants.TESTNET_API_URL if settings.HYPERLIQUID_TESTNET else constants.MAINNET_API_URL
            logger.info(f"[BROKER] Hyperliquid Routing to: {base_url}")
            
            # [SOVEREIGN SHIELD] Retry loop — SDK fetches metadata on init and can crash
            # with 'list index out of range' if the API returns empty data.
            max_retries = 3
            for attempt in range(1, max_retries + 1):
                try:
                    logger.info(f"[BROKER] SDK Init attempt {attempt}/{max_retries}...")
                    self.info = Info(base_url, skip_ws=False)  # Allow WebSocket for fills
                    logger.info("[BROKER] Info object created successfully.")
                    self.exchange = Exchange(
                        self.account, 
                        base_url,
                        account_address=self.address
                    )
                    logger.info("[BROKER] Exchange object created successfully.")
                    break  # Success — exit retry loop
                except (IndexError, KeyError, TypeError) as sdk_err:
                    import traceback
                    logger.warning(f"[BROKER] SDK Init attempt {attempt} failed (transient): {sdk_err}\n{traceback.format_exc()}")
                    if attempt < max_retries:
                        import time as _time
                        _time.sleep(2)
                    else:
                        logger.error(f"[BROKER] SDK Init FAILED after {max_retries} attempts. Broker will be OFFLINE.")
                        self.info = None
                        self.exchange = None
                        return  # Don't raise — let the engine continue without HL
            
            # Connectivity Probe (non-fatal)
            self._check_connection()
            
            # Start User Fill Listener (Background SDK Thread)
            if not self._subscribed:
                try:
                    self.info.subscribe({"type": "userFills", "user": self.address}, self._handle_fill_event)
                    self._subscribed = True
                    logger.info(f"[BROKER] 👂 Hyperliquid Listener ACTIVE for {self.address[:6]}...")
                except Exception as sub_err:
                    logger.warning(f"[BROKER] Failed to subscribe to fills: {sub_err}")
            else:
                logger.debug("[BROKER] Hyperliquid fill listener already active; skipping redundant subscription.")
                
            logger.info("[BROKER] Hyperliquid SDK: Re-init Complete.")
        except Exception as e:
            logger.error(f"[BROKER] Hyperliquid Re-init Failed: {e}")
            raise e

    def _handle_fill_event(self, event: Dict[str, Any]):
        """
        Callback for Hyperliquid WebSocket fills.
        Updates the tracker in real-time.
        """
        try:
            # event is often a list or dict depending on SDK version
            fills = event if isinstance(event, list) else event.get('data', {}).get('fills', [])
            if not fills: return

            from services.tracker import get_performance_tracker
            tracker = get_performance_tracker()
            
            for fill in fills:
                # [BUGFIX] Ignore historical fills pushed during websocket connection
                fill_time = int(fill.get('time', 0))
                if fill_time > 0 and fill_time < self._startup_time_ms:
                    continue
                    
                coin = fill.get('coin')
                side = "BUY" if fill.get('side') == 'B' else "SELL"
                px = float(fill.get('px', 0))
                sz = float(fill.get('sz', 0))
                oid = fill.get('oid')
                
                logger.info(f"[LISTENER] ⚡ HL FILL DETECTED: {side} {sz} {coin} @ ${px:.4f} (OID: {oid})")
                
                # Update PerformanceTracker (This is the "Source of Truth" fix)
                # Standardize symbol
                symbol = f"{coin}USDC"
                
                # [REAL-TIME SYNC] Inject the fill into the tracker immediately
                if hasattr(tracker, 'update_from_fill'):
                    tracker.update_from_fill(symbol, side, px, sz, oid)
                else:
                    # Fallback: Trigger a background sync if the specialized method doesn't exist yet
                    # [REAL-TIME SYNC] ⚡ FILL DETECTED.
                    # Note: We are in an SDK background thread. 
                    # The main Tracker sync loop (running in the main asyncio thread) 
                    # will pick up this fill on the next tick.
                    pass
                
        except Exception as e:
            logger.error(f"[LISTENER] Error handling fill event: {e}")


    def _rate_limit(self):
        """Enforce rate limiting between API calls with dynamic backoff"""
        with self._lock:
            now = time.time()
            
            # Apply dynamic backoff if we've hit rate limits
            if self._rate_limit_backoff > 0:
                sleep_time = self._rate_limit_backoff
                logger.warning(f"[BROKER] Rate limit backoff: sleeping {sleep_time:.2f}s")
                time.sleep(sleep_time)
                self._rate_limit_backoff = 0  # Reset after backoff
                self._last_api_call = time.time()
                return
            
            # Normal rate limiting
            time_since_last = now - self._last_api_call
            if time_since_last < RATE_LIMIT_DELAY:
                sleep_time = RATE_LIMIT_DELAY - time_since_last
                time.sleep(sleep_time)
            self._last_api_call = time.time()

    def _is_retryable_error(self, error_str: str) -> bool:
        """Check if error indicates we should retry with backoff"""
        error_lower = error_str.lower()
        
        # Check for rate limit errors
        if any(pattern in error_lower for pattern in RATE_LIMIT_ERRORS):
            return True
            
        # Check for other retryable errors
        if any(pattern in error_lower for pattern in RETRYABLE_ERRORS):
            return True
            
        return False

    def _is_rate_limit_error(self, error_str: str) -> bool:
        """Check if error indicates rate limiting"""
        error_lower = error_str.lower()
        return any(pattern in error_lower for pattern in RATE_LIMIT_ERRORS)

    def _handle_retryable_error(self, error_str: str):
        """Handle retryable errors with exponential backoff"""
        self._consecutive_errors += 1
        
        # Exponential backoff: 1s, 2s, 4s, 8s, max 30s
        backoff = min(2 ** (self._consecutive_errors - 1), 30)
        self._rate_limit_backoff = backoff
        
        # Determine error type for logging
        if self._is_rate_limit_error(error_str):
            error_type = "Rate limit"
        elif '422' in error_str or 'deserialize' in error_str.lower():
            error_type = "JSON deserialization"
        else:
            error_type = "Retryable error"
            
        logger.error(f"[BROKER] {error_type} detected ({error_str}). Backing off {backoff}s (error #{self._consecutive_errors})")
        
        # Reset error count on successful call after backoff
        if self._consecutive_errors > 5:
            logger.warning("[BROKER] Multiple retryable errors - consider reducing API call frequency")

    def _get_cached(self, cache_key: str, fetch_func, cache_duration_key: str):
        """Get cached data or fetch if expired with rate limit handling"""
        now = time.time()
        
        # Fast path: unlocked cache check
        with self._lock:
            if cache_key in self._cache and cache_key in self._cache_timestamps:
                age = now - self._cache_timestamps[cache_key]
                if age < CACHE_DURATION[cache_duration_key]:
                    return self._cache[cache_key]
        
        # Slow path: fetch fresh data
        # We grab the lock to ensure we serialize network requests and rate limits
        with self._lock:
            # Double check inside the lock
            now = time.time()
            if cache_key in self._cache and cache_key in self._cache_timestamps:
                age = now - self._cache_timestamps[cache_key]
                if age < CACHE_DURATION[cache_duration_key]:
                    return self._cache[cache_key]

            # Rate limit before fetching
            self._rate_limit()
            
            # Fetch fresh data with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    data = fetch_func()
                    # Success - reset error counter
                    self._consecutive_errors = 0
                    self._cache[cache_key] = data
                    self._cache_timestamps[cache_key] = time.time()
                    return data
                except Exception as e:
                    error_str = str(e)
                    
                    # Check if it's a retryable error (rate limit, 422, etc.)
                    if self._is_retryable_error(error_str):
                        self._handle_retryable_error(error_str)
                        if attempt < max_retries - 1:
                            continue  # Retry after backoff
                
                # For non-retryable errors, return stale cache if available
                if cache_key in self._cache:
                    logger.warning(f"[BROKER] API failed, using stale cache for {cache_key}: {e}")
                    return self._cache[cache_key]
                
                # No cache available and last attempt failed
                if attempt == max_retries - 1:
                    raise Exception(error_str)
                
                # Brief delay before retry for non-retryable errors
                time.sleep(0.5 * (attempt + 1))
        
        # After loop: If we are here, all attempts failed
        # Final Fallback check: Return stale cache if available
        if cache_key in self._cache:
            logger.warning(f"[BROKER] Persistence Failure: All API retries exhausted for {cache_key}. Using STALE CACHE fallback.")
            return self._cache[cache_key]
            
        # Hard fail if no cache at all
        logger.error(f"[BROKER] Fatal API Error: Retries exhausted and no cache available for {cache_key}")
        raise last_error if 'last_error' in locals() else Exception("API Retries Exhausted")

    def _check_connection(self):
        """Verify connectivity by fetching user state."""
        try:
            state = self.info.user_state(self.address)
            logger.info(f"[BROKER] Hyperliquid Connected. Margin Summary: {state.get('marginSummary', 'N/A')}")
        except Exception as e:
            logger.warning(f"[BROKER] Hyperliquid Connect Probe Failed: {e}")

    async def get_balance(self, asset: str) -> float:
        """
        Returns 'withdrawable' (USDC) balance (Free Collateral).
        Hyperliquid uses USDC as collateral.
        """
        if asset in ["USD", "USDC", "USDT"]:
             return await self.get_withdrawable_cash()
        return 0.0

    async def get_withdrawable_cash(self) -> float:
        """
        Returns the free collateral available for withdrawal (Equity - Margin).
        """
        try:
            state = await self.get_margin_state()
            return state.get('available_margin', 0.0)
        except:
            return 0.0

    async def get_equity(self) -> float:
        """
        Returns the total account value (Net Equity = Cash + Unrealized PnL).
        """
        try:
            state = await self.get_margin_state()
            return state.get('account_value', 0.0)
        except:
            return 0.0

    async def get_position(self, symbol: str) -> float:
        """
        Get current position size for a coin (e.g. 'BTC', 'ETH').
        """
        try:
            # Consistent mapping via SymbolNormalizer
            clean_symbol = self._map_symbol_to_coin(symbol)

            # Get cached user state
            state = await asyncio.to_thread(
                self._get_cached, 
                f"user_state_{self.address}", 
                lambda: self.info.user_state(self.address),
                'user_state'
            )
            # 1. Check PERPS
            positions = state.get("assetPositions", [])
            for p in positions:
                pos = p.get("position", p) if isinstance(p, dict) else {}
                if pos.get("coin") == clean_symbol:
                    qty = float(pos.get("szi", 0.0))
                    if clean_symbol.startswith("k") and clean_symbol[1:].isalpha():
                        qty = qty * 1000.0
                    return qty
            
            # 2. Check SPOT
            # Note: Spot symbols in userState are usually the coin name (e.g. 'HYPE')
            # our clean_symbol should match.
            spot_balances = state.get("spotAssetBalances", [])
            for b in spot_balances:
                if b.get("coin") == clean_symbol:
                    # 'total' includes both available and locked in orders
                    return float(b.get("total", 0.0))
            
            return 0.0
        except Exception as e:
            logger.error(f"[BROKER] HL Position Error: {e}")
            return 0.0
            
    async def get_all_positions(self) -> list:
        """
        Get all open positions.
        """
        try:
            # Get cached user state
            user_state = await asyncio.to_thread(
                self._get_cached, 
                f"user_state_{self.address}", 
                lambda: self.info.user_state(self.address),
                'user_state'
            )
            
            # Extract Positions
            positions = []
            
            # 1. Fetch PERP Positions
            positions_data = user_state.get("assetPositions", [])
            from services.symbol_normalizer import get_symbol_normalizer
            sn = get_symbol_normalizer()
            
            for p in positions_data:
                # Robust extraction: Position might be flat or nested under 'position'
                pos_data = p.get('position', p) if isinstance(p, dict) else {}
                coin = pos_data.get('coin')
                qty = float(pos_data.get('szi', 0))
                
                if qty == 0: continue
                
                # Side
                side = "LONG" if qty > 0 else "SHORT"
                entry_px = float(pos_data.get('entryPx', 0))
                pnl = float(pos_data.get('unrealizedPnl', 0))
                
                # Standardize
                system_symbol = sn.to_system(coin)
                if not system_symbol: continue

                # UN-SCALE K-ASSET QUANTITY
                if coin.startswith("k") and coin[1:].isalpha():
                    qty = qty * 1000.0
                
                positions.append({
                    'symbol': system_symbol,
                    'side': side,
                    'qty': abs(qty),
                    'entry_price': entry_px,
                    'unrealized_pnl': pnl,
                    'current_price': 0 
                })
                
            # 2. Fetch SPOT Holdings
            spot_balances = user_state.get("spotAssetBalances", [])
            for b in spot_balances:
                coin = b.get('coin')
                # Skip USDC/USDT from positions list
                if coin in ["USDC", "USDT"]: continue
                
                qty = float(b.get('total', 0))
                if qty <= 0.0001: continue
                
                # Standardize to System Symbol
                system_symbol = sn.to_system(coin)
                
                positions.append({
                    'symbol': system_symbol,
                    'side': 'LONG', # Spot is always long
                    'qty': qty,
                    'entry_price': 0, 
                    'unrealized_pnl': 0,
                    'current_price': 0
                })
                
            return positions
            
        except Exception as e:
            logger.error(f"[Hyperliquid] Failed to fetch positions: {e}")
            return []

    async def get_trades(self, symbol: str, limit: int = 5) -> list:
        """
        Fetch recent trades (fills) for a specific symbol.
        Used by Tracker to reconstruct history for adopted positions.
        """
        try:
            from services.symbol_normalizer import get_symbol_normalizer
            sn = get_symbol_normalizer()
            coin = sn.to_hyperliquid(symbol)
            
            # Fetch fills with caching
            fills = await asyncio.to_thread(
                self._get_cached, 
                f"user_fills_{self.address}", 
                lambda: self.info.user_fills(self.address),
                'user_state'  # Use same cache duration as user_state
            )
            
            # Filter for this coin
            # Note: HL API might return 'coin' as name or '@index' in fills
            # In most cases it returns the name. We'll check both if it's a native asset.
            relevant_fills = []
            for f in fills:
                f_coin = f.get('coin')
                if f_coin == coin:
                    relevant_fills.append(f)
                elif coin.startswith("@") and f_coin in ["HYPE", "PURR"]:
                    # Handle index-to-name mapping for native fills
                    if (coin == "@1" and f_coin == "HYPE") or (coin == "@0" and f_coin == "PURR"):
                        relevant_fills.append(f)
            
            # Sort by time descend? (API usually returns newest first, but let's be safe)
            # time is in ms
            relevant_fills.sort(key=lambda x: x.get('time', 0), reverse=True)
            
            trades = []
            for f in relevant_fills[:limit]:
                # Map HL 'B'/'A' to 'BUY'/'SELL'
                hl_side = f.get('side', '')
                side = 'BUY' if hl_side == 'B' else 'SELL'
                
                qty = float(f.get('sz', 0.0))
                # UN-SCALE K-ASSET QUANTITY
                if coin.startswith("k") and coin[1:].isalpha():
                    qty = qty * 1000.0
                
                trades.append({
                    'symbol': symbol,
                    'id': str(f.get('tid', f.get('oid', ''))),
                    'orderId': str(f.get('oid', '')),
                    'side': side,
                    'price': float(f.get('px', 0.0)),
                    'quantity': qty,
                    'cost': float(f.get('px', 0.0)) * qty,
                    'time': int(f.get('time', 0)), # ms timestamp
                    'timestamp': int(f.get('time', 0)),
                    'datetime': None, # construct if needed
                    'fee': {
                        'cost': float(f.get('fee', 0)),
                        'currency': f.get('feeToken', 'USDC')
                    },
                    'isBuyer': (side == 'BUY'),
                    'isMaker': False # Unknown from simple fill data usually
                })
                
            return trades
            
        except Exception as e:
            logger.warning(f"[Hyperliquid] Failed to fetch trades for {symbol}: {e}")
            return []

    async def _ensure_safety(self, symbol: str):
        """
        SAFETY SEAL: Enforces margin limits for Hyperliquid.
        Note: Hyperliquid doesn't have traditional leverage/margin mode like Binance,
        but we check margin utilization to prevent over-leveraging.
        """
        try:
            from config import get_settings
            settings = get_settings()
            
            # Get cached user state
            state = await asyncio.to_thread(
                self._get_cached, 
                f"user_state_{self.address}", 
                lambda: self.info.user_state(self.address),
                'user_state'
            )
            margin_summary = state.get("marginSummary", {})
            
            account_value = float(margin_summary.get("accountValue", 0.0))
            margin_used = float(margin_summary.get("totalMarginUsed", 0.0))
            
            # Safety check: If margin utilization > 80%, warn
            if account_value > 0:
                utilization = margin_used / account_value
                if utilization > 0.80:
                    logger.warning(f"[SAFETY] ⚠️ High margin utilization: {utilization*100:.1f}% (Account: ${account_value:.2f})")
            
            # Check minimum account value (Neutralized: 1.0 fallback)
            min_value = getattr(settings, 'MIN_ACCOUNT_VALUE', 1.0)
            if account_value < min_value:
                logger.warning(f"[SAFETY] ⚠️ Low account value: ${account_value:.2f} < ${min_value:.2f}")
        except Exception as e:
            logger.debug(f"[SAFETY] Hyperliquid safety check failed: {e}")
    
    async def get_margin_state(self) -> Dict[str, float]:
        """
        Query Hyperliquid margin state with caching.
        
        Returns real-time margin utilization metrics needed for accurate
        position sizing that accounts for already-used margin.
        
        Returns:
            Dict with keys:
                - 'account_value': Total account equity in USDC
                - 'margin_used': Margin currently locked in open positions
                - 'available_margin': Free margin available for new positions
                - 'utilization': Margin usage ratio (0.0 to 1.0)
        """
        try:
            # [ROBUSTNESS] Safety check for SDK state
            if not self.info:
                logger.warning("[HL] Cannot fetch margin state: Info object is None. Attempting reconnect...")
                await asyncio.to_thread(self._reinit_sdk)
                if not self.info:
                    return {
                        'account_value': 0.0, 'margin_used': 0.0, 
                        'available_margin': 0.0, 'utilization': 0.0
                    }

            # Use existing cached state (same call as _ensure_safety and get_balance)
            state = await asyncio.to_thread(
                self._get_cached,
                f"user_state_{self.address}",
                lambda: self.info.user_state(self.address) if self.info else {},
                'user_state'  # FIX: Use existing cache key, not 'user_state_margin'
            )
            
            margin_summary = state.get("marginSummary", {})
            if not margin_summary:
                logger.warning(f"[HL] No marginSummary found in user_state! Keys: {list(state.keys())}")
            else:
                logger.debug(f"[HL] Margin Summary: {margin_summary}")
            
            # 1. PERPS EQUITY
            perp_equity = float(margin_summary.get("accountValue", 0.0))
            margin_used = float(margin_summary.get("totalMarginUsed", 0.0))
            
            # 2. SPOT EQUITY (Value all assets, not just stables)
            spot_equity = 0.0
            from services.data_manager import get_data_manager
            dm = get_data_manager()
            
            # Fetch dedicated spot user state since it resides on a separate ledger in Hyperliquid UAM
            try:
                spot_state = await asyncio.to_thread(
                    self._get_cached,
                    f"spot_user_state_{self.address}",
                    lambda: self.info.spot_user_state(self.address) if self.info else {},
                    'user_state'
                )
                spot_balances = spot_state.get("balances", [])
            except Exception as spot_err:
                logger.warning(f"[HL] Failed to fetch spot state: {spot_err}")
                spot_balances = []
            
            for b in spot_balances:
                coin = b.get("coin")
                total = float(b.get("total", 0.0))
                if total <= 0: continue
                
                if coin in ["USDC", "USDT"]:
                    spot_equity += total
                else:
                    # Value other spot assets (LDO, GAS, IMX)
                    try:
                        # Try to get price from DM cache
                        symbol = f"{coin}USDC"
                        price = await asyncio.to_thread(dm.get_latest_price, symbol)
                        if price and price > 0:
                            spot_equity += total * price
                    except Exception:
                        pass
            
            # 3. TOTAL EQUITY
            account_value = perp_equity + spot_equity
            
            # Calculate available margin
            # On Hyperliquid, available margin usually refers to the Perps account,
            # but for our system's budget, we want the TOTAL free cash.
            available = account_value - margin_used
            
            # Calculate utilization ratio relative to total equity
            utilization = (margin_used / account_value) if account_value > 0 else 0.0
            
            return {
                'account_value': account_value,
                'perp_equity': perp_equity,
                'spot_equity': spot_equity,
                'margin_used': margin_used,
                'available_margin': max(0.0, available),
                'utilization': utilization
            }
            
        except Exception as e:
            logger.error(f"[HL] Failed to get margin state: {e}")
            # Return safe defaults on error
            return {
                'account_value': 0.0,
                'margin_used': 0.0,
                'available_margin': 0.0,
                'utilization': 0.0
            }


    async def submit_order(self, symbol: str, side: str, qty: float, order_type: str = "market", time_in_force: str = "ioc", reduce_only: bool = False, **kwargs) -> Any:
        """
        Submit Data to L1.
        
        Args:
            symbol: Trading pair
            side: "BUY" or "SELL"
            qty: Quantity
            order_type: "market" or "limit"
            time_in_force: Time in force ("ioc", "gtc", etc.)
            reduce_only: If True, order can only reduce existing position (default: False)
            **kwargs: Additional parameters
        """
        try:
            # Map parameters
            is_buy = side.lower() == "buy"
            
            # Symbol map (Hyperliquid uses coin names like "BTC", "ETH", not "BTCUSDT")
            coin = self._map_symbol_to_coin(symbol)
            
            # --- TRADFI GUARD ---
            # If the asset is a known TradFi bridge (SQQQ, RDDT, BRENTOIL) but NOT on HL perps
            # we should skip execution to avoid API errors.
            unsupported = ["SQQQ", "RDDT"] 
            if any(u in coin for u in unsupported):
                logger.warning(f"[BROKER] Skipping execution for {symbol} - TradFi Monitor Only.")
                return None

            # --- K-SCALING (SHIB -> kSHIB, PEPE -> kPEPE, etc.) ---
            # Hyperliquid lists some micro-priced assets in "kilo" units (1k tokens = 1 unit).
            # Quantities from the system are in raw tokens, so divide by 1000.
            if coin.startswith("k") and coin[1:].isalpha():
                qty = qty / 1000.0
                logger.info(f"[BROKER] K-Scaled quantity for {coin}: {qty}")

            # --- MARGIN SAFETY VALVE ---
            # We must check safety for ANY order that increases exposure (Opening a trade).
            # For simplicity, we check ALL Market Open orders.
            # (Closing orders usually use 'reduce_only' or separate API calls, but careful logic needed)
            
            # Since we use 'market_open', we assume we are entering a position.
            # Note: If we are closing a position, this check might prevent us from closing if account is low?
            # ideally we only block OPENING orders.
            # But allowing 'sell' to close a long is good.
            # Allowing 'buy' to close a short is good.
            # Determining if it's an OPEN or CLOSE is hard without knowing current position.
            
            # FIX: Only block if we are INCREASING risk.
            # Without state, we'll apply the FLOOR check to everything (safest for now),
            # BUT we should verify we aren't blocking a rescue close.
            
            # For now, let's enable it for BOTH, but add a LOG warning.
            # Ideally, checks should be: "If Account < $10, only allow Closing."
            
            check_safety = True # Default
            
            if check_safety:
                from config import get_settings
                settings = get_settings()
                
            # Get cached user state for safety checks
            state = await asyncio.to_thread(
                self._get_cached, 
                f"user_state_{self.address}", 
                lambda: self.info.user_state(self.address),
                'user_state'
            )
            positions = state.get("assetPositions", [])
            
            # Fetch unified margin state to correctly account for Spot UAM balances
            margin_state = await self.get_margin_state()
            account_value = margin_state.get('account_value', 0.0)
            margin_used = margin_state.get('margin_used', 0.0)

            # Infer close/reduce intent from live position side/size.
            # This guards against upstream cases where reduce_only wasn't forwarded.
            current_pos_size = 0.0
            for p in positions:
                pos = p.get("position", {})
                if pos.get("coin") == coin:
                    try:
                        current_pos_size = float(pos.get("szi", 0.0))
                    except Exception:
                        current_pos_size = 0.0
                    break
            side_up = side.upper()
            closes_long = side_up == "SELL" and current_pos_size > 0
            closes_short = side_up == "BUY" and current_pos_size < 0
            opposite_side_close = closes_long or closes_short
            abs_pos = abs(current_pos_size)
            abs_qty = abs(float(qty))
            would_flip = opposite_side_close and abs_qty > (abs_pos + 1e-12)
            inferred_reduce_only = opposite_side_close and abs_pos > 0 and not would_flip
            
            # 1. Equity Floor Check (Survival Mode)
            # If we are effectively broke, STOP. (Neutralized: 1.0 fallback)
            min_account_value = getattr(settings, 'MIN_ACCOUNT_VALUE', 1.0)
            if account_value < min_account_value:
                # Allow closing? We need to know if we have a position.
                # Simple heuristic: If Margin Used > 0, we might be closing. Allow it.
                # If Margin Used == 0, we are opening. BLOCK IT.
                if margin_used == 0 and not (reduce_only or inferred_reduce_only):
                    error_msg = f"Account Value (${account_value:.2f}) is below survival floor (${min_account_value:.2f}). No existing positions to close."
                    logger.warning(f"[SAFETY] 🛡️ REJECTED {side.upper()} {coin}: {error_msg}")
                    self._last_error = error_msg
                    return None
                else:
                    logger.info(
                        f"[SAFETY] ⚠️ ALLOWING {side.upper()} {coin} despite low equity "
                        f"(${account_value:.2f}) - close/reduce detected "
                        f"(reduce_only={reduce_only}, inferred={inferred_reduce_only}, pos={current_pos_size}, qty={qty})."
                    )

            # 2. Utilization Check (Risk Management)
            # When margin is high, force reduce-only to ensure we can only CLOSE positions (reduce risk)
            # This is CRITICAL: High margin = danger zone, so we MUST allow closing to reduce exposure
            if account_value > 0:
                utilization = margin_used / account_value
                safe_threshold = getattr(settings, 'HL_MARGIN_SAFE_THRESHOLD', 0.75)  # Default 75% max utilization
                
                if utilization > safe_threshold:
                    if not (reduce_only or inferred_reduce_only):
                        error_msg = f"High margin utilization ({utilization*100:.1f}% > {safe_threshold*100:.0f}%). Rejected NEW ENTRY order."
                        logger.warning(f"[SAFETY] ⚠️ {error_msg}")
                        self._last_error = error_msg
                        return None
                    else:
                        logger.info(
                            f"[SAFETY] ✅ High margin utilization ({utilization*100:.1f}%), "
                            f"allowing risk-reducing order (reduce_only={reduce_only}, "
                            f"inferred={inferred_reduce_only}, pos={current_pos_size}, qty={qty})."
                        )

            logger.info(f"[BROKER] HL SUBMIT: {side} {qty} {coin}")
            
            # Fetch metadata for precision (Cached if possible, but for now we fetch to be safe or use self.info if initialized)
            # Ideally we cache this in __init__, but let's try to get it here or use a cached property
            # For robustness in this fix, we'll assume self.info is available.
            
            # Helper to get decimals
            def get_sz_decimals(symbol_coin):
                try:
                    # Sync call to get meta
                    # We should cache this, but for now let's grab it.
                    # Warning: meta() is an API call.
                    # We'll use a simple caching strategy on the instance if needed, 
                    # but let's see if we can access it via info directly.
                    # self.info.meta() returns the big dict.
                   
                    # Let's perform the meta fetch in the thread executor to avoid blocking
                    return None # We will do it inside the thread for safety
                except Exception as e:
                    error_msg = f"Meta fetch failed: {str(e)}"
                    logger.warning(f"[HYPERLIQUID] {error_msg}")
                    self._last_error = error_msg
                    return None

            # Helper for 5 Significant Figures (Hyperliquid Standard)
            # Hyperliquid requires prices to have at most 5 significant figures.
            def _round_px(price: float) -> float:
                if not price or price <= 0: return 0.0
                
                try:
                    # 1. Hyperliquid SDK Standard: 5 Significant Figures
                    # Formula: round(value, sig_figs - floor(log10(value)) - 1)
                    sig_figs = 5
                    exponent = math.floor(math.log10(abs(price)))
                    decimals = sig_figs - exponent - 1
                    
                    # 2. Safety Clamp: Hyperliquid rarely allows more than 6 decimals for perps.
                    # Even for sub-cent coins, we cap at 6 to avoid "Invalid Price" rejections.
                    max_decimals = 6
                    decimals = min(max_decimals, max(0, decimals))
                    
                    rounded = round(price, decimals)
                    
                    # 3. Multiple of Tick Size (Optional but safer)
                    # For most HL assets, the tick size is 10^-decimals.
                    # We ensure we don't have floating point noise.
                    return float(f"{rounded:.{decimals}f}")
                except Exception as e:
                    logger.warning(f"[BROKER] Rounding error for {price}: {e}")
                    return price

            # Execute via thread with RETRY logic for Broken Pipes
            def _execute_hl_order():
                retries = 2
                for attempt in range(retries):
                    try:
                        # 1. Fetch Metadata for Precision (CACHED)
                        meta = self._get_cached(
                            "universe_meta",
                            lambda: self.info.meta(),
                            'meta'
                        )
                        # 1a. Fetch Asset Metadata (Unified Perp Lookup)
                        universe = meta.get('universe', [])
                        sz_decimals = None
                        matched_asset = None
                        for asset in universe:
                            if asset.get('name') == coin:
                                matched_asset = asset
                                sz_decimals = asset.get('szDecimals')
                                break
                                
                        final_qty = qty
                        if sz_decimals is not None:
                            # Standard precision adjustment (round to nearest)
                            final_qty = round(qty, sz_decimals)
                            logger.info(f"[BROKER] HL Precision Adjust: {qty} -> {final_qty} (Decimals={sz_decimals})")
                        else:
                            logger.warning(f"[BROKER] HL metadata missing precision for {coin}. Using raw qty {qty}.")
                            if matched_asset is None:
                                logger.warning(f"[BROKER] HL coin {coin} not found in universe metadata.")
                        
                        if final_qty <= 0:
                             error_msg = f"Quantity rounded to zero ({qty} -> {final_qty})"
                             logger.warning(f"[BROKER] HL Order Aborted: {error_msg}")
                             self._last_error = error_msg
                             return None

                        # 1b. Minimum Notional Guard (Round UP to ~$10.10)
                        # Prevents "notional below minimum" rejections from HL
                        try:
                            # Use price from kwargs or fetch L2 snapshot
                            price_ref = float(kwargs.get('price', 0))
                            if price_ref <= 0:
                                l2_ref = self._get_cached(f"l2_snapshot_{coin}", lambda: self.info.l2_snapshot(coin), 'l2_snapshot')
                                price_ref = float(l2_ref['levels'][0][0]['px']) if l2_ref.get('levels') else 0
                            
                            if price_ref > 0:
                                notional = final_qty * price_ref
                                # [SAFETY FIX] ONLY round up if NOT reducing/closing.
                                # Rounding up on a close order creates a reverse position (Double Buy Trap).
                                if notional < 10.10 and not (reduce_only or inferred_reduce_only):
                                    old_q = final_qty
                                    # Target 10.20 to be safe with spread/fees
                                    # [FIX] ROUND UP to ensure we stay ABOVE the floor after precision adjustment
                                    raw_required_q = 10.20 / price_ref
                                    if sz_decimals is not None:
                                        # Manual ceil to sz_decimals precision
                                        multiplier = 10 ** sz_decimals
                                        final_qty = math.ceil(raw_required_q * multiplier) / multiplier
                                    else:
                                        final_qty = raw_required_q
                                        
                                    logger.info(f"[BROKER] 🛡️ HL Notional ROUND-UP: {old_q} -> {final_qty} {coin} (~${final_qty*price_ref:.2f})")
                                elif notional < 10.0 and (reduce_only or inferred_reduce_only):
                                    logger.warning(f"[BROKER] ⚠️ Attempting to CLOSE dust position {coin} (${notional:.2f}). Notional below HL minimum, might fail.")
                        except Exception as notional_err:
                            logger.warning(f"[BROKER] Notional guard skipped: {notional_err}")

                        # 2. Check for LIMIT_ORDER_FIRST mode (Slingshot Sniper)
                        from config import get_settings
                        settings = get_settings()
                        
                        # 2a. SET LEVERAGE on HL for this coin (required — HL tracks leverage per-coin per-account)
                        if not coin.startswith("@"):  # Skip for spot tokens
                            try:
                                leverage_map = getattr(settings, 'SYMBOL_LEVERAGE_MAP', {})
                                target_leverage = int(leverage_map.get(coin, getattr(settings, 'HYPERLIQUID_LEVERAGE', 20)))
                                
                                # [OPTIMIZATION] Only update if not in cache or changed
                                if getattr(self, '_leverage_cache', {}).get(coin) != target_leverage:
                                    lev_result = self.exchange.update_leverage(target_leverage, coin, True)  # True = cross margin
                                    if lev_result and lev_result.get('status') == 'ok':
                                        if not hasattr(self, '_leverage_cache'): self._leverage_cache = {}
                                        self._leverage_cache[coin] = target_leverage
                                        logger.info(f"[BROKER] ⚡ Leverage set: {coin} → {target_leverage}x")
                                    else:
                                        logger.debug(f"[BROKER] Leverage update response: {lev_result}")
                                # else: leverage is already correct, skip API call
                            except Exception as lev_err:
                                logger.warning(f"[BROKER] ⚠️ Could not set leverage for {coin}: {lev_err}")

                        order_type = kwargs.get('order_type', 'market')
                        use_limit_first = getattr(settings, 'LIMIT_ORDER_FIRST', False) if order_type != 'market' else False
                        limit_offset = getattr(settings, 'LIMIT_ORDER_OFFSET_PCT', 0.001)
                        
                        if use_limit_first:
                            # Calculate limit price (0.1% better than current)
                            current_price = float(kwargs.get('price', 0))
                            if current_price > 0:
                                if is_buy:
                                    limit_price = current_price * (1 - limit_offset)
                                else:
                                    limit_price = current_price * (1 + limit_offset)
                                
                                # Round to 5 sig figs
                                limit_price = _round_px(limit_price)
                                
                                logger.info(f"[BROKER] 🎯 LIMIT-FIRST: {'BUY' if is_buy else 'SELL'} {final_qty} {coin} @ ${limit_price}")
                                
                                try:
                                    # Place limit order with GTC
                                    limit_result = self.exchange.order(
                                        coin,
                                        is_buy,
                                        final_qty,
                                        limit_price,
                                        {"limit": {"tif": "Gtc"}},
                                        False # reduce_only=False
                                    )
                                    
                                    # Check if order was placed
                                    if limit_result and limit_result.get('status') == 'ok':
                                        order_data = limit_result.get('response', {}).get('data', {})
                                        statuses = order_data.get('statuses', [])
                                        
                                        if statuses and isinstance(statuses[0], dict):
                                            if 'filled' in statuses[0]:
                                                logger.info(f"[BROKER] ✅ LIMIT FILLED IMMEDIATELY!")
                                                return limit_result
                                            elif 'resting' in statuses[0]:
                                                oid = statuses[0]['resting'].get('oid')
                                                # [OPTIMIZATION] Reduced wait from 8s to 3s for snappier execution
                                                logger.info(f"[BROKER] ⏳ LIMIT RESTING (OID: {oid}) - Waiting 3s for Maker fill...")
                                                import time
                                                start_wait = time.time()
                                                time.sleep(3) 
                                                logger.debug(f"[BROKER] Wait complete in {time.time() - start_wait:.3f}s")
                                                
                                                # Use cached open orders
                                                open_orders = self._get_cached(
                                                    f"open_orders_{self.address}",
                                                    lambda: self.info.open_orders(self.address),
                                                    'open_orders'
                                                )
                                                
                                                # Check if order is still open
                                                is_open = any(o.get('oid') == oid for o in open_orders)
                                                
                                                if not is_open:
                                                    # Critical Check: Was it FILLED or CANCELED?
                                                    # Don't assume success just because it's not open.
                                                    try:
                                                        order_query = self.info.query_order_by_oid(self.address, oid)
                                                        status = order_query.get('order', {}).get('status') or order_query.get('status')
                                                        
                                                        if status == 'filled':
                                                            logger.info(f"[BROKER] ✅ LIMIT FILLED (Confirmed by query)!")
                                                            return limit_result
                                                        elif status == 'canceled' or status == 'rejected':
                                                            logger.warning(f"[BROKER] ⚠️ Limit order {oid} was {status}. Falling back to MARKET.")
                                                            # Do NOT return - fall through to Market Order logic
                                                        else:
                                                            logger.warning(f"[BROKER] ⚠️ Limit order {oid} status is '{status}'. Falling back to MARKET.")
                                                            # Do NOT return - fall through
                                                    except Exception as e:
                                                        logger.error(f"[BROKER] Failed to verify order status {oid}: {e}. Assuming failed, falling back to MARKET.")
                                                        # Fall through
                                                else:
                                                    logger.info(f"[BROKER] ⚡ LIMIT NOT FILLED - Cancelling, falling back to MARKET")
                                                    try:
                                                        self.exchange.cancel(coin, oid)
                                                        
                                                        # [SAFETY CHECK] Check for partial fills
                                                        # If the limit order was partially filled, we must reduce the market order size
                                                        # to avoid buying more than intended (Double Buy Trap).
                                                        order_query = self.info.query_order_by_oid(self.address, oid)
                                                        order_info = order_query.get('order', {})
                                                        
                                                        # Hyperliquid 'order' object typically contains 'sz' (original) and 'filledSz' 
                                                        # or we can infer from status updates.
                                                        # Using safer 'filledSz' if available, otherwise 0.
                                                        filled_qty = float(order_info.get('filledSz', 0))
                                                        
                                                        if filled_qty > 0:
                                                            logger.warning(f"[BROKER] ⚠️ PARTIAL FILL DETECTED: {filled_qty} of {final_qty} {coin}. Adjusting Market Order...")
                                                            final_qty = max(0.0, final_qty - filled_qty)
                                                            
                                                            if final_qty == 0:
                                                                logger.info(f"[BROKER] ✅ Limit order fully filled (partially) - Skipping Market Order.")
                                                                return limit_result
                                                                
                                                    except Exception as e:
                                                        logger.warning(f"[BROKER] Partial fill check failed ({e}). Assuming 0 filled (RISK OF DOUBLE BUY).")
                                                        pass # Likely already closed or race condition
                                except Exception as e:
                                    logger.warning(f"[BROKER] Limit order failed ({e}), falling back to market")

                        # 2b. Handle explicit LIMIT orders (when order_type == "LIMIT")
                        if order_type and order_type.upper() == "LIMIT":
                            limit_price = float(kwargs.get('price', 0))
                            if limit_price > 0:
                                # Round to 5 sig figs (Hyperliquid Standard)
                                limit_price = _round_px(limit_price)
                                
                                logger.info(f"[BROKER] 🎯 LIMIT ORDER: {'BUY' if is_buy else 'SELL'} {final_qty} {coin} @ ${limit_price}")
                                
                                try:
                                    # Place limit order with GTC
                                    limit_result = self.exchange.order(
                                        coin,
                                        is_buy,
                                        final_qty,
                                        limit_price,
                                        {"limit": {"tif": "Gtc"}},
                                        reduce_only
                                    )
                                    
                                    if limit_result and limit_result.get('status') == 'ok':
                                        logger.info(f"[BROKER] ✅ LIMIT ORDER PLACED")
                                        return limit_result
                                    else:
                                        logger.warning(f"[BROKER] ⚠️ LIMIT ORDER FAILED: {limit_result}")
                                        return None
                                except Exception as e:
                                    logger.error(f"[BROKER] Limit order placement error: {e}")
                                    self._last_error = f"Limit order error: {str(e)}"
                                    return None
                            else:
                                logger.warning(f"[BROKER] ⚠️ LIMIT order requested but no price provided")
                                self._last_error = "LIMIT order requires price parameter"
                                return None

                        # 3. Place Market Order (Default or Fallback)
                        is_spot = coin.startswith("@")
                        
                        if reduce_only:
                            # Use order API with market-like limit price and reduce_only
                            try:
                                # [SAFETY FIX] Confirm we actually have a position to reduce
                                # Calling info.user_state takes time, so we trust our passed logic mostly,
                                # but to fix the "Reduce only order would increase position" error,
                                # we should try to be smart about direction or clamp size.
                                
                                # Fetch current position state to clamp size if needed (CACHED)
                                user_state = self._get_cached(
                                    f"user_state_{self.address}",
                                    lambda: self.info.user_state(self.address),
                                    'user_state'
                                )
                                positions = user_state.get("assetPositions", [])
                                current_pos_size = 0.0
                                for p in positions:
                                    pos = p.get("position", {})
                                    if pos.get("coin") == coin:
                                        current_pos_size = float(pos.get("szi", 0.0))
                                        break
                                
                                # Check direction alignment
                                # If we are BUYing, we must have a SHORT position (negative size)
                                # If we are SELLing, we must have a LONG position (positive size)
                                has_valid_position = False
                                if is_buy:
                                    if current_pos_size < 0: has_valid_position = True
                                else:
                                    if current_pos_size > 0: has_valid_position = True
                                    
                                if not has_valid_position:
                                    if current_pos_size == 0:
                                        err_msg = f"REDUCE-ONLY ABORTED: No open position for {coin}"
                                        logger.warning(f"[BROKER] 🛑 {err_msg}. (Qty: {final_qty})")
                                        self._last_error = err_msg
                                    else:
                                        err_msg = f"REDUCE-ONLY ABORTED: Wrong side ({side} vs {current_pos_size})"
                                        logger.warning(f"[BROKER] 🛑 {err_msg}")
                                        self._last_error = err_msg
                                    return None

                                # Auto-Clamp Quantity if trying to close more than we have
                                # (Avoids "Reduce only order would increase position" by not overshooting)
                                abs_pos_size = abs(current_pos_size)
                                if final_qty > abs_pos_size:
                                    logger.warning(f"[BROKER] ⚠️ Clamping Reduce-Only {coin}: {final_qty} -> {abs_pos_size}")
                                    final_qty = abs_pos_size

                                # --- MINIMUM NOTIONAL GUARD (Reduce-Only) ---
                                # High-priced assets (e.g. PAXG ~$3200 with szDecimals=3) can produce
                                # reduce-only quantities with notional < $10, causing HL rejection.
                                # If the resulting notional is below $10.20, escalate to full close.
                                try:
                                    price_ref = float(kwargs.get('price', 0))
                                    if price_ref <= 0:
                                        l2_ref = self._get_cached(f"l2_snapshot_{coin}", lambda: self.info.l2_snapshot(coin), 'l2_snapshot')
                                        price_ref = float(l2_ref['levels'][0][0]['px']) if l2_ref.get('levels') else 0
                                    if price_ref > 0:
                                        reduce_notional = final_qty * price_ref
                                        if reduce_notional < 10.10:
                                            # If below minimum, close the ENTIRE position instead
                                            # (partial reduce below minimum is rejected by HL anyway)
                                            logger.info(
                                                f"[BROKER] 🛡️ Reduce-Only Notional too small: "
                                                f"{final_qty} {coin} = ${reduce_notional:.2f} < $10.10. "
                                                f"Escalating to full close: {abs_pos_size} {coin}"
                                            )
                                            final_qty = abs_pos_size
                                except Exception as notional_reduce_err:
                                    logger.warning(f"[BROKER] Reduce-only notional guard skipped: {notional_reduce_err}")
                                    
                                if final_qty <= 0:
                                    err_msg = f"Reduce-Only resulted in 0 quantity after clamp"
                                    logger.warning(f"[BROKER] {err_msg}.")
                                    self._last_error = err_msg
                                    return None

                                # Get cached L2 snapshot for pricing
                                l2_book = self._get_cached(
                                    f"l2_snapshot_{coin}",
                                    lambda: self.info.l2_snapshot(coin),
                                    'l2_snapshot'
                                )
                                if is_buy:
                                    best_ask = float(l2_book['levels'][0][0]['px']) if l2_book.get('levels') else 0
                                    limit_price = best_ask * 1.001 if best_ask else 0
                                else:
                                    best_bid = float(l2_book['levels'][1][0]['px']) if len(l2_book.get('levels', [])) > 1 else 0
                                    limit_price = best_bid * 0.999 if best_bid else 0
                                
                                if limit_price == 0:
                                    logger.warning(f"[BROKER] Could not get market price for reduce-only order")
                                    return None
                                
                                # Round to 5 sig figs (Hyperliquid Standard)
                                limit_price = _round_px(limit_price)
                                
                                logger.info(f"[BROKER] HL REDUCE-ONLY: {side} {final_qty} {coin} @ ~{limit_price}")
                                
                                return self.exchange.order(
                                    coin,
                                    is_buy,
                                    final_qty,
                                    limit_price,
                                    {"limit": {"tif": "Ioc"}},  # IOC for immediate execution
                                    reduce_only
                                )
                            except Exception as e:
                                logger.error(f"[BROKER] Reduce-only order failed: {e}")
                                return None
                        else:
                            if is_spot:
                                # Spot Market Order (Use order API with aggressive price or market_order if exists)
                                # Safest: use order() with a high slippage limit price
                                l2_book = self._get_cached(
                                    f"l2_snapshot_{coin}",
                                    lambda: self.info.l2_snapshot(coin),
                                    'l2_snapshot'
                                )
                                if is_buy:
                                    best_ask = float(l2_book['levels'][0][0]['px']) if l2_book.get('levels') else 0
                                    limit_price = _round_px(best_ask * 1.02, sz_decimals or 0) # 2% slippage for spot market
                                else:
                                    best_bid = float(l2_book['levels'][1][0]['px']) if len(l2_book.get('levels', [])) > 1 else 0
                                    limit_price = _round_px(best_bid * 0.98, sz_decimals or 0) # 2% slippage for spot market
                                    
                                return self.exchange.order(
                                    coin,
                                    is_buy,
                                    final_qty,
                                    limit_price,
                                    {"limit": {"tif": "Ioc"}},
                                    False # reduce_only=False
                                )
                            else:
                                # Standard Perp market_open (Replaced with aggressive LIMIT to ensure precision)
                                l2_book = self._get_cached(
                                    f"l2_snapshot_{coin}",
                                    lambda: self.info.l2_snapshot(coin),
                                    'l2_snapshot'
                                )
                                if is_buy:
                                    best_ask = float(l2_book['levels'][0][0]['px']) if l2_book.get('levels') else 0
                                    limit_price = _round_px(best_ask * 1.01) # 1% slippage
                                else:
                                    best_bid = float(l2_book['levels'][1][0]['px']) if len(l2_book.get('levels', [])) > 1 else 0
                                    limit_price = _round_px(best_bid * 0.99) # 1% slippage
                                    
                                if limit_price == 0:
                                    # Fallback if book is empty
                                    return self.exchange.market_open(coin, is_buy, final_qty, None, 0.02)
                                    
                                logger.info(f"[BROKER] HL MARKET-AS-LIMIT: {side} {final_qty} {coin} @ {limit_price}")
                                return self.exchange.order(
                                    coin,
                                    is_buy,
                                    final_qty,
                                    limit_price,
                                    {"limit": {"tif": "Ioc"}},
                                    False
                                )
                    except OSError as e:
                        # Catch "Bad file descriptor" (9) or "Broken pipe" (32)
                        logger.warning(f"[BROKER] HL Connection Broken ({e}). Re-initializing SDK (Attempt {attempt+1}/{retries})...")
                        self._reinit_sdk() # This runs in thread, might race? No, _reinit uses local imports/fresh objects.
                        # Continue to next attempt
                    except Exception as e:
                         # Other errors are fatal
                         raise e
                # Retry loop exhausted - connection issues
                error_msg = "Hyperliquid connection failed after retries (Broken Pipe/Bad File Descriptor)"
                logger.error(f"[BROKER] {error_msg}")
                self._last_error = error_msg
                return None

            res = await asyncio.to_thread(_execute_hl_order)
            
            # Check for specific error structures in the response
            # Format: {'status': 'ok', 'response': {'type': 'order', 'data': {'statuses': [{'error': '...'}]}}}
            if res and isinstance(res, dict):
                # Robust parsing: Handle cases where 'response' might be a string (error) or dict
                resp_obj = res.get('response', {})
                
                # Case 1: SDK/API returned a top-level error string
                if res.get('status') == 'err' and isinstance(resp_obj, str):
                    logger.error(f"[BROKER] HL Top-Level Error: {resp_obj}")
                    self._last_error = f"Hyperliquid API error: {resp_obj}"
                    return None
                
                # Case 2: Response is a dict, check for nested order statuses
                if isinstance(resp_obj, dict):
                    response_data = resp_obj.get('data', {})
                    statuses = response_data.get('statuses', [])
                    if statuses and isinstance(statuses, list) and len(statuses) > 0:
                        first_status = statuses[0]
                        if isinstance(first_status, dict) and first_status.get('error'):
                            error_msg = first_status.get('error')
                            logger.error(f"[BROKER] HL Order Failed: {error_msg}")
                            self._last_error = f"Hyperliquid API error: {error_msg}"
                            return None
            
            logger.info(f"[BROKER] HL ORDER RESULT: {res}")
            return res
            
        except Exception as e:
            error_msg = f"Hyperliquid execution error: {str(e)}"
            logger.error(f"[BROKER] HL Execution Error: {e}")
            self._last_error = error_msg
            return None

    # Conform to BaseBroker interface
    async def place_order(self, symbol: str, side: str, order_type: str, quantity: float, price: float = None, params: Dict = {}) -> Any:
        # 0. SAFETY SEAL: Enforce margin limits before placing order
        await self._ensure_safety(symbol)
        
        # Standardize args
        # BaseBroker: symbol, side, order_type, quantity, price, params
        # CRITICAL: Pass price through kwargs so submit_order can use it for limit orders
        if price is not None:
            params['price'] = price
        return await self.submit_order(symbol, side, quantity, order_type, **params)

    async def cancel_order(self, order_id: int, symbol: str):
        """
        Cancels a specific order by ID with rate limiting and retry logic.
        Note: order_id must be an integer for HyperLiquid API compatibility.
        """
        try:
            # Ensure order_id is integer
            if isinstance(order_id, str):
                try:
                    order_id = int(order_id)
                except ValueError:
                    logger.error(f"[BROKER] Invalid order_id format: {order_id} (must be convertible to int)")
                    return False
            
            # Clean symbol to coin format
            coin = symbol.replace("/USD", "").replace("/USDC", "").replace("-PERP", "")
            if coin.endswith("USDC"): coin = coin[:-4]
            if coin.endswith("USDT"): coin = coin[:-4]  # Strip USDT suffix
            
            logger.info(f"[BROKER] Hyperliquid: Cancelling Order #{order_id} for {coin}")
            
            # Use rate limiting and retry logic
            def _cancel_with_retry():
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        # Apply rate limiting
                        self._rate_limit()
                        
                        res = self.exchange.cancel(coin, order_id)
                        
                        if res and isinstance(res, dict) and res.get('status') == 'ok':
                            logger.info(f"[BROKER] Hyperliquid: Order #{order_id} cancelled successfully.")
                            # Clear open orders cache since we changed the order state
                            cache_key = f"open_orders_{self.address}"
                            if cache_key in self._cache:
                                del self._cache[cache_key]
                                del self._cache_timestamps[cache_key]
                            return True
                        else:
                            # Check if it's a retryable error (rate limit, 422, etc.)
                            error_str = str(res) if res else "Unknown error"
                            if self._is_retryable_error(error_str):
                                self._handle_retryable_error(error_str)
                                if attempt < max_retries - 1:
                                    continue  # Retry after backoff
                            
                            logger.warning(f"[BROKER] Hyperliquid Cancel Fail for #{order_id}: {res}")
                            return False
                            
                    except Exception as e:
                        error_str = str(e)
                        
                        # Check if it's a retryable error
                        if self._is_retryable_error(error_str):
                            self._handle_retryable_error(error_str)
                            if attempt < max_retries - 1:
                                continue  # Retry after backoff
                        
                        # For other errors, log and retry
                        logger.warning(f"[BROKER] Cancel attempt {attempt + 1} failed: {e}")
                        if attempt < max_retries - 1:
                            time.sleep(0.5 * (attempt + 1))  # Brief delay before retry
                        else:
                            raise
                
                return False
            
            return await asyncio.to_thread(_cancel_with_retry)
                
        except Exception as e:
            logger.error(f"[BROKER] Hyperliquid Cancel Order Error: {e}")
            return False

    async def get_open_orders(self, symbol: str = None) -> list:
        """
        Get all open orders with caching. If symbol (coin) is provided, filters by that coin.
        
        Returns:
            List of order dicts with keys: order_id, symbol, coin, side, size, limit_price, order_type, etc.
        """
        try:
            # Fetch Open Orders from Hyperliquid with caching
            open_orders = await asyncio.to_thread(
                self._get_cached,
                f"open_orders_{self.address}",
                lambda: self.info.open_orders(self.address),
                'open_orders'
            )
            
            if not open_orders:
                return []

            # Clean requested symbol if present
            target_coin = None
            if symbol:
                target_coin = symbol.replace("/USD", "").replace("/USDC", "").replace("-PERP", "")
                if target_coin.endswith("USDC"): target_coin = target_coin[:-4]
                if target_coin.endswith("USDT"): target_coin = target_coin[:-4]  # Strip USDT suffix

            # Filter and format orders
            filtered_orders = []
            for order in open_orders:
                coin = order.get('coin')
                
                # Filter if symbol provided
                if target_coin and coin != target_coin:
                    continue
                
                # Format order for consistent API response
                formatted_order = {
                    'order_id': order.get('oid'),
                    'symbol': f"{coin}USDC",  # Standardize to USDC format
                    'coin': coin,
                    'side': 'BUY' if order.get('side') == 'B' else 'SELL',
                    'size': float(order.get('sz', 0)),
                    'limit_price': float(order.get('limitPx', 0)) if order.get('limitPx') else None,
                    'order_type': 'LIMIT',
                    'reduce_only': order.get('reduceOnly', False),
                    'trigger_price': None,  # Extract if trigger order
                }
                
                # Extract order type details
                order_type = order.get('orderType', {})
                if 'trigger' in order_type:
                    trigger_data = order_type.get('trigger', {})
                    formatted_order['trigger_price'] = float(trigger_data.get('triggerPx', 0)) if trigger_data.get('triggerPx') else None
                    formatted_order['order_type'] = 'TRIGGER'
                    formatted_order['tpsl'] = trigger_data.get('tpsl', '')  # 'sl' or 'tp'
                elif 'limit' in order_type:
                    limit_data = order_type.get('limit', {})
                    formatted_order['time_in_force'] = limit_data.get('tif', 'GTC')
                
                filtered_orders.append(formatted_order)
            
            return filtered_orders
                
        except Exception as e:
            logger.error(f"[BROKER] Hyperliquid Get Open Orders Error: {e}")
            return []

    async def cancel_all_orders(self, symbol: str = None):
        """
        Cancels all open orders with rate limiting. If symbol (coin) is provided, filters by that coin.
        """
        try:
            # 1. Fetch Open Orders with caching
            open_orders = await asyncio.to_thread(
                self._get_cached,
                f"open_orders_{self.address}",
                lambda: self.info.open_orders(self.address),
                'open_orders'
            )
            
            if not open_orders:
                logger.info("[BROKER] Hyperliquid: No open orders to cancel.")
                return []

            cancelled_ids = []
            
            # Clean requested symbol if present
            target_coin = None
            if symbol:
                target_coin = symbol.replace("/USD", "").replace("/USDC", "").replace("-PERP", "")
                if target_coin.endswith("USDC"): target_coin = target_coin[:-4]
                if target_coin.endswith("USDT"): target_coin = target_coin[:-4]  # Strip USDT suffix

            # 2. Iterate and Cancel with rate limiting
            for order in open_orders:
                coin = order.get('coin')
                oid = order.get('oid')
                
                # Filter if symbol provided
                if target_coin and coin != target_coin:
                    continue
                
                # Execute Cancel with rate limiting
                logger.info(f"[BROKER] Hyperliquid: Cancelling Order #{oid} for {coin}")
                
                try:
                    # Apply rate limiting before each cancel
                    await asyncio.to_thread(self._rate_limit)
                    
                    res = await asyncio.to_thread(self.exchange.cancel, coin, oid)
                    
                    # Check result
                    if res and isinstance(res, dict) and res.get('status') == 'ok':
                        cancelled_ids.append(oid)
                        # Clear open orders cache since we changed the order state
                        cache_key = f"open_orders_{self.address}"
                        if cache_key in self._cache:
                            del self._cache[cache_key]
                            del self._cache_timestamps[cache_key]
                    else:
                        # Check if it's a retryable error (rate limit, 422, etc.)
                        error_str = str(res) if res else "Unknown error"
                        if self._is_retryable_error(error_str):
                            await asyncio.to_thread(self._handle_retryable_error, error_str)
                            # Retry this cancel after backoff
                            try:
                                res = await asyncio.to_thread(self.exchange.cancel, coin, oid)
                                if res and isinstance(res, dict) and res.get('status') == 'ok':
                                    cancelled_ids.append(oid)
                                    # Clear open orders cache since we changed the order state
                                    cache_key = f"open_orders_{self.address}"
                                    if cache_key in self._cache:
                                        del self._cache[cache_key]
                                        del self._cache_timestamps[cache_key]
                                else:
                                    logger.warning(f"[BROKER] Hyperliquid Cancel Fail for #{oid}: {res}")
                            except Exception as retry_e:
                                logger.warning(f"[BROKER] Retry cancel failed for #{oid}: {retry_e}")
                        else:
                            logger.warning(f"[BROKER] Hyperliquid Cancel Fail for #{oid}: {res}")
                            
                except Exception as e:
                    error_str = str(e)
                    if self._is_retryable_error(error_str):
                        await asyncio.to_thread(self._handle_retryable_error, error_str)
                    logger.warning(f"[BROKER] Cancel failed for #{oid}: {e}")
                
                # Brief delay between cancels to avoid overwhelming the API
                await asyncio.sleep(0.1)
            
            return cancelled_ids
                
        except Exception as e:
            logger.error(f"[BROKER] Hyperliquid Cancel All Error: {e}")
            return []

    def _map_symbol_to_coin(self, symbol: str) -> str:
        """Helper to map symbol to Hyperliquid coin name using SymbolNormalizer."""
        from services.symbol_normalizer import get_symbol_normalizer
        return get_symbol_normalizer().to_hyperliquid(symbol)
    
    async def _get_precision(self, coin: str) -> tuple:
        """Get size and price decimals for a coin from metadata."""
        try:
            meta = await asyncio.to_thread(self.info.meta)
            universe = meta.get('universe', [])
            
            sz_decimals = 2  # Default
            px_decimals = 2  # Default
            
            for asset in universe:
                if asset['name'] == coin:
                    sz_decimals = asset.get('szDecimals', 2)
                    break
            
            return sz_decimals, px_decimals
        except Exception as e:
            logger.warning(f"[BROKER] Could not fetch precision for {coin}: {e}")
            return 2, 2  # Safe defaults

    def _round_to_sig_figs(self, price: float, sig_figs: int = 5) -> float:
        """Round price to Hyperliquid's 5 significant figures."""
        if price == 0: return 0.0
        return float(f"{price:.{sig_figs}g}")

    async def place_stop_loss(self, symbol: str, side: str, qty: float, 
                              trigger_price: float, reduce_only: bool = True) -> Any:
        """
        Place stop loss order (triggers market order when price hits trigger).
        
        Args:
            symbol: Trading pair (e.g., "XRPUSDC")
            side: "BUY" (to close SHORT) or "SELL" (to close LONG)
            qty: Quantity to close
            trigger_price: Price that triggers the stop
            reduce_only: If True, can only close positions (default: True)
            
        Returns:
            Order result from exchange
        """
        try:
            coin = self._map_symbol_to_coin(symbol)
            is_buy = side.lower() == "buy"
            
            # Get precision from metadata
            sz_decimals, px_decimals = await self._get_precision(coin)
            
            # Round quantity and price
            qty = round(qty, sz_decimals)
            trigger_price = self._round_to_sig_figs(trigger_price)
            
            if qty <= 0:
                logger.warning(f"[SAFETY] Stop loss quantity rounded to zero for {symbol}")
                return None
            
            # Build order request
            # Hyperliquid SDK expects triggerPx (camelCase) in the trigger order structure
            order_type = {
                "trigger": {
                    "triggerPx": trigger_price,  # camelCase, not snake_case
                    "isMarket": True, 
                    "tpsl": "sl"
                }
            }
            
            # Place order
            # Hyperliquid SDK order() signature: order(coin, is_buy, sz, limit_px, order_type, reduce_only)
            result = await asyncio.to_thread(
                self.exchange.order,
                coin,
                is_buy,
                qty,
                trigger_price,  # limit_px parameter
                order_type,     # order_type dict
                reduce_only     # reduce_only flag
            )
            
            logger.info(f"[SAFETY] 🛡️ Stop Loss placed @ {trigger_price} for {symbol} (qty: {qty})")
            return result
            
        except Exception as e:
            logger.error(f"[SAFETY] Failed to place stop loss for {symbol}: {e}")
            self._last_error = f"Stop loss placement error: {str(e)}"
            return None

    async def place_take_profit(self, symbol: str, side: str, qty: float,
                                trigger_price: float, reduce_only: bool = True) -> Any:
        """
        Place take profit order (triggers limit order when price hits trigger).
        
        Args:
            symbol: Trading pair (e.g., "XRPUSDC")
            side: "BUY" (to close SHORT) or "SELL" (to close LONG)
            qty: Quantity to close
            trigger_price: Price that triggers the take profit
            reduce_only: If True, can only close positions (default: True)
            
        Returns:
            Order result from exchange
        """
        try:
            coin = self._map_symbol_to_coin(symbol)
            is_buy = side.lower() == "buy"
            
            # Get precision from metadata
            sz_decimals, px_decimals = await self._get_precision(coin)
            
            # Round quantity and price
            qty = round(qty, sz_decimals)
            trigger_price = self._round_to_sig_figs(trigger_price)
            
            if qty <= 0:
                logger.warning(f"[SAFETY] Take profit quantity rounded to zero for {symbol}")
                return None
            
            # Build order request
            # Hyperliquid SDK expects triggerPx (camelCase) in the trigger order structure
            order_type = {
                "trigger": {
                    "triggerPx": trigger_price,  # camelCase, not snake_case
                    "isMarket": False,  # Use limit for maker rebate
                    "tpsl": "tp"
                }
            }
            
            # Place order
            # Hyperliquid SDK order() signature: order(coin, is_buy, sz, limit_px, order_type, reduce_only)
            result = await asyncio.to_thread(
                self.exchange.order,
                coin,
                is_buy,
                qty,
                trigger_price,  # limit_px parameter
                order_type,     # order_type dict
                reduce_only     # reduce_only flag
            )
            
            logger.info(f"[SAFETY] 💰 Take Profit placed @ {trigger_price} for {symbol} (qty: {qty})")
            return result
            
        except Exception as e:
            logger.error(f"[SAFETY] Failed to place take profit for {symbol}: {e}")
            self._last_error = f"Take profit placement error: {str(e)}"
            return None

    async def place_bracket_orders(self, symbol: str, side: str, qty: float,
                                   entry_price: float, stop_loss_pct: float = 0.05,
                                   take_profit_pct: float = 0.03) -> Dict[str, Any]:
        """
        Place stop loss AND take profit orders after entry (bracket order).
        
        Args:
            symbol: Trading pair (e.g., "XRPUSDC")
            side: "BUY" (for LONG position) or "SELL" (for SHORT position)
            qty: Position quantity
            entry_price: Entry price of position
            stop_loss_pct: Stop loss percentage from entry (default 5%)
            take_profit_pct: Take profit percentage from entry (default 3%)
            
        Returns:
            Dict with both order results: {"stop_loss": result, "take_profit": result}
        """
        try:
            # Calculate prices based on side
            if side.lower() == "buy":  # LONG position
                sl_price = entry_price * (1 - stop_loss_pct)  # 5% below for LONG
                tp_price = entry_price * (1 + take_profit_pct)  # 3% above for LONG
                sl_side = "SELL"  # Sell to close LONG
                tp_side = "SELL"
            else:  # SHORT position
                sl_price = entry_price * (1 + stop_loss_pct)  # 5% above for SHORT
                tp_price = entry_price * (1 - take_profit_pct)  # 3% below for SHORT
                sl_side = "BUY"  # Buy to close SHORT
                tp_side = "BUY"
            
            logger.info(f"[SAFETY] 🎯 Placing bracket orders for {symbol} {side.upper()}: SL @ {sl_price:.4f} | TP @ {tp_price:.4f}")
            
            # Place both orders
            sl_result = await self.place_stop_loss(symbol, sl_side, qty, sl_price, reduce_only=True)
            tp_result = await self.place_take_profit(symbol, tp_side, qty, tp_price, reduce_only=True)
            
            success_count = sum([1 for r in [sl_result, tp_result] if r is not None])
            logger.info(f"[SAFETY] Bracket orders placed: {success_count}/2 successful")
            
            return {
                "stop_loss": sl_result,
                "take_profit": tp_result,
                "success_count": success_count
            }
            
        except Exception as e:
            logger.error(f"[SAFETY] Failed to place bracket orders for {symbol}: {e}")
            self._last_error = f"Bracket order placement error: {str(e)}"
            return {"stop_loss": None, "take_profit": None, "success_count": 0}

    async def close(self):
        """Cleanly shutdown the SDK and WebSocket manager to prevent zombie threads."""
        logger.info("[BROKER] Closing Hyperliquid SDK Connection...")
        try:
            if hasattr(self, 'info') and self.info and hasattr(self.info, 'ws_manager'):
                self.info.ws_manager.stop()
                logger.info("[BROKER] Hyperliquid WebSocket stopped.")
        except Exception as e:
            logger.warning(f"[BROKER] Error stopping Hyperliquid WebSocket: {e}")
        logger.info("[BROKER] Hyperliquid Connection Closed.")

    async def cleanup_dust_positions(self, min_value_usd: float = 1.0) -> int:
        """
        Automatically close positions worth less than min_value_usd.
        Returns number of positions closed.
        
        This prevents margin waste from tiny residual positions.
        """
        try:
            positions = await self.get_all_positions()
            closed_count = 0
            
            for pos in positions:
                coin = pos.get("symbol")
                size = abs(pos.get("qty", 0))
                entry_price = pos.get("entryPrice", 0)
                
                # Estimate position value
                position_value = size * entry_price
                
                if position_value > 0 and position_value < min_value_usd:
                    logger.info(f"[BROKER] 🧹 DUST CLEANUP: Closing {coin} (Value: ${position_value:.4f})")
                    
                    try:
                        # market_close(coin) closes the full position
                        result = await asyncio.to_thread(self.exchange.market_close, coin)
                        
                        if result and isinstance(result, dict) and result.get('status') == 'ok':
                            logger.info(f"[BROKER] ✅ Dust position {coin} closed successfully")
                            closed_count += 1
                        else:
                            logger.warning(f"[BROKER] ⚠️ Dust close for {coin} returned: {result}")
                    except Exception as e:
                        logger.error(f"[BROKER] ❌ Failed to close dust {coin}: {e}")
            
            if closed_count > 0:
                logger.info(f"[BROKER] 🧹 Dust cleanup complete: {closed_count} positions closed")
            
            return closed_count
            
        except Exception as e:
            logger.error(f"[BROKER] Dust cleanup error: {e}")
            return 0

    async def get_max_leverage(self, symbol: str) -> float:
        """
        Get the maximum leverage for a specific symbol on Hyperliquid.
        Defaults to 20.0 or settings if metadata fetch fails.
        """
        try:
            # 1. Native Spot Detection (DEPRECATED: HYPE/PURR now Perps)
            if symbol.startswith("@"):
                return 1.0
            coin = symbol.replace("/USD", "").replace("/USDC", "").replace("-PERP", "")
            if coin.endswith("USDC"): coin = coin[:-4]
            
            # 2. Fetch Perp Metadata (CACHED)
            meta = await asyncio.to_thread(
                self._get_cached,
                "universe_meta",
                lambda: self.info.meta(),
                'meta'
            )
            
            if meta:
                universe = meta.get('universe', [])
                for asset in universe:
                    if asset['name'] == coin:
                        return float(asset.get('maxLeverage', 20.0))
            
            # 3. Check Spot Metadata if not in Perps
            spot_meta = await asyncio.to_thread(
                self._get_cached,
                "spot_meta",
                lambda: self.info.spot_meta(),
                'spot_meta'
            )
            if spot_meta:
                tokens = spot_meta.get('tokens', [])
                for token in tokens:
                    if token.get('name') == coin:
                        return 1.0 # Spot is always 1x leverage

            return 20.0 # Default fallback for perps
        except Exception as e:
            logger.warning(f"[BROKER] Failed to get max leverage for {symbol}: {e}")
            return 20.0
