import asyncio
import logging
import json
from binance import AsyncClient, BinanceSocketManager
from tenacity import retry, wait_exponential, retry_if_exception_type, stop_after_attempt, before_sleep_log

logger = logging.getLogger("WebSocketManager")

class WebSocketManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(WebSocketManager, cls).__new__(cls)
            cls._instance.client = None
            cls._instance.bm = None
            cls._instance.ts = None
            cls._instance.buffer = {}
            cls._instance._keep_running = True
        return cls._instance

    @property
    def is_connected(self):
        """Check if connection is active."""
        return self.client is not None and self._keep_running

    async def start(self):
        """Initialize connection to Binance and start the background listener.
        Uses retry/backoff for robustness and subscribes to the configured channels.
        """
        logger.info("Initializing WebSocket Manager...")
        if not self.client:
            from config import get_settings
            settings = get_settings()
            
            # PROXY FAILSAFE SETUP
            requests_params = {}
            use_proxy = False
            # [STATIC IP UPGRADE] Proxy Disabled
            # if settings.EGRESS_PROXY_URL:
            #     logger.debug(f"[WebSocket] Using Egress Proxy: {settings.EGRESS_PROXY_URL}")
            #     requests_params['proxies'] = {
            #         'http': settings.EGRESS_PROXY_URL,
            #         'https': settings.EGRESS_PROXY_URL
            #     }
            #     use_proxy = True
            
            self.client = await AsyncClient.create(requests_params={**requests_params, 'timeout': 30})
            
            # [FAILSAFE] Verify Connectivity
            if use_proxy:
                try:
                    await self.client.ping()
                except Exception as e:
                     err = str(e).lower()
                     if "timeout" in err or "proxy" in err or "connection" in err:
                         logger.warning(f"[WebSocket] ⚠️ PROXY FAILURE: {e}")
                         logger.warning("[WebSocket] 🔄 PROXY BYPASS ACTIVATED (Direct Connection)")
                         # Close failed client
                         await self.client.close_connection()
                         # Re-init without proxy
                         self.client = await AsyncClient.create(requests_params={'timeout': 30})
            self.bm = BinanceSocketManager(self.client)
            
            # Channels to monitor
            # CRITICAL: Use same symbol generation as trading service
            from config import get_settings
            from config.settings import get_trading_symbols
            settings = get_settings()
            
            # Get symbols from settings (same as trading service uses)
            CORE_SYMBOLS = get_trading_symbols(settings)
            
            # Convert to Binance Stream format (lowercase + @ticker)
            # REPAIR: Use Central SymbolNormalizer to validate valid crypto pairs
            # This is a SYSTEMIC FIX, not a bridge. It ensures we respect the global dictionary.
            from services.symbol_normalizer import get_symbol_normalizer
            normalizer = get_symbol_normalizer()
            
            channels = []
            for s in CORE_SYMBOLS:
                # 1. Normalize/Validate via Central Authority
                binance_symbol = normalizer.to_binance(s)
                
                if binance_symbol:
                    # Valid Crypto Pair
                    channels.append(f"{binance_symbol.lower()}@ticker")
                else:
                    logger.debug(f"[WebSocket] Skipping Non-Binance/TradFi symbol: {s}")
            
            # Add Tier 1 symbols from universe calibration (for auto-discovery)
            # This allows auto-discovery engine to monitor high-liquidity symbols
            try:
                if getattr(settings, 'AUTO_DISCOVERY_ENABLED', False):
                    from services.data_manager import get_data_manager
                    dm = get_data_manager()
                    calibration = await dm.calibrate_universe(lookback_days=2)
                    tier_1_symbols = calibration.get("core", [])
                    
                    # Add Tier 1 symbols that aren't already in whitelist
                    tier_1_set = set(s.upper() for s in tier_1_symbols)
                    whitelist_set = set(CORE_SYMBOLS)
                    new_symbols = tier_1_set - whitelist_set
                    
                    for symbol in new_symbols:
                        binance_symbol = normalizer.to_binance(symbol)
                        if binance_symbol:
                            channels.append(f"{binance_symbol.lower()}@ticker")
                    
                    if new_symbols:
                        logger.info(f"[WebSocket] Added {len(new_symbols)} Tier 1 symbols for auto-discovery monitoring")
            except Exception as e:
                logger.warning(f"[WebSocket] Failed to add Tier 1 symbols: {e}")
            
            # Add extras for monitoring if needed (e.g. XRP)
            extras = ["xrpusdc"]
            for e in extras:
                if e.upper() not in CORE_SYMBOLS:
                    channels.append(f"{e.lower()}@ticker")
            
            # Create the multiplex socket
            self.ts = self.bm.multiplex_socket(channels)
            
            # CRITICAL: Increase internal queue size to prevent overflow during heavy loop activity
            # The python-binance default is 100, which is too small for 60+ channels plus heavy processing.
            if hasattr(self.ts, '_queue'):
                self.ts._queue = asyncio.Queue(maxsize=1000)
                logger.debug("[WebSocket] Internal queue size boosted to 1000.")

            tier1_count = max(0, len(channels) - len(CORE_SYMBOLS) - len(extras))
            logger.info(f"Subscribing to {len(channels)} channels ({len(CORE_SYMBOLS)} whitelist + {tier1_count} Tier 1)...")
            logger.info(f"[WebSocket] CHANNELS: {channels}")
            
            # Start the listener loop in background
            asyncio.create_task(self._process_stream())

    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=30),
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(100),  # Practically infinite for a daemon
        before_sleep=before_sleep_log(logger, logging.INFO)
    )
    async def _process_stream(self):
        """The Listener Loop (The Ear) - With robust reconnection and drain logic."""
        # --- HYBRID DATA ROUTING (The Bridge) ---
        # Start the "Slow Lane" for TradFi assets (Polling)
        # This complements the "Fast Lane" (Binance WS) below
        asyncio.create_task(self._poll_global_assets(), name="watchtower_bridge")

        try:
            logger.info("[WS] Binance Stream Connecting...")
            async with self.ts as tscm:
                logger.info("[WS] Binance Stream Connected.")
                consecutive_timeouts = 0
                
                while self._keep_running:
                    try:
                        # Process messages with short timeout to stay responsive
                        res = await asyncio.wait_for(tscm.recv(), timeout=2.0)
                        consecutive_timeouts = 0  # Reset on success
                        
                        if res:
                            self._handle_data(res)
                            
                    except asyncio.TimeoutError:
                        consecutive_timeouts += 1
                        # If we get many consecutive timeouts, the connection may be dead
                        if consecutive_timeouts > 30:  # 60 seconds of silence
                            logger.warning("[WS] Connection appears stale - forcing reconnect")
                            raise ConnectionError("Stale connection detected")
                        continue
                        
        except Exception as e:
            error_name = type(e).__name__
            
            # Handle queue overflow gracefully
            if "QueueOverflow" in error_name or "queue" in str(e).lower():
                logger.warning("[WS] Queue overflow - clearing buffer and reconnecting...")
                # Clear old data to prevent stale prices
                self.buffer.clear()
                
            # Handle connection closed
            elif "ReadLoopClosed" in error_name or "closed" in str(e).lower():
                logger.warning("[WS] Connection closed - will reconnect...")
                
            else:
                logger.error(f"[WS] Stream error: {error_name} - {e}")
            
            # Re-raise so Tenacity handles retry
            raise

    async def _poll_global_assets(self):
        """
        The 'Slow Lane' for TradFi assets.
        Polls Watchtower for symbols that Binance WS doesn't cover.
        """
        from services.watchtower import get_watchtower
        from config import get_settings
        from config.settings import get_trading_symbols
        
        tower = get_watchtower()
        
        while self._keep_running:
            try:
                settings = get_settings()
                all_symbols = get_trading_symbols(settings)
                
                # Filter for Non-Crypto (TradFi)
                # Heuristic: If it has Usdt/usdc/busd or is a known crypto, skip.
                # Actually, our taxonomy handles this, or we check common suffixes.
                tradfi_symbols = []
                for s in all_symbols:
                    s_upper = s.upper()
                    # Skip typical crypto pairs
                    if s_upper.endswith("USDC") or s_upper.endswith("USDT") or s_upper.endswith("BUSD"):
                        continue
                    # Skip pure crypto tickers usually found on Binance
                    if s_upper in ["BTC", "ETH", "SOL", "BNB"]: 
                        continue
                        
                    tradfi_symbols.append(s)
                
                if not tradfi_symbols:
                    await asyncio.sleep(60) # Nothing to do
                    continue
                    
                # Poll Watchtower
                for symbol in tradfi_symbols:
                    if not self._keep_running: break
                    
                    price = await tower.fetch_price(symbol)
                    if price and price > 0:
                        # Inject into Buffer (Mocking Binance Format)
                        # payload = {'s': symbol, 'c': price, 'v': 0}
                        self.buffer[symbol] = {
                            's': symbol,
                            'c': str(price), # Binance sends strings
                            'v': "0.0",      # Volume often unknown here
                            'q': "0.0"       # Quote Volume
                        }
                        
                    # Rate Limit Protection (Yahoo is strict)
                    # Distribute checks over the 10s interval
                    await asyncio.sleep(1.0) 
                
                # Wait before next full cycle
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.warning(f"[WS-Bridge] TradFi polling error: {e}")
                await asyncio.sleep(10)


    def _handle_data(self, res):
        """Ingest raw data into the buffer."""
        try:
            if 'data' in res:
                payload = res['data']
                symbol = payload['s'] # Symbol (BTCUSDT)
                self.buffer[symbol] = payload
        except Exception:
            pass

    def get_latest_buffer(self):
        # Return a shallow copy to avoid callers mutating the internal buffer
        try:
            return dict(self.buffer)
        except Exception:
            # Fallback to original buffer if copy fails for any reason
            return self.buffer

    async def stop(self):
        self._keep_running = False
        if self.client:
            await self.client.close_connection()
            logger.info("WebSocket Connection Closed.")

def get_websocket_manager():
    return WebSocketManager()
