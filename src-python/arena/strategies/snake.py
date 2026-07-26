from typing import Dict, Any
from arena.api import IStrategy
import pandas as pd
import numpy as np

class TheSnake(IStrategy):
    """
    The Mount: The Snake (Water/Poison)
    Archetype: Sniper / Hidden Execution.
    
    Philosophy:
        "I do not chase. I wait."
        The Snake sets a "Moon Line" (Hidden Level). 
        It does not place orders. It waits for the price to cross the line.
        
    Lore:
        - The Snake Crossing the Moon: The precise moment of intersection.
    """
    
    def __init__(self, skills: Dict[str, Any] = None):
        super().__init__(skills)
        self.moon_phase = 0 # current state

    @property
    def name(self) -> str:
        return "The Snake"

    @property
    def class_type(self) -> str:
        return "Assassin" 

    def default_skills(self) -> Dict[str, Any]:
        return {
            "moon_period": 3, # BETA MODE: Ultra-fast crossover for frequent signals
            "strike_zone": 0.001, # Tolerance for the 'Crossing'
            "magic_level_interval": 100, # The "00" Psychological Levels
            "magic_level_tolerance": 5   # How close price must be to level
        }

    def next_candle(self, df: pd.DataFrame) -> float:
        """
        Snake Logic:
        1. Calculate The Moon Line (e.g., SMA 50).
        2. Check for Crossing.
        3. Strike.
        """
        if len(df) < self.skills['moon_period']: return 0.0
        
        moon_period = self.skills['moon_period']
        closes = df['close']
        
        # The Moon Line (Hidden Level)
        moon_line = closes.rolling(moon_period).mean().iloc[-1]
        
        current_price = closes.iloc[-1]
        prev_price = closes.iloc[-2]
        
        # Check for CROSSING
        # Bullish Crossing: Price went from Below Moon to Above Moon
        if prev_price < moon_line and current_price > moon_line:
            # print(f"[SNAKE] 🐍 STRIKE LONG! (Price: {current_price} crossed Moon: {moon_line})")
            return 1.0 # STRIKE LONG
            
        # Bearish Crossing: Price went from Above Moon to Below Moon
        if prev_price > moon_line and current_price < moon_line:
            # print(f"[SNAKE] 🐍 STRIKE SHORT! (Price: {current_price} crossed Moon: {moon_line})")
            return -1.0 # STRIKE SHORT
            
        # The Snake is hidden. No signal otherwise.
        return 0.0

    def on_tick(self, market_state: Dict[str, Any]) -> float:
        # BETA MODE: High-Frequency Testing (Moon Period = 3)
        # But we respect the "Spirit" - Logic Driven, not Random.
        
        price = market_state.get('price', 0.0)
        
        interval = self.skills.get('magic_level_interval', 100)
        tolerance = self.skills.get('magic_level_tolerance', 5)
        
        if interval > 0 and int(price) % interval < tolerance: # Close to a 'Magic' level
             # print(f"[SNAKE] 🐍 STRIKE! Precision Clean. Price: {price}") # Silent
             # return 1.0 # Disabled for Live Stability, Snake waits for next_candle
             pass
             
        return 0.0
