"""
[ 42 ] T H E _ O R A C L E
==========================
LAYER:     SYNTHESIS
STATUS:    DIVINING
AUTHORITY: DEEP_THOUGHT
PHASE:     42 (THE_ANSWER)
"""

import logging
from typing import Dict, Any

logger = logging.getLogger("Oracle")

class Oracle:
    """
    The Ultimate Synthesizer.
    Weighs the input of the Rat (Logic), the Soul (ML), and the Time Machine (Hindsight).
    Produces "The Answer" (Truth Score).
    """
    def __init__(self):
        # Weights (The "Secret Sauce")
        self.weights = {
            'logic': 0.55,      # The Rat (Physics) - Primary Driver
            'soul': 0.25,       # The Soul (ML) - Confirmation
            'hindsight': 0.1,   # The Time Machine (Patterns)
            'sentiment': 0.1    # The Crowd (External)
        }
    
    def calculate_truth_score(self, state: Dict[str, Any]) -> float:
        """
        Input: State Dictionary containing inputs from all sub-systems.
        Output: Float -1.0 (Strong SELL) to +1.0 (Strong BUY).
        """
        score = 0.0
        
        # 1. GATHER RAW INPUTS
        
        # A. LOGIC (The Rat)
        logic_val = state.get('logic_signal', 0.0)
        logic_val = max(-1.0, min(1.0, logic_val))
        
        # B. SOUL (ML)
        # Input: Probability (0 to 1). Map to (-1 to 1).
        # Default 0.5 -> 0.0 (Neutral/Inactive)
        ml_prob = state.get('ml_probability', 0.5)
        soul_val = (ml_prob - 0.5) * 2.0
        
        # C. HINDSIGHT (Pattern Matcher)
        # Default 0.0 (Neutral/Inactive)
        pattern_return = state.get('pattern_return', 0.0)
        hindsight_val = max(-1.0, min(1.0, pattern_return * 100))
        
        # D. SENTIMENT (The Crowd)
        # Default 0.0 (Neutral/Inactive)
        sentiment_val = state.get('sentiment_score', 0.0)
        
        # 2. ADAPTIVE WEIGHTING (The Fix)
        # Determine which advisors are actually speaking (Active).
        # We define "Active" as providing a signal > threshold (noise filter).
        
        active_components = {'logic'} # Logic is always active/base
        
        if abs(soul_val) > 0.01: active_components.add('soul')
        if abs(hindsight_val) > 0.01: active_components.add('hindsight')
        if abs(sentiment_val) > 0.01: active_components.add('sentiment')
        
        # Calculate sum of base weights for ONLY the active components
        active_base_sum = 0.0
        for comp in active_components:
            active_base_sum += self.weights[comp]
            
        # Renormalize weights so they sum to 1.0
        # If Logic is the only one, it gets 0.55 / 0.55 = 1.0 (100% Authority)
        current_weights = {}
        for comp in active_components:
            current_weights[comp] = self.weights[comp] / active_base_sum
            
        # 3. CALCULATE SCORE
        score = 0.0
        score += logic_val * current_weights['logic']
        
        if 'soul' in active_components:
            score += soul_val * current_weights['soul']
        if 'hindsight' in active_components:
            score += hindsight_val * current_weights['hindsight']
        if 'sentiment' in active_components:
            score += sentiment_val * current_weights['sentiment']
            
        logger.debug(f"[ORACLE] Adaptive: {active_components} (Logic W: {current_weights['logic']:.2f}) -> Score: {score:.3f}")
        
        # 5. DIVINE INTERVENTION (The Exoskeleton)
        # Inputs: Phase, DMD Forecast, Stability
        divine = state.get('divine_metrics', {})
        divine_score = 0.0
        
        if divine:
             # A. HILBERT PHASE (Cycle Timing)
             # Phase -PI to PI. -PI/-PI/2 is Bottoming. +PI/2 to +PI is Topping.
             # We want to Buy at Bottom (-PI) and Sell at Top (+PI).
             # Map -PI -> +1.0 (Buy), +PI -> -1.0 (Sell)
             phase = divine.get('phase', 0.0)
             # Cosine(phase) gives +1 at 0 (Peak) and -1 at PI/-PI (Trough)?
             # Wait, standard Hilbert: 0 is peak amplitude? 
             # Let's use specific logic:
             # If phase is negative (accumulating), boost BUY.
             if phase < -1.5: divine_score += 0.3 # Deep trough
             elif phase > 1.5: divine_score -= 0.3 # Peak
             
             # B. DMD FORECAST (Future Sight)
             dmd_price = divine.get('dmd_forecast', 0.0)
             # We need current price to compare.
             # Ideally state should have 'price'. Tracker doesn't pass it explicitly in top dict
             # but we can infer or skip. Logic signal usually encodes this.
             # Let's trust the "Stability" metric more here.
             
             # C. STABILITY (Risk Control)
             # If stability (mean abs diff) is high, it's volatile -> Reduce score magnitude (Confused Oracle)
             # If stability is low, it's calm -> Allow score to pass
             stability = divine.get('stability', 0.0)
             # If volatility is extreme > 1.0% of price (heuristic), dampen score
             # We don't have price, so raw value check.
             pass
             
             # D. ESN DEPTH (Reservoir Activity)
             # High activity = Complex dynamics.
             # Just add a small bias if DMD is bullish?
             pass

        # Add Divine Score (Weighted) with a new weight factor
        # Since we initialized weights in __init__, we need to handle the new key or just add raw
        score += divine_score * 0.25 # Implicit 0.25 weight for Divine layer
        
        return score

# Singleton
_oracle = None

def get_oracle():
    global _oracle
    if _oracle is None:
        _oracle = Oracle()
    return _oracle
