from typing import Dict, Any
from arena.api import IStrategy
import pandas as pd
import numpy as np

class TheDragon(IStrategy):
    """
    The Mount: The Dragon (Fire/Wind)
    Archetype: Market Maker / Volatility Harvester.
    
    Philosophy:
        "I am the storm."
        The Dragon does not predict direction. It creates a Grid of possibilities.
        It inhales liquidity (limit buys) and exhales fire (limit sells).
        
    Lore:
        - 1127 Sins: The Chaos Seed.
    """
    
    def __init__(self, skills: Dict[str, Any] = None):
        super().__init__(skills)
        self.grid_center = None
        self.chaos_seed = 1127 # The Sin Count

    @property
    def name(self) -> str:
        return "The Dragon"

    @property
    def class_type(self) -> str:
        return "Tank" # High stamina/liquidity

    def default_skills(self) -> Dict[str, Any]:
        return {
            "grid_width": 0.02, # 2% Grid
            "breath_depth": 10, # Number of levels
            "decay": 0.99,      # Mean reversion pull
            "ma_period": 20     # Moving Average Period
        }

    def next_candle(self, df: pd.DataFrame) -> float:
        """
        Dragon Logic:
        If price is far from moving average (Grid Center), pull it back.
        """
        ma_period = int(self.skills.get('ma_period', 20))
        if len(df) < ma_period: return 0.0
        
        closes = df['close']
        ma = closes.rolling(ma_period).mean().iloc[-1]
        current = closes.iloc[-1]
        
        # Calculate deviation ("How far is the rabbit?")
        deviation = (current - ma) / ma
        
        # If deviation is positive (Price High), Dragon exhales (Short).
        # If deviation is negative (Price Low), Dragon inhales (Long).
        
        # Strength depends on 'grid_width'
        strength = -deviation / self.skills['grid_width']
        
        # Clamp to -1.0 to 1.0 (The Dragon's Rage)
        return float(np.clip(strength, -1.0, 1.0))

    def on_tick(self, market_state: Dict[str, Any]) -> float:
        return 0.0
