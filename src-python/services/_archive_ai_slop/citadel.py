import logging
import os
import time
import json
from typing import Dict, Optional
from core.failsafe import atomic_write

logger = logging.getLogger("Citadel")

class Citadel:
    """
    The Citadel (Phase 20).
    Central Risk Management Engine.
    Enforces 'Hard' Limits that Strategy/Manager cannot override.
    """
    def __init__(self):
        # Configuration (Hard Coded Safety)
        self.config = {
            "max_daily_loss_pct": 0.05, # 5% Max Daily Loss
            "max_drawdown_pct": 0.05,   # 5% Max Total Drawdown from HWM
            "max_leverage": 3.0,        # 3x Max Leverage
            "max_position_size_pct": 8.0, # 80% (Spot)
            "circuit_breaker_timeout": 600 # 10m  Cool down
        }
        
        # State
        self.state = {
            "daily_start_balance": 100.0,
            "current_balance": 100.0,
            "high_water_mark": 0.0,
            "daily_loss": 0.0,
            "circuit_breaker_active": False,
            "cb_trigger_time": 0
        }
        
        self.load_state()

    def update_balance(self, balance: float):
        """Called every tick to update risk metrics."""
        # SANITIZE INPUT IMMEDIATELY
        safe_balance = 0.0
        if isinstance(balance, dict):
             safe_balance = float(balance.get('total_equity', balance.get('total', 0.0)))
        else:
             safe_balance = float(balance)

        if self.state["daily_start_balance"] == 0:
            self.state["daily_start_balance"] = safe_balance
            
        self.state["current_balance"] = safe_balance
        
        # Update HWM
        if safe_balance > self.state["high_water_mark"]:
            self.state["high_water_mark"] = safe_balance
            
        # Calculate Daily PnL
        daily_pnl = safe_balance - self.state["daily_start_balance"]
        self.state["daily_loss"] = -daily_pnl if daily_pnl < 0 else 0.0
        
        self.save_state()

    def check_risk(self, proposal: Dict) -> bool:
        """
        Returns True if SAFE, False if RISK_EVENT.
        """
        now = time.time()
        
        # 0. GOD MODE BYPASS (Phase 99)
        from config import get_settings
        env_mode = get_settings().ENV_MODE
        
        # 1. Check Circuit Breaker
        if self.state["circuit_breaker_active"]:
            # Check Timeout
            if now - self.state["cb_trigger_time"] > self.config["circuit_breaker_timeout"]:
                self.reset_circuit_breaker()
                logger.info("[CITADEL] 🟢 Circuit Breaker Cooled Down. Systems Online.")
            else:
                if env_mode == "production":
                    logger.critical("[CITADEL] 🔴 CIRCUIT BREAKER ACTIVE. TRADING BLOCKED IN PRODUCTION.")
                return False

        # 2. Check Daily Loss Limit
        daily_loss_pct = 0.0
        if self.state["daily_start_balance"] > 0:
            daily_loss_pct = self.state["daily_loss"] / self.state["daily_start_balance"]
            
        if daily_loss_pct > self.config["max_daily_loss_pct"]:
            self.trigger_circuit_breaker("Max Daily Loss Exceeded")
            if env_mode == "production":
                logger.critical(f"[CITADEL] 🔴 DAILY LOSS LIMIT ({daily_loss_pct*100:.2f}%) HIT. TRADING BLOCKED.")
            return False
            
        # 3. Check Max Drawdown
        drawdown_pct = 0.0
        if self.state["high_water_mark"] > 0:
            drawdown_pct = (self.state["high_water_mark"] - self.state["current_balance"]) / self.state["high_water_mark"]
            
        if drawdown_pct > self.config["max_drawdown_pct"]:
             self.trigger_circuit_breaker(f"Max Drawdown Exceeded ({drawdown_pct*100:.2f}%)")
             if env_mode == "production":
                 logger.critical(f"[CITADEL] 🔴 MAX DRAWDOWN ({drawdown_pct*100:.2f}%) HIT. TRADING BLOCKED.")
             return False

        # 4. Check Position Size
        # proposal = {symbol, side, quantity, price?}
        if proposal and isinstance(proposal, dict):
             qty = float(proposal.get('quantity', 0))
             price = float(proposal.get('price', 0))
             if price == 0:
                  # Estimate price if market order (using last known balance as proxy? No, need feed)
                  # For now, if price is missing, we skip or use 1.0 placeholder if safer?
                  # Better: Require 'price' or 'estimated_price' in proposal.
                  pass
             
             notional = qty * price
             if notional > 0 and self.state["current_balance"] > 0:
                  pct_of_equity = notional / self.state["current_balance"]
                  if pct_of_equity > self.config["max_position_size_pct"]:
                       logger.warning(f"[CITADEL] 🛡️ REJECTED: Position Size {pct_of_equity*100:.2f}% > Limit {self.config['max_position_size_pct']*100}%")
                       return False

        return True

    def trigger_circuit_breaker(self, reason: str):
        if not self.state["circuit_breaker_active"]:
            self.state["circuit_breaker_active"] = True
            self.state["cb_trigger_time"] = time.time()
            logger.critical(f"[CITADEL] 🔴 CIRCUIT BREAKER TRIPPED: {reason}")
            self.save_state()

    def reset_circuit_breaker(self):
        self.state["circuit_breaker_active"] = False
        self.state["cb_trigger_time"] = 0
        self.state["daily_start_balance"] = self.state["current_balance"] # Reset daily baseline
        self.save_state()

    def load_state(self):
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            path = os.path.join(base_dir, "citadel_state.json")
            with open(path, "r") as f:
                saved = json.load(f)
                self.state.update(saved)
        except:
            pass

    def save_state(self):
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            path = os.path.join(base_dir, "citadel_state.json")
            with atomic_write(path) as f:
                json.dump(self.state, f, indent=4)
        except:
            pass

# Singleton
_citadel = None
def get_citadel():
    global _citadel
    if _citadel is None:
        _citadel = Citadel()
    return _citadel
