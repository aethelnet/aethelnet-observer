"""
Ouroboros: Core Entropy Decay
=============================
Distilled from legacy LLM-based mutating daemon.
The core philosophical truth of Ouroboros is Self-Regulation:
When the market becomes too chaotic (Z-Score > 4.5), the system 
eats its own tail (confidence) to protect the portfolio.

No void entities, no LLM queries. Pure mathematical decay.
"""

import math
import logging
import asyncio

logger = logging.getLogger("LGNN.Ouroboros")

def apply_ouroboros_decay(z_score: float, current_confidence: float) -> float:
    """
    Exponentially decays the confidence scalar if z_score exceeds the chaos threshold.
    """
    chaos_threshold = 4.0
    abs_z = abs(z_score)
    
    if abs_z > chaos_threshold:
        # Topological shear factor
        shear_factor = abs_z - chaos_threshold
        decay_multiplier = math.e ** (-shear_factor * 0.5) # Tune 0.5 for steepness
        new_confidence = current_confidence * decay_multiplier
        logger.debug(f"[Ouroboros] Market Chaos detected (Z={z_score:.2f}). Decayed confidence from {current_confidence:.2f} to {new_confidence:.2f}")
        return new_confidence
        
    return current_confidence


class LegacyOuroborosDaemon:
    """
    Dummy daemon to prevent backend crashes from legacy imports in main.py.
    """
    def __init__(self):
        self.is_running = False
        
    async def run_forever(self):
        self.is_running = True
        logger.info("[Ouroboros] Legacy daemon bypassed. Ouroboros is now a mathematical constraint.")
        while self.is_running:
            await asyncio.sleep(86400) # Sleep forever

ouroboros = LegacyOuroborosDaemon()
