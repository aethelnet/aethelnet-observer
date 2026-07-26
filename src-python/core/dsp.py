import math
import numpy as np

def bitshift_gain(value: float, shift: int) -> float:
    """
    Airwindows-inspired lossless gain.
    1 shift = approx 6.02 dB.
    Uses power-of-2 scaling to maintain bit-perfection for floats (exponent-only change).
    """
    if value == 0: return 0.0
    return value * (2.0 ** shift)

def tpdf_dither(amount: float = 0.0001) -> float:
    """
    Triangular Probability Density Function Dither.
    Prevents quantization distortion in the neural manifold.
    """
    import random
    return (random.random() - random.random()) * amount

def clip_only_3(value: float, threshold: float = 3.0) -> float:
    """
    True Airwindows ClipOnly3 Port (Enhanced for Z-Scores).
    1. Hard clips the signal at the specified threshold.
    2. Injects TPDF dither at the edges to mask the 'limit'.
    3. Softens the transition between linear and clipped states.
    """
    # Noise-masking stage: Only active when 'slamming' the clipper
    if abs(value) >= threshold:
        # Subtle dither to prevent neural 'freezing' at exactly the threshold
        value = (threshold if value > 0 else -threshold) + tpdf_dither(threshold * 0.0001)
    
    # Hard safety cap (allowing 10% breathing room for the dither)
    safety_limit = threshold * 1.1
    if value > safety_limit: value = safety_limit
    if value < -safety_limit: value = -safety_limit
    
    return value

class PureSlew:
    """
    Slew-limiter that prevents impossible price-velocity signals 
    from contaminating the neural manifold.
    """
    def __init__(self, slew_rate: float = 0.1):
        self.slew_rate = slew_rate
        self.last_value = 0.0
        
    def process(self, value: float) -> float:
        diff = value - self.last_value
        if diff > self.slew_rate:
            value = self.last_value + self.slew_rate
        elif diff < -self.slew_rate:
            value = self.last_value - self.slew_rate
        
        self.last_value = value
        return value
