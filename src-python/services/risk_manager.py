
"""
Risk Manager
Guardian of the Sovereign.
Enforces safety overrides to prevent catastrophic loss.
"""
import logging
from services.tracker import get_performance_tracker

logger = logging.getLogger("RiskManager")

class RiskManager:
    def __init__(self):
        self.tracker = get_performance_tracker()
        self.max_drawdown_limit = 0.08 # 8% Hard Stop
        self.max_position_size_pct = 0.2 # 20% of Equity max per trade
        
    def check_trade_risk(self, symbol: str, side: str, qty: float, price: float) -> dict:
        """
        Evaluates a proposed trade against risk parameters.
        Returns: {"allowed": bool, "reason": str}
        """
        stats = self.tracker.get_stats()
        
        # 1. Drawdown Check
        # If we hit the 8% limit, we are in "Lockdown". Only REDUCE risk (Sell) is allowed.
        dd = stats.get('drawdown_percentage', 0.0)
        if dd >= (self.max_drawdown_limit * 100):
            if side == "BUY":
                return {"allowed": False, "reason": f"Drawdown Limit Hit ({dd:.1f}% >= 8.0%). Trading Halted."}
            
        # 2. Position Sizing Check (Simulation)
        # Assume $10k mock equity if not real
        equity = stats.get('current_equity', 10000.0)
        trade_value = qty * price
        
        if trade_value > (equity * self.max_position_size_pct):
            return {
                "allowed": False, 
                "reason": f"Position Size Violation (${trade_value:.0f} > {self.max_position_size_pct:.0%} of Equity)"
            }

        return {"allowed": True, "reason": "Risk Validated"}

_risk_manager = None

def get_risk_manager():
    global _risk_manager
    if not _risk_manager:
        _risk_manager = RiskManager()
    return _risk_manager
