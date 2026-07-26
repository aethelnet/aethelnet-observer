"""
Brain Exoskeleton: Market Timing & Phase Detection
==================================================
Distilled from legacy ESN/DMD/PCA bloat.
The core philosophical truth of the Exoskeleton: Market Exhaustion Detection.

Uses a clean Hilbert Transform to detect the phase of the market cycle,
preventing the Rebalancer from entering trends at the absolute peak (exhaustion).
"""

import numpy as np
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger("BrainExoskeleton")

try:
    from scipy.signal import hilbert, detrend
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    logger.warning("scipy not found - phase detection disabled")

class BrainExoskeleton:
    """
    Lean Exoskeleton containing only the proven mathematical models (Hilbert Phase).
    Returns dummy values for legacy UI endpoints to prevent breaking the Telegram bot.
    """
    def __init__(self, window=40):
        self.window = window

    def _compute_hilbert(self, prices: List[float]) -> Tuple[float, float]:
        if not HAS_SCIPY or len(prices) < self.window:
            return 0.0, 0.0
        try:
            arr = np.array(prices[-self.window:])
            detrended = detrend(arr)
            analytic = hilbert(detrended)
            
            phase = float(np.angle(analytic[-1]))
            envelope = float(np.abs(analytic[-1]))
            
            avg_envelope = np.mean(np.abs(analytic))
            if avg_envelope > 0:
                envelope = envelope / avg_envelope
                
            return phase, envelope
        except Exception as e:
            logger.debug(f"Hilbert calculation failed: {e}")
            return 0.0, 0.0

    def analyze(self, history_prices: List[float], history_vols: List[float], z_scores: List[float]) -> Dict:
        """
        Runs the core phase analysis.
        """
        if not history_prices or len(history_prices) < 5: 
            last_price = float(history_prices[-1]) if history_prices else 0.0
            return {
                "clean_price": last_price,
                "phase": 0.0, 
                "envelope": 0.0,
                "dmd_forecast": last_price,
                "stability": 0.0,
                "esn_depth": 0.0
            }

        # 1. Hilbert Phase (Cycle Position) - The only signal that matters for Sizing
        phase, envelope = self._compute_hilbert(history_prices)
        
        # 2. Stability (Volatility measure used for general context)
        stability = 0.0
        try:
            lookback = min(len(history_prices)-1, 20)
            base = np.array(history_prices[-(lookback+1):-1])
            base[base == 0] = 1.0 # Protect division
            pct_changes = np.abs(np.diff(history_prices[-lookback-1:]) / base)
            stability = float(np.mean(pct_changes)) * 100.0
        except Exception:
            pass

        return {
            "clean_price": float(history_prices[-1]),
            "phase": float(phase),
            "envelope": float(envelope),
            "dmd_forecast": float(history_prices[-1]), # Legacy format
            "stability": float(stability),
            "esn_depth": 0.0 # Legacy format
        }
