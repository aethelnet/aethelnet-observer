"""
Shadow Engine - Parallel Espresso Preset Trading
Runs ghost trades with 10s holds to detect regime changes

🌀 USER-FRIENDLY SHADOW TRADING 🌀
- Automatically loads your .env settings
- Clear progress logging for validation criteria
- Simple stats that make sense
"""
import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from dataclasses import dataclass
from services.data_manager import get_data_manager
from services.data.schema import ShadowTrade, ShadowValidation

logger = logging.getLogger("ShadowEngine")

@dataclass
class ValidationCriteria:
    """Trading validation criteria for live trading readiness"""
    MIN_TRADES: int = 75
    MIN_WIN_RATE: float = 0.45
    MAX_DRAWDOWN: float = 0.08
    TARGET_HOURS: float = 3.0

@dataclass
class ShadowConfig:
    """Espresso preset - Ultra-fast trading configuration"""
    MIN_HOLD_TIME: int = 10  # 10 seconds (vs 45s for Coffee Trader)
    SIGNAL_PERSISTENCE: int = 1  # Immediate action (vs 2 for Coffee)
    SIGNAL_THRESHOLD: float = 0.65  # Higher threshold for quality
    POSITION_SIZE: float = 0.05  # 5% per trade (matches main system)
    MAX_POSITIONS: int = 3  # Limit concurrent positions

class ShadowPosition:
    """Ghost position for shadow trading"""
    def __init__(self, symbol: str, side: str, entry_price: float, quantity: float, timestamp: float):
        self.symbol = symbol
        self.side = side  # "LONG" or "SHORT"
        self.entry_price = entry_price
        self.quantity = quantity
        self.entry_time = timestamp
        self.unrealized_pnl = 0.0
        
    def update_pnl(self, current_price: float):
        """Update unrealized P&L"""
        if self.side == "LONG":
            self.unrealized_pnl = (current_price - self.entry_price) * self.quantity
        else:  # SHORT
            self.unrealized_pnl = (self.entry_price - current_price) * self.quantity

class ShadowEngine:
    """
    🌀 Shadow Engine - Your Parallel Trading Assistant
    
    Runs alongside your main Coffee Trader to detect when market conditions
    favor ultra-fast Espresso trading. User-friendly and automatic!
    """
    
    def __init__(self, settings=None):
        # Load settings from your .env file automatically
        if settings:
            self.config = ShadowConfig(
                MIN_HOLD_TIME=settings.SHADOW_MIN_HOLD_TIME,
                SIGNAL_THRESHOLD=settings.SHADOW_SIGNAL_THRESHOLD,
                POSITION_SIZE=settings.SHADOW_POSITION_SIZE,
                MAX_POSITIONS=settings.SHADOW_MAX_POSITIONS
            )
            self.validation = ValidationCriteria(
                MIN_TRADES=settings.VALIDATION_MIN_TRADES,
                MIN_WIN_RATE=settings.VALIDATION_MIN_WIN_RATE,
                MAX_DRAWDOWN=settings.VALIDATION_MAX_DRAWDOWN,
                TARGET_HOURS=settings.VALIDATION_TARGET_HOURS
            )
        else:
            self.config = ShadowConfig()
            self.validation = ValidationCriteria()
        
        # Trading state
        self.positions: Dict[str, ShadowPosition] = {}
        self.closed_trades = []
        self.total_pnl = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        self.starting_balance = 10000.0  # Virtual balance for tracking
        self.peak_pnl = 0.0
        self.peak_equity = self.starting_balance
        self.last_regime_check = datetime.now().timestamp()
        self.regime_check_interval = 600  # 10 minutes
        self.session_start_time = datetime.now().timestamp()
        self.emergency_stop = False
        
        # [SOVEREIGN EXORCISM] One-time flush of stalled ghost positions
        # The engine was blind to exit signals for weeks; we clear the ghosts.
        self.positions = {}
        self.total_trades = 0
        self.winning_trades = 0
        self.total_pnl = 0.0
        logger.info("[SHADOW] [EXORCISM] Satellite Spectral Lock BROKEN. Resetting for new DNA.")

        # self._restore_state() # NEUTRALIZED: Prevent resurrection of 36k historical ghosts
        
        logger.info(f"Session started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Validation criteria: {self.validation.MIN_TRADES} trades, {self.validation.MIN_WIN_RATE:.1%} win rate, {self.validation.MAX_DRAWDOWN:.1%} max drawdown")

    def _restore_state(self):
        """
        Omni-Resurrection: Rebuilds state from the database.
        Allows the bot to die and rise again without losing validation progress.
        """
        try:
             dm = get_data_manager()
             db = dm.SessionLocal()
             
             # 1. Fetch all shadow trades ever recorded
             from services.data.schema import ShadowTrade
             try:
                 trades = db.query(ShadowTrade).all()
             except Exception:
                 # Table might not exist yet
                 trades = []
                 
             if not trades:
                 logger.info("No previous shadow history found. Starting fresh.")
                 db.close()
                 return

             # 2. Replay History
             logger.info(f"Restoring state from {len(trades)} historical shadow trades...")
             
             self.total_trades = len(trades)
             self.total_pnl = sum(t.pnl for t in trades)
             self.winning_trades = sum(1 for t in trades if t.pnl > 0)
             
             # 3. Re-calculate Peak PnL (Approximation)
             # We assume linear accumulation for peak calculation since we don't have time-series of equity
             # This is "good enough" for validation robustness
             running_pnl = 0.0
             peak = 0.0
             for t in trades:
                 running_pnl += t.pnl
                 if running_pnl > peak:
                     peak = running_pnl
             
             self.peak_pnl = peak
             self.peak_equity = self.starting_balance + self.peak_pnl
             
             logger.info(f"State Restored! Trades: {self.total_trades} | PnL: ${self.total_pnl:.2f} | Win Rate: {self.winning_trades/max(1,self.total_trades):.1%}")
             
             db.close()
             
        except Exception as e:
             logger.warning(f"Failed to restore state from DB: {e}")
    
    def should_enter_position(self, symbol: str, signal: float, price: float, settings=None) -> Optional[str]:
        """Determine if we should enter a position"""
        # Check if we already have a position
        if symbol in self.positions:
            return None
            
        # Check max positions limit
        if len(self.positions) >= self.config.MAX_POSITIONS:
            return None
        
        # Use Oracle if enabled, otherwise use preset threshold
        use_oracle = getattr(settings, 'ORACLE_ENABLED', True) if settings else False
        use_preset = getattr(settings, 'USE_PRESET_FILTERS', False) if settings else True
        
        if use_oracle and not use_preset and settings:
            # ORACLE MODE: Use Oracle truth score
            try:
                from incubator.oracle import get_oracle
                from services.brain import get_engine
                
                oracle = get_oracle()
                brain_engine = get_engine()
                
                # Collect Oracle signals (similar to main trading service)
                oracle_state = {
                    'logic_signal': signal,
                    'ml_probability': 0.5,  # Default neutral
                    'pattern_return': 0.0,  # Default no pattern
                    'sentiment_score': 0.0  # Default neutral
                }
                
                # Try to get ML probability from brain
                try:
                    if hasattr(brain_engine, 'compute_future_projection'):
                        projection = brain_engine.compute_future_projection(lookahead_minutes=5, symbol=symbol)
                        if projection:
                            proj_signal = projection.get('signal', 0.0)
                            oracle_state['ml_probability'] = 0.5 + (proj_signal / 4.0)
                            oracle_state['ml_probability'] = max(0.0, min(1.0, oracle_state['ml_probability']))
                except Exception:
                    pass
                
                truth_score = oracle.calculate_truth_score(oracle_state)
                
                # Oracle threshold (0.5 = moderate signal)
                ORACLE_THRESHOLD = 0.5
                if abs(truth_score) < ORACLE_THRESHOLD:
                    return None
                
                # Determine side from Oracle truth score
                return "LONG" if truth_score > 0 else "SHORT"
            except Exception as e:
                logger.debug(f"[SHADOW] Oracle error, falling back to preset: {e}")
                # Fall through to preset logic
        
        # PRESET MODE: Use threshold-based decision
        # Check signal strength (Espresso threshold)
        if abs(signal) < self.config.SIGNAL_THRESHOLD:
            return None
            
        # Determine side
        return "LONG" if signal > 0 else "SHORT"
    
    def should_exit_position(self, position: ShadowPosition, signal: float, current_time: float) -> bool:
        """Determine if we should exit a position"""
        # Check minimum hold time (Espresso: 10s)
        if current_time - position.entry_time < self.config.MIN_HOLD_TIME:
            return False
            
        # Exit on signal reversal (Espresso: immediate)
        if position.side == "LONG" and signal < -self.config.SIGNAL_THRESHOLD:
            return True
        elif position.side == "SHORT" and signal > self.config.SIGNAL_THRESHOLD:
            return True
            
        # Exit on stop loss (simple 2% stop)
        if position.unrealized_pnl < -position.quantity * 0.02:
            return True
            
        return False
    
    def enter_position(self, symbol: str, side: str, price: float, timestamp: float):
        """Enter a ghost position"""
        position = ShadowPosition(
            symbol=symbol,
            side=side,
            entry_price=price,
            quantity=self.config.POSITION_SIZE,
            timestamp=timestamp
        )
        
        self.positions[symbol] = position
        logger.info(f"Shadow {side} {symbol} @ {price:.2f}")
    
    def exit_position(self, symbol: str, price: float, timestamp: float):
        """Exit a ghost position"""
        if symbol not in self.positions:
            return
            
        position = self.positions[symbol]
        position.update_pnl(price)
        
        # Record closed trade
        hold_time = timestamp - position.entry_time
        trade = {
            'symbol': symbol,
            'side': position.side,
            'entry_price': position.entry_price,
            'exit_price': price,
            'quantity': position.quantity,
            'pnl': position.unrealized_pnl,
            'hold_time': hold_time,
            'timestamp': timestamp
        }
        
        self.closed_trades.append(trade)
        self.total_pnl += position.unrealized_pnl
        self.total_trades += 1
        
        if position.unrealized_pnl > 0:
            self.winning_trades += 1
            
        logger.info(f"Shadow EXIT {symbol} @ {price:.2f} | P&L: {position.unrealized_pnl:.2f}")
        
        # PERSISTENCE: Save Trade to Supabase
        try:
             dm = get_data_manager()
             db = dm.SessionLocal()
             trade_record = ShadowTrade(
                 symbol=symbol,
                 side=position.side,
                 entry_price=position.entry_price,
                 exit_price=price,
                 quantity=position.quantity,
                 pnl=position.unrealized_pnl,
                 hold_time=hold_time,
                 timestamp=timestamp
             )
             db.add(trade_record)
             db.commit()
             db.close()
        except Exception as e:
             logger.error(f"Failed to persist shadow trade: {e}")

        # Remove position
        del self.positions[symbol]
    
    def update_positions(self, symbol: str, price: float):
        """Update all position P&L"""
        if symbol in self.positions:
            self.positions[symbol].update_pnl(price)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get shadow trading statistics with validation criteria"""
        win_rate = self.winning_trades / max(self.total_trades, 1) if self.total_trades > 0 else 0.0
        
        # Calculate unrealized P&L
        unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
        total_pnl = self.total_pnl + unrealized_pnl
        
        # Update peak P&L for drawdown calculation
        if total_pnl > self.peak_pnl:
            self.peak_pnl = total_pnl
            self.peak_equity = self.starting_balance + self.peak_pnl
            
        # Calculate current drawdown
        current_drawdown = (self.peak_pnl - total_pnl) / max(abs(self.peak_pnl), 1.0) if self.peak_pnl != 0 else 0.0
        
        # Session duration
        session_duration = datetime.now().timestamp() - self.session_start_time
        
        # Fast-track validation status
        validation_status = self.check_validation_criteria(total_pnl, win_rate, current_drawdown, session_duration)
        
        return {
            'total_pnl': round(total_pnl, 2),
            'realized_pnl': round(self.total_pnl, 2),
            'unrealized_pnl': round(unrealized_pnl, 2),
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'win_rate': round(win_rate, 3),
            'current_drawdown': round(current_drawdown, 3),
            'peak_pnl': round(self.peak_pnl, 2),
            'open_positions': len(self.positions),
            'current_equity': round(self.starting_balance + total_pnl, 2),
            'peak_equity': round(self.peak_equity, 2),
            'drawdown_percentage': round(current_drawdown * 100, 2),
            'session_duration_hours': round(session_duration / 3600, 1),
            'trades_per_hour': round(self.total_trades / max(session_duration / 3600, 0.1), 1),
            'emergency_stop': self.emergency_stop,
            'validation_status': validation_status,
            'closed_trades': self.closed_trades[-10:],  # Last 10 trades
            'positions': {k: {
                'side': v.side,
                'entry_price': v.entry_price,
                'unrealized_pnl': round(v.unrealized_pnl, 2),
                'hold_time': round(datetime.now().timestamp() - v.entry_time, 1)
            } for k, v in self.positions.items()}
        }
    
    def check_regime_change(self, main_pnl: float):
        """Check if shadow is outperforming main trader"""
        current_time = datetime.now().timestamp()
        
        # Only check every 10 minutes
        if current_time - self.last_regime_check < self.regime_check_interval:
            return
            
        self.last_regime_check = current_time
        
        shadow_stats = self.get_stats()
        shadow_pnl = shadow_stats['total_pnl']
        
        # Need minimum trades for valid comparison
        if shadow_stats['total_trades'] < 5:
            return
            
        # Check if shadow is outperforming by 50%
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if shadow_pnl > main_pnl * 1.5 and main_pnl > 0 and shadow_stats['win_rate'] > 0.5:
            logger.critical(
                f"[{timestamp}] [SHADOW] REGIME CHANGE: ESPRESSO RECOMMENDED | "
                f"Main P&L=${main_pnl:.2f} | Shadow P&L=${shadow_pnl:.2f} | "
                f"Shadow WR={shadow_stats['win_rate']:.1%} | Trades={shadow_stats['total_trades']}"
            )
            return "ESPRESSO"
            
        elif shadow_pnl < main_pnl * 0.5 and shadow_pnl < 0:
            logger.info(
                f"[{timestamp}] [SHADOW] REGIME STABLE: Coffee Trader performing better | "
                f"Main P&L=${main_pnl:.2f} | Shadow P&L=${shadow_pnl:.2f}"
            )
            return "COFFEE"
            
        return "NEUTRAL"
    
    def check_validation_criteria(self, total_pnl: float, win_rate: float, drawdown: float, session_hours: float) -> Dict[str, Any]:
        """
        Check trading validation criteria for live trading readiness.
        
        User-friendly validation that tells you exactly what you need.
        """
        criteria = {
            'trades_met': self.total_trades >= self.validation.MIN_TRADES,
            'win_rate_met': win_rate >= self.validation.MIN_WIN_RATE,
            'drawdown_met': drawdown <= self.validation.MAX_DRAWDOWN,
            'time_remaining': max(0, self.validation.TARGET_HOURS - session_hours),
            'trades_needed': max(0, self.validation.MIN_TRADES - self.total_trades),
            'live_ready': False
        }
        
        # Check if all criteria met
        criteria['live_ready'] = (
            criteria['trades_met'] and 
            criteria['win_rate_met'] and 
            criteria['drawdown_met']
        )
        
        # Log validation progress on milestones or status changes (every 25 trades or when criteria change)
        should_log_progress = (
            self.total_trades > 0 and 
            (self.total_trades % 25 == 0 or criteria['live_ready'] or 
             any([not criteria['trades_met'], not criteria['win_rate_met'], not criteria['drawdown_met']]))
        )
        
        if should_log_progress:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # PERSISTENCE: Save Validation Status
            try:
                 dm = get_data_manager()
                 db = dm.SessionLocal()
                 val_record = ShadowValidation(
                     total_trades=self.total_trades,
                     win_rate=win_rate,
                     total_pnl=total_pnl,
                     drawdown=drawdown,
                     is_ready=1 if criteria['live_ready'] else 0
                 )
                 db.add(val_record)
                 db.commit()
                 db.close()
            except Exception as e:
                 logger.error(f"Failed to persist validation status: {e}")

            if criteria['live_ready']:
                logger.info(f"[{timestamp}] [SHADOW] VALIDATION COMPLETE - All criteria met for live trading!")
                logger.info(f"[{timestamp}] [SHADOW] [OK] Trades: {self.total_trades}/{self.validation.MIN_TRADES} | "
                              f"Win Rate: {win_rate:.1%} | Drawdown: {drawdown:.1%} | "
                              f"Total PnL: ${total_pnl:.2f}")
                logger.info(f"[{timestamp}] [SHADOW] Ready for live trading - Set BINANCE_TESTNET=false to enable")
            else:
                remaining_time = criteria['time_remaining']
                status_parts = []
                if not criteria['trades_met']:
                    status_parts.append(f"Trades: {self.total_trades}/{self.validation.MIN_TRADES} ({criteria['trades_needed']} needed)")
                else:
                    status_parts.append(f"Trades: {self.total_trades}/{self.validation.MIN_TRADES} OK")
                    
                if not criteria['win_rate_met']:
                    status_parts.append(f"Win Rate: {win_rate:.1%} (need {self.validation.MIN_WIN_RATE:.1%})")
                else:
                    status_parts.append(f"Win Rate: {win_rate:.1%} OK")
                    
                if not criteria['drawdown_met']:
                    status_parts.append(f"Drawdown: {drawdown:.1%} (limit {self.validation.MAX_DRAWDOWN:.1%})")
                else:
                    status_parts.append(f"Drawdown: {drawdown:.1%} OK")
                
                logger.info(f"[{timestamp}] [SHADOW] Validation Progress ({remaining_time:.1f}h remaining) | " + " | ".join(status_parts))
        
        return criteria
    
    def trigger_emergency_stop(self, reason: str = "Manual stop"):
        """Emergency stop for testing"""
        self.emergency_stop = True
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        win_rate = self.winning_trades / max(self.total_trades, 1) if self.total_trades > 0 else 0.0
        logger.critical(
            f"[{timestamp}] [SHADOW] 🛑 EMERGENCY STOP TRIGGERED | "
            f"reason={reason} | trades={self.total_trades} | win_rate={win_rate:.1%} | "
            f"open_positions={len(self.positions)}"
        )
        
        # Close all positions immediately
        for symbol in list(self.positions.keys()):
            position = self.positions[symbol]
            logger.critical(
                f"[{timestamp}] [SHADOW] Emergency exit | "
                f"symbol={symbol} | side={position.side} | "
                f"entry_price={position.entry_price:.2f} | unrealized_pnl={position.unrealized_pnl:.2f}"
            )
            # Note: In real implementation, this would trigger actual position closure
    
    async def tick(self, symbol: str, price: float, signal: float, settings=None):
        """Process one tick of shadow trading"""
        try:
            # Check emergency stop
            if self.emergency_stop:
                return
                
            current_time = datetime.now().timestamp()
            
            # Update existing positions
            self.update_positions(symbol, price)
            
            # Check for exits first
            to_exit = []
            for pos_symbol, position in self.positions.items():
                if pos_symbol == symbol and self.should_exit_position(position, signal, current_time):
                    to_exit.append(pos_symbol)
            
            for pos_symbol in to_exit:
                self.exit_position(pos_symbol, price, current_time)
            
            # Check for new entries (unless emergency stop)
            if not self.emergency_stop:
                side = self.should_enter_position(symbol, signal, price, settings)
                if side:
                    self.enter_position(symbol, side, price, current_time)
                
        except Exception as e:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            logger.error(
                f"[{timestamp}] [SHADOW] Error in tick processing | "
                f"symbol={symbol} | price={price:.2f} | signal={signal:.2f} | "
                f"error={type(e).__name__}: {str(e)}",
                exc_info=True  # Include full stack trace
            )

# Global shadow engine instance
_shadow_engine: Optional[ShadowEngine] = None

def get_simple_shadow_stats() -> str:
    """
    🌀 Get a simple, human-readable summary of shadow trading
    
    Perfect for quick status checks - returns a nice formatted string
    """
    engine = get_shadow_engine()
    stats = engine.get_stats()
    
    status = "🌀 SHADOW ENGINE STATUS\n"
    status += f"Trades: {stats['total_trades']} | "
    status += f"Win Rate: {stats['win_rate']:.1%} | "
    status += f"P&L: ${stats['total_pnl']:.2f}\n"
    
    if stats['validation_status']['live_ready']:
        status += "🎉 LIVE READY! All validation criteria met!"
    else:
        needed = stats['validation_status']['trades_needed']
        status += f"🚀 Progress: {needed} more trades needed for validation"
    
    return status

def get_simple_shadow_stats_cleaned() -> str:
    """Helper for non-emoji stats"""
    engine = get_shadow_engine()
    stats = engine.get_stats()
    status = f"Shadow: {stats['total_trades']} trades | WR {stats['win_rate']:.1%} | PnL ${stats['total_pnl']:.2f}"
    if stats['validation_status']['live_ready']:
        status += " [READY]"
    else:
        status += f" (Need {stats['validation_status']['trades_needed']} more)"
    return status

def get_shadow_engine(settings=None) -> ShadowEngine:
    """
    Get your Shadow Engine instance - automatically configured from .env
    
    This is your parallel trading assistant that helps detect regime changes.
    Just call this function and it handles everything for you!
    """
    global _shadow_engine
    if _shadow_engine is None:
        # Automatically load settings if not provided
        if settings is None:
            try:
                from config import get_settings
                settings = get_settings()
                logger.debug("Shadow Engine: Loaded settings from config")
            except Exception as e:
                logger.warning(f"Shadow Engine: Could not load settings, using defaults: {e}")
                settings = None
        _shadow_engine = ShadowEngine(settings)
        logger.info("Shadow Engine ready to assist your trading!")
    return _shadow_engine
