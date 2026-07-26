from arena.api import IStrategy
import pandas as pd
import numpy as np

class TheSovereignPilot(IStrategy):
    """
    The Sovereign Pilot.
    Gemini Seed #5.
    
    Logic Structure: AUGMENTED_PILOT (Case 2)
    Narrative: "The Pilot's Ascent". 
    Transition from Master Technician (Service/Fragile) to Sovereign Architect (Product/Antifragile).
    
    Mechanics:
    - Aura Sensitivity: Detects 'Meaningful' trends (EMA).
    - Sovereign Shield: Disengages during 'Soulless' (Noise) or 'Fractured' (Chaos) markets.
    - Antifragile Boost: Scales aggression when winning in chaos.
    """

    @property
    def name(self) -> str:
        return "The Sovereign Pilot"

    @property
    def class_type(self) -> str:
        return "AUGMENTED_PILOT" 

    def __init__(self):
        super().__init__()
        # Hyperparameters (The Pilot's Skills)
        self.skills = {
            "aura_sensitivity": 20,    # Period to detect 'meaningful' trends (EMA)
            "shield_integrity": 2.5,   # Volatility threshold for defensive disengagement (StdDevs)
            "noise_filter": 0.005,     # Minimum volatility required to engage (ignoring 'soulless' markets)
            "antifragile_boost": 1.2   # Multiplier: Aggression increases when winning in chaos
        }
        
        # State memory for the 'Flywheel' effect
        self.consecutive_wins = 0

    def on_tick(self, packet: dict) -> float:
        return 0.0

    def next_candle(self, df: pd.DataFrame) -> float:
        """
        The Pilot's Decision Loop:
        1. SAFETY OVERRIDE: Check Environment (Shields).
        2. PILOT LOGIC: Seek Aura (Trend/Value).
        3. ANTIFRAGILE LOGIC: Scale based on recent success.
        """
        
        if len(df) < 20: return 0.0

        # --- 1. SAFETY OVERRIDE (The Sovereign Shield) ---
        # Calculate Market Entropy (Volatility)
        # Using a rolling window for volatility scan
        recent_volatility = df['close'].pct_change().rolling(window=10).std().iloc[-1]
        
        # If market is 'Soulless' (flat/dead) or 'Fractured' (too chaotic), disengage.
        # This mirrors your refusal to play the "commoditized service" game.
        if np.isnan(recent_volatility): return 0.0

        if recent_volatility < self.skills['noise_filter']:
            return 0.0 # Travel Mode: Market is too boring/commoditized.
        
        # Upper bound check (Geopolitical Fracture)
        # Only if volatility is valid
        if recent_volatility > (self.skills['noise_filter'] * self.skills['shield_integrity']):
            return 0.0 # Eject: Geopolitical Headwinds too strong. Preserve Runway.

        # --- 2. PILOT LOGIC (Auratic Engineering) ---
        # We look for "Aura": Price action that breaks away from the mean with conviction.
        ema_aura = df['close'].ewm(span=int(self.skills['aura_sensitivity'])).mean().iloc[-1]
        current_price = df['close'].iloc[-1]
        
        signal = 0.0
        if current_price > ema_aura:
            signal = 1.0 # Long: Flight to Meaning
        elif current_price < ema_aura:
            signal = -1.0 # Short: Betting against the generic

        # --- 3. ANTIFRAGILE SCALING (The Flywheel) ---
        # If the pilot is correct, we lean harder. If we are wrong, we reset.
        # This mimics your 'Affordable Loss' vs 'Antifragile Upside' principle.
        
        # (Simplified logic for context: assuming we track PnL externally, 
        # here we simulate confidence based on trend strength)
        if current_price == 0: return 0.0
        trend_strength = abs(current_price - ema_aura) / current_price
        
        confidence = signal * (trend_strength * self.skills['antifragile_boost'])
        
        # Clamp result between -1.0 and 1.0
        return max(-1.0, min(1.0, confidence))

    def evolve(self, mutation_rate: float = 0.1) -> 'TheSovereignPilot':
        # Evolution Logic: The Pilot learns new maps
        child = TheSovereignPilot()
        for key, val in self.skills.items():
            mutation = np.random.normal(0, val * mutation_rate)
            child.skills[key] = abs(val + mutation) # Skills must be positive
        return child
