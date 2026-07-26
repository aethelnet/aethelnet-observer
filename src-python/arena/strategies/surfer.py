from typing import Dict, Any
from arena.api import IStrategy

class TheSurfer(IStrategy):
    """
    The Druid.
    Rides the Wave.
    Exits at the first sign of turbulence.
    "Be water, my friend."
    """
    @property
    def name(self) -> str:
        return "The Surfer"

    @property
    def class_type(self) -> str:
        return "Druid"

    def on_tick(self, market_state: Dict[str, Any]) -> float:
        z_score = market_state.get('z_score', 0)
        entropy = market_state.get('entropy', 0)
        
        # 1. If water is choppy (High Entropy), PADDLE OUT (Exit)
        if entropy > 0.5:
            return 0.0
            
        # 2. If Wave is building (Momentum), RIDE IT
        if z_score > 0.5:
            return 0.8 # Long
        elif z_score < -0.5:
            return -0.8 # Short
            
        # 3. Else, float
        return 0.0
