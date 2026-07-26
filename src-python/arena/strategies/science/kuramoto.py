from typing import List, Dict, Any
import numpy as np
import pandas as pd
from arena.api import IStrategy

class TheKuramoto(IStrategy):
    """
    The Kuramoto: Synchronization of Oscillators.
    Markets vibrate. We detect when different timeframes (frequencies)
    Phase Lock (synchronize).
    Constructive Interference = Big Move.
    """
    def __init__(self):
        super().__init__()
        # Skills: Coupling Strength (K)
        self.skills = {
            "coupling_k": 0.5, # How easily phases lock
            "natural_freq": 10, # Base frequency (e.g. 10 candle cycle)
            "coherence_threshold": 0.8 # Requirements to trigger trade
        }

    @property
    def name(self) -> str:
        return "The Kuramoto"

    @property
    def class_type(self) -> str:
        return "PHYSICIST"

    def on_tick(self, packet: Dict[str, Any]) -> float:
        return 0.0
        
    def next_candle(self, window_df: pd.DataFrame) -> float:
        # Detect Dominant Frequency (Spectroscopy)
        closes = window_df['close'].values
        # Fibonacci Horizons for High-Dimensional Sync
        horizons = [3, 5, 8, 13, 21, 34, 55, 89]
        
        if len(closes) < max(horizons):
            return 0.0
            
        from scipy.signal import hilbert, detrend
        
        def get_stable_phase(period):
            if len(closes) < period: return 0.0
            try:
                sig = detrend(closes[-period:])
                return float(np.angle(hilbert(sig)[-1]))
            except:
                min_p, max_p = np.min(closes[-period:]), np.max(closes[-period:])
                if max_p == min_p: return 0.0
                return ((closes[-1] - min_p) / (max_p - min_p) * 2 * np.pi) - np.pi
            
        phases = [get_stable_phase(h) for h in horizons]
        
        # Calculate Order Parameter (r)
        complex_sum = sum(np.exp(1j * p) for p in phases)
        r = np.abs(complex_sum) / len(horizons)
        
        # Action
        if r > self.skills['coherence_threshold']:
            avg_phase = np.mean(phases)
            if avg_phase < -1.5: return 1.0 # Synced Bottom
            elif avg_phase > 1.5: return -1.0 # Synced Top
        
        return 0.0

    def get_raw_sync(self, window_df: pd.DataFrame) -> float:
        """Exposes the Signed Kuramoto Sync (r * sign(avg_phase)) for Neural Manifold."""
        closes = window_df['close'].values
        horizons = [5, 8, 13, 21, 34, 55, 89]
        if len(closes) < max(horizons): return 0.0
        
        from scipy.signal import hilbert, detrend
        def get_p(period):
            try:
                sig = detrend(closes[-period:])
                return np.angle(hilbert(sig)[-1])
            except: return 0.0
            
        phases = [get_p(h) for h in horizons]
        r = np.abs(sum(np.exp(1j * p) for p in phases)) / len(horizons)
        avg_p = np.mean(phases)
        
        # Return Signed Coherence: +r for Sync High, -r for Sync Low
        return float(r * (1.0 if avg_p > 0 else -1.0))

    def evolve(self, mutation_rate: float = 0.1) -> 'TheKuramoto':
        child = TheKuramoto()
        for key, val in self.skills.items():
            change = 1.0 + np.random.uniform(-mutation_rate, mutation_rate)
            child.skills[key] = val * change
        return child
