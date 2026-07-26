
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger("Analysis.Signals")

class SignalGenerator:
    async def get_actionable_trade_setup(self, symbol: str, event: Dict[str, Any], current_price: float) -> Optional[Dict[str, Any]]:
        """
        Generate actionable trade setup from event prediction.
        """
        if not event or not symbol: return None
        
        etype = event.get('type')
        eprice = event.get('price', 0)
        confidence = event.get('confidence', 0)
        time_str = event.get('time_str', 'soon')
        dev_pct = event.get('deviation_pct', 0)
        
        action = None
        entry = current_price
        target = 0
        stop = 0
        
        if etype == 'low':
            # Buy the dip
            action = "BUY LIMIT"
            entry = eprice * 1.002 # Slightly above low
            target = entry * 1.015 # 1.5% target
            stop = entry * 0.995   # 0.5% stop
        elif etype == 'high':
            # Short the top
            action = "SELL LIMIT"
            entry = eprice * 0.998
            target = entry * 0.985
            stop = entry * 1.005
        elif etype == 'reversal_up':
            action = "BUY STOP"
            entry = current_price * 1.001
            target = entry * 1.02
            stop = entry * 0.99
        elif etype == 'reversal_down':
            action = "SELL STOP"
            entry = current_price * 0.999
            target = entry * 0.98
            stop = entry * 1.01
        
        if not action: return None
        
        # Risk Reward
        risk = abs(entry - stop)
        reward = abs(target - entry)
        rr = reward / risk if risk > 0 else 0
        
        if rr < 1.0: return None # Filter bad RR
        
        return {
            "symbol": symbol,
            "action": action,
            "entry_price": entry,
            "target_price": target,
            "stop_loss": stop,
            "risk_reward": round(rr, 2),
            "confidence": int(confidence * 100),
            "entry_time": time_str,
            "profit_pct": (reward/entry)*100,
            "risk_pct": (risk/entry)*100,
            "position_size": 0.0 # Calculator required for size
        }
