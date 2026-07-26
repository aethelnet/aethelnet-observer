import logging
import asyncio
import time
from typing import Dict, Any, Optional
from brokers.base import BaseBroker
from brokers.binance import BinanceBroker
from brokers.alpaca import AlpacaBroker
from brokers.hyperliquid import HyperliquidBroker
from config import get_settings

logger = logging.getLogger("OmniRouter")

class OmniRouter:
    """
    Central multi-venue router for order execution.

    Responsibilities:
    - Route orders to the correct broker (heuristics + explicit routing).
    - Provide a unified get_balance/get_position/get_funding_rate interface across brokers.
    - Offer non-invasive telemetry snapshots for health checks and diagnostics.
    - Maintain a small last-error buffer (_last_error) for upstream services to include in logs.
    - Prevent re-entrant auto-finance checks between wallet and router (reentrancy guard).

    The router is intentionally defensive: routing failures raise clearly worded RuntimeError
    so callers can take explicit remediation actions rather than silently continuing.
    """
    def __init__(self):
        self.brokers: Dict[str, BaseBroker] = {}
        # Reentrancy guard to prevent recursive auto-finance checks between router and wallet
        self._auto_finance_running: bool = False
        self._last_error = None  # Store last error for propagation
        
        # --- CACHE: The Forensic Shield ---
        self._balance_cache: Dict[str, float] = {}  # asset -> amount
        self._last_balance_fetch: float = 0.0
        self._cache_ttl = 5.0 # 5 seconds of serenity
        
        self._init_brokers()

    async def connect(self) -> bool:
        """
        Async entry point for broker connectivity.
        Initializes connections for all brokers in parallel.
        """
        if not self.brokers:
            logger.warning("[ROUTER] No brokers to connect.")
            return True
            
        logger.info(f"[ROUTER] Connecting {len(self.brokers)} brokers in parallel...")
        
        # Collect all connect tasks
        tasks = []
        names = []
        for name, broker in self.brokers.items():
            tasks.append(broker.connect())
            names.append(name)
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = 0

    async def close(self):
        """Cleanly close all connected brokers."""
        logger.info("[ROUTER] Closing all broker connections...")
        for name, broker in self.brokers.items():
            try:
                if hasattr(broker, 'close'):
                    if asyncio.iscoroutinefunction(broker.close):
                        await broker.close()
                    else:
                        broker.close()
            except Exception as e:
                logger.warning(f"[ROUTER] Error closing broker {name}: {e}")
        for name, res in zip(names, results):
            if isinstance(res, Exception):
                logger.error(f"[ROUTER] ❌ Broker '{name}' connection crashed: {res}")
            elif res is False:
                logger.warning(f"[ROUTER] ⚠️ Broker '{name}' failed to connect.")
            else:
                success_count += 1
                
        logger.info(f"[ROUTER] Connection Phase Complete. {success_count}/{len(self.brokers)} brokers ONLINE.")
        return success_count > 0

    def reload(self):
        """
         HOT-RELOAD: Re-reads keys and re-initializes brokers.
        """
        logger.info("[ROUTER] 🔄 RELOADING BROKER CONNECTIONS...")
        # Close existing
        for name, broker in self.brokers.items():
            try:
                # We can't await in sync method, but reload is likely called from async context.
                # However, OmniRouter is often used in sync/async mix.
                # Ideally, reload should be async.
                pass 
            except: pass
        
        self.brokers = {}
        self._init_brokers()
        logger.info("[ROUTER] ✅ RELOAD COMPLETE.")

    def _init_brokers(self):
        settings = get_settings()
        from services.keychain import get_keychain
        kc = get_keychain()
        
        # 1. Initialize Binance (Crypto)
        # Use testnet keys if BINANCE_TESTNET is enabled, otherwise use live keys
        if settings.BINANCE_TESTNET:
            # Use testnet keys if available, fallback to regular keys
            binance_keys = kc.get_keys('binance_testnet') or kc.get_keys('BINANCE_TESTNET')
            api_key = binance_keys.get('api_key') if binance_keys else settings.BINANCE_TESTNET_API_KEY or settings.BINANCE_API_KEY
            secret_key = binance_keys.get('secret_key') if binance_keys else settings.BINANCE_TESTNET_SECRET_KEY or settings.BINANCE_SECRET_KEY
        else:
            # Use live keys
            binance_keys = kc.get_keys('binance') or kc.get_keys('BINANCE')
            api_key = binance_keys.get('api_key') if binance_keys else settings.BINANCE_API_KEY
            secret_key = binance_keys.get('secret_key') if binance_keys else settings.BINANCE_SECRET_KEY
        
        # UNLOCK SECRETS (Fix for -2008 Error)
        if hasattr(api_key, 'get_secret_value'):
            api_key = api_key.get_secret_value()
        if hasattr(secret_key, 'get_secret_value'):
            secret_key = secret_key.get_secret_value()
        
        if api_key and secret_key:
            # --- PHASE 14: THE BIFROST (Twin Engines) ---
            # Try to start BOTH Spot and Futures engines
            
            # Engine 1: SPOT
            try:
                self.brokers['binance_spot'] = BinanceBroker(api_key, secret_key, auto_detect=False, force_mode='spot')
                logger.info("[ROUTER] 🟢 Binance Spot Engine: ONLINE")
            except Exception as e:
                logger.warning(f"[ROUTER] 🟡 Binance Spot Init Failed: {e}")

            # Engine 2: FUTURES
            # Only start if NOT in strict SPOT mode (to avoid -2015 errors in restricted regions)
            if settings.TRADING_MODE.upper() != "SPOT":
                try:
                    self.brokers['binance_future'] = BinanceBroker(api_key, secret_key, auto_detect=False, force_mode='future')
                    logger.info("[ROUTER] 🟣 Binance Futures Engine: ONLINE")
                except Exception as e:
                    logger.warning(f"[ROUTER] 🟡 Binance Futures Init Failed: {e}")
            else:
                logger.info("[ROUTER] ⚪ Futures Engine Disabled (SPOT Mode Active).")

            # Set Primary Alias 'binance' to Spot (Default) or Futures (Fallback)
            if 'binance_spot' in self.brokers:
                self.brokers['binance'] = self.brokers['binance_spot']
            elif 'binance_future' in self.brokers:
                self.brokers['binance'] = self.brokers['binance_future']
            else:
                logger.error("[ROUTER] 🔴 CRITICAL: Could not start ANY Binance Engine.")
        
        # 2. Initialize Alpaca (Stocks) — DUAL MODE: Live + Paper
        alpaca_keys = kc.get_keys('alpaca') or kc.get_keys('ALPACA')
        # Try keychain first, then settings, then .env via settings
        alpaca_key = None
        alpaca_secret = None
        
        if alpaca_keys:
            alpaca_key = alpaca_keys.get('api_key')
            alpaca_secret = alpaca_keys.get('secret_key')
        else:
            # Get from settings (which loads from .env)
            alpaca_key = getattr(settings, 'ALPACA_API_KEY', None)
            alpaca_secret = getattr(settings, 'ALPACA_SECRET_KEY', None)
            # Unwrap SecretStr if needed
            if hasattr(alpaca_key, 'get_secret_value'):
                alpaca_key = alpaca_key.get_secret_value()
            if hasattr(alpaca_secret, 'get_secret_value'):
                alpaca_secret = alpaca_secret.get_secret_value()
        
        if alpaca_key and alpaca_secret:
            # Engine A: PRIMARY (Live or Paper based on ALPACA_PAPER setting)
            try:
                is_paper = getattr(settings, 'ALPACA_PAPER', True)
                self.brokers['alpaca'] = AlpacaBroker(alpaca_key, alpaca_secret, paper=is_paper)
                mode_label = 'PAPER' if is_paper else 'LIVE'
                logger.info(f"[ROUTER] 🟢 Alpaca PRIMARY ({mode_label}) Uplink Established.")
            except Exception as e:
                logger.error(f"[ROUTER] Alpaca PRIMARY Init Failed: {e}")
            
            # Engine B: SHADOW (Always Paper — for mirroring/validation)
            # Uses separate paper keys if available, otherwise same keys forced to paper mode
            paper_key = getattr(settings, 'ALPACA_PAPER_API_KEY', None)
            paper_secret = getattr(settings, 'ALPACA_PAPER_SECRET_KEY', None)
            if hasattr(paper_key, 'get_secret_value'):
                paper_key = paper_key.get_secret_value()
            if hasattr(paper_secret, 'get_secret_value'):
                paper_secret = paper_secret.get_secret_value()
            
            # If no separate paper keys, reuse primary keys with paper=True
            shadow_key = paper_key or alpaca_key
            shadow_secret = paper_secret or alpaca_secret
            
            try:
                self.brokers['alpaca_paper'] = AlpacaBroker(shadow_key, shadow_secret, paper=True)
                logger.info("[ROUTER] 📋 Alpaca PAPER (Shadow) Uplink Established.")
            except Exception as e:
                logger.warning(f"[ROUTER] Alpaca PAPER Shadow Init Failed: {e}")
        else:
            logger.warning("[ROUTER] No Alpaca Keys found. Stock trading disabled.")

        # 3. Initialize Hyperliquid (DeFi)
        # Check settings or env for key
        hl_key = getattr(settings, "HYPERLIQUID_PRIVATE_KEY", None)
        
        # Unwrap SecretStr if needed
        if hasattr(hl_key, 'get_secret_value'):
            hl_key = hl_key.get_secret_value()
            
        if not hl_key:
            import os
            hl_key = os.getenv("HYPERLIQUID_PRIVATE_KEY")
            
        # Initialize if mode fits OR explicit key provided
        is_defi_mode = settings.TRADING_MODE.upper() in ["DEFI", "HYPERLIQUID"]
        
        if hl_key:
            try:
                self.brokers['hyperliquid'] = HyperliquidBroker(hl_key)
                logger.info("[ROUTER] ⚡ Hyperliquid Bridge: ONLINE")
            except Exception as e:
                logger.error(f"[ROUTER] Hyperliquid Init Failed: {e}")
        elif is_defi_mode:
            logger.error("[ROUTER] ❌ DEFI Mode enabled but HYPERLIQUID_PRIVATE_KEY missing.")

    def _route(self, symbol: str) -> Optional[BaseBroker]:
        """
        Determines the correct broker for a given symbol.
        """
        settings = get_settings()
        is_defi_mode = settings.TRADING_MODE.upper() in ["DEFI", "HYPERLIQUID"]

        # Strip venue suffix if present (e.g., DOGE@hyperliquid -> DOGE)
        if "@" in symbol:
            venue = symbol.split('@')[1].lower()
            if venue == "hyperliquid" and is_defi_mode:
                return self.brokers.get('hyperliquid')
            symbol = symbol.split('@')[0]

        # Heuristic 1: Explicit Futures Suffix (e.g., BTC/USDT:USDT)
        if ':' in symbol:
            return self.brokers.get('binance_future')
            
        # [TRADFI PROTECTION]
        # Never route Forex or Commodities to Live Brokers (unless we add one specifically for them)
        # These symbols are handled by DataManager/YahooConnector for quotes.
        taxonomy = settings.UNIVERSE_TAXONOMY.get("CATEGORIES", {})
        forex_list = taxonomy.get("FOREX", [])
        commodity_list = taxonomy.get("COMMODITIES", [])
        
        if symbol in forex_list or symbol in commodity_list or any(c in symbol for c in ["=", "^"]):
            return None # No live broker for these

        # [BROAD DEFI ROUTING]
        if is_defi_mode:
            if any(symbol.endswith(q) for q in ["USDC", "USDT", "BUSD", "BTC", "ETH"]) or symbol.endswith("-PERP"):
                return self.brokers.get('hyperliquid')
            
            # Tighten catch-all for alphabetic symbols that are NOT known stocks
            if len(symbol) <= 8 and symbol.isalpha():
                from services.execution import is_stock_symbol
                if is_stock_symbol(symbol):
                    return self.brokers.get('alpaca')
                
                # If it's alphabetic but not a known stock, check if it's 6 chars (Forex candidate)
                if len(symbol) == 6:
                     return None # Likely Forex, let Yahoo handle

                return self.brokers.get('hyperliquid')

        # Heuristic 2: Crypto usually ends in USDT, BUSD, USDC, BTC, ETH
        if any(symbol.endswith(q) for q in ["USDC", "USDT", "BUSD", "BTC", "ETH"]):
            # Default to Spot if available, else Futures (Smart Fallback)
            return self.brokers.get('binance_spot') or self.brokers.get('binance_future')
            
        # Heuristic 3: Stocks are usually 1-4 chars
        if len(symbol) <= 5 and symbol.isalpha():
             return self.brokers.get('alpaca')

        # Fallback
        return None

    async def get_balance(self, asset: str, force: bool = False) -> float:
        """
        Get balance with intelligent caching.
        """
        now = time.time()
        if not force and (now - self._last_balance_fetch < self._cache_ttl):
            if asset in self._balance_cache:
                return self._balance_cache[asset]

        # RECONCILE (Refresh Cache)
        try:
            if asset == 'USDC':
                spot = await self.brokers['binance_spot'].get_balance(asset) if 'binance_spot' in self.brokers else 0.0
                future = await self.brokers['binance_future'].get_balance(asset) if 'binance_future' in self.brokers else 0.0
                hl = await self.brokers['hyperliquid'].get_balance(asset) if 'hyperliquid' in self.brokers else 0.0
                val = spot + future + hl
                self._balance_cache[asset] = val
                self._last_balance_fetch = now
                return val
                
            elif asset == 'USD':
                broker = self.brokers.get('alpaca')
                val = await broker.get_balance(asset) if broker else 0.0
                self._balance_cache[asset] = val
                self._last_balance_fetch = now
                return val
        except Exception as e:
            logger.warning(f"[ROUTER] Cache refresh failed: {e}")
            return self._balance_cache.get(asset, 0.0)

        return 0.0

    async def get_total_equity(self, force: bool = False) -> float:
        """
        Aggregates Total Equity with caching.
        """
        now = time.time()
        if not force and (now - self._last_balance_fetch < self._cache_ttl):
            # If we have a reasonably fresh cache for all major assets, return sum
            if 'USDC' in self._balance_cache and 'USD' in self._balance_cache:
                return self._balance_cache['USDC'] + self._balance_cache['USD']

        total = 0.0
        # This will trigger get_balance for each, which will update the cache
        usdc = await self.get_balance('USDC', force=force)
        usd = await self.get_balance('USD', force=force)
        
        return usdc + usd
    
    async def get_trading_capital(self, symbol: str = None) -> float:
        """
        Get available capital for trading, sourced from the broker that will
        actually execute the trade.

        If symbol is provided, uses _route(symbol) to determine the correct
        broker — so Alpaca USD is used for stocks, Hyperliquid USDC for perps,
        and Binance USDC for crypto spot/futures.

        If no symbol is provided, falls back to the mode-based heuristic for
        backward compatibility.

        Returns:
            float: Available capital with safety buffer applied.
        """
        from config import get_settings
        settings = get_settings()
        safety_buffer = getattr(settings, 'MARGIN_SAFETY_BUFFER', 0.80)
        reserve_pct = getattr(settings, 'RESERVE_PERCENTAGE', 0.30)

        # --- SYMBOL-AWARE ROUTING (preferred path) ---
        if symbol:
            broker = self._route(symbol)
            if broker:
                try:
                    # Identify which broker we got and query the right asset
                    if broker == self.brokers.get('alpaca') or broker == self.brokers.get('alpaca_paper'):
                        capital = await broker.get_balance('USD')
                        logger.debug(f"[ROUTER CAPITAL] {symbol} → Alpaca USD ${capital:.2f}")
                    elif broker == self.brokers.get('hyperliquid'):
                        # [SVRGN FIX]: Use Total Equity, not just withdrawable cash
                        # If we have 100% margin utilization, get_balance returns 0, but we still have equity!
                        capital = await broker.get_equity()
                        logger.debug(f"[ROUTER CAPITAL] {symbol} → Hyperliquid Equity ${capital:.2f}")
                    elif broker == self.brokers.get('binance_future'):
                        # Future/Margin: Account Value
                        state = await broker.get_margin_state()
                        capital = state.get('account_value', 0.0)
                        logger.debug(f"[ROUTER CAPITAL] {symbol} → Binance Futures Equity ${capital:.2f}")
                    else:
                        # Binance spot — try USDC then USDT
                        capital = await broker.get_balance('USDC')
                        if capital < 10:
                            capital = await broker.get_balance('USDT')
                        logger.debug(f"[ROUTER CAPITAL] {symbol} → Binance Spot ${capital:.2f}")

                    return capital * (1 - reserve_pct) * safety_buffer
                except Exception as e:
                    logger.warning(f"[ROUTER CAPITAL] Symbol-aware lookup failed for {symbol}: {e}")

        # --- FALLBACK: Mode-based heuristic (backward compat) ---
        broker = None
        if settings.TRADING_MODE.upper() == "DEFI":
            broker = self.brokers.get('hyperliquid')
        elif settings.TRADING_MODE.upper() == "FUTURES":
            broker = self.brokers.get('binance_future')
        else:
            # Check Alpaca first — if it has more capital it's the funded account
            alpaca_broker = self.brokers.get('alpaca')
            binance_broker = self.brokers.get('binance_spot')
            try:
                alpaca_usd = await alpaca_broker.get_balance('USD') if alpaca_broker else 0.0
                binance_usd = await binance_broker.get_balance('USDC') if binance_broker else 0.0
                if alpaca_usd > binance_usd:
                    logger.debug(f"[ROUTER CAPITAL] Fallback → Alpaca ${alpaca_usd:.2f}")
                    return alpaca_usd * (1 - reserve_pct) * safety_buffer
            except Exception:
                pass
            broker = binance_broker

        if not broker or not hasattr(broker, 'get_margin_state'):
            logger.warning("[ROUTER] Broker doesn't support margin queries, using simple balance")
            if settings.TRADING_MODE.upper() == "DEFI":
                return await self.get_balance('USDC')
            else:
                return await self.get_balance('USDT')

        # Get margin state from broker
        margin_state = await broker.get_margin_state()
        available = margin_state.get('available_margin', 0.0)
        utilization = margin_state.get('utilization', 0.0)
        safe_capital = available * safety_buffer

        logger.debug(
            f"[ROUTER CAPITAL] "
            f"Total=${margin_state.get('account_value', 0):.2f}, "
            f"Used=${margin_state.get('margin_used', 0):.2f}, "
            f"Available=${available:.2f}, "
            f"Safe=${safe_capital:.2f} "
            f"(Util: {utilization*100:.1f}%, Buffer: {safety_buffer*100:.0f}%)"
        )

        return safe_capital




    async def get_margin_state(self) -> Dict[str, float]:
        """
        Query current margin state from the active broker.
        
        Returns:
            Dict: Margin state containing account_value, margin_used, 
                  available_margin, and utilization.
        """
        from config import get_settings
        settings = get_settings()
        
        # Determine which broker to query based on trading mode
        broker = None
        if settings.TRADING_MODE.upper() == "DEFI":
            broker = self.brokers.get('hyperliquid')
        elif settings.TRADING_MODE.upper() == "FUTURES":
            broker = self.brokers.get('binance_future')
        else:
            broker = self.brokers.get('binance_spot')
            
        if not broker or not hasattr(broker, 'get_margin_state'):
            # Fallback for brokers that don't support margin
            equity = await self.get_total_equity()
            return {
                'account_value': equity,
                'margin_used': 0.0,
                'available_margin': equity,
                'utilization': 0.0
            }
            
        return await broker.get_margin_state()


    async def get_funding_rate(self, symbol: str) -> float:
        """
        Get funding rate for a symbol.
        """
        broker = self._route(symbol)
        if broker and hasattr(broker, 'get_funding_rate'):
            return await broker.get_funding_rate(symbol)
        return 0.0

    async def get_position(self, symbol: str) -> Optional[float]:
        broker = self._route(symbol)
        if broker:
            return await broker.get_position(symbol)
        return None # Return None to signal "Unknown/No Route" rather than flat.

    async def get_all_positions(self) -> list:
        """
        Aggregate all open positions across ALL brokers in parallel.
        Returns unified list of dicts.
        """
        tasks = []
        broker_names = []
        for name, broker in self.brokers.items():
            if hasattr(broker, 'get_all_positions'):
                tasks.append(broker.get_all_positions())
                broker_names.append(name)
        
        if not tasks:
            return []
            
        all_positions = []
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for name, result in zip(broker_names, results):
            if isinstance(result, Exception):
                logger.warning(f"[ROUTER] Failed to get positions from {name}: {result}")
                continue
            if result:
                for p in result:
                    p['broker'] = name
                all_positions.extend(result)
                
        return all_positions

    async def get_trades(self, symbol: str, limit: int = 5) -> list:
        """
        Fetch recent trades for a symbol from the routed broker.
        """
        broker = self._route(symbol)
        if broker and hasattr(broker, 'get_trades'):
            try:
                return await broker.get_trades(symbol, limit)
            except Exception as e:
                logger.warning(f"[ROUTER] Failed to get trades for {symbol}: {e}")
                return []
        return []

    async def place_order(self, symbol: str, side: str, order_type: str, quantity: float, price: float = None, params: Dict = {}) -> Any:
        broker = self._route(symbol)
        if not broker:
            # Special case: If we are in DEFI mode and it's a crypto symbol, 
            # we SHOULD have a Hyperliquid broker.
            settings = get_settings()
            if settings.TRADING_MODE.upper() in ["DEFI", "HYPERLIQUID"] and ("USDC" in symbol or "PERP" in symbol):
                msg = f"Hyperliquid broker is OFFLINE or not initialized for {symbol}. Check API keys."
            else:
                msg = f"No route for {symbol} (missing broker or API keys)"
            
            self._last_error = msg
            logger.error(f"[ROUTER] {msg}")
            
            # If this is an EXIT order (sell for long, buy for short), and we have NO ROUTE,
            # we should log it but perhaps not crash the entire loop?
            # For now, keep the raise but make the message more helpful.
            raise RuntimeError(msg)
        
        # Check if we need auto-financing before placing order (non-invasive snapshot)
        try:
            from services.wallet import get_wallet
            wallet = get_wallet()

            # Prevent re-entrant auto-finance checks that can cause recursion between wallet and router.
            if getattr(self, "_auto_finance_running", False):
                logger.debug("[ROUTER] Auto-finance check already running; skipping to avoid recursion.")
            else:
                self._auto_finance_running = True
                try:
                    # Use a read-only snapshot to decide whether to warn/log about low balances.
                    snap = await wallet.get_snapshot()
                    target_key = None
                    if 'binance_spot' in self.brokers and broker == self.brokers['binance_spot']:
                        target_key = 'binance_spot'
                    elif 'binance_future' in self.brokers and broker == self.brokers['binance_future']:
                        target_key = 'binance_future'
                    elif 'alpaca' in self.brokers and broker == self.brokers['alpaca']:
                        target_key = 'alpaca'

                    if target_key:
                        wallets = snap.get('wallets', {})
                        tw = wallets.get(target_key, {})
                        base_bal = None
                        if tw:
                            balances = tw.get('balances', {})
                            # Check common stablecoins / fiat keys for a best-effort available balance
                            for coin in ('USDC', 'USDT', 'USD', 'EUR', 'BUSD'):
                                if coin in balances:
                                    val = balances[coin]
                                    # Support both dict shapes and simple numeric shapes
                                    if isinstance(val, dict):
                                        base_bal = val.get('free')
                                    else:
                                        try:
                                            base_bal = float(val)
                                        except Exception:
                                            base_bal = None
                                    break
                        logger.debug(f"[ROUTER] Pre-order snapshot for {target_key}: base_free={base_bal}")
                finally:
                    self._auto_finance_running = False
        except Exception as e:
            logger.warning(f"[ROUTER] Auto-finance check failed: {e}")
        
        try:
            # 💉 DETECTIVE NEEDLE 1 FIX:
            # Binance Spot strictly forbids the 'reduceOnly' parameter (unlike Binance Futures or HL)
            # If we are routing to a Spot broker, manually sanitize this Futures-only key before it crashes CCXT.
            if getattr(self, 'brokers', {}).get('binance_spot') == broker:
                if params and ('reduce_only' in params or 'reduceOnly' in params):
                    params.pop('reduce_only', None)
                    params.pop('reduceOnly', None)
                    logger.debug("[ROUTER] Sanitized Futures flag (reduceOnly) for Spot Broker to prevent InvalidOrder error.")

            result = await broker.place_order(symbol, side, order_type, quantity, price, params)
            # If order failed (returned None), capture broker error if available
            if result is None and hasattr(broker, '_last_error') and broker._last_error:
                self._last_error = broker._last_error
            
            # [DUAL MODE] Mirror stock orders to Alpaca Paper for validation
            # Non-blocking: Paper mirror failure never affects the primary order
            if broker == self.brokers.get('alpaca') and 'alpaca_paper' in self.brokers:
                asyncio.ensure_future(self._mirror_to_alpaca_paper(symbol, side, order_type, quantity, price, params))
            
            return result
        except Exception as e:
            self._last_error = str(e)
            raise

    async def _mirror_to_alpaca_paper(self, symbol: str, side: str, order_type: str,
                                       quantity: float, price: float = None, params: Dict = {}):
        """
        [DUAL MODE] Fire a shadow order on Alpaca Paper.
        Fully defensive — never raises, never blocks.
        """
        try:
            paper_broker = self.brokers.get('alpaca_paper')
            if not paper_broker:
                return
            # Strip tracking params that would collide with primary
            shadow_params = {k: v for k, v in params.items() if k != 'clientOrderId'}
            result = await paper_broker.place_order(symbol, side, order_type, quantity, price, shadow_params)
            if result:
                logger.info(f"[DUAL MODE] 📋 Alpaca Paper MIRROR: {side} {quantity} {symbol} — Filled: {result.get('id', 'OK')}")
            else:
                logger.warning(f"[DUAL MODE] 📋 Alpaca Paper MIRROR: {side} {symbol} — Rejected (None result)")
        except Exception as e:
            logger.warning(f"[DUAL MODE] 📋 Alpaca Paper MIRROR FAILED for {symbol}: {e}")

    async def get_open_orders(self, symbol: str = None) -> list:
        """
        Get all open orders across all brokers in parallel. 
        If symbol is provided, filters by that symbol.
        """
        tasks = []
        broker_names = []
        for name, broker in self.brokers.items():
            if hasattr(broker, 'get_open_orders'):
                tasks.append(broker.get_open_orders(symbol))
                broker_names.append(name)
        
        if not tasks:
            return []
            
        all_orders = []
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for name, result in zip(broker_names, results):
            if isinstance(result, Exception):
                logger.warning(f"[ROUTER] Failed to get open orders from {name}: {result}")
                continue
            if result:
                for order in result:
                    order['broker'] = name
                all_orders.extend(result)
                
        return all_orders

    async def cancel_all_orders(self, symbol: str) -> bool:
        broker = self._route(symbol)
        if broker:
            return await broker.cancel_all_orders(symbol)
        return False

    async def get_max_leverage(self, symbol: str) -> float:
        broker = self._route(symbol)
        if broker:
            return await broker.get_max_leverage(symbol)
        return 1.0

    async def place_bracket_orders(self, symbol: str, side: str, qty: float,
                                   entry_price: float, stop_loss_pct: float = 0.05,
                                   take_profit_pct: float = 0.03) -> Dict[str, Any]:
        """
        Place bracket orders (stop loss + take profit) after position entry.
        
        Routes to appropriate broker and places both safety orders.
        Only supported on Hyperliquid currently.
        """
        broker = self._route(symbol)
        if not broker:
            logger.warning(f"[ROUTER] No broker found for bracket orders on {symbol}")
            return {"stop_loss": None, "take_profit": None, "success_count": 0}
        
        # Check if broker supports bracket orders
        if not hasattr(broker, 'place_bracket_orders'):
            logger.warning(f"[ROUTER] Broker for {symbol} doesn't support bracket orders")
            return {"stop_loss": None, "take_profit": None, "success_count": 0}
        
        try:
            result = await broker.place_bracket_orders(symbol, side, qty, entry_price, 
                                                       stop_loss_pct, take_profit_pct)
            return result
        except Exception as e:
            logger.error(f"[ROUTER] Bracket order placement failed for {symbol}: {e}")
            self._last_error = str(e)
            return {"stop_loss": None, "take_profit": None, "success_count": 0}

    async def close(self):
        for name, broker in self.brokers.items():
            await broker.close()

    async def get_telemetry_snapshot(self) -> Dict[str, Any]:
        """
        Returns a snapshot of real balances for UI telemetry in parallel.
        """
        tasks = {}
        
        # 1. Binance Spot
        if 'binance_spot' in self.brokers:
            tasks['binance_spot'] = self.brokers['binance_spot'].get_all_balances()
            
        # 2. Binance Futures
        if 'binance_future' in self.brokers:
            tasks['binance_future'] = self.brokers['binance_future'].get_all_balances()
            
        # 3. Alpaca
        if 'alpaca' in self.brokers:
             # Since it's just one call, we could wrap it or just await it. 
             # To keep it parallel, we wrap it.
             async def _get_alpaca():
                 usd_bal = await self.brokers['alpaca'].get_balance('USD')
                 return {'USD': {'free': usd_bal, 'locked': 0.0}}
             tasks['alpaca'] = _get_alpaca()
             
        # 4. Hyperliquid
        if 'hyperliquid' in self.brokers:
             async def _get_hl():
                 hl_state = await self.brokers['hyperliquid'].get_margin_state()
                 return {
                     'USDC': {
                         'free': hl_state.get('available_margin', 0.0),
                         'locked': hl_state.get('margin_used', 0.0),
                         'equity': hl_state.get('account_value', 0.0)
                     }
                 }
             tasks['hyperliquid'] = _get_hl()
             
        if not tasks:
            return {}
            
        keys = list(tasks.keys())
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        snapshot = {}
        for key, result in zip(keys, results):
            if isinstance(result, Exception):
                logger.warning(f"[ROUTER] Telemetry fetch failed for {key}: {result}")
                continue
            snapshot[key] = result
             
        return snapshot

_omni_router = None

def get_omni_router():
    global _omni_router
    if _omni_router is None:
        _omni_router = OmniRouter()
    return _omni_router
