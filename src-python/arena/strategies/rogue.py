from typing import Dict, Any
from arena.api import IStrategy

class TheRogue(IStrategy):
    @property
    def name(self) -> str:
        return "The Rogue"

    @property
    def class_type(self) -> str:
        return "Rogue"

    def on_tick(self, market_state: Dict[str, Any]) -> float:
        # The Rogue likes Momentum (Volatility).
        # If price moved fast, he chases it (Scalp).
        
        z_score = market_state.get('z_score', 0)
        
        # Simple Logic: If Momentum > 2.0 (Fast Move), Go Long.
        if z_score > 2.0:
            return 1.0
        # If Momentum < -2.0 (Crash), Short Hard.
        elif z_score < -2.0:
            return -1.0
            
        return 0.0 # Stay in shadows
