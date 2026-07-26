from arena.api import IStrategy
import pandas as pd
import numpy as np
import random

class EchoWeaverStrategy(IStrategy):
    """
    Echo Weaver Strategy (Nika's Rhythm).
    Gemini Seed #6.
    
    Logic: Case 3: STATE_MACHINE (Alchemist/Biology).
    - Uses a synthetic 'Circadian Rhythm' to switch modes.
    - Ground Protocol (10-13): Maintenance.
    - Hardware Load (14-18): Logic/Trend.
    - System Reset (18-22): Rest.
    - God Mode (22-02): Chaos/Scar Hunting.
    """

    @property
    def name(self) -> str:
        return "The Echo Weaver"

    @property
    def class_type(self) -> str:
        return "ALCHEMIST"

    def __init__(self, skills=None):
        super().__init__()
        # Hyperparameters representing the User's DNA
        self.skills = skills if skills else {
            "architect_discipline": 0.5,  # Ability to follow trend in 'Hardware Last'
            "alchemist_aggression": 0.8,  # Leverage used in 'God Mode'
            "scar_sensitivity": 0.02,     # % Drop required to trigger a 'Sanctuary' buy
            "reset_discipline": 1.0       # Probability of actually adhering to the rest period
        }

    def _get_state(self, hour: int) -> str:
        """Determines the Alchemical State based on Circadian Rhythm."""
        if 10 <= hour < 13:
            return "GROUND_PROTOCOL"
        elif 14 <= hour < 18:
            return "HARDWARE_LOAD"
        elif 18 <= hour < 22:
            return "SYSTEM_RESET"
        elif 22 <= hour or hour < 2:
            return "GOD_MODE"
        else:
            return "DORMANCY" # Sleep phase (Owl mode ending)

    def on_tick(self, packet: dict) -> float:
        return 0.0

    def next_candle(self, df: pd.DataFrame) -> float:
        # 1. Determine State
        # We need a datetime index to fetch "hour".
        if not isinstance(df.index, pd.DatetimeIndex):
            # Fallback for synthetic data w/o datetime index
            # Map length/step to a 24h cycle
            simulated_hour = (len(df) % 240) // 10 
        else:
            simulated_hour = df.index[-1].hour
        
        state = self._get_state(simulated_hour)

        current_price = df['close'].iloc[-1]
        prev_price = df['close'].iloc[-2]
        
        # 2. Execute Logic based on State
        
        if state == "SYSTEM_RESET":
            # The Fighter rests. No exposure.
            if random.random() < self.skills['reset_discipline']:
                return 0.0
            else:
                return 0.1 # Fidgeting/Noise

        elif state == "GROUND_PROTOCOL":
            # Input & Maintenance. Small, mean-reverting trades.
            ma_short = df['close'].tail(5).mean()
            if current_price < ma_short:
                return 0.2 # Gentle buy
            return 0.0

        elif state == "HARDWARE_LOAD":
            # The Architect. Pure Logic. Trend Following.
            ma_long = df['close'].tail(50).mean()
            if current_price > ma_long:
                return 1.0 * self.skills['architect_discipline']
            elif current_price < ma_long:
                return -1.0 * self.skills['architect_discipline']
            return 0.0

        elif state == "GOD_MODE":
            # The Alchemist. Finding beauty in flaws (Scars).
            if prev_price == 0: return 0.0
            pct_change = (current_price - prev_price) / prev_price
            
            if pct_change < -self.skills['scar_sensitivity']:
                # We catch the falling knife because we see it as a "Sanctuary"
                return 1.0 * self.skills['alchemist_aggression']
            
            # Otherwise, trade volatility expansion
            volatility = df['close'].tail(10).std()
            long_vol = df['close'].tail(100).std()
            if volatility > long_vol:
                 return 1.0 * self.skills['alchemist_aggression'] # Ride the chaos
            
            return 0.0

        return 0.0

    def evolve(self, mutation_rate: float = 0.1) -> 'EchoWeaverStrategy':
        # Mutate the DNA
        new_skills = self.skills.copy()
        for key in new_skills:
            if random.random() < mutation_rate:
                change = random.uniform(-0.1, 0.1)
                new_skills[key] = max(0.0, min(1.0, new_skills[key] + change))
        return EchoWeaverStrategy(skills=new_skills)
