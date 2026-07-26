import math
import time
from collections import deque
from typing import Dict, List, Optional
from decimal import Decimal

class AirwindowsConsole:
    """
    The Airwindows Console (Auratic Edition).
    Supports multiple 'Purest' eras: Console9 (Divine/Golden Ratio) 
    and ConsoleLA (Large Analog/SubTight).
    """
    
    def __init__(self, flavor: str = "console9", sample_rate: float = 1.0):
        self.flavor = flavor.lower()
        self.sample_rate = sample_rate
        
        # --- STATE ---
        self.last_sample = 0.0
        self.intermediate = deque([0.0] * 16, maxlen=16)
        self.slew_buffer = deque([0.0] * 32, maxlen=32)
        self.fpd = int(time.time()) & 0xFFFFFFFF
        
        # ConsoleLA specific (SubTight)
        self.sub_a = 0.0
        self.sub_b = 0.0
        self.sub_c = 0.0
        
    def _tpdf_dither(self) -> float:
        self.fpd ^= (self.fpd << 13) & 0xFFFFFFFF
        self.fpd ^= (self.fpd >> 17) & 0xFFFFFFFF
        self.fpd ^= (self.fpd << 5) & 0xFFFFFFFF
        return (self.fpd / 4294967295.0) * 1.1e-15

    def encode(self, input_sample: float) -> float:
        """
        [CONSOLE ENCODE]
        Prepares signal for the bus.
        """
        if self.flavor == "console9":
            # Divine Saturation (Golden Ratio)
            phi = 0.618033988749895
            inv_phi = 1.618033988749895
            x = input_sample * phi
            if x > 1.0: return 1.0
            if x < -1.0: return -1.0
            if x > 0.0: return -math.expm1(math.log1p(-x) * inv_phi)
            return math.expm1(math.log1p(x) * inv_phi)
            
        elif self.flavor == "consolela":
            # Large Analog Saturation (Spiral/Density Hybrid)
            abs_x = abs(input_sample)
            if abs_x < 1e-18: return input_sample
            spiral = math.sin(input_sample * abs_x) / abs_x
            density = math.sin(input_sample)
            return (spiral * 0.8) + (density * 0.2)
            
        return math.sin(input_sample)

    def decode(self, bus_sample: float) -> float:
        """
        [CONSOLE DECODE]
        Recovers linear signal from the bus.
        """
        if self.flavor == "console9":
            # Inverse Divine Saturation
            phi = 0.618033988749895
            inv_phi = 1.618033988749895
            x = bus_sample
            if x > 1.0: x = 1.0
            if x < -1.0: x = -1.0
            if x > 0.0: x = 1.0 - math.pow(1.0 - x, phi)
            else: x = -1.0 + math.pow(1.0 + x, phi)
            return x / phi
            
        return math.asin(max(-1.0, min(1.0, bus_sample)))

    def apply_subtight(self, input_sample: float) -> float:
        """
        [CONSOLE LA SUBTIGHT]
        Removes low-frequency 'muck' (DC drift) using non-linear sin-filters.
        """
        sub_trim = 0.0011 # ConsoleLA default
        s = input_sample * sub_trim
        
        # Non-linear Sub-filter Cascade
        scale = 0.5 + abs(s * 0.5)
        s = self.sub_a + (math.sin(self.sub_a - s) * scale)
        self.sub_a = s * scale
        
        s = self.sub_b + (math.sin(self.sub_b - s) * scale)
        self.sub_b = s * scale
        
        s = self.sub_c + (math.sin(self.sub_c - s) * scale)
        self.sub_c = s * scale
        
        # Sub-sample is amplified back and subtracted from original
        return input_sample - (max(-0.25, min(0.25, s)) * 16.0)

    def master_desk(self, input_sample: float) -> float:
        """
        [CLIPONLY3 MASTER]
        Final analog limiting stage.
        """
        # Logic from ClipOnly3Proc.cpp
        thresh = 0.9085097
        hard_limit = 0.94
        
        # Slew-compensated dynamic clipping
        current_slew = abs(self.last_sample - input_sample)
        self.slew_buffer.append(current_slew)
        self.last_sample = input_sample
        
        max_slew = max(self.slew_buffer)
        post_clip_thresh = 0.94 / (1.0 + (max_slew * 1.3986013))
        
        return max(-post_clip_thresh, min(post_clip_thresh, input_sample)) + self._tpdf_dither()
