from typing import Dict, Any
from arena.api import IStrategy
import pandas as pd

class TheGooseBull(IStrategy):
    """
    The Perma-Bull.
    Just screams BUY continuously. 
    Used by the LayerTracker as a baseline vector to lock onto runaway uptrends.
    """
    
    def __init__(self, skills: Dict[str, Any] = None):
        super().__init__(skills)

    @property
    def name(self) -> str:
        return "The Goose Bull"

    @property
    def class_type(self) -> str:
        return "Baseline" 

    def default_skills(self) -> Dict[str, Any]:
        return {}

    def next_candle(self, df: pd.DataFrame) -> float:
        return 1.0

    def on_tick(self, market_state: Dict[str, Any]) -> float:
        return 1.0


class TheGooseBear(IStrategy):
    """
    The Perma-Bear.
    Just screams SELL continuously. 
    Used by the LayerTracker as a baseline vector to lock onto runaway downtrends.
    """
    
    def __init__(self, skills: Dict[str, Any] = None):
        super().__init__(skills)

    @property
    def name(self) -> str:
        return "The Goose Bear"

    @property
    def class_type(self) -> str:
        return "Baseline" 

    def default_skills(self) -> Dict[str, Any]:
        return {}

    def next_candle(self, df: pd.DataFrame) -> float:
        return -1.0

    def on_tick(self, market_state: Dict[str, Any]) -> float:
        return -1.0
