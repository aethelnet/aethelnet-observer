from typing import Dict, Any
from arena.api import IStrategy

class TheAlchemist(IStrategy):
    """
    The Support Class.
    Doesn't look at Price directly.
    Looks at Physics (Entropy, Flow).
    """
    @property
    def name(self) -> str:
        return "The Alchemist"

    @property
    def class_type(self) -> str:
        return "Alchemist"
        
    def equip_emerald_tablet(self):
        """
        LEGENDARY GEAR: The Emerald Tablet.
        Effect: Transmutation. (Tolerates higher entropy).
        """
        print("[ALCHEMIST] Equipping The Emerald Tablet. Knowledge +100%.")
        self.entropy_threshold = 0.95
        
    def __init__(self):
        self.entropy_threshold = 0.9 # TIMESKIP UPGRADE: Chaos Mastery (was 0.8)

    def on_tick(self, market_state: Dict[str, Any]) -> float:
        # The Alchemist checks the "State of Matter"
        
        entropy = market_state.get('entropy', 0)
        flow_regime = market_state.get('regime', 'unknown')
        
        # 1. Gas State (High Entropy)
        if entropy > self.entropy_threshold:
            return 0.0 # Liquidate. Too volatile.
            
        # 2. Liquid State (Laminar Flow)
        # Map System Regimes to Alchemist Physics
        if flow_regime in ['JOY', 'SAD', 'GREED', 'FEAR', 'laminar']:
            # Follow the current, don't question it.
            trend = market_state.get('trend_strength', 0.0) # [FIX] Standardized Trend
            return trend * 1.0 # Max allocation in clean water
            
        # 3. Turbulent State (Storm)
        if flow_regime == 'turbulent':
            return 0.0 # CASH IS KING in a storm.
            
        # 4. Solid State (Ice/Range)
        # Scalp the boundaries
        # TIMESKIP LESSON: Don't assume Ice holds.
        return 0.0 # Safety First.
        
