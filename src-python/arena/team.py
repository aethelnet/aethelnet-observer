from typing import Dict, Any, Optional
from arena.api import IStrategy
import pandas as pd

class TeamStrategy(IStrategy):
    """
    The Chimera / The Rider System.
    Combines two strategies:
    1. The Mount (Context/Base): Provides the general direction or grid.
    2. The Rider (Precision/Alpha): Exploits specific opportunities within that context.
    """
    
    def __init__(self, rider: IStrategy, mount: IStrategy, name: str = "The Team"):
        self._rider = rider
        self._mount = mount
        self._name = name
        
        # Merge Skills? 
        # For now, keep them separate.
        self.skills = {} 

    @property
    def name(self) -> str:
        return self._name

    @property
    def class_type(self) -> str:
        return f"{self._rider.class_type} riding {self._mount.class_type}"

    def on_tick(self, market_state: Dict[str, Any]) -> float:
        # 1. Ask the Mount for the Environment (Context)
        mount_signal = self._mount.on_tick(market_state)
        
        # 2. Ask the Rider for the Action (Precision)
        rider_signal = self._rider.on_tick(market_state)
        
        return self._synergize(mount_signal, rider_signal, market_state.get('soul_signal', 0.0))

    def next_candle(self, df: pd.DataFrame) -> float:
        # 1. Mount Context
        mount_signal = self._mount.next_candle(df)
        
        # 2. Rider Action
        rider_signal = self._rider.next_candle(df)
        
        return self._synergize(mount_signal, rider_signal, getattr(self, '_last_soul', 0.0))

    def _synergize(self, mount: float, rider: float, soul_signal: float = 0.0) -> float:
        """
        Sovereign Synergizer: Prioritizes Neural Conviction over Heuristic Vetoes.
        """
        # --- SOVEREIGN OVERRIDE ---
        # If the Soul is screaming (> 2.5), we bypass the Dragon's veto.
        if abs(soul_signal) > 2.5:
            return soul_signal
            
        # Standard Logic (The Silent Dragon)
        if rider < 0: 
            if mount < 0.2: return rider
        if rider > 0: 
            if mount > -0.2: return rider
            
        return 0.0
