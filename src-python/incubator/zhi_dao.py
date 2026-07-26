from typing import List, Dict, Any
import numpy as np

class ZhiDao:
    """
    Chapter 21: Zhi Dao (Knowing the Way).
    
    "Crucial Self-Examination."
    
    Logic:
    1. Review recent history (The "3 Day" window).
    2. If performance is poor, trigger calibration.
    """
    
    def __init__(self):
        self.window_size = 72 # "3 Days" (72 Hours) or 72 Trades
        
    def examine_self(self, trade_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Critically examines the self.
        Returns a 'Correction' dict.
        """
        if len(trade_history) < 10:
            return None # Not enough data to judge
            
        recent = trade_history[-self.window_size:]
        
        # Calculate Metrics
        pnls = [t.get('pnl_pct', 0) for t in recent]
        win_rate = sum(1 for p in pnls if p > 0) / len(pnls)
        total_pnl = sum(pnls)
        
        print(f"[ZHI DAO] Examining {len(recent)} trades. Win Rate: {win_rate:.2f}, PnL: {total_pnl:.2f}%")
        
        correction = {}
        
        # 1. The Discipline Check
        # If losing money, we need to be MORE STRICT.
        if total_pnl < 0:
            print("[ZHI DAO] The Way is lost. Increasing Discipline.")
            correction['wick_sensitivity'] = 4.0 # Make Rat harder to trigger
            correction['grid_width'] = 0.1 # Make Dragon wider
            
        # 2. The Aggression Check
        # If winning too easily (High Win Rate > 80%), we are leaving money on the table.
        elif win_rate > 0.8:
            print("[ZHI DAO] The Way is too easy. Increasing Aggression.")
            correction['wick_sensitivity'] = 2.0 # Trigger more often
            
        return correction
