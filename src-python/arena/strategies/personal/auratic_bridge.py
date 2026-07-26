from arena.api import IStrategy
import pandas as pd
import numpy as np
import random
from typing import Dict, Any

class TheAuraticBridge(IStrategy):
    """
    The Auratic Bridge (Architect/Alchemist).
    Gemini Seed #3.
    
    Concept:
    - Architect (Default): Conservative Trend Following.
    - Alchemist (Triggered): Mean Reversion during Chaos (God Mode).
    """
    @property
    def name(self) -> str:
        return "The Auratic Bridge"

    @property
    def class_type(self) -> str:
        return "HYBRID"

    def __init__(self, patience=20, aggression=1.5, structure_lock=0.02, skills: Dict[str, Any] = None):
        # Allow instantiation via skills dict (generic loader) or args (specific)
        super().__init__()
        
        if skills:
            self.skills = skills
        else:
            self.skills = {
                "architect_window": int(patience),      # Timeframe for structural analysis (SMA)
                "alchemist_trigger": float(aggression), # Volatility multiplier to trigger God Mode
                "structure_integrity": float(structure_lock) # Stop loss / Safety clamp
            }

    def on_tick(self, packet: dict) -> float:
        return 0.0

    def next_candle(self, df: pd.DataFrame) -> float:
        # Minimum data check
        window = int(self.skills["architect_window"])
        if len(df) < window + 1:
            return 0.0

        # 1. Analyze the Structure (The Architect)
        closes = df['close'].values
        sma = np.mean(closes[-window:])
        current_price = closes[-1]
        
        # Calculate Volatility (Standard Deviation)
        volatility = np.std(closes[-window:])
        
        # 2. Determine State
        # If volatility is excessively high, Logic fails -> Switch to Alchemist (Intuition/Mean Reversion)
        threshold = max(0.1, closes[-2] * (self.skills["structure_integrity"] * self.skills["alchemist_trigger"]))
        if volatility > threshold:
            
            # --- ALCHEMIST MODE (God Mode: 22:00 - 02:00) ---
            # Exploits the chaos. If price rips up, short it. If it crashes, buy it.
            # Represents: extracting value from the "rich" (irrational exuberance).
            if current_price > sma + (2 * volatility):
                return -1.0 # Aggressive Short
            elif current_price < sma - (2 * volatility):
                return 1.0  # Aggressive Long
            return 0.0

        else:
            # --- ARCHITECT MODE (Hardware Load: 14:00 - 18:00) ---
            # Follows the structure. Safe, logical building.
            # If price is above structure (SMA), we support it.
            if current_price > sma:
                return 0.5 # Moderate Long
            elif current_price < sma:
                return -0.5 # Moderate Short
                
        return 0.0

    def evolve(self, mutation_rate: float = 0.1) -> 'TheAuraticBridge':
        # Mutate the balance between Order and Chaos
        # We use the generic skills inheritance for simplicity in the loop,
        # but re-implement per user spec.
        
        new_skills = self.skills.copy()
        
        if random.random() < mutation_rate:
            # Mutate window (Architect's patience)
            new_skills["architect_window"] = max(5, int(new_skills["architect_window"] * random.uniform(0.8, 1.2)))
        
        if random.random() < mutation_rate:
            # Mutate trigger (Alchemist's wake-up call)
            new_skills["alchemist_trigger"] = new_skills["alchemist_trigger"] * random.uniform(0.9, 1.1)
            
        return TheAuraticBridge(skills=new_skills)
