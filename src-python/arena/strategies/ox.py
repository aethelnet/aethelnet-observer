from typing import Dict, Any
from arena.api import IStrategy
import pandas as pd
import numpy as np

class TheOx(IStrategy):
    """
    The Mount: The Ox (Rhino/Amos)
    Archetype: Tank / Stamina.
    
    Philosophy:
        "I do not stop."
        The Ox is a Trend Follower with massive conviction.
        It uses DCA (Dollar Cost Averaging) to absorb drawdowns ("Thick Skin").
        
    Lore:
        - Amos the Rhino: Carries the burdern.
    """
    
    def __init__(self, skills: Dict[str, Any] = None):
        super().__init__(skills)
        self.entry_price = 0.0

    @property
    def name(self) -> str:
        return "The Ox"

    @property
    def class_type(self) -> str:
        return "Paladin" 

    def default_skills(self) -> Dict[str, Any]:
        return {
            "dca_zone": 0.05, # Buy more every 5% drop
            "conviction": 0.9 # High conviction trend following
        }

    def next_candle(self, df: pd.DataFrame) -> float:
        """
        Ox Logic:
        1. Identify Macro Trend (200 SMA).
        2. If Bullish, Buy.
        3. If Price Drops, Buy More (DCA).
        4. Never sell on noise (HODL).
        """
        if len(df) < 200: return 0.0
        
        closes = df['close']
        sma200 = closes.rolling(200).mean().iloc[-1]
        current_price = closes.iloc[-1]
        
        # 1. Macro Trend Check
        # The Ox is an Optimist (Long Only).
        # "I do not move backwards."
        
        if current_price > sma200:
            # Bullish Context
            if self.entry_price == 0.0:
                 self.entry_price = current_price
                 return 0.5 # (Initial Entry)
                 
            # DCA Logic: If price dropped X% from entry, Buy More
            drop = (current_price - self.entry_price) / self.entry_price
            
            if drop < -self.skills['dca_zone']:
                self.entry_price = current_price # Reset average
                return 1.0 # MAX BUY (DCA)
            
            return 0.1 # Maintain maintenance buying
            
        else:
            # Bearish Context
            # The Ox does NOT sell. It endures.
            # Ideally it hedges, but for now it just stops buying.
            return 0.0
            
    def on_tick(self, market_state: Dict[str, Any]) -> float:
        return 0.0
