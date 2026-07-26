from typing import Dict, Any
from arena.api import IStrategy

class TheBerserker(IStrategy):
    """
    The Barbarian.
    Uses Martingale sizing.
    Doubles down on losers.
    "Rage only increases."
    """
    def __init__(self):
        self.consecutive_losses = 0

    @property
    def name(self) -> str:
        return "The Berserker"

    @property
    def class_type(self) -> str:
        return "Barbarian"

    def on_tick(self, market_state: Dict[str, Any]) -> float:
        # The Berserker is a counter-trend grid trader
        z_score = market_state.get('z_score', 0)
        
        # Simple Logic: Always fade the move
        if z_score > 1.0:
            return -0.5 * (1 + self.consecutive_losses) # Short
        elif z_score < -1.0:
             return 0.5 * (1 + self.consecutive_losses) # Long
             
        return 0.0

    def on_gladiator_death(self):
        print(f"[{self.name}] RAGE QUIT! (Resetting losses)")
        self.consecutive_losses = 0
