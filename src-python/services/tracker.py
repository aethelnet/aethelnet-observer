import os
import json
import time
import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from config import get_settings
from services.wallet import get_wallet
from services.database import get_database
from services.websocket_manager import get_websocket_manager

# Logger Setup
logger = logging.getLogger("Tracker")
logger.setLevel(logging.INFO)

class PerformanceTracker:
    # Persistence file path (in project root)
    PERSISTENCE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "performance.json")
    
    def __init__(self):
        self.positions = {}  # symbol -> {"side": "LONG/SHORT", "entry_price": float, "quantity": float, "entry_time": float}
        self.closed_trades = []
        self.total_pnl = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        self.signal_history = {}  # symbol -> [last 5 signals] for persistence tracking
        self.last_save_time = time.time()
        self.peak_equity = 0.0  # Track highest portfolio value for drawdown percentage
        self.starting_balance = 10000.0  # Default starting balance (10k)
        
        # Load persisted data if exists
        self._load_from_disk()

        # Load open positions from database so positions survive restarts (best-effort).
        try:
            db = get_database()
            loaded_positions = []
            if hasattr(db, "get_open_positions"):
                loaded_positions = db.get_open_positions()
            elif hasattr(db, "get_positions"):
                loaded_positions = db.get_positions()
            elif hasattr(db, "list_positions"):
                loaded_positions = db.list_positions()
            else:
                loaded_positions = []

            for p in loaded_positions:
                # Accept multiple possible field names for compatibility with different DB payloads.
                symbol = p.get("symbol") or p.get("ticker") or p.get("sym")
                if not symbol:
                    continue
                
                qty = float(p.get("quantity", p.get("qty", 0.0)))
                # SKIP GHOSTS: Do not load positions with 0 quantity
                if qty <= 0.00001:
                    continue

                self.positions[symbol] = {
                    "side": p.get("side", "LONG"),
                    "entry_price": float(p.get("entry_price", p.get("avg_price", p.get("price", 0.0)))),
                    "quantity": qty,
                    "entry_time": float(p.get("entry_time", time.time()))
                }

        except Exception:
            logger.debug("Failed to load open positions from DB", exc_info=True)
            pass
    async def sync_with_wallet(self):
        """
        Hydrates the tracker from the actual wallet state.
        - Adds missing positions (Orphan recovery)
        - Removes invalid positions (Ghost busting) 
        - Attempts to fetch real entry time/price from Order History
        """
        try:
            logger.info("[TRACKER] 🔄 Starting Wallet Sync (Hydration)...")
            wallet = get_wallet()
            # Force refresh from exchange
            balances = await wallet.get_all_balances()
            spot_balances = balances.get('binance_spot', {})
            
            # 1. Get Real Positions (Qty * Price > Dust)
            real_positions = {}
            from services.symbol_normalizer import get_symbol_normalizer
            normalizer = get_symbol_normalizer()
            
            # We need a price map to value the assets
            from services.data_manager import get_data_manager
            dm = get_data_manager()
            
            # Iterate through ALL sub-wallets (Binance Spot, Futures, Alpaca)
            for wallet_key, sub_wallet in balances.items():
                # Skip the Mother Vault
                if "mother_vault" in wallet_key: continue
                
                for asset, bal in sub_wallet.items():
                    free = float(bal.get('free', 0))
                    locked = float(bal.get('locked', 0))
                    total = free + locked
                    if total <= 0: continue
                    
                    # Ignore stablecoins / fiat
                    if asset in ["USDT", "USDC", "FDUSD", "TUSD", "USD", "EUR"]:
                         continue 
                    
                    # Handle BNB dust
                    if asset == "BNB" and total < 0.1: 
                         continue

                    # Construct Symbol
                    # For Alpaca, the 'asset' is already the symbol (e.g., 'NFLX')
                    # For Crypto, we usually append USDC (e.g. BTC -> BTCUSDC)
                    symbol = asset
                    if wallet_key.startswith('binance'):
                        symbol = f"{asset}USDC"
                    
                    # Calculate Value
                    current_price = 0.0
                    if 'all_prices' not in locals():
                        try:
                            all_prices = await dm.get_all_ticker_prices()
                        except:
                            all_prices = {}
                            
                    current_price = all_prices.get(symbol, all_prices.get(symbol.replace('USDC', 'USDT'), 0.0))
                    
                    if current_price == 0:
                        try:
                            price_lookup = await asyncio.to_thread(dm.get_latest_price, symbol)
                            current_price = float(price_lookup or 0.0)
                        except:
                            pass
                    
                    # if current_price <= 0: continue (Logic moved to Line 140)
                    
                    value_usd = total * current_price

                    # DUST FILTER: Increase threshold to prevent "Infinite Execution Loops" on unsellable scraps
                    # Binance Min Notional is usually $5-$10. We ignore anything under $2.00 to be safe.
                    # For Alpaca (Stocks), we can keep it lower ($0.05) to track even small fractional shares.
                    threshold = 2.00 if "USDC" in symbol or "USDT" in symbol else 0.05
                    
                    if value_usd > threshold or (current_price == 0 and total > 0):
                        real_positions[symbol] = {
                            "quantity": total,
                            "current_price": current_price if current_price > 0 else 0.0 # explicit
                        }
            
            # 1.5 Fetch Broker Positions (Alpaca/Exchanges returning separate position endpoints)
            try:
                from brokers.router import get_omni_router
                router = get_omni_router()
                broker_positions = await router.get_all_positions()
                
                for bp in broker_positions:
                    sym = bp.get('symbol')
                    qty = float(bp.get('qty', 0))
                    
                    if not sym or abs(qty) < 0.0001: continue
                    
                    # If this symbol was already found via wallet balance (e.g. Crypto), prefer the Position data
                    # as it contains more metadata (entry price, pnl)
                    current_price = float(bp.get('current_price', 0))
                    if current_price == 0 and sym in real_positions:
                        current_price = real_positions[sym]['current_price']
                        
                    entry_price = float(bp.get('entry_price', 0))
                    # Fallback: If entry price is 0 (broken metadata), use current price as best guess
                    if entry_price == 0 and current_price > 0:
                        entry_price = current_price
                        logger.warning(f"[TRACKER] ⚠️ Fixed missing entry price for {sym} using current price: {entry_price}")
                        
                    real_positions[sym] = {
                        "quantity": qty,
                        "current_price": current_price,
                        "entry_price": float(bp.get('entry_price', 0)),
                        "unrealized_pnl": float(bp.get('unrealized_pnl', 0)),
                        "side": bp.get('side', 'long').upper()
                    }
                    # logger.info(f"[TRACKER] Broker Reported Position: {sym} (Qty: {qty})")
            except Exception as e:
                logger.warning(f"[TRACKER] Broker position fetch failed: {e}")

            # 2. Reconcile: Tracker vs Reality
            
            # A) Detect Ghosts (In Tracker, Not in Reality)
            tracked_symbols = list(self.positions.keys())
            for sym in tracked_symbols:
                if sym not in real_positions:
                    logger.warning(f"[TRACKER] 👻 Ghost Detected: {sym}. Purging...")
                    self.close_position(sym, 0.0, force_close=True) # FORCE bypass hold time
            
            # B) Detect Orphans (In Reality, Not in Tracker)
            for sym, info in real_positions.items():
                if sym not in self.positions:
                    logger.info(f"[TRACKER] 👶 Orphan Found: {sym} (Qty: {info['quantity']}). Adopting...")
                    
                    # Try to find original entry time/price
                    entry_time = time.time()
                    entry_price = info['current_price']
                    
                    try:
                        # Attempt to fetch trades
                        from brokers.router import OmniRouter
                        router = OmniRouter()
                        trades = await router.get_trades(sym, limit=5) # Last 5 trades
                        if trades:
                            # Find the last BUY
                            for t in reversed(trades):
                                if t.get('isBuyer') or t.get('side') == 'BUY':
                                    entry_price = float(t.get('price', entry_price))
                                    entry_time = t.get('time', time.time() * 1000) / 1000.0
                                    logger.info(f"[TRACKER] 🕰️ Found History for {sym}: Entered {datetime.fromtimestamp(entry_time)}")
                                    break
                    except Exception as e:
                        logger.warning(f"[TRACKER] History fetch failed for {sym}: {e}. Using current time.")
                        
                    # ADD TO TRACKER
                    self.positions[sym] = {
                        "side": "LONG",
                        "entry_price": entry_price,
                        "quantity": info['quantity'],
                        "entry_time": entry_time,
                        "highest_price": info['current_price'],
                        "lowest_price": info['current_price'],
                        "stop_price": None # Reset stops for safety, let execution re-calc
                    }
                    # Subscribe to live data for PnL tracking
                    try:
                        get_websocket_manager().subscribe([sym])
                    except Exception:
                        pass
            
            # C) Price Sanity Check for existing positions
            # If the entry price is wildly different from reality (>2x), it's likely a symbol collision (e.g. QQQ vs NQ futures)
            for sym, tracked in self.positions.items():
                if sym in real_positions:
                    reality = real_positions[sym]
                    if reality['current_price'] > 0:
                        ratio = tracked['entry_price'] / reality['current_price']
                        if ratio > 2.0 or ratio < 0.5:
                            logger.warning(f"[TRACKER] 🚨 Price Discrepancy for {sym}: Tracked ${tracked['entry_price']} vs Reality ${reality['current_price']}. Re-baselining...")
                            tracked['entry_price'] = reality['current_price']
                            tracked['stop_price'] = None # Kill stop to prevent immediate trigger
                        
            # Persist the clean state
            self._save_to_disk()
            logger.info("[TRACKER] ✅ Hydration Complete.")
            
        except Exception as e:
             logger.error(f"[TRACKER] Hydration Error: {e}")
    def open_position(self, symbol: str, side: str, price: float, quantity: float, stop_price: float = None):
        """Open a new position.

        stop_price: optional numeric stop price for the position (exchange stop or local monitor).
        """
        if symbol in self.positions:
            # Close existing position first (attempt best-effort exit using current price)
            try:
                self.close_position(symbol, price)
            except Exception:
                # If close fails, continue to open new position record (best-effort compatibility)
                logger.debug("Existing position close failed while opening a new one", exc_info=True)

        # Persist the stop price (if any) alongside the in-memory position record.
        self.positions[symbol] = {
            "side": side,
            "entry_price": price,
            "quantity": quantity,
            "entry_time": time.time(),
            "highest_price": price,  # Track highest price for trailing stop (LONG positions)
            "lowest_price": price,   # Track lowest price for trailing stop (SHORT positions)
            "stop_price": stop_price
        }

        # Subscribe to live data for PnL tracking
        try:
            get_websocket_manager().subscribe([symbol])
        except Exception:
            pass
            
        logger.info(f"[TRACKER] Opened {side} position: {symbol} @ ${price:.2f} | stop=${stop_price if stop_price is not None else 'none'}")

    def update_position_price(self, symbol: str, current_price: float):
        """
        Update highest/lowest price for MFE/MAE tracking.
        Call this on every price tick for open positions.
        """
        if symbol not in self.positions:
            return
        
        pos = self.positions[symbol]
        
        # Track extremes
        if current_price > pos.get("highest_price", 0):
            pos["highest_price"] = current_price
        if current_price < pos.get("lowest_price", float('inf')):
            pos["lowest_price"] = current_price

        # Persist open position to DB (best-effort). Try common DB method names for compatibility.
        try:
            db = get_database()
            if hasattr(db, "upsert_position"):
                try:
                    # Try storing minimal canonical payload where supported
                    db.upsert_position(symbol=symbol, quantity=quantity, avg_price=price, metadata={"side": side, "entry_time": self.positions[symbol]["entry_time"]})
                except TypeError:
                    # Older helpers may accept different arg names; fallback to generic call
                    try:
                        db.upsert_position(symbol=symbol, side=side, entry_price=price, quantity=quantity, entry_time=self.positions[symbol]["entry_time"])
                    except Exception:
                        pass
            elif hasattr(db, "insert_position"):
                # Some DB helpers use a positional insert API; pass common arguments.
                try:
                    db.insert_position(symbol, self.positions[symbol]["entry_time"], side, price, quantity)
                except TypeError:
                    # Fallback: try named params
                    try:
                        db.insert_position(symbol=symbol, ts=self.positions[symbol]["entry_time"], side=side, price=price, quantity=quantity)
                    except Exception:
                        pass
        except Exception:
            logger.debug("Failed to persist open position to DB", exc_info=True)

        # Best-effort: attach most-recent persisted signal id (if available) to in-memory position
        try:
            from services.brain import get_engine
            engine = get_engine()
            sid = getattr(engine, "last_signal_ids", {}).get(symbol)
            if sid:
                self.positions[symbol]["signal_id"] = sid
        except Exception:
            pass
        
    def close_position(self, symbol, exit_price, force_close=False):
        """Close an existing position and calculate P&L."""
        if symbol not in self.positions:
            return 0.0
            
        pos = self.positions[symbol]
        entry_price = pos["entry_price"]
        quantity = pos["quantity"]
        side = pos["side"]
        hold_time = time.time() - pos["entry_time"]
        
        # Load settings for Min Hold Time
        settings = get_settings()
        min_hold = getattr(settings, 'MIN_HOLD_TIME', 45)

        # WHIPSAW PROTECTION: Minimum hold time check
        # Check if the singleton execution engine has a dynamic hold time override
        min_hold = getattr(settings, 'MIN_HOLD_TIME', 45)
        try:
            from services.execution import ExecutionEngine
            # Dynamic hold time check simplified
            pass
        except:
            pass
        
        if not force_close and hold_time < min_hold:
            logger.warning(f"[WHIPSAW] Blocked early close: {symbol} held {hold_time:.1f}s < {min_hold}s minimum")
            return 0.0
        
        # Calculate P&L
        if side == "LONG":
            pnl = (exit_price - entry_price) * quantity
        else:  # SHORT
            pnl = (entry_price - exit_price) * quantity
            
        # Update stats
        self.total_pnl += pnl
        self.total_trades += 1
        if pnl > 0:
            self.winning_trades += 1
        
        # Update peak equity for drawdown calculation
        current_equity = self.starting_balance + self.total_pnl
        if current_equity > self.peak_equity:
            self.peak_equity = current_equity
            
        # Record trade
        exit_time = time.time()
        
        # [GEN2] Calculate MFE, MAE, and Regret
        highest_price = pos.get("highest_price", exit_price)
        lowest_price = pos.get("lowest_price", exit_price)
        
        if side == "LONG":
            # MFE = Best possible profit (if exited at peak)
            mfe_pnl = (highest_price - entry_price) * quantity
            # MAE = Worst drawdown during hold
            mae_pnl = (lowest_price - entry_price) * quantity
            # Regret = Money left on the table
            regret = mfe_pnl - pnl if mfe_pnl > pnl else 0
            regret_pct = (highest_price - exit_price) / entry_price if entry_price > 0 else 0
        else:  # SHORT
            mfe_pnl = (entry_price - lowest_price) * quantity
            mae_pnl = (entry_price - highest_price) * quantity
            regret = mfe_pnl - pnl if mfe_pnl > pnl else 0
            regret_pct = (exit_price - lowest_price) / entry_price if entry_price > 0 else 0
        
        trade = {
            "symbol": symbol,
            "side": side,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "quantity": quantity,
            "pnl": pnl,
            "hold_time": hold_time,
            "exit_time": exit_time,
            "entry_time": pos["entry_time"],
            # [GEN2] Regret Metrics
            "mfe_pnl": mfe_pnl,
            "mae_pnl": mae_pnl,
            "regret": regret,
            "regret_pct": regret_pct,
            "highest_price": highest_price,
            "lowest_price": lowest_price
        }
        self.closed_trades.append(trade)
    
        # --- ARCHIVE TRADE (JSONL) ---
        try:
            from services.trade_logger import get_archive
            archive = get_archive()
            archive.log_trade(trade)
        except Exception as e:
            logger.warning(f"[TRACKER] Failed to archive trade: {e}")

        # Persist trade and key metrics to DB (best-effort)
        trade_row_id = None
        try:
            db = get_database()
            # ts in seconds
            ts = time.time()
            trade_row_id = db.insert_trade(symbol, ts, side, exit_price, quantity, metadata={"entry_price": entry_price, "hold_time": hold_time})
            db.insert_metric("total_pnl", self.total_pnl, ts=ts)
            db.insert_metric("total_trades", float(self.total_trades), ts=ts)
            db.insert_metric("peak_equity", float(self.peak_equity), ts=ts)
        except Exception:
            logger.debug("Failed to persist trade/metrics to DB", exc_info=True)
        
        # Best-effort: create mapping between the persisted signal (if known) and this trade
        try:
            db = get_database()
            signal_id = pos.get("signal_id")
            if trade_row_id and signal_id and hasattr(db, "insert_signal_trade"):
                try:
                    db.insert_signal_trade(int(signal_id), int(trade_row_id))
                except Exception:
                    logger.debug("Failed to persist signal->trade mapping", exc_info=True)
        except Exception:
            logger.debug("Failed to write signal->trade mapping (outer)", exc_info=True)

        # Remove position from DB (best-effort) and in-memory
        try:
            db = get_database()
            if hasattr(db, "delete_position"):
                db.delete_position(symbol)
            elif hasattr(db, "remove_position"):
                db.remove_position(symbol)
            elif hasattr(db, "upsert_position"):
                # mark as closed by setting quantity to 0
                try:
                    db.upsert_position(symbol=symbol, quantity=0, avg_price=entry_price, metadata={"side": side, "closed": True})
                except TypeError:
                    # older signature fallback
                    try:
                        db.upsert_position(symbol=symbol, side=side, entry_price=entry_price, quantity=0, entry_time=pos.get("entry_time"))
                    except Exception:
                        pass
        except Exception:
            logger.debug("Failed to remove position from DB", exc_info=True)

        # Remove in-memory position
        del self.positions[symbol]
        
        logger.info(f"[TRACKER] Closed {side} position: {symbol} @ ${exit_price:.2f} | P&L: ${pnl:.4f} | Hold: {hold_time:.1f}s")
        
        # Auto-save after each trade
        self._save_to_disk()
        
        return pnl
        
    def get_stats(self):
        """Returns consolidated stats for reporting"""
        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0.0
        
        # Calculate drawdown percentage
        current_equity = self.starting_balance + self.total_pnl
        if self.peak_equity > 0:
            drawdown_percentage = ((self.peak_equity - current_equity) / self.peak_equity) * 100
        else:
            # If no peak yet, use starting balance as reference
            self.peak_equity = max(self.starting_balance, current_equity)
            drawdown_percentage = ((self.starting_balance - current_equity) / self.starting_balance) * 100
        
        return {
            "total_pnl": self.total_pnl,
            "daily_pnl": self.get_daily_pnl(),
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "win_rate": win_rate,
            "open_positions": len(self.positions),
            "closed_trades": self.closed_trades[-100:],  # Last 100 trades for drawdown calculation
            "shadow_pnl": getattr(self, 'shadow_pnl', 0.0),
            "drawdown_percentage": drawdown_percentage,
            "peak_equity": self.peak_equity,
            "current_equity": current_equity
        }

    def get_daily_pnl(self) -> float:
        """Calculate PnL for the rolling 24-hour window."""
        now = time.time()
        day_ago = now - 86400
        daily_pnl = 0.0
        for trade in self.closed_trades:
            if trade['exit_time'] >= day_ago:
                daily_pnl += trade['pnl']
        return daily_pnl
        
    def check_signal_persistence(self, symbol, signal):
        """Check if signal has been persistent for required number of ticks."""
        settings = get_settings()
        threshold = getattr(settings, 'SIGNAL_THRESHOLD', 0.5)
        persistence_req = getattr(settings, 'SIGNAL_PERSISTENCE', 3)
        
        if symbol not in self.signal_history:
            self.signal_history[symbol] = []
            
        # Add current signal to history
        self.signal_history[symbol].append(signal)
        
        # Keep only last 5 signals (or persistence req + 2)
        if len(self.signal_history[symbol]) > 5:
            self.signal_history[symbol] = self.signal_history[symbol][-5:]
            
        # Check persistence for buy signals (> threshold)
        if signal > threshold:
            recent_signals = self.signal_history[symbol][-persistence_req:]
            if len(recent_signals) >= persistence_req:
                persistent = all(s > threshold for s in recent_signals)
                if not persistent:
                    logger.info(f"[PERSISTENCE] {symbol} BUY signal not persistent: {recent_signals}")
                return persistent
            else:
                logger.info(f"[PERSISTENCE] {symbol} BUY signal building: {len(recent_signals)}/{persistence_req}")
                return False
                
        # Check persistence for sell signals (< -threshold)
        elif signal < -threshold:
            recent_signals = self.signal_history[symbol][-persistence_req:]
            if len(recent_signals) >= persistence_req:
                persistent = all(s < -threshold for s in recent_signals)
                if not persistent:
                    logger.info(f"[PERSISTENCE] {symbol} SELL signal not persistent: {recent_signals}")
                return persistent
            else:
                logger.info(f"[PERSISTENCE] {symbol} SELL signal building: {len(recent_signals)}/{persistence_req}")
                return False
                
        return False
    
    def _collect_oracle_signals(self, symbol: str, price: float, brain_engine, settings) -> Dict[str, Any]:
        """
        Collect all signal sources for Oracle synthesis.
        Returns state dictionary with all inputs for Oracle.
        """
        state = {}
        
        # 1. LOGIC SIGNAL (Z-Score from BrainEngine)
        logic_signal = 0.0
        if hasattr(brain_engine, 'states'):
            s_state = brain_engine.states.get(symbol)
            if s_state and s_state.get('z_score_history'):
                logic_signal = s_state['z_score_history'][-1]
        state['logic_signal'] = logic_signal
        
        # 2. ML PROBABILITY (from BrainEngine or Auto-Discovery)
        ml_probability = 0.5  # Default neutral
        try:
            # A. Try explicit ML State (The Soul - XGBoost)
            if hasattr(brain_engine, 'states'):
                s_state = brain_engine.states.get(symbol)
                if s_state and 'ml_probability' in s_state:
                    ml_probability = s_state['ml_probability']
            
            # B. Fallback to Projection Heuristic (if Soul is silent/neutral)
            if abs(ml_probability - 0.5) < 0.001:
                # Try to get ML prediction from brain engine
                if hasattr(brain_engine, 'compute_projection'):
                    projection = brain_engine.compute_projection(lookahead=1, symbol=symbol)
                    if projection:
                        # Use signal direction as probability proxy
                        signal = projection.get('signal', 0.0)
                        # Convert z-score to probability (0-1 range)
                        ml_probability = 0.5 + (signal / 4.0)  # Normalize to 0-1, clamp later
                        ml_probability = max(0.0, min(1.0, ml_probability))
        except Exception as e:
            logger.debug(f"[ORACLE] Could not get ML probability: {e}")
        state['ml_probability'] = ml_probability

        # 2.5 DIVINE METRICS (The Exoskeleton)
        # Collect advanced metrics (Phase, DMD Forecast, etc.)
        divine_metrics = {}
        try:
             if hasattr(brain_engine, 'get_divine_metrics'):
                  divine_metrics = brain_engine.get_divine_metrics(symbol)
        except Exception as e:
             logger.debug(f"[ORACLE] Could not get divine metrics: {e}")
        state['divine_metrics'] = divine_metrics
        
        # 3. PATTERN RETURN (from Episode Pattern Matcher)
        pattern_return = 0.0  # Default no pattern prediction
        try:
            from services.episode_pattern_matcher import get_episode_pattern_matcher
            try:
                pattern_matcher = get_episode_pattern_matcher()
            except Exception:
                pattern_matcher = None
            if pattern_matcher and hasattr(pattern_matcher, 'patterns') and pattern_matcher.patterns:
                # Get current market conditions for pattern matching
                # Use brain engine's volatility and momentum if available
                volatility = getattr(brain_engine, 'running_volatility', 0.0)
                momentum = 0.0
                if hasattr(brain_engine, 'price_history') and len(brain_engine.price_history) >= 2:
                    momentum = (brain_engine.price_history[-1] - brain_engine.price_history[-2]) / brain_engine.price_history[-2]
                
                # Determine regime
                regime = "Crash/Panic" if volatility > 5.0 else ("Active" if volatility > 1.5 else "Stagnant")
                
                # --- GLOBAL CONTEXT PREP ---
                global_ctx = {"regime": "Unknown", "correlation": 0.0}
                try:
                    # Attempt to get Leader Context from Brain Engine States
                    leader = "BTCUSDC"
                    if symbol == "BTCUSDC": leader = "ETHUSDC"
                    
                    if hasattr(brain_engine, 'states'):
                         l_state = brain_engine.states.get(leader)
                         s_state = brain_engine.states.get(symbol)
                         
                         if l_state:
                             # Leader Regime
                             l_vol = l_state.get('volatility', 0.0)
                             if l_vol > 5.0: global_ctx['regime'] = "Crash/Panic"
                             elif l_vol > 1.5: global_ctx['regime'] = "Active"
                             else: global_ctx['regime'] = "Stagnant"
                             
                             # Correlation
                             if s_state:
                                 l_prices = l_state.get('price_history', [])
                                 s_prices = s_state.get('price_history', [])
                                 # Basic correlation check
                                 if len(l_prices) > 10 and len(s_prices) > 10:
                                     try:
                                         import numpy as np
                                         # Truncate to min len
                                         min_len = min(len(l_prices), len(s_prices))
                                         # Use last N points
                                         lp = l_prices[-min_len:]
                                         sp = s_prices[-min_len:]
                                         corr = np.corrcoef(lp, sp)[0, 1]
                                         if not np.isnan(corr):
                                             global_ctx['correlation'] = float(corr)
                                     except:
                                         pass
                except Exception as e:
                    logger.debug(f"[ORACLE] Context error: {e}")

                # Match pattern and get score (0-1)
                pattern_score = pattern_matcher.match_pattern(
                    symbol=symbol,
                    volatility=volatility,
                    volume=0.0,  # Volume not available in this context
                    signal_strength=abs(logic_signal),
                    regime=regime,
                    momentum=momentum,
                    global_context=global_ctx
                )
                
                # [FIX] Backtest showed: threshold 0.1 + direction check = 78.6% WR, 2.68 PF
                # Original 0.5 was too strict, filtered all trades
                if pattern_score > 0.1:  # Lowered from 0.5 based on backtest
                    matching_patterns = [p for p in pattern_matcher.patterns if p.success_rate > 0.5]
                    if matching_patterns:
                        avg_pnl = sum(p.avg_pnl_pct for p in matching_patterns) / len(matching_patterns)
                        
                        # [FIX] Direction alignment check (key improvement)
                        # Only use pattern prediction if direction matches signal
                        pattern_direction = 1.0 if avg_pnl > 0 else -1.0
                        signal_direction = 1.0 if logic_signal > 0 else -1.0
                        
                        if pattern_direction == signal_direction:
                            # Pattern confirms signal direction - boost confidence
                            pattern_return = avg_pnl * pattern_score
                        else:
                            # Pattern contradicts signal - skip this trade
                            pattern_return = 0.0
        except Exception as e:
            logger.debug(f"[ORACLE] Could not get pattern return: {e}")
        state['pattern_return'] = pattern_return
        
        # 4. SENTIMENT SCORE
        try:
            from services.sentiment_analyzer import get_sentiment_analyzer
            sentiment_analyzer = get_sentiment_analyzer()
            # Pass context (price, signal) for potential future use
            context = {
                'price': price,
                'signal': logic_signal,
                'symbol': symbol
            }
            sentiment_score = sentiment_analyzer.get_sentiment(symbol, context)
        except Exception as e:
            logger.debug(f"[ORACLE] Could not get sentiment score: {e}")
            sentiment_score = 0.0  # Default neutral on error
        state['sentiment_score'] = sentiment_score
        
        return state
    
    def _load_from_disk(self):
        """Load persisted performance data from disk."""
        if os.path.exists(self.PERSISTENCE_FILE):
            try:
                with open(self.PERSISTENCE_FILE, 'r') as f:
                    data = json.load(f)
                    self.total_pnl = data.get('total_pnl', 0.0)
                    self.total_trades = data.get('total_trades', 0)
                    self.winning_trades = data.get('winning_trades', 0)
                    # Load last 100 closed trades (keep recent history)
                    self.closed_trades = data.get('closed_trades', [])[-100:]
                    # Load open positions (backup to DB)
                    self.positions.update(data.get('positions', {}))
                    # Load peak equity for drawdown calculation
                    self.peak_equity = data.get('peak_equity', self.starting_balance + self.total_pnl)
                    logger.info(f"[TRACKER] Loaded persisted stats: P&L=${self.total_pnl:.2f}, Trades={self.total_trades}, Win Rate={self.winning_trades/self.total_trades*100 if self.total_trades > 0 else 0:.1f}%")
            except Exception as e:
                logger.warning(f"[TRACKER] [WARN] Failed to load persistence file: {e}")
    
    def _save_to_disk(self):
        """Save current performance data to disk."""
        try:
            # Only save every 30 seconds to avoid excessive disk writes
            if time.time() - self.last_save_time < 30:
                return
                
            data = {
                'total_pnl': self.total_pnl,
                'total_trades': self.total_trades,
                'winning_trades': self.winning_trades,
                'closed_trades': self.closed_trades[-100:],  # Keep last 100 trades
                'positions': self.positions,  # Cross-resilience backup to DB
                'peak_equity': self.peak_equity,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.PERSISTENCE_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.last_save_time = time.time()
            logger.debug(f"[TRACKER] Saved performance data to {self.PERSISTENCE_FILE}")
            # Also persist summary metrics to DB (best-effort)
            try:
                db = get_database()
                ts = datetime.now().timestamp()
                db.insert_metric("total_pnl", self.total_pnl, ts=ts)
                db.insert_metric("total_trades", float(self.total_trades), ts=ts)
                db.insert_metric("peak_equity", float(self.peak_equity), ts=ts)
            except Exception:
                logger.debug("Failed to persist performance metrics to DB", exc_info=True)
        except Exception as e:
            logger.warning(f"[TRACKER] [WARN] Failed to save persistence file: {e}")

# Global performance tracker
# --- SINGLETON GETTER ---
_tracker_instance = None

def get_performance_tracker():
    """
    Returns the singleton instance of PerformanceTracker.
    Ensures that both the Bot (Stats) and the Trading Service (Execution)
    share the SAME memory state.
    """
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = PerformanceTracker()
    return _tracker_instance
