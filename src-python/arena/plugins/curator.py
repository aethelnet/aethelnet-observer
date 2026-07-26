from .base import IPlugin
from typing import Dict, List

class CuratorPlugin(IPlugin):
    """
    The Curator (Selection Domain).
    Decides which strategies deserve training time based on Merit.
    """
    def __init__(self):
        self.performance_ledger: Dict[str, float] = {} # {strategy_name: last_pnl}

    @property
    def name(self) -> str:
        return "The Curator"

    def on_generation_complete(self, stats: dict):
        # Update ledger (Cumulative)
        name = stats.get('strategy_name')
        pnl = stats.get('pnl', 0.0)
        if name:
            current = self.performance_ledger.get(name, 0.0)
            self.performance_ledger[name] = current + pnl
            print(f"[Curator] {name} PnL Update: {pnl:.2f} -> Total: {self.performance_ledger[name]:.2f}")

    def on_strategy_selected(self, strategy_name: str) -> bool:
        # Meritocracy Logic: The Hard Floor
        cumulative_pnl = self.performance_ledger.get(strategy_name, 0.0)
        
        # If a strategy has lost too much capital, it is exiled.
        if cumulative_pnl < -1000.0:
            print(f"[Curator] {strategy_name} Exiled (PnL: {cumulative_pnl:.2f} < -1000.0)")
            return False
            
        return True
