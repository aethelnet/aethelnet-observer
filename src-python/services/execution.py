
import asyncio
import logging
import time
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple

# Third-party
import aiohttp
from pytz import timezone as pytz_timezone

# Local imports
from config import get_settings
from core.failsafe import PanicSwitch
from core.error_utils import format_order_error
from services.wallet import get_wallet
from services.tracker import get_performance_tracker
from services.brain import get_engine
from services.universe import get_universe_manager
from services.websocket_manager import get_websocket_manager
from incubator.oracle import get_oracle
from brokers.router import OmniRouter
from services.news_correlation import get_news_correlation
from services.paper_broker import get_broker

# Logger
logger = logging.getLogger("Execution")
logger.setLevel(logging.INFO)

# --- UTILITIES ---

def is_stock_symbol(symbol: str) -> bool:
    """
    Detect if a symbol is a stock (vs crypto).
    Stocks are typically 1-4 characters, indices start with '^', or known stock symbols.
    """
    if not symbol:
        return False
    # Remove common suffixes that might be added
    clean_symbol = symbol.split('/')[0].split(':')[0].upper()
    # Known stock patterns
    if len(clean_symbol) <= 4 and clean_symbol.isalpha():
        # Could be a stock (AAPL, TSLA, SPY, etc.)
        # Exclude common crypto patterns
        if clean_symbol.endswith(('USDT', 'USDC', 'BUSD', 'BTC', 'ETH', 'EUR', 'SOL', 'ADA', 'DOT', 'XRP', 'BNB', 'LTC', 'AVAX', 'LINK', 'MATIC')):
            return False
        return True
    # Indices
    if clean_symbol.startswith('^'):
        return True
    return False

def is_market_open(extended_hours: bool = False) -> Tuple[bool, str]:
    """
    Check if US stock market is currently open.
    
    Regular hours: 9:30 AM - 4:00 PM ET, Monday-Friday
    Extended hours (if enabled): 4:00 AM - 9:30 AM ET (pre-market) and 4:00 PM - 8:00 PM ET (after-hours)
    
    Returns:
        (is_open: bool, reason: str) - Tuple indicating if market is open and reason if closed
    """
    try:
        # Get current time in Eastern Time
        et_tz = pytz_timezone('America/New_York')
        now_et = datetime.now(et_tz)
        
        # Check if weekend
        weekday = now_et.weekday()  # 0=Monday, 6=Sunday
        if weekday >= 5:  # Saturday (5) or Sunday (6)
            next_open = now_et + timedelta(days=(7 - weekday))
            next_open = next_open.replace(hour=9, minute=30, second=0, microsecond=0)
            return False, f"Weekend - Market closed. Next open: {next_open.strftime('%A %B %d, %Y at %I:%M %p ET')}"
        
        # Get current time components
        current_time = now_et.time()
        market_open = datetime.strptime("09:30", "%H:%M").time()
        market_close = datetime.strptime("16:00", "%H:%M").time()
        
        # Check regular market hours
        if market_open <= current_time <= market_close:
            return True, "Market is open (regular hours)"
        
        # Check extended hours if enabled
        if extended_hours:
            pre_market_open = datetime.strptime("04:00", "%H:%M").time()
            pre_market_close = datetime.strptime("09:30", "%H:%M").time()
            after_hours_open = datetime.strptime("16:00", "%H:%M").time()
            after_hours_close = datetime.strptime("20:00", "%H:%M").time()
            
            if (pre_market_open <= current_time < pre_market_close) or \
               (after_hours_open < current_time <= after_hours_close):
                return True, "Market is open (extended hours)"
        
        # Market is closed
        if current_time < market_open:
            # Before market open
            next_open = now_et.replace(hour=9, minute=30, second=0, microsecond=0)
            if now_et.date() != next_open.date():
                # If it's after hours, next open is tomorrow
                next_open += timedelta(days=1)
            return False, f"Pre-market - Market opens at {next_open.strftime('%I:%M %p ET')}"
        else:
            # After market close
            next_open = now_et + timedelta(days=1)
            next_open = next_open.replace(hour=9, minute=30, second=0, microsecond=0)
            # Skip weekends
            while next_open.weekday() >= 5:
                next_open += timedelta(days=1)
            return False, f"After hours - Market closed. Next open: {next_open.strftime('%A %B %d, %Y at %I:%M %p ET')}"
            
    except Exception as e:
        logger.warning(f"[MARKET HOURS] Error checking market hours: {e}. Assuming market is open.")
        return True, "Error checking hours - assuming open"

async def _notify_admin(message: str):
    try:
        from services.bot.core import bot_internal_notify
        success = await bot_internal_notify(message)
        if success:
             logger.info("[NOTIFY] Alert dispatched via Bot Core.")
        else:
             logger.warning("[NOTIFY] Bot Core returned failure.")
    except Exception as e:
        logger.error(f"Failed to send trade notification via Bot Core: {e}")

# --- EXECUTION ENGINE ---

class ExecutionEngine:
    def __init__(self):
        self.tracker = get_performance_tracker()
        self.iteration_count = 0
        self.last_summary_time = time.time()
        self.warned_balance_symbols: Set[str] = set()
        self.consecutive_errors = 0
        self.MAX_CONSECUTIVE_ERRORS = 5
        
        # Load active symbols from settings
        # Note: This might need to be dynamic if symbols change
        self.SYMBOLS = self._load_symbols()
        
    def _load_symbols(self) -> List[str]:
        settings = get_settings()
        whitelist = getattr(settings, 'SYMBOLS_WHITELIST', '')
        if whitelist and isinstance(whitelist, str):
            configured_symbols = [s.strip() for s in whitelist.split(',') if s.strip()]
            if configured_symbols:
                return configured_symbols
        # Fallback
        return ["BTCUSDC", "ETHUSDC", "SOLUSDC", "BNBUSDC", "ADAUSDC"]

    async def tick(self):
        """Execute one complete trading cycle iteration."""
        try:
            settings = get_settings()
            ws_manager = get_websocket_manager()
            brain_engine = get_engine()
            universe_manager = get_universe_manager()
            
            # Check panic switch first
            if PanicSwitch.is_active():
                logger.warning("[TRADING] Panic switch active - skipping trading iteration")
                await asyncio.sleep(1)
                return

            if self.iteration_count == 0:
                 logger.info(f"[EXECUTION] Engine STARTED. Execution Enabled: {settings.EXECUTION_ENABLED} | Testnet: {settings.BINANCE_TESTNET}")

            # Dynamic risk parameter reload (every iteration for real-time control)
            try:
                wallet = get_wallet()
                self.risk_params = wallet.get_risk_params()
                self.SIGNAL_THRESHOLD = self.risk_params.get('threshold', 0.5)
                self.SIGNAL_PERSISTENCE = self.risk_params.get('persistence', 2)
                self.MIN_HOLD_TIME = self.risk_params.get('hold_time', 90)
            except Exception:
                self.risk_params = {}
                self.SIGNAL_THRESHOLD = 0.5 # Default
                self.SIGNAL_PERSISTENCE = 2
                self.MIN_HOLD_TIME = 90

            # Get latest market data
            buffer = ws_manager.get_latest_buffer()
            
            # HEARTBEAT: Confirm loop is running
            # Heartbeat & Sync
            self.iteration_count += 1
            if self.iteration_count == 1 or self.iteration_count % 60 == 0:
                logger.info(f"[HEARTBEAT] Tick {self.iteration_count} | Buffer: {len(buffer)} symbols")

            # AUTOMATIC SELF-HEALING (Every ~5 minutes)
            # Syncs internal tracker with actual exchange balances/positions
            if self.iteration_count % 300 == 0:
                logger.info("[SELF-HEALING] 🩹 Triggering periodic Wallet Sync...")
                # Run sync in background so we don't block tick logic for too long
                asyncio.create_task(self.tracker.sync_with_wallet())

            # Track signals for summary
            symbol_data = {}
            strong_signals = 0
            scan_results = []
            
            # Sync Symbols (Reload occasionally)
            if self.iteration_count % 300 == 0:
                self.SYMBOLS = self._load_symbols()

            # --- DATA INGESTION ---
            if self.iteration_count % 10 == 0:
                logger.info(f"[DEBUG-EXEC] Buffer size: {len(buffer)}")
            for symbol in self.SYMBOLS:
                if symbol in buffer:
                    price_data = buffer[symbol]
                    price = float(price_data.get('c', 0))
                    volume = float(price_data.get('v', 0))
                    
                    if price > 0:
                        # Feed Paper Broker (Live Terminal Support)
                        try:
                            broker = get_broker()
                            broker.on_tick(symbol, {'close': price, 'high': price, 'low': price, 'timestamp': time.time()})
                        except Exception as e:
                            logger.debug(f"Paper Broker Tick Fail: {e}")

                        # Feed brain & universe
                        current_time = time.time() * 1000
                        brain_engine.ingest_candle(int(current_time), price, volume, symbol=symbol)
                        universe_manager.ingest_tick(symbol, current_time, price, volume, False)
                        
                        # Get signal (NEURAL LINK ENABLED)
                        signal = 0.0
                        state = brain_engine.states.get(symbol)
                        if state:
                            # Prioritize the synthesized Neural Signal (Phase + DMD + Z)
                            if 'neural_signal' in state:
                                signal = state['neural_signal']
                            # Fallback to Raw Statistical Z-Score
                            elif state.get('z_score_history'):
                                signal = state['z_score_history'][-1]
                        
                        symbol_data[symbol] = {"price": price, "signal": signal}
                        scan_results.append(f"{symbol}:{signal:.2f}")

                        # --- SHADOW ENGINE INTEGRATION ---
                        try:
                            pass
                        except Exception as e:
                            logger.debug(f"[SHADOW] Tick failed for {symbol}: {e}")

            # Log scan overview
            if self.iteration_count % 10 == 0 and scan_results:
                best_symbol = max(symbol_data.keys(), key=lambda s: abs(symbol_data[s]["signal"])) if symbol_data else "None"
                logger.info(f"[SCAN] {' '.join(scan_results[:5])}... ({len(scan_results)}) → {best_symbol} top")

            # --- AUTO DISCOVERY ---
            if getattr(settings, 'AUTO_DISCOVERY_ENABLED', False):
                await self._process_auto_discovery(buffer, brain_engine, universe_manager)

            # --- LIVE STRATEGY MANAGER (Calendar + Sentiment Wiring) ---
            # Pass market_state to auto_pilot for Event Blackout & News Fuse
            if hasattr(brain_engine, 'live_manager') and brain_engine.live_manager:
                for target_symbol, target_data in symbol_data.items():
                    try:
                        z_score = target_data.get("signal", 0.0)
                        
                        # Get sentiment from brain state
                        sentiment_bias = 0.0
                        ml_prob = None
                        
                        brain_state = brain_engine.states.get(target_symbol, {})
                        sentiment_bias = brain_state.get('sentiment_bias', 0.0)
                        ml_prob = brain_state.get('ml_probability') # None if not computed
                        
                        market_state = {
                            'z_score': z_score,
                            'sentiment_bias': sentiment_bias,
                            'ml_probability': ml_prob, # <--- The Heavy Artillery Signal
                            'price': target_data.get("price", 0.0),
                            'symbol': target_symbol,
                            'velocity': brain_state.get('velocity', 0.0), # [FIXED] Sourced from Brain
                            'trend_strength': brain_state.get('trend_strength', 0.0), # [NEW] Sourced from Brain
                            'levels': brain_state.get('levels', []), # [new] Sourced from Brain (Support/Resistance)
                            'entropy': brain_state.get('entropy', 0.0) # [ALCHEMIST FIX] Sourced from Brain
                        }
                        
                        # [BRAIN TRANSPLANT] Capture The Rat's Decision
                        autopilot_signal = brain_engine.live_manager.on_tick(market_state)
                        
                        # If The Rat speaks, we listen.
                        if autopilot_signal is not None and autopilot_signal != 0.0:
                            # Override the raw Z-Score signal with the Rat's optimized decision
                            # This injects GCP training (Sensitivity) and Safety Checks (Velocity) into the flow.
                            # Only log if it meaningfully overrides the raw signal
                            if abs(z_score - autopilot_signal) > 0.1:
                                logger.info(f"[ENSEMBLE] {target_symbol} Raw: {z_score:.2f} -> Override: {autopilot_signal:.2f}")
                            symbol_data[target_symbol]['signal'] = float(autopilot_signal)
                            symbol_data[target_symbol]['source'] = "AUTOPILOT_RAT" # Mark source for logs
                                
                    except Exception as e:
                        logger.debug(f"[MANAGER] Tick failed for {target_symbol}: {e}")

            # --- TRADING LOGIC ---
            for symbol in self.SYMBOLS:
                if symbol in symbol_data:
                    await self._process_symbol_logic(symbol, symbol_data[symbol], brain_engine, settings)

             # --- STOP LOSS & PROFIT TARGET ENFORCEMENT ---
            await self._enforce_stops_and_targets(symbol_data, settings)

            # --- SUMMARY LOGGING ---
            await self._log_summary(symbol_data, strong_signals)
            
            # --- SLEEP THROTTLING ---
            resource_mode = getattr(settings, 'RESOURCE_MODE', 'ECO').upper()
            sleep_time = 2.0 if resource_mode == "ECO" else (0.5 if resource_mode == "ELITE" else 1.0)
            
            self.consecutive_errors = 0 # Reset on success
            await asyncio.sleep(sleep_time)

        except (ConnectionError, TimeoutError) as e:
            self.consecutive_errors += 1
            logger.warning(f"[TRADING] Network error: {e}. Retrying...")
            if self.consecutive_errors >= self.MAX_CONSECUTIVE_ERRORS:
                logger.critical("[TRADING] CRITICAL: Too many consecutive network errors.")
                # PanicSwitch.activate("Too many consecutive network errors")
            await asyncio.sleep(5)
        except Exception as e:
             self.consecutive_errors += 1
             logger.error(f"[TRADING] Unexpected error: {e}", exc_info=True)
             if self.consecutive_errors >= self.MAX_CONSECUTIVE_ERRORS:
                  logger.critical("[TRADING] CRITICAL: System instability.")
                  # PanicSwitch.activate(f"Consecutive errors: {e}")
             await asyncio.sleep(1)

    async def _process_auto_discovery(self, buffer, brain_engine, universe_manager):
        try:
            from services.auto_discovery_engine import get_auto_discovery_engine
            auto_engine = get_auto_discovery_engine()
            active_discovered = auto_engine.get_active_symbols()
            for symbol in active_discovered:
                if symbol in buffer:
                    price_data = buffer[symbol]
                    price = float(price_data.get('c', 0))
                    volume = float(price_data.get('v', 0))
                    current_time = time.time() * 1000
                    brain_engine.ingest_candle(int(current_time), price, volume, symbol=symbol)
                    universe_manager.ingest_tick(symbol, current_time, price, volume, False)
                    
                    signal = 0.0
                    if brain_engine.z_score_history:
                        signal = brain_engine.z_score_history[-1] # Simplification
                    
                    await auto_engine.process_tick(symbol, price, signal)
        except Exception as e:
            logger.debug(f"[AUTO-DISCOVERY] Error: {e}")

    async def _process_symbol_logic(self, symbol, data, brain_engine, settings):
        price = data["price"]
        # [ARMADA PATCH] Prioritize Neural Signal (Exoskeleton) over raw Z-Score
        try:
            state = brain_engine._get_state(symbol)
            signal = state.get('neural_signal', data["signal"])
            # Fallback if neural_signal is None/0 but we have raw signal
            if not signal and data["signal"]: 
                signal = data["signal"]
        except Exception:
            signal = data["signal"]
            
        # --- REVERSION TOGGLE (Mean Reversion Mode) ---
        if getattr(settings, 'USE_RAT_MEAN_REVERSION', False) or getattr(settings, 'SIGNAL_REVERSION', False):
            # Invert the signal: High Z-Score (overbought) becomes negative (SELL)
            signal = -signal
        
        # Stock Market Checks
        if is_stock_symbol(symbol):
            extended_hours = getattr(settings, 'ALPACA_EXTENDED_HOURS', False)
            market_open, reason = is_market_open(extended_hours=extended_hours)
            if not market_open:
                if self.iteration_count % 60 == 0:
                    logger.info(f"[MARKET HOURS] {symbol}: {reason}")
                return

        # --- MAX DAILY LOSS KILL SWITCH ---
        # Stop everything if we bled too much today
        daily_loss_limit = getattr(settings, 'MAX_DAILY_LOSS', 500.0)
        current_daily_pnl = self.tracker.get_daily_pnl()
        
        if current_daily_pnl <= -daily_loss_limit:
            if self.iteration_count % 30 == 0:
                logger.critical(f"[KILL SWITCH] 🛑 DAILY LOSS LIMIT HIT! PnL: ${current_daily_pnl:.2f} <= -${daily_loss_limit:.2f}. TRADING HALTED.")
            return

        # Decision Logic
        use_oracle = getattr(settings, 'ORACLE_ENABLED', True)
        use_preset = getattr(settings, 'USE_PRESET_FILTERS', False)
        
        should_trade = False
        truth_score = 0.0
        decision_reason = ""
        
        if use_oracle and not use_preset:
             # ORACLE
             oracle_state = self.tracker._collect_oracle_signals(symbol, price, brain_engine, settings)
             oracle = get_oracle()
             truth_score = oracle.calculate_truth_score(oracle_state)
             if truth_score is None: truth_score = 0.0
             
             # Dynamic Oracle Threshold: Matches the user's Risk Slider exactly
             ORACLE_THRESHOLD = self.SIGNAL_THRESHOLD 
             
             # [OVERRIDE] LEGENDARY MOMENTUM (Z > 2.0) - Bypass News/Oracle
             # 2.0 is statistically significant (95%). We trust the math.
             if abs(signal) > 2.0:
                 should_trade = True
                 decision_reason = f"LEGEND MOMENTUM (Z={signal:.2f})"
                 truth_score = signal # Trust the raw momentum
                 if self.iteration_count % 20 == 0:
                      logger.info(f"[EXECUTION] {symbol} LEGENDARY OVERRIDE (Z={signal:.2f})")
             
             elif abs(truth_score) > ORACLE_THRESHOLD:
                 should_trade = True
                 decision_reason = f"Oracle truth_score={truth_score:.3f}"
                 if self.iteration_count % 20 == 0:
                      logger.info(f"[ORACLE] {symbol} score={truth_score:.3f}")
        else:
             # PRESET
             # Use dynamic threshold from RISK slider
             if abs(signal) > self.SIGNAL_THRESHOLD:
                 # Check persistence from RISK slider
                 if not self.tracker.check_signal_persistence(symbol, signal):
                      # We need to ensure check_signal_persistence uses our current persistence req
                      # but for now we'll just let it use the tracker's internal logic
                      pass
                 
                 should_trade = True
                 decision_reason = f"Preset threshold={self.SIGNAL_THRESHOLD:.3f}"
                 truth_score = signal
        if should_trade:
             # --- SENTIMENT OVERRIDE (VETO) ---
             # If Reddit/News sentiment is strongly negative (-0.5) but signal says BUY (+1.5), block it.
             # If sentiment is strongly positive (+0.5) but signal says SELL (-1.5), block it.
             try:
                 sym_state = brain_engine._get_state(symbol) if hasattr(brain_engine, '_get_state') else brain_engine.states.get(symbol, {})
                 sentiment_bias = sym_state.get('sentiment_bias', 0.0)
                 
                 # Only veto if the sentiment is strong enough to matter
                 if abs(sentiment_bias) >= 0.4:
                     # Check for contradiction: Math says Buy (signal > 0), Sentiment says Sell (bias < 0)
                     if (signal > 0 and sentiment_bias < 0) or (signal < 0 and sentiment_bias > 0):
                         if self.iteration_count % 10 == 0:
                             logger.warning(f"[SENTIMENT VETO] 🛑 Swarm blocked {symbol} trade! Math: {signal:.2f}, Sentiment: {sentiment_bias:.2f}")
                         should_trade = False
             except Exception as e:
                 logger.debug(f"[SENTIMENT VETO] Error checking sentiment: {e}")
                 
        if should_trade:
            trade_signal = truth_score if (use_oracle and not use_preset) else signal
            
            # Check Existing Position
            if symbol in self.tracker.positions:
                # If we have a position and signal is SELL (negative), we must allow execution
                if trade_signal < 0:
                    await self._execute_sell(symbol, price, decision_reason, trade_signal, settings)
                return # Don't try to buy more
            
            position_size_pct = settings.MAX_POSITION_SIZE
            if trade_signal > 0: # BUY
                await self._execute_buy(symbol, price, decision_reason, trade_signal, settings)
            elif trade_signal < 0: # SELL
                await self._execute_sell(symbol, price, decision_reason, trade_signal, settings)

    async def _execute_buy(self, symbol, price, reason, signal, settings):
        if symbol in self.tracker.positions:
             # Already long (assuming single position per symbol)
             return

        # Execution Logic (Router, Wallet Check)
        if not settings.EXECUTION_ENABLED:
             sim_quantity = 0.001
             logger.info(f"[SIMULATION] BUY {sim_quantity} {symbol} @ {price} ({reason})")
             self.tracker.open_position(symbol, "LONG", price, sim_quantity)
             
             # [BIFROST] Delegate to Swarm
             try:
                 from routers.swarm import get_swarm_manager
                 swarm = get_swarm_manager()
                 
                 # Determine Mode
                 trade_mode = "PAPER" # Default to safety
                 if settings.EXECUTION_ENABLED and not getattr(settings, 'BINANCE_PAPER', True):
                     trade_mode = "LIVE"
                 
                 await swarm.broadcast_order(symbol, "BUY", sim_quantity, price, reason, mode=trade_mode)
             except Exception as e:
                 logger.debug(f"Swarm delegation failed: {e}")
             return

        # Real Execution
        try:

            from brokers.router import get_omni_router
            router = get_omni_router()
            wallet = get_wallet()
            
            # --- SMART POSITION SIZING ---
            # 1. Get Trading Pool Balance (USDC/USDT)
            # We blindly assume USDC for now as per settings defaults, or check multiple
            capital = wallet.get_trading_pool_balance("USDC")
            if capital < 10: # Try USDT if USDC is empty
                capital = wallet.get_trading_pool_balance("USDT")
            
            # 2. Calculate Target Position Size (USD Value)
            # Default 5% of trading pool, but handle Small Accounts
            pos_size_pct = settings.MAX_POSITION_SIZE
            
            # SMALL ACCOUNT OVERRIDE: If capital < $200, use larger % to hit exchange mins
            if capital < 200:
                pos_size_pct = max(pos_size_pct, 0.40) # Use 40% for small accounts
            
            # ROLE SEPARATION: Apply Hilbert Phase size multiplier
            # When cycle phase confirms entry signal, position is 30% larger
            size_mult = 1.0
            try:
                brain_engine = get_engine()
                sym_state = brain_engine.states.get(symbol, {})
                hilbert_mult = sym_state.get('size_multiplier', 1.0)
                
                # [GHOST CONFIDENCE] Apply prediction-accuracy based scaling
                from services.watchtower import get_watchtower
                tower = get_watchtower()
                ghost_mult = tower.get_confidence_multiplier(symbol)
                
                # [ENTROPY PENALTY] Reduce size if uncertainty is high
                entropy = sym_state.get('entropy', 0.1) # 0.0 to 1.0
                entropy_mult = max(0.2, 1.0 - (entropy * 0.8)) # High entropy (e.g. 0.8) -> multiplier 0.36
                
                # Compound all multipliers
                size_mult = hilbert_mult * ghost_mult * entropy_mult
                
                if size_mult != 1.0:
                    logger.info(f"[EXECUTION] Size adjustment {symbol}: Hilbert={hilbert_mult:.2f}x, Ghost={ghost_mult:.2f}x, EntropyPenalty={entropy_mult:.2f}x → {size_mult:.2f}x")
            except Exception:
                pass
                
            target_value = capital * pos_size_pct * size_mult
            
            # Safety: Ensure we have enough capital
            # Exchange usually requires ~$10. We'll allow $5 for now.
            if capital < 5 or target_value < 5:
                # Minimum trade size check
                if self.iteration_count % 50 == 0:
                    logger.warning(f"[EXECUTION][WARN] Insufficient Capital/Size: Pool=${capital:.2f}, Target=${target_value:.2f}")
                return

            # 3. Calculate Quantity
            qty = target_value / price
            
            # 4. Precision Truncation (Safety: Let the broker/exchange precision helper handle it)
            # Hardcoded .5f is too precise for some meme coins and causes LOT_SIZE errors.
            # We keep it as-is here but THE BROKER will sanitize it properly via CCXT.
            # We ensure we are at least $10 (Binance MinNotional) + 10% buffer
            MIN_USD = 11.0 
            if target_value < MIN_USD:
                 target_value = MIN_USD
                 qty = target_value / price
            
            # Pass full precision string to avoid float noise
            qty_str = f"{qty:.8f}"
            qty = float(qty_str)
            logger.debug(f"[EXECUTION] Calculated qty for {symbol}: {qty_str}")
            
            # Generate Local ID for Tracking (Fallback and Searchability)
            import uuid
            client_oid = f"AUR-{str(uuid.uuid4())[:8].upper()}"
            
            logger.info(f"[LIVE][BUY] EXECUTING BUY: {symbol} | Qty: {qty} | Val: ${target_value:.2f} | Pool: ${capital:.2f} | REF: {client_oid}")
            
            
            # [BIFROST] Swarm Delegation Check
            if getattr(settings, "SWARM_EXECUTION_ENABLED", False):
                try:
                    from routers.swarm import get_swarm_manager
                    swarm = get_swarm_manager()
                    
                    # Determine Mode
                    trade_mode = "PAPER"
                    if settings.EXECUTION_ENABLED and not getattr(settings, 'BINANCE_PAPER', True):
                        trade_mode = "LIVE"
                        
                    await swarm.broadcast_order(symbol, "BUY", qty, price, reason, mode=trade_mode)
                    logger.info(f"[EXECUTION] Delegated BUY {symbol} {qty} to Swarm (Mode: {trade_mode}).")
                    # We return early, assuming Swarm handles it.
                    # TODO: Listen for confirmation?
                    
                    self.tracker.record_trade({
                        "symbol": symbol, "side": "BUY", "quantity": qty, "price": price, 
                        "pnl": 0, "timestamp": self.tracker._get_timestamp(),
                        "delegated": True
                    })
                    return
                except Exception as e:
                    logger.debug(f"Swarm delegation failed: {e}")

            # TODO: Pass clientOrderId to router.place_order if supported, currently just tracking locally
            order_result = await router.place_order(symbol, "BUY", "MARKET", qty, price)
            
            if order_result:
                tx_id = order_result.get('orderId') or order_result.get('clientOrderId') or client_oid
                avg_price = order_result.get('average', price) # Fallback if not returned
                if not avg_price or avg_price == 0: avg_price = price
                
                # Risk Calc for Notification
                sl_price = float(avg_price) * (1.0 - settings.STOP_LOSS)
                tp_price = float(avg_price) * (1.0 + settings.PROFIT_TARGET)
                
                # Calculate estimated PnL at target
                est_win_usd = (tp_price - float(avg_price)) * qty
                est_loss_usd = (float(avg_price) - sl_price) * qty
                
                # Detect venue from symbol
                venue = "Hyperliquid" if symbol.endswith("USDC") else "Binance" if symbol.endswith(("USDT", "BUSD")) else "Alpaca"
                
                try:
                    msg = (
                        f"<b>[ 🟢 ENTRY EXECUTED ]</b>\n"
                        f"<code>════════════════════════</code>\n"
                        f"ASSET: <b>{symbol}</b>\n"
                        f"VENUE: <b>{venue}</b>\n"
                        f"SIDE : <b>LONG</b>\n"
                        f"PRICE: <code>${float(avg_price):,.8f}</code>\n"
                        f"SIZE : <code>{qty} (~${target_value:.2f})</code>\n"
                        f"<code>────────────────────────</code>\n"
                        f"TARGET: <code>${tp_price:.8f} (+{settings.PROFIT_TARGET*100:.1f}%)</code>\n"
                        f"STOP  : <code>${sl_price:.8f} (-{settings.STOP_LOSS*100:.1f}%)</code>\n"
                        f"R/R   : <code>Risk ${est_loss_usd:.2f} / Reward ${est_win_usd:.2f}</code>\n"
                        f"ID    : <code>#{tx_id}</code>\n"
                        f"<code>════════════════════════</code>"
                    )
                    await _notify_admin(msg)
                except Exception as e:
                    logger.error(f"Failed to send BUY notification: {e}")
                try:
                    from lgnn.websocket import manager
                    import json
                    asyncio.create_task(manager.broadcast(json.dumps({
                        "type": "TRADE_EXECUTION",
                        "payload": {
                            "symbol": symbol,
                            "side": "LONG",
                            "price": float(avg_price),
                            "qty": qty,
                            "usd_value": target_value,
                            "venue": venue,
                            "tx_id": tx_id
                        }
                    })))
                except Exception as e:
                    logger.debug(f"Failed to broadcast TRADE_EXECUTION: {e}")

                logger.info(f"[EXECUTION][SUCCESS] BUY SUCCESS: {symbol} Order #{tx_id}")
                
                # --- STOP LOSS CALCULATION ---
                # Fix: Calculate and attach explicit stop price to the position
                stop_price = None
                if settings.STOP_LOSS_ENABLED and settings.STOP_LOSS > 0:
                    stop_loss_pct = settings.STOP_LOSS
                    stop_price = float(avg_price) * (1.0 - stop_loss_pct)
                    logger.info(f"[RISK] Attaching Stop Loss at ${stop_price:.2f} (-{stop_loss_pct*100:.1f}%)")

                # Update Tracker
                self.tracker.open_position(symbol, "LONG", avg_price, qty, stop_price=stop_price)
            else:
                logger.error(f"[EXECUTION][FAIL] BUY FAILED for {symbol}: Router returned None")
                
        except Exception as e:
            logger.error(f"[EXECUTION][CRITICAL] BUY CRITICAL ERROR: {type(e).__name__}: {e}", exc_info=True)

    async def _execute_sell(self, symbol, price, reason, signal, settings):
        # DEBOUNCE: If we recently closed this (simulated or real), don't spam exit logic
        if not hasattr(self, "recently_closed"):
            self.recently_closed = {}
        
        # Cleanup old entries
        current_time = time.time()
        for s in list(self.recently_closed.keys()):
            if current_time - self.recently_closed[s] > 300: # 5 min cool-off
                del self.recently_closed[s]
                
        if symbol in self.recently_closed:
            return

        if symbol not in self.tracker.positions:
            return
            
        pos = self.tracker.positions[symbol]
        qty = pos.get('quantity', 0)
        entry_price = float(pos.get('entry_price', price))
        
        if not settings.EXECUTION_ENABLED:
            logger.info(f"[SIMULATION] SELL {qty} {symbol} @ {price}")
            self.tracker.close_position(symbol, price)
            
            # [BIFROST] Delegate to Swarm
            try:
                from routers.swarm import get_swarm_manager
                swarm = get_swarm_manager()
                
                # Determine Mode (Simulation context is always PAPER unless explicitly overriding logic elsewhere, 
                # but let's stick to the settings for consistency or force PAPER for simulation block)
                trade_mode = "PAPER" 
                
                await swarm.broadcast_order(symbol, "SELL", qty, price, reason, mode=trade_mode)
            except Exception as e:
                logger.debug(f"Swarm delegation failed: {e}")
            return

        try:
             from brokers.router import get_omni_router
             router = get_omni_router()
             
             # [BIFROST] Swarm Delegation Check (SELL)
             if getattr(settings, "SWARM_EXECUTION_ENABLED", False):
                 try:
                     from routers.swarm import get_swarm_manager
                     swarm = get_swarm_manager()
                     
                     # Determine Mode
                     trade_mode = "PAPER"
                     if settings.EXECUTION_ENABLED and not getattr(settings, 'BINANCE_PAPER', True):
                         trade_mode = "LIVE"
                         
                     await swarm.broadcast_order(symbol, "SELL", qty, price, reason, mode=trade_mode)
                     logger.info(f"[EXECUTION] Delegated SELL {symbol} {qty} to Swarm (Mode: {trade_mode}).")
                     
                     self.tracker.close_position(symbol, price) # Assume Swarm closes it? Or wait? 
                     # For now, we assume close for tracking purposes.
                     return
                 except Exception as e:
                     logger.debug(f"Swarm delegation failed: {e}")

             logger.info(f"[LIVE] SELL {qty} {symbol} @ {price}")
             order_result = await router.place_order(symbol, "SELL", "MARKET", qty, price, params={"reduceOnly": True, "reduce_only": True})
             
             if order_result:
                 # PnL Calculation
                 pnl = (price - entry_price) * qty
                 pnl_pct = ((price - entry_price) / entry_price) * 100
                 sign = "+" if pnl >= 0 else "-"
                 outcome = "WIN" if pnl >= 0 else "LOSS"
                 outcome_emoji = "🟢" if pnl >= 0 else "🔴"
                 
                 # Dynamic Context based on Reason
                 context_note = "Trend Reversal"
                 if "Profit Target" in reason: context_note = "Target Hit"
                 elif "Stop Loss" in reason: context_note = "Risk Limit"
                 elif "Trailing" in reason: context_note = "Profit Lock"
                 
                 # Detect venue from symbol
                 venue = "Hyperliquid" if symbol.endswith("USDC") else "Binance" if symbol.endswith(("USDT", "BUSD")) else "Alpaca"
                 
                 try:
                     msg = (
                        f"<b>[ {outcome_emoji} EXIT EXECUTION ]</b>\n"
                        f"<code>════════════════════════</code>\n"
                        f"ASSET: <b>{symbol}</b>\n"
                        f"VENUE: <b>{venue}</b>\n"
                        f"TYPE : {context_note}\n"
                        f"PRICE: <code>${price:,.8f}</code>\n"
                        f"PnL  : <b>{sign}${abs(pnl):.2f} ({sign}{abs(pnl_pct):.2f}%)</b>\n"
                        f"<code>────────────────────────</code>\n"
                        f"REASON: {reason}\n"
                        f"RESULT: <b>{outcome}</b>\n"
                        f"<code>════════════════════════</code>"
                     )
                     await _notify_admin(msg)
                 except Exception as e:
                     logger.error(f"Failed to send SELL notification: {e}")
                 
                 # ONLY CLOSE TRACKER IF ORDER WAS SUCCESSFUL
                 self.tracker.close_position(symbol, price)
                 
                 try:
                     from lgnn.websocket import manager
                     import json
                     asyncio.create_task(manager.broadcast(json.dumps({
                         "type": "TRADE_EXECUTION",
                         "payload": {
                             "symbol": symbol,
                             "side": "SELL",
                             "price": float(price),
                             "qty": qty,
                             "pnl": pnl,
                             "pnl_pct": pnl_pct,
                             "venue": venue,
                             "reason": reason
                         }
                     })))
                 except Exception as e:
                     logger.debug(f"Failed to broadcast TRADE_EXECUTION: {e}")
             else:
                 # CRITICAL: Order failed (None returned). DO NOT CLOSE POSITION via tracker.
                 # This prevents "Ghost Positions" where we think we sold but didn't.
                 logger.error(f"[EXECUTION][FAIL] SELL FAILED for {symbol}: Router returned None.")
                 
                 last_err = getattr(router, '_last_error', "")
                 # AUTO-HEAL for Hyperliquid: If HL says no position, purge it locally.
                 if last_err and ("No open position" in last_err or "REDUCE-ONLY ABORTED" in last_err):
                     logger.warning(f"[SELF-HEALING] Detected Ghost Position for {symbol} on Hyperliquid. Purging from tracker...")
                     self.tracker.close_position(symbol, price)
                     await _notify_admin(f"<b>[ 👻 GHOST EXORCISED ]</b>\nSystem removed invalid position for {symbol}.\n(Exchange reported zero balance)")
                 else:
                     logger.error("Position retained in tracker.")
        except Exception as e:
             logger.error(f"[ORDER] SELL Error: {e}")
             # AUTO-HEAL: If we tried to sell but Binance says "Insufficient Balance" (-2010),
             # it means we are holding a Ghost Position. We must delete it.
             error_str = str(e)
             last_err = getattr(router, '_last_error', "") if 'router' in locals() else ""
             combined_err = f"{error_str} {last_err}"
             
             if "Account has insufficient balance" in combined_err or "-2010" in combined_err or "No open position" in combined_err or "REDUCE-ONLY ABORTED" in combined_err:
                 logger.warning(f"[SELF-HEALING] Detected Ghost Position for {symbol}. Purging from tracker...")
                 self.tracker.close_position(symbol, price)
                 await _notify_admin(f"<b>[ 👻 GHOST EXORCISED ]</b>\nSystem removed invalid position for {symbol}.\n(Exchange reported zero balance)")

    async def _enforce_stops_and_targets(self, symbol_data, settings):
        # ... logic for stop loss and profit target ...
        try:
            open_positions = dict(self.tracker.positions)
            for psym, pinfo in open_positions.items():
                if psym in symbol_data:
                    current_price = symbol_data[psym]['price']
                    entry_price = pinfo.get('entry_price', 0)
                    
                    # --- TRAILING STOP LOGIC ---
                    if getattr(settings, 'TRAILING_STOP', False):
                         # 1. Update High/Low Water Mark for MFE/MAE Tracking
                         self.tracker.update_position_price(psym, current_price)
                         # Refresh pinfo from tracker after update
                         pinfo = self.tracker.positions.get(psym, pinfo)
                         
                         highest = pinfo.get('highest_price', entry_price)
                         
                         # 2. Activation Threshold (Only trail if we are in profit)
                         # [SANITIZED] specific setting or default 0.5%
                         activation_pct = getattr(settings, 'TRAILING_ACTIVATION', 0.005)
                         activation_threshold = 1.0 + activation_pct 
                         
                         if highest > (entry_price * activation_threshold):
                             stop_pct = getattr(settings, 'STOP_LOSS', 0.012)
                             trailing_stop_price = highest * (1.0 - stop_pct)
                             
                             if current_price < trailing_stop_price:
                                 locked_pnl = (current_price - entry_price) / entry_price
                                 logger.info(f"[TRAILING] {psym} Triggered! High: ${highest:.2f} -> Now: ${current_price:.2f} (Locked +{locked_pnl*100:.2f}%)")
                                 await self._execute_sell(psym, current_price, f"Trailing Stop (+{locked_pnl*100:.2f}%)", -1, settings)
                                 continue
                    
                    # --- HARD STOP LOSS ---
                    stop = pinfo.get('stop_price')
                    if stop and current_price <= stop:
                        logger.warning(f"[STOP] {psym} price {current_price} <= {stop}")
                        await self._execute_sell(psym, current_price, "Stop Loss", -1, settings)
                        continue

                    # --- PROFIT TARGET ---
                    target = getattr(settings, 'PROFIT_TARGET', 0.0)
                    if target > 0 and entry_price > 0:
                        profit = (current_price - entry_price) / entry_price
                        if profit >= target:
                            logger.info(f"[PROFIT] {psym} hit target {profit*100:.2f}%")
                            await self._execute_sell(psym, current_price, "Profit Target", -1, settings)

        except Exception as e:
            logger.debug(f"Stop/Target check failed: {e}")

    async def _log_summary(self, symbol_data, strong_signals):
        current_time = time.time()
        if current_time - self.last_summary_time >= 30:
             stats = self.tracker.get_stats()
             logger.info(f"[SUMMARY] P&L: ${stats['total_pnl']:.2f} | Trades: {stats['total_trades']}")
             self.tracker._save_to_disk()
             self.last_summary_time = current_time
