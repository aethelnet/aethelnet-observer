"""
Continuous Rebalancer — The Sovereign Position Manager
======================================================
Philosophy:
    - Prophet says "down, I'm sure" → reinbuttern
    - Prophet says "I don't know"   → reduce risk
    
    Position Size = abs(soul_val) × MAX_POSITION_USD
    Side          = sign(soul_val)
    
    Every tick: compare target vs actual, rebalance the delta.
    No thresholds. No vetoes. No cooldowns. Just conviction = capital.
"""
import asyncio
import time
import math
from core.logger import get_logger
logger = get_logger("ContinuousRebalancer")


class ContinuousRebalancer:
    """
    Replaces discrete Entry/Exit logic with continuous position management.
    The ProphitNet's conviction directly maps to position size.
    """
    
    def __init__(self, settings):
        self.settings = settings
        self.max_position_usd = getattr(settings, 'MAX_POSITION_SIZE_USD', 100.0)
        self.min_order_usd = getattr(settings, 'MIN_REBALANCE_DELTA_USD', 15.0)  # Aligned with settings.py
        self.leverage = getattr(settings, 'HYPERLIQUID_LEVERAGE', 20.0)
        self.last_rebalance_time = {}
        self.rebalance_cooldown = getattr(settings, 'REBALANCE_COOLDOWN', 300.0)  # 5 min chill mode
        self.signal_hysteresis = getattr(settings, 'SIGNAL_HYSTERESIS', 0.15)    # 15% conviction change threshold
        self.scorpio_scalar = getattr(settings, 'SCORPIO_SCALAR', 1.5)
        self.last_soul_val = {}
        self.iteration_count = 0
        self._router = None
    
    async def _get_router(self):
        if self._router is None:
            from brokers.router import get_omni_router
            self._router = get_omni_router()
        return self._router
    
    def compute_target(self, soul_val: float) -> dict:
        """
        Pure math. No side effects.
        
        soul_val: float in [-1.0, 1.0] from ProphitNet (tanh output)
        
        Returns:
            {
                'side': 'LONG' | 'SHORT' | 'FLAT',
                'conviction': float 0.0-1.0,
                'target_usd': float (notional target size)
            }
        """
        conviction = abs(soul_val)
        
        if conviction < 0.01:
            return {'side': 'FLAT', 'conviction': 0.0, 'target_usd': 0.0}
        
        side = 'LONG' if soul_val > 0 else 'SHORT'
        target_usd = conviction * self.max_position_usd
        
        return {
            'side': side,
            'conviction': conviction,
            'target_usd': target_usd
        }
    
    async def rebalance(self, symbol: str, soul_val: float, z_score: float, price: float, 
                        dry_run: bool = True, is_scorpio: bool = False,
                        tracker=None, target_usd_override: float = None) -> dict:
        """
        The Sovereign Rebalance Loop ('The Soup Logic').
        Now with Agile Z-Score Sizing.
        """
        self.iteration_count += 1
        
        # Determine the logical trading direction based on the unified signal polarity (already aligned at brain source)
        svrgn_direction = "BUY" if soul_val > 0 else "SELL"
        
        # --- 1. Initialize Result Object ---
        result = {
            'symbol': symbol,
            'soul_val': soul_val,
            'z_score': z_score,
            'target_usd': 0.0,
            'target_side': 'FLAT',
            'total_equity': 0.0,
            'tradable_capital': 0.0,
            'current_side': 'FLAT',
            'current_usd': 0.0,
            'delta_usd': 0.0,
            'action': 'HOLD'
        }

        # --- 2. Get Live Context ---
        router = await self._get_router()
        
        # Read Current Position early to avoid UnboundLocalErrors
        is_flat = True
        current_qty = 0.0
        current_usd = 0.0
        current_side = 'FLAT'
        try:
            current_qty = await router.get_position(symbol)
            if current_qty is None: current_qty = 0.0
            current_usd = abs(current_qty) * price
            current_side = 'LONG' if current_qty > 0.0 else 'SHORT'
            if current_usd <= 1.0: # Ignore dust under $1.00
                current_side = 'FLAT'
            is_flat = current_side == 'FLAT'
        except Exception as e:
            logger.error(f"[SVRGN] Failed to read position for {symbol}: {e}")

        result.update({
            'current_side': current_side,
            'current_usd': current_usd,
            'is_flat': is_flat,
            'current_qty': current_qty
        })
        
        # --- 3. The Sovereign Signal & Conviction ---
        # [FIXED SIZING] We use the Base Threshold (4.7) for sizing to prevent "shriveling"
        base_threshold = getattr(self.settings, 'SIGNAL_THRESHOLD', 4.7)
        conviction = abs(z_score) / (base_threshold if base_threshold > 0 else 1.0)
        
        # [ADAPTIVE GATE] Shift threshold higher as margin utilization increases
        margin_state = await router.get_margin_state()
        utilization = margin_state.get('utilization', 0.0)
        
        # Scalar: +10.0 Z-score pickiness at 100% utilization
        adaptive_scalar = getattr(self.settings, 'ADAPTIVE_THRESHOLD_SCALAR', 10.0)
        entry_threshold = base_threshold + (utilization * adaptive_scalar)
        
        # [HEARTBEAT] Prove the logic is live even when silent
        if self.iteration_count % 100 == 0:
            logger.info(f"[SVRGN] Pulse | Threshold: {entry_threshold:.2f} | Util: {utilization*100:.1f}% | Mode: Golden")
        
        # [DEADZONE] Decoupled Gates: Entry uses Adaptive, Exit uses Base with Hysteresis
        # This prevents the "Margin-Induced Panic Close" loop and guards against premature exits.
        exit_factor = getattr(self.settings, 'SIGNAL_HYSTERESIS', 0.0)
        exit_threshold = base_threshold * (1.0 - exit_factor)
        
        active_gate = entry_threshold if current_usd <= 0.1 else exit_threshold
        
        if abs(z_score) < active_gate:
            # If we have a position, we still want to log the status
            if current_usd > 0.1:
                logger.debug(f"[SVRGN] {symbol} | Release-Gate: {active_gate:.2f} | Signal {abs(z_score):.2f} < Gate (Closing)")
            target_side = "FLAT"
        else:
            # Reversion Logic: Positive soul_val (positive Z-Score) means price is ABOVE mean. We SHORT to ride it down.
            # Negative soul_val means price is BELOW mean. We LONG to ride it up.
            target_side = "SHORT" if soul_val > 0 else "LONG"
        
        # Check Cooldown (Sovereign Shield)
        now = time.time()
        last_t = self.last_rebalance_time.get(symbol, 0)
        cooldown_period = getattr(self.settings, 'REBALANCE_COOLDOWN', 300.0)
        in_cooldown = (now - last_t) < cooldown_period
        
        # Calculate Soul Delta (Hysteresis)
        prev_soul = self.last_soul_val.get(symbol, 0.0)
        soul_delta = abs(soul_val - prev_soul)
          
        # --- 4. Calculate 'The Pot' ---
        total_equity = await router.get_trading_capital(symbol)
        reserve_pct = getattr(self.settings, 'CASH_RESERVE_PCT', 0.10)
        tradable_capital = total_equity * (1.0 - reserve_pct)
        
        # --- [AUTO-SCALER] Dynamic Notional Cap ---
        # If POSITION_SIZE_PCT_OF_EQUITY is set (e.g. 20.0), we calculate max_pos based on equity
        scaling_pct = getattr(self.settings, 'POSITION_SIZE_PCT_OF_EQUITY', None)
        if scaling_pct is not None:
            dynamic_max_pos = total_equity * (float(scaling_pct) / 100.0)
            # Ensure it's at least the exchange minimum to allow the trade to fire
            active_max_pos = max(dynamic_max_pos, 15.5)
        else:
            active_max_pos = self.max_position_usd

        # --- 5. The Sovereign Decision Matrix ---
        # (entry_threshold is already adaptively calculated in Section 3)
        
        # --- SCORPIO STING: Decision Acceleration ---
        if is_scorpio:
            # Scorpio allows a slightly earlier entry (20% easier)
            entry_threshold *= 0.8
            if conviction > 0.8: # Relative conviction
                in_cooldown = False
                logger.info(f"[SVRGN] 🦂 SCORPIO STING ACTIVE for {symbol} | Bypassing Cooldown.")
        
        # Current Position (Already read in Section 2)
        result.update({
            'total_equity': total_equity,
            'tradable_capital': tradable_capital
        })

        # Sovereign Zenith Timing Guard (Hold Fire) for any new directional entries
        is_new_entry = (current_side == 'FLAT' and target_side != 'FLAT')
        is_flip_entry = (current_side != 'FLAT' and target_side != 'FLAT' and target_side != current_side)
        
        phase_multiplier = 1.0
        phase_reason = ""
        
        if (is_new_entry or is_flip_entry) and abs(z_score) >= entry_threshold and not in_cooldown:
            try:
                from services.brain_full import get_engine
                from services.oracle import get_oracle
                brain_engine = get_engine()
                oracle = get_oracle()
                oracle_state = oracle.collect_market_state(symbol, price, brain_engine, self.settings)
                
                phase_multiplier, phase_reason = self.evaluate_exoskeleton_sizing(symbol, target_side, oracle_state)
            except Exception as e:
                logger.debug(f"[Rebalancer] Exoskeleton check skipped due to error: {e}")
                
            if phase_multiplier < 1.0:
                logger.info(f"[REBALANCER] ⚖️ EXOSKELETON SIZING on {symbol} {target_side}: {phase_reason} (Multiplier: {phase_multiplier:.2f})")
                
        final_target_usd = 0.0
        
        # Clamp conviction so the DSP 10.0 headroom scaling doesn't multiply position size by 10
        # A conviction of 1.0 means we use 100% of MAX_POSITION_USD.
        # Since soul_val can reach ~9.4 now, we normalize it against the entry_threshold (4.7).
        normalized_conviction = min(1.0, conviction / entry_threshold) if entry_threshold > 0 else 1.0
        
        # [CORE ASPECT] Ouroboros: Eat tail (reduce conviction) during market chaos
        from services.ouroboros import apply_ouroboros_decay
        normalized_conviction = apply_ouroboros_decay(z_score, normalized_conviction)
        
        if target_side == 'FLAT':
            # We are in the Deadzone. Target is 0.
            final_target_usd = 0.0
        elif current_side == 'FLAT':
            # Opening a NEW position
            if abs(z_score) >= entry_threshold and not in_cooldown:
                size_scalar = self.scorpio_scalar if is_scorpio else 1.0
                final_target_usd = min(normalized_conviction * active_max_pos * size_scalar * phase_multiplier, tradable_capital)
        else:
            # Maintaining or Rebalancing an existing position
            if target_side != current_side:
                # Polarity Flip - only if significant conviction and not in cooldown
                if abs(z_score) >= entry_threshold and not in_cooldown:
                    size_scalar = self.scorpio_scalar if is_scorpio else 1.0
                    final_target_usd = min(normalized_conviction * active_max_pos * size_scalar * phase_multiplier, tradable_capital)
                else:
                    # Not enough conviction to flip or in cooldown: Stay in current side
                    target_side = current_side
                    final_target_usd = current_usd
            else:
                # Same side: Normal rebalance
                size_scalar = self.scorpio_scalar if is_scorpio else 1.0
                final_target_usd = min(normalized_conviction * active_max_pos * size_scalar, tradable_capital)
            
        # --- 6. Execution Formatting & Hysteresis ---
        target_usd = final_target_usd
        
        # [SOVEREIGN OVERRIDE] Apply Global Exponential Distribution if provided
        if target_usd_override is not None and target_side != "FLAT":
            target_usd = target_usd_override
            logger.debug(f"[SVRGN] {symbol} Applying Global Override: ${target_usd:.2f}")

        if 0 < target_usd < 15.5:
            target_usd = 15.5

        result.update({'target_usd': target_usd, 'target_side': target_side})

        # Final Safety Check: Signal Hysteresis (Only for rebalancing existing positions)
        if not is_flat and target_usd > 0 and soul_delta < self.signal_hysteresis:
             return result

        # --- 7. Calculate Delta ---
        if target_side == current_side:
            delta_usd = target_usd - current_usd
            
            # [ANTI-MARTINGALE / PROFIT-RIDER GUARD]
            # Prevent the "Constant Notional" trap where it sells winners (because USD value inflated) 
            # and buys losers (because USD value dropped). We only allow trades that align with conviction drift.
            abs_soul = abs(soul_val)
            abs_prev = abs(prev_soul)
            
            if abs_soul > abs_prev and delta_usd < 0:
                logger.info(f"[SVRGN] 🛡️ Anti-Martingale: Blocking profit-trimming on {symbol}. Conviction increased, letting winner run.")
                delta_usd = 0.0
            elif abs_soul < abs_prev and delta_usd > 0:
                logger.info(f"[SVRGN] 🛡️ Anti-Martingale: Blocking averaging-down on {symbol}. Conviction decreased, refusing to feed loser.")
                delta_usd = 0.0
                
        elif target_side == 'FLAT':
            delta_usd = -current_usd
        elif current_side == 'FLAT':
            delta_usd = target_usd
        else:
            delta_usd = current_usd + target_usd # Flip
            
        result['delta_usd'] = delta_usd

        # --- 8. Threshold & Action ---
        is_exit = (target_side == 'FLAT' and current_usd > 0.1)
        if not is_exit and abs(delta_usd) < self.min_order_usd:
            return result

        needs_flip = (current_side != 'FLAT' and target_side != 'FLAT' and current_side != target_side)
        if needs_flip: action = f'FLIP_{current_side}_TO_{target_side}'
        elif target_side == 'FLAT': action = f'CLOSE_{current_side}'
        elif current_side == 'FLAT': action = f'OPEN_{target_side}'
        elif delta_usd > 0: action = f'SCALE_UP_{target_side}'
        else: action = f'SCALE_DOWN_{target_side}'
        
        result['action'] = action
        
        # --- Log 'The Soup' Distribution ---
        conv_bar = '█' * int(min(conviction, 1.0) * 10) + '░' * (10 - int(min(conviction, 1.0) * 10))
        logger.info(
            f"[SVRGN] {symbol:<8} Z:{z_score:+.2f} | Conv:[{conv_bar}]({conviction:.2f}) "
            f"| Target: {target_side} ${target_usd:7.2f} "
            f"| Current: ${current_usd:7.2f} "
            f"| Δ: ${delta_usd:+7.2f} → {action}"
        )

        if dry_run:
            logger.info(f"[REBALANCER] 🛡️ {symbol} DRY RUN - Skipping actual order placement.")
            return result

        # --- 9. Execution ---
        try:
            if needs_flip:
                await self._close_position(symbol, current_side, current_qty, price)
                if tracker: tracker.update_from_fill(symbol, 'BUY' if current_side == 'SHORT' else 'SELL', current_qty, price, 'hyperliquid')
                await self._open_position(symbol, target_side, target_usd/price, price)
                if tracker: tracker.update_from_fill(symbol, 'BUY' if target_side == 'LONG' else 'SELL', target_usd/price, price, 'hyperliquid')
            elif target_side == 'FLAT':
                await self._close_position(symbol, current_side, current_qty, price)
                if tracker: tracker.update_from_fill(symbol, 'BUY' if current_side == 'SHORT' else 'SELL', current_qty, price, 'hyperliquid')
            elif current_side == 'FLAT':
                await self._open_position(symbol, target_side, target_usd/price, price)
                if tracker: tracker.update_from_fill(symbol, 'BUY' if target_side == 'LONG' else 'SELL', target_usd/price, price, 'hyperliquid')
            elif delta_usd > 0:
                await self._open_position(symbol, target_side, delta_usd/price, price)
                if tracker: tracker.update_from_fill(symbol, 'BUY' if target_side == 'LONG' else 'SELL', delta_usd/price, price, 'hyperliquid')
            else:
                await self._close_position(symbol, current_side, abs(delta_usd)/price, price)
                if tracker: tracker.update_from_fill(symbol, 'BUY' if current_side == 'SHORT' else 'SELL', abs(delta_usd)/price, price, 'hyperliquid')
            
            self.last_rebalance_time[symbol] = now
            self.last_soul_val[symbol] = soul_val
        except Exception as e:
            logger.error(f"[REBALANCER] {symbol} Execution Fail: {e}")
            
        return result
    
    def evaluate_exoskeleton_sizing(self, symbol: str, side: str, oracle_state: dict) -> tuple[float, str]:
        """
        Exoskeleton Watchtower Sizing.
        Scales down the entry size based on Hilbert Phase instead of hard blocking.
        Returns: (multiplier, reason)
        """
        if not oracle_state:
            return 1.0, ""
            
        # 1. Hilbert Phase Timing Gate
        divine = oracle_state.get('divine_metrics', {})
        phase = divine.get('phase', None)
        
        # Phase range is [-pi, pi]
        # For a LONG trend entry, the market is pumping. 
        # The phase starts negative, crosses 0 at max momentum, and reaches +pi at the absolute peak/exhaustion.
        # If phase is extremely high (e.g. > 1.5), we are entering very late in the pump.
        if phase is not None and phase != 0.0:
            if side == "LONG":
                if phase > 2.0:
                    return 0.1, f"Phase {phase:+.2f} indicates extreme exhaustion (Peak). Scout size only."
                elif phase > 1.0:
                    return 0.5, f"Phase {phase:+.2f} indicates late entry. Reducing size."
            elif side == "SHORT":
                if phase < -2.0:
                    return 0.1, f"Phase {phase:+.2f} indicates extreme exhaustion (Trough). Scout size only."
                elif phase < -1.0:
                    return 0.5, f"Phase {phase:+.2f} indicates late entry. Reducing size."

        # 2. Consensus Gate (Trend quiet, Reversion screaming)
        turtle_signal = oracle_state.get('arena_turtle', 0.0)
        rat_signal = oracle_state.get('arena_rat', 0.0)
        dragon_signal = oracle_state.get('arena_dragon', 0.0)

        # If we are entering LONG but Reversion algorithms are screaming to SHORT, reduce size
        if side == "LONG":
            if rat_signal < -0.5 and dragon_signal < -0.5:
                return 0.5, f"Reversion algorithms disagree heavily (Rat: {rat_signal:.2f})."
        elif side == "SHORT":
            if rat_signal > 0.5 and dragon_signal > 0.5:
                return 0.5, f"Reversion algorithms disagree heavily (Rat: {rat_signal:.2f})."

        return 1.0, ""

    async def _open_position(self, symbol, side, qty, price):
        """Open or add to a position."""
        router = await self._get_router()
        res = None
        qty = abs(float(qty))
        order_type = getattr(self.settings, 'REBALANCER_ORDER_TYPE', 'market')
        if side == 'LONG':
            res = await router.place_order(symbol, 'buy', order_type, qty, price)
        else:
            res = await router.place_order(symbol, 'sell', order_type, qty, price)
        
        if res:
            logger.info(f"[REBALANCER] ✅ {symbol} Opened {side} {qty:.6f} @ ${price:.2f} using {order_type.upper()}")
        else:
            error = getattr(router, '_last_error', 'Unknown Error')
            logger.error(f"[REBALANCER] ❌ {symbol} Open Failed: {error}")
    
    async def _close_position(self, symbol, side, qty, price):
        """Close or reduce a position."""
        router = await self._get_router()
        res = None
        qty = abs(float(qty))
        order_type = getattr(self.settings, 'REBALANCER_ORDER_TYPE', 'market')
        if side == 'LONG':
            res = await router.place_order(symbol, 'sell', order_type, qty, price, {'reduce_only': True})
        else:
            res = await router.place_order(symbol, 'buy', order_type, qty, price, {'reduce_only': True})
            
        if res:
            logger.info(f"[REBALANCER] ✅ {symbol} Closed {side} {qty:.6f} @ ${price:.2f} using {order_type.upper()}")
        else:
            error = getattr(router, '_last_error', 'Unknown Error')
            logger.error(f"[REBALANCER] ❌ {symbol} Close Failed: {error}")


# --- Singleton ---
_instance = None

def get_rebalancer(settings=None):
    global _instance
    if _instance is None:
        if settings is None:
            from config.settings import get_settings
            settings = get_settings()
        _instance = ContinuousRebalancer(settings)
    return _instance
