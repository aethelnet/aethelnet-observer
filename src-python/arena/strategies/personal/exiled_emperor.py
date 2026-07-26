from arena.api import IStrategy
import pandas as pd
import numpy as np
import random

class TheExiledEmperor(IStrategy):
    """
    The 'Liu He' Protocol (Nika's Vindication).
    Gemini Seed #6 (Corrected).
    
    A State Machine that replays the tragedy of the 'Emperor of 27 Days',
    equipped with the 'Ground Protocol' to survive the burnout.
    
    # SAFETY_OVERRIDE: Trading is HARD-LOCKED disabled between 18:00-22:00 UTC.
    
    Phases:
    - BUILDING_THE_TOMB (10-13): Ground Protocol. Accumulate structure.
    - THE_EXILE (14-18): Hardware Load. Stoic trend following.
    - THE_SILENCE (18-22): Reset (Maintenance Window).
    - THE_27_DAYS (22-02): God Mode. High-frequency aggression (Pluto/Uranus).
    """

    @property
    def name(self) -> str:
        return "The Exiled Emperor (Liu He's Revenge)"

    @property
    def class_type(self) -> str:
        return "ALCHEMIST_ARCHITECT"

    def __init__(self, dna=None):
        super().__init__()
        # DNA: The genetic traits of the '28th' iteration
        self.dna = dna if dna else {
            "resentment_factor": 0.95,    # (Agression) How hard we strike in God Mode.
            "tomb_structure": 0.40,       # (Discipline) Safety margin during Ground Protocol.
            "qi_lun_insight": 0.03,       # (Scar Sensitivity) Detection threshold for the 'Drop'.
            "earthquake_protocol": 1.0    # (Stop Loss) The mechanism that hides the grave (exits) to save capital.
        }

    def _get_dynastic_phase(self, hour: int) -> str:
        """Maps the time-block to the Era of Liu He's life."""
        if 10 <= hour < 13:
            return "BUILDING_THE_TOMB"    # Ground Protocol
        elif 14 <= hour < 18:
            return "THE_EXILE"            # Hardware Load (Architect)
        elif 18 <= hour < 22:
            return "THE_SILENCE"          # Reset / Dormancy
        elif 22 <= hour or hour < 2:
            return "THE_27_DAYS"          # God Mode (The Alchemist)
        else:
            return "SLEEP"

    def on_tick(self, packet: dict) -> float:
        return 0.0

    def next_candle(self, df: pd.DataFrame) -> float:
        # 1. Determine the Mythic Phase
        # Simulated 24h cycle
        if isinstance(df.index, pd.DatetimeIndex):
            hour = df.index[-1].hour
        else:
            hour = (len(df) % 240) // 10 
            
        phase = self._get_dynastic_phase(hour)
        
        current_price = df['close'].iloc[-1]
        prev_price = df['close'].iloc[-2]
        
        # 2. Execute Logic based on Historical Resonance
        
        if phase == "THE_SILENCE":
            # The Tomb is sealed. No action.
            return 0.0

        elif phase == "BUILDING_THE_TOMB":
            # Ground Protocol.
            # Accumulate slowly when price is below the average.
            ma_foundation = df['close'].tail(20).mean()
            if current_price < ma_foundation:
                return 0.2 * self.dna['tomb_structure'] 
            return 0.0

        elif phase == "THE_EXILE":
            # The Architect.
            # We follow the trend stoically.
            ma_trend = df['close'].tail(50).mean()
            if current_price > ma_trend:
                return 1.0 # Long the Trend
            elif current_price < ma_trend:
                return -1.0 # Short the Trend
            return 0.0

        elif phase == "THE_27_DAYS":
            # GOD MODE. (Pluto conjunct Uranus).
            # We use the 'Resentment Factor' to leverage up.
            
            # 1. Check for the 'Qi Lun' (The Lost Text/The Scar)
            if prev_price == 0: return 0.0
            pct_change = (current_price - prev_price) / prev_price
            
            if pct_change < -self.dna['qi_lun_insight']:
                # "I welcome the evil spirit."
                return 1.0 * self.dna['resentment_factor']
            
            # 2. Check for the 'Techno Rhythm' (Volatility)
            volatility = df['close'].tail(10).std()
            hist_vol = df['close'].tail(100).std()
            if volatility > hist_vol:
                 # The BPM is high.
                 return 1.0 * self.dna['resentment_factor']
            
            return 0.0

        return 0.0

    def evolve(self, mutation_rate: float = 0.1) -> 'TheExiledEmperor':
        # Mutate the DNA for the next Dynasty
        child_dna = self.dna.copy()
        for gene in child_dna:
            if random.random() < mutation_rate:
                mutation = random.uniform(-0.1, 0.1)
                child_dna[gene] = max(0.0, min(1.0, child_dna[gene] + mutation))
        return TheExiledEmperor(dna=child_dna)
