from typing import Dict, Any
from arena.api import IStrategy

class TheTank(IStrategy):
    """
    The Paladin. 
    High HP (Capital Preservation).
    Trades rare Mean Reversion events.
    ""Refuses to die.""
    """
    @property
    def name(self) -> str:
        return "The Tank"

    @property
    def class_type(self) -> str:
        return "Tank"

    def default_skills(self) -> Dict[str, Any]:
        return {
            'z_trigger': 3.0,
            'fade_size': 0.7, # TIMESKIP UPGRADE: Heavier Punches (was 0.5)
            'support_nibble': 0.40 # TIMESKIP UPGRADE: Stronger Shoulders (was 0.25)
        }
        
    def equip_aegis(self):
        """
        LEGENDARY GEAR: Aegis of the Immortal.
        Effect: Divine Armor. (Increases buying power during crashes).
        """
        print("[TANK] Equipping Aegis of the Immortal. Defense +50%.")
        self.skills['support_nibble'] = 0.5 # Double the support buy size

    def on_tick(self, market_state: Dict[str, Any]) -> float:
        # The Tank only moves when the market is overextended.
        # It fades the move (Mean Reversion).
        
        z_score = market_state.get('z_score', 0)
        
        trigger = self.skills['z_trigger']
        fade_size = self.skills['fade_size']
        nibble = self.skills['support_nibble']
        
        # Logic: If Z-Score is extreme (> 3.0), Short.
        # But only if Volume is dropping (Exhaustion).
        volume_trend = market_state.get('volume_trend', 0) # Assumed indicator
        
        if z_score > trigger: 
            # Fade the pump
            return -fade_size # Conservative size
            
        elif z_score < -trigger: # Crash
            # Context: Don't catch a falling knife unless we see support
            return nibble # Small nibble buy
            
        return 0.0 # Shield Up (Cash)
