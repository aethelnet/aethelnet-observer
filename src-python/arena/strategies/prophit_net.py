from typing import Dict, Any
from arena.api import IStrategy
import pandas as pd
import numpy as np
import logging
import math
from config import get_settings

logger = logging.getLogger("Strategy.ProphitNet")

class ProphitNetStrategy(IStrategy):
    """
    ProphitNet (The Final Evolution).
    The culmination of market physics and LGNN semantic topology.
    Designed for the pursuit of absolute knowledge over simple profit.
    """
    @property
    def name(self) -> str:
        return "ProphitNet"

    @property
    def class_type(self) -> str:
        return "Omniscience"

    def default_skills(self) -> Dict[str, Any]:
        """Genetics that the Arena will evolve."""
        settings = get_settings()
        self.signal_metadata = {}
        
        return {
            'soul_pan': 0.75,                # Weighting: 75% LGNN, 25% Physics
            'confidence_gate': 0.20,         # Minimum neural conviction to act
            'physics_limit': 3.0,            # Cap the Z-Score influence
            'profit_target': getattr(settings, 'PROFIT_TARGET', 0.02),
            'stop_loss': getattr(settings, 'STOP_LOSS', 0.015),
            'velocity_dampener': 0.8,        # How much to punish extreme spikes
            'topology_trust_multiplier': 1.5, # Boost signal if LGNN is extremely confident
            'chaos_immunity': 2.5,           # Skip trades if market velocity exceeds this
            'dynamic_sizing_factor': 0.5     # Shrink position size dynamically in high volatility
        }
        
    def __init__(self, skills: Dict[str, Any] = None):
        super().__init__(skills)
        # --- THE FAREWELL GIFTS (Relics of the Creator's Sanity) ---
        self.relics = {
            "behelit": True,       # The Crimson Behelit (Mastery of Equanimity)
            "beans": True,         # The Magic Beans (Sustenance during Drawdowns)
            "goose": True,         # The Golden Goose (Luck & Serendipity)
            "tarot": "THE_WORLD",  # The Tarot Card (Final Completion)
        }
        logger.info("[ProphitNet] 🌌 The Omniscience Engine is online.")
        logger.info(f"[ProphitNet] 🎒 Equipped with the Creator's Relics: {list(self.relics.keys())}")

    def _soft_limit(self, val: float, limit: float) -> float:
        if limit <= 0: return 0.0
        return max(-limit, min(val, limit)) / limit

    def on_tick(self, market_state: Dict[str, Any]) -> float:
        """
        The Master Algorithm: Blends LGNN Probabilities with Raw Physics.
        """
        # 1. Extract LGNN Probability (The "Soul")
        # Defaults to 0.5 (neutral) if the graph hasn't formed an opinion
        soul_pred = float(market_state.get('soul_pred', 0.5))
        if math.isnan(soul_pred): soul_pred = 0.5
        
        # Scale [0.0 to 1.0] -> [-1.0 to 1.0]
        neural_val = (soul_pred - 0.5) * 2.0
        
        # 2. Extract Physics (The "Body")
        z_score = float(market_state.get('z_score', 0.0))
        if math.isnan(z_score): z_score = 0.0
        z_velocity = float(market_state.get('z_velocity', 0.0))
        
        # Cap physics extremes
        limit = self.skills.get('physics_limit', 3.0)
        physics_val = self._soft_limit(z_score, limit=limit)
        
        # 3. Chaos Immunity & Dampeners
        dampener_str = self.skills.get('velocity_dampener', 0.8)
        chaos_threshold = self.skills.get('chaos_immunity', 2.5)
        
        if abs(z_velocity) > chaos_threshold:
            # Absolute chaos: LGNN overrides physics completely or we step out
            physics_val *= 0.1 
        elif abs(z_velocity) > 2.0:
            physics_val *= (1.0 - dampener_str)

        # 4. Fusion with Topology Trust
        pan = self.skills.get('soul_pan', 0.75)
        
        # If LGNN is highly confident (> 0.8 or < 0.2), boost its trust dynamically
        if abs(neural_val) > 0.8:
            trust_mult = self.skills.get('topology_trust_multiplier', 1.5)
            pan = min(0.95, pan * trust_mult)
            
        fusion_signal = (neural_val * pan) + (physics_val * (1.0 - pan))
        
        # 5. Conviction Gate
        gate = self.skills.get('confidence_gate', 0.20)
        
        # [THE BEHELIT EFFECT] 
        # If the Behelit is active, it grants equanimity. 
        # We don't panic during massive dips; we actually lower the gate to catch the blood in the streets.
        if self.relics.get('behelit') and z_score < -3.0:
            gate *= 0.5  
            
        # [THE GOOSE EFFECT]
        # The Golden Goose gives a tiny serendipitous boost to positive neural conviction.
        if self.relics.get('goose') and neural_val > 0.5:
            fusion_signal *= 1.05

        if abs(fusion_signal) < gate:
            fusion_signal = 0.0

        # Global Reversion switch
        settings = get_settings()
        if getattr(settings, 'SIGNAL_REVERSION', False):
            fusion_signal = -fusion_signal

        symbol = market_state.get('symbol', 'UNK')
        self.signal_metadata[symbol] = {
            "neural_val": neural_val,
            "physics_val": physics_val,
            "fusion_signal": fusion_signal,
            "profit_target": self.skills.get('profit_target', 0.02),
            "stop_loss": self.skills.get('stop_loss', 0.015)
        }

        return fusion_signal

    def next_candle(self, window_df: pd.DataFrame) -> Dict[str, Any]:
        """Legacy compatibility"""
        closes = window_df['close'].values
        if len(closes) < 11: return {'action': 0.0}
        
        ma = np.mean(closes[-11:])
        std = np.std(closes[-11:])
        sigma = (closes[-1] - ma) / std if std > 1e-6 else 0.0
        
        # In pure backtest without LGNN, fallback to physics
        limit = self.skills.get('physics_limit', 3.0)
        action = self._soft_limit(sigma, limit)
        
        return {
            'action': action,
            'sigma': sigma
        }
