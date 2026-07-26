from typing import Dict, Any
from arena.api import IStrategy

class TheArchitect(IStrategy):
    """
    The Planner.
    Looks for Structure (Support/Resistance).
    "I build foundation."
    """
    @property
    def name(self) -> str:
        return "The Architect"

    @property
    def class_type(self) -> str:
        return "Alchemist"

    def on_tick(self, market_state: Dict[str, Any]) -> float:
        # The Architect looks for price interacting with 'Levels'
        levels = market_state.get('levels', [])
        price = market_state.get('price', 0)
        
        if not levels or price == 0:
            return 0.0
            
        support = levels[0]
        resistance = levels[1]
        
        # Simple Rejection Logic
        # If Price is near Resistance (within 0.5%), sell.
        # If Price is near Support (within 0.5%), buy.
        
        if price >= resistance * 0.995:
             return -0.5
        elif price <= support * 1.005:
             return 0.5
            
        return 0.0
