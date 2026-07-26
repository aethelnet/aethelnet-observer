"""
Continuous Rebalancer — The Sovereign Position Manager (Stripped & Simplified)
=============================================================================
Philosophy:
    - XGBoost ML Model dictates soul_val [-1.0, 1.0]
    - Position Size = abs(soul_val) × MAX_POSITION_USD
    - Side          = sign(soul_val)
    
    Every tick: compare target vs actual, rebalance the delta.
    No thresholds. No vetoes. No cooldowns. Pure ML Conviction.
"""
import asyncio
import time
from core.logger import get_logger

logger = get_logger("ContinuousRebalancer")

class ContinuousRebalancer:
    def __init__(self, settings):
        self.settings = settings
        self.max_position_usd = getattr(settings, 'MAX_POSITION_SIZE_USD', 100.0)
        self.min_order_usd = getattr(settings, 'MIN_REBALANCE_DELTA_USD', 15.0)
        self.iteration_count = 0
        self._router = None

    async def _get_router(self):
        if self._router is None:
            from brokers.router import get_omni_router
            self._router = get_omni_router()
        return self._router

    async def rebalance(self, symbol: str, soul_val: float, z_score: float, price: float, 
                        dry_run: bool = True, is_scorpio: bool = False,
                        tracker=None, target_usd_override: float = None) -> dict:
        self.iteration_count += 1
        
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

        router = await self._get_router()
        
        # Read Current Position
        current_qty = 0.0
        try:
            current_qty = await router.get_position(symbol)
            if current_qty is None: current_qty = 0.0
        except Exception as e:
            logger.error(f"[SVRGN] Failed to read position for {symbol}: {e}")

        current_usd = abs(current_qty) * price
        current_side = 'LONG' if current_qty > 0.0 else ('SHORT' if current_qty < 0.0 else 'FLAT')
        if current_usd <= 1.0: 
            current_side = 'FLAT'

        result.update({
            'current_side': current_side,
            'current_usd': current_usd,
            'current_qty': current_qty
        })
        
        # Calculate 'The Pot'
        total_equity = await router.get_trading_capital(symbol)
        reserve_pct = getattr(self.settings, 'CASH_RESERVE_PCT', 0.10)
        tradable_capital = total_equity * (1.0 - reserve_pct)
        
        result.update({
            'total_equity': total_equity,
            'tradable_capital': tradable_capital
        })

        # --- The Oracle Decision (XGBoost + LGNN Consensus) ---
        xgb_conviction = abs(soul_val)
        xgb_side = "LONG" if soul_val > 0 else "SHORT"
        
        # 1. Fetch LGNN Macro State (Real Entropy from FastAPI)
        try:
            import requests
            resp = await asyncio.to_thread(requests.get, "http://127.0.0.1:8001/api/lgnn/vitals", {"timeout": 2})
            if resp.status_code == 200:
                data = resp.json()
                macro_entropy = data.get("entropy", 0.5)
                macro_mass = float(data.get("nodes", 50))
            else:
                macro_mass = 50.0
                macro_entropy = 0.5
        except Exception as e:
            logger.error(f"[SVRGN] LGNN Vitals Query failed: {e}")
            macro_mass = 50.0
            macro_entropy = 0.5
            
        # 2. Compute Structural Stability (Resonance)
        # High entropy = Graph is fracturing = Panic = VETO trade
        # Low entropy = Graph is stable = Green light
        stability_factor = max(0.0, 1.0 - (macro_entropy * 1.5)) # if entropy > 0.66, stability is 0
        
        # Final conviction is XGBoost scaled by Graph Stability
        final_conviction = xgb_conviction * stability_factor
        
        if final_conviction < 0.05: # Minimal noise filter or VETO activated
            target_side = "FLAT"
            target_usd = 0.0
            if xgb_conviction >= 0.05 and final_conviction < 0.05:
                logger.warning(f"[ORACLE] XGBoost {xgb_side} VETOED by LGNN (Entropy: {macro_entropy:.2f})")
        else:
            target_side = xgb_side
            target_usd = min(final_conviction * self.max_position_usd, tradable_capital)

        # Global Override
        if target_usd_override is not None and target_side != "FLAT":
            target_usd = target_usd_override

        # Exchange Minimums
        if 0 < target_usd < 15.5:
            target_usd = 15.5 if target_side != "FLAT" else 0.0

        result.update({'target_usd': target_usd, 'target_side': target_side})

        # Calculate Delta
        if target_side == current_side:
            delta_usd = target_usd - current_usd
        elif target_side == 'FLAT':
            delta_usd = -current_usd
        elif current_side == 'FLAT':
            delta_usd = target_usd
        else:
            delta_usd = current_usd + target_usd # Flip
            
        result['delta_usd'] = delta_usd

        # Threshold & Action
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
        
        # Log Execution Plan
        conv_bar = '█' * int(min(final_conviction, 1.0) * 10) + '░' * (10 - int(min(final_conviction, 1.0) * 10))
        logger.info(
            f"[SVRGN] {symbol:<8} Z:{z_score:+.2f} | Oracle:[{conv_bar}]({final_conviction:.2f}) "
            f"| Target: {target_side} ${target_usd:7.2f} "
            f"| Current: ${current_usd:7.2f} "
            f"| Δ: ${delta_usd:+7.2f} → {action}"
        )

        if dry_run:
            return result

        # Execution
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
        except Exception as e:
            logger.error(f"[REBALANCER] {symbol} Execution Fail: {e}")
            
        return result

    async def _open_position(self, symbol, side, qty, price):
        router = await self._get_router()
        qty = abs(float(qty))
        order_type = getattr(self.settings, 'REBALANCER_ORDER_TYPE', 'market')
        res = await router.place_order(symbol, 'buy' if side == 'LONG' else 'sell', order_type, qty, price)
        if res:
            logger.info(f"[REBALANCER] ✅ {symbol} Opened {side} {qty:.6f} @ ${price:.2f}")
        else:
            logger.error(f"[REBALANCER] ❌ {symbol} Open Failed: {getattr(router, '_last_error', 'Unknown Error')}")
    
    async def _close_position(self, symbol, side, qty, price):
        router = await self._get_router()
        qty = abs(float(qty))
        order_type = getattr(self.settings, 'REBALANCER_ORDER_TYPE', 'market')
        res = await router.place_order(symbol, 'sell' if side == 'LONG' else 'buy', order_type, qty, price, {'reduce_only': True})
        if res:
            logger.info(f"[REBALANCER] ✅ {symbol} Closed {side} {qty:.6f} @ ${price:.2f}")
        else:
            logger.error(f"[REBALANCER] ❌ {symbol} Close Failed: {getattr(router, '_last_error', 'Unknown Error')}")


_instance = None
def get_rebalancer(settings=None):
    global _instance
    if _instance is None:
        if settings is None:
            from config.settings import get_settings
            settings = get_settings()
        _instance = ContinuousRebalancer(settings)
    return _instance
