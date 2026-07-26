import math
import numpy as np
from decimal import Decimal, getcontext
from typing import Union, List

# Set precision for "Infinite" internal calculations
getcontext().prec = 64

GOLDEN_RATIO = Decimal('1.618033988749894848204586834365638117720309179805761715001922')
PHIDIA = Decimal('1') / GOLDEN_RATIO

class DivineMath:
    """
    System Tool for Unshackled Precision.
    Fused with Airwindows ClipOnly3 and Spiral saturation logic.
    """
    
    def __init__(self):
        # State for ClipOnly3 logic
        self.last_sample = 0.0
        self.intermediate = [0.0] * 16
        self.slew_buffer = [0.0] * 32
        self.was_pos_clip = False
        self.was_neg_clip = False
        self.fpd = 123456789 # Seed for dither
    
    @staticmethod
    def shift_gain(value: Union[float, Decimal], steps: int) -> Decimal:
        v = Decimal(str(value))
        return v * (Decimal('2') ** steps)

    @staticmethod
    def quantize_to_ratio(value: Union[float, Decimal], ratio: Decimal = PHIDIA) -> Decimal:
        v = Decimal(str(value))
        if v == 0: return Decimal('0')
        multiples = (v / ratio).to_integral_value()
        return multiples * ratio

    @staticmethod
    def spiral_saturation(value: float, drive: float = 1.0) -> float:
        """
        Airwindows 'Spiral' logic.
        Unique saturation curve: sin(x*|x|) / |x|
        """
        x = float(value) * drive
        abs_x = abs(x)
        if abs_x < 1e-18: return x
        return math.sin(x * abs_x) / abs_x

    def clip_only_3(self, input_sample: float) -> float:
        """
        Python implementation of Airwindows ClipOnly3.
        Provides hard clipping without digital artifacts using slew-compensation.
        """
        # Simple TPDF noise simulation (0.076 scaling from source)
        self.fpd ^= (self.fpd << 13) & 0xFFFFFFFF
        self.fpd ^= (self.fpd >> 17) & 0xFFFFFFFF
        self.fpd ^= (self.fpd << 5) & 0xFFFFFFFF
        noise = 1.0 - ((self.fpd / 4294967295.0) * 0.076)
        
        # Clip Threshold (0.908... from source)
        thresh = 0.9085097
        hard_limit = 0.94
        
        # Positive Clip Memory
        if self.was_pos_clip:
            if input_sample < self.last_sample:
                self.last_sample = (thresh * noise) + (input_sample * (1.0 - noise))
            else:
                self.last_sample = hard_limit
        self.was_pos_clip = False
        if input_sample > thresh:
            self.was_pos_clip = True
            input_sample = (thresh * noise) + (self.last_sample * (1.0 - noise))
            
        # Negative Clip Memory
        if self.was_neg_clip:
            if input_sample > self.last_sample:
                self.last_sample = (-thresh * noise) + (input_sample * (1.0 - noise))
            else:
                self.last_sample = -hard_limit
        self.was_neg_clip = False
        if input_sample < -thresh:
            self.was_neg_clip = True
            input_sample = (-thresh * noise) + (self.last_sample * (1.0 - noise))
            
        # Slew Logic
        current_slew = abs(self.last_sample - input_sample)
        self.slew_buffer.append(current_slew)
        self.slew_buffer.pop(0)
        
        # Latency/Spacing simulation (using 1 for trading data)
        self.last_sample = input_sample
        
        # Dynamic Post-Clip based on Max Slew
        max_slew = max(self.slew_buffer)
        post_clip_thresh = 0.94 / (1.0 + (max_slew * 1.3986013))
        
        if input_sample > post_clip_thresh: input_sample = post_clip_thresh
        if input_sample < -post_clip_thresh: input_sample = -post_clip_thresh
        
        return input_sample

    @staticmethod
    def get_leverage_step(volatility: float) -> int:
        if volatility <= 0: return 0
        return -int(math.log2(max(1.0, volatility / 0.02)))

    @staticmethod
    def calculate_bloom(value: float, threshold: float, bloom: float) -> float:
        """
        Symmetric conviction bloom: sign(v) * tanh((abs(v) - threshold) / bloom)
        Centralized 'Sacred Geometry' for all trading logic.
        """
        abs_val = abs(value)
        if abs_val < threshold:
            return 0.0
            
        delta = abs_val - threshold
        if bloom <= 0:
            return 1.0 if value > 0 else -1.0
            
        conv = math.tanh(delta / bloom)
        return conv if value > 0 else -conv

    @staticmethod
    def calculate_z_score(prices: Union[List[float], np.ndarray], period: int) -> float:
        """
        Calculates a localized Z-score for the current price relative to a period.
        """
        if len(prices) < 2:
            return 0.0
        
        actual_period = min(len(prices), period)
        if actual_period < 2:
            return 0.0
            
        slice_prices = np.array(prices[-actual_period:], dtype=np.float64)
        std = np.std(slice_prices)
        if std == 0:
            return 0.0
            
        return float((prices[-1] - np.mean(slice_prices)) / std)
