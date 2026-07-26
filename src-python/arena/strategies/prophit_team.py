from arena.team import TeamStrategy
from arena.strategies.rat import TheRat
from arena.strategies.dragon import TheDragon

class TheProphitTeam(TeamStrategy):
    """
    Phase 1: Mastery of the Dragon.
    
    The Rat rides The Dragon.
    - Dragon: Creates a volatility grid (Mean Reversion).
    - Rat: Snipes panic wicks within that grid.
    
    Synergy:
    - When Dragon is pulling back (Mean Reversion), Rat doubles down on Wicks.
    - They share the same goal (Profit from Noise), but different timeframes.
    """
    
    def __init__(self):
        # Rat: 3 Sigma (Rare Wicks only)
        rider = TheRat() 
        rider.skills['wick_sensitivity'] = 3.0
        
        # Dragon: 8% Grid (Deep Breathing only)
        mount = TheDragon(skills={"grid_width": 0.08}) 
        
        super().__init__(
            rider=rider, 
            mount=mount, 
            name="The Prophit Team (Rat + Dragon)"
        )
