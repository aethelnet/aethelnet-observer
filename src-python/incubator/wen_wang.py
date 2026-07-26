import json
import os
from typing import Dict, Any

class WenWang:
    """
    Chapter 22: Wen Wang (Asking about the King).
    
    The Archive of Legitimacy.
    Monitors trades and identifies "Royal Trades" (Perfect Execution).
    
    Criteria for a Royal Trade:
    1. PnL > 1.0% (Significant Gain)
    2. Drawdown ~ 0.0% (Perfect Entry / Zero Pain)
    """
    
    def __init__(self, archive_path="liu_he_tomb.json"):
        self.archive_path = archive_path
        self.royal_trades = []
        self._load_archive()
        
    def _load_archive(self):
        if os.path.exists(self.archive_path):
            try:
                with open(self.archive_path, 'r') as f:
                    self.royal_trades = json.load(f)
            except:
                self.royal_trades = []
                
    def inspect_trade(self, trade_result: Dict[str, Any]):
        """
        "The King asks: Was this trade legitimate?"
        """
        pnl = trade_result.get('pnl_pct', 0.0)
        max_fef = trade_result.get('max_fef', 0.0) # Maximum Favorable Excursion (Runup)
        max_mae = trade_result.get('max_mae', 0.0) # Maximum Adverse Excursion (Drawdown)
        
        # Criteria:
        # 1. Profitable
        if pnl < 0.5: return # Not worthy of the King
        
        # 2. Precision (Low Drawdown)
        # If the trade went against us by more than 0.1%, it wasn't perfect.
        is_perfect = abs(max_mae) < 0.1 
        
        if is_perfect:
            print(f"[WEN WANG] A Royal Trade Discovered! PnL: {pnl:.2f}%, Drawdown: {max_mae:.2f}%")
            self.save_trade(trade_result)
            
    def save_trade(self, trade: Dict[str, Any]):
        self.royal_trades.append(trade)
        with open(self.archive_path, 'w') as f:
            json.dump(self.royal_trades, f, indent=4)
