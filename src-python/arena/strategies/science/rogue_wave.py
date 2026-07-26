from ...api import IStrategy
import numpy as np
import pandas as pd

class TheRogueWave(IStrategy):
    """
    The Rogue Wave (Interference Strategy).
    
    Concept:
        Ocean waves usually cancel out (Destructive Interference).
        Rarely, they align crest-to-crest (Constructive Interference) to form a Monster.
        
    Mechanic:
        - Decomposes price into 3 wave components:
            1. Short (Ripples)
            2. Medium (Swell)
            3. Long (Tide)
        - Computes 'Interference Amplitude' (Sum of normalized waves).
        - If Sum > Threshold (e.g., 2.5 out of 3.0), we bet on a Breakout.
    """
    @property
    def name(self) -> str:
        return "The Rogue Wave"

    @property
    def class_type(self) -> str:
        return "SCIENTIST"

    def default_skills(self) -> dict:
        return {
            'short_period': 5,
            'medium_period': 20,
            'long_period': 50,
            'threshold': 2.5
        }

    def on_tick(self, packet: dict) -> float:
        return 0.0
        
    def next_candle(self, df: pd.DataFrame) -> float:
        if len(df) < self.skills['long_period'] + 5:
            return 0.0
            
        closes = df['close'].values
        
        # 1. Decompose waves (Using detrended oscillators)
        
        def distinct_wave(period):
            # Simple Proxy: Price relative to Moving Average (normalized)
            ma = pd.Series(closes).rolling(period).mean().iloc[-1]
            price = closes[-1]
            # Normalize by ATR or Stdev ideally, here simple % diff
            res = (price - ma) / price * 100
            # Clip to [-1, 1] essentially
            return np.tanh(res) 
            
        w1 = distinct_wave(int(self.skills['short_period']))
        w2 = distinct_wave(int(self.skills['medium_period']))
        w3 = distinct_wave(int(self.skills['long_period']))
        
        # 2. Constructive Interference
        amplitude = w1 + w2 + w3 # Max possible ~3.0, Min ~-3.0
        
        signal = 0.0
        
        if amplitude > self.skills['threshold']:
            # All waves pushing UP
            signal = 1.0
        elif amplitude < -self.skills['threshold']:
            # All waves pushing DOWN
            signal = -1.0
            
        return signal

    def evolve(self, mutation_rate: float = 0.1) -> 'IStrategy':
        child = TheRogueWave()
        # Mutate periods slightly
        child.skills['medium_period'] = int(self.skills['medium_period'] * np.random.normal(1, mutation_rate))
        child.skills['threshold'] = np.clip(self.skills['threshold'] + np.random.normal(0, 0.1), 1.0, 3.0)
        return child
