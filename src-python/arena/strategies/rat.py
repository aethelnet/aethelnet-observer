from typing import Dict, Any
from arena.api import IStrategy
import pandas as pd
import numpy as np
import logging
from config import get_settings
import time
import math

logger = logging.getLogger("Strategy.Rat")

class TheRat(IStrategy):
    """
    Sovereign Rat (The Minimalist Scavenger).
    Refined and de-bloated. Focuses on pure price physics.
    
    Logic:
    - Pure Z-Score Trajectory.
    - Below threshold: Trend Following.
    - Above threshold: Mean Reversion.
    - Liberated: Respects SIGNAL_REVERSION for global polarity.
    """
    @property
    def name(self) -> str:
        return "The Rat"

    @property
    def class_type(self) -> str:
        return "Rogue"

    def default_skills(self) -> Dict[str, Any]:
        """Base stats for the Rat. Calibrated for the Sovereign Engine."""
        settings = get_settings()
        self.signal_metadata = {} # {symbol: metadata_dict}
        
        return {
            'wick_lookback': 11,
            'mean_reversion_strength': 3.18, 
            'profit_target': getattr(settings, 'PROFIT_TARGET', 0.015),
            'velocity_threshold': 1.2,
            'confidence_threshold': 0.4
        }
        
    def __init__(self, skills: Dict[str, Any] = None):
        super().__init__(skills)
        logger.info("[Rat] 🧬 Sovereign Core Active. (Minimalist Mode)")

    def on_tick(self, market_state: Dict[str, Any]) -> float:
        """
        The Pure Sensor: Mapping Market Physics to Signal Conviction.
        """
        # 1. Physics Extraction
        z_score = float(market_state.get('z_score', 0.0))
        if math.isnan(z_score): z_score = 0.0
        
        velocity = float(market_state.get('velocity', 0.0))
        z_velocity = float(market_state.get('z_velocity', 0.0))
        
        # 2. Physics-Based Dampeners
        # Trend Dampener: Dampen trend if momentum is reversing (exhaustion)
        trend_dampener = 1.0
        if (z_score * z_velocity) < 0:
            exhaustion = min(abs(z_velocity) * 5.0, 1.0)
            trend_dampener = 1.0 - (exhaustion * 0.85)

        # Reversion Dampener: Dampen reversion if momentum is still accelerating (don't step in front of a train)
        reversion_dampener = 1.0
        if (z_score * z_velocity) > 0:
            acceleration = min(abs(z_velocity) * 5.0, 1.0)
            reversion_dampener = 1.0 - (acceleration * 0.85)

        # 3. Decision Matrix (Trend vs Reversion)
        mrs = self.skills.get('mean_reversion_strength', 3.18)
        
        if abs(z_score) >= mrs:
            final_signal = -z_score * reversion_dampener  # Fade the extreme safely
        else:
            final_signal = z_score * trend_dampener       # Ride the drift safely

        # 4. Global Liberation (Polarity Flip)
        settings = get_settings()
        if getattr(settings, 'SIGNAL_REVERSION', False):
            final_signal = -final_signal

        # 5. Metadata for Execution Layer
        symbol = market_state.get('symbol', 'UNK')
        self.signal_metadata[symbol] = {
            "z_score": z_score,
            "dampener": reversion_dampener if abs(z_score) >= mrs else trend_dampener,
            "velocity": velocity,
            "final": final_signal,
            "profit_target": self.skills.get('profit_target', 0.015),
        }

        return final_signal

    def next_candle(self, window_df: pd.DataFrame) -> Dict[str, Any]:
        """Legacy compatibility for backtesting engines."""
        closes = window_df['close'].values
        if len(closes) < 11: return {'action': 0.0}
        
        # Simple Z-Score calculation
        ma = np.mean(closes[-11:])
        std = np.std(closes[-11:])
        sigma = (closes[-1] - ma) / std if std > 1e-6 else 0.0
        
        # Action logic matches on_tick
        mrs = self.skills.get('mean_reversion_strength', 3.18)
        action = -1.0 if abs(sigma) >= mrs else 1.0
        if sigma < 0: action = -action # Flip for side
        
        return {
            'action': action * (abs(sigma) / mrs),
            'sigma': sigma
        }
