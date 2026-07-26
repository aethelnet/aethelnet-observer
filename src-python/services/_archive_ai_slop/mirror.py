"""
[ 50 ] T H E _ M I R R O R
==========================
LAYER:     META_LEARNING
STATUS:    REFLECTING
AUTHORITY: SELF
PHASE:     50 (REFLECTION)
"""

import logging
from typing import Dict, List
import numpy as np

logger = logging.getLogger("Mirror")

class Mirror:
    """
    The Meta-Leaner.
    Observes the Oracle's predictions vs Reality.
    Adjusts the weights of [Logic, Soul, Hindsight] based on who is 'Right'.
    """
    def __init__(self, oracle_instance):
        self.oracle = oracle_instance
        self.history = [] # List of {timestamp, predictions: {}, outcome: float}
        self.learning_rate = 0.01

    def absorb_outcome(self, inputs: Dict[str, float], actual_return: float):
        """
        inputs: {'logic': 0.8, 'soul': -0.2, 'hindsight': 0.5} (Raw signals before weighting)
        actual_return: 0.005 (0.5%)
        """
        # Directional correctness check
        # We want to increase weight of inputs that matched the SIGN of actual_return
        
        target_sign = np.sign(actual_return)
        if target_sign == 0: return

        updates = {}
        
        for component, signal in inputs.items():
            current_weight = self.oracle.weights.get(component, 0.25)
            
            # Did this component predict the right direction?
            if np.sign(signal) == target_sign:
                # Correct! Reward it.
                # Heuristic: Reward more if the signal was strong
                reward = abs(signal) * self.learning_rate
                new_weight = current_weight + reward
            else:
                # Wrong! Punish it.
                punishment = abs(signal) * self.learning_rate
                new_weight = current_weight - punishment
                
            updates[component] = max(0.05, min(0.8, new_weight)) # Clamp 5% to 80%

        # Normalize weights to sum to 1.0 (Softmax-ish or just Simple Norm)
        total_weight = sum(updates.values())
        if total_weight > 0:
            for k in updates:
                updates[k] /= total_weight
                
        # Apply to Oracle
        self.oracle.weights.update(updates)
        
        # Log occasionally
        if np.random.random() < 0.05:
            logger.info(f"[Mirror] Reflected Weights: {self.oracle.weights}")

# Singleton is tricky because it needs the oracle instance.
# We will init it inside Brain or Omni.
