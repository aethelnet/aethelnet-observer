
# Aesthetic fractal generator extending ASCIIArt
import random
import math

class FractalWeaver:
    """
    Generates complex, evolving ASCII/Unicode art based on user interaction state.
    Used for the 'Achievement' summary message.
    """
    
    CHARS_DENSITY = " .'`^,:;Il!i~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
    
    @staticmethod
    def generate_consciousness_fractal(width: int, height: int, complexity: int, seed: float) -> str:
        """
        Generates a dense, intricate unicode fractal block.
        'complexity' (0-100) drives recursion depth and character variation.
        """
        output = []
        cx, cy = -0.7, 0.27015  # Julia set constant base
        
        # Modify C based on seed/complexity
        cx += (seed % 1.0) * 0.1
        cy += (math.sin(seed) * 0.1)
        
        # Grid scan
        for y in range(height):
            line = ""
            for x in range(width):
                # Normalize coordinates to -1.5 to 1.5
                zx = 1.5 * (x - width / 2) / (0.5 * width)
                zy = 1.0 * (y - height / 2) / (0.5 * height)
                
                i = 0
                max_iter = 20 + int(complexity * 0.8)
                
                while zx*zx + zy*zy < 4 and i < max_iter:
                    xtemp = zx*zx - zy*zy + cx
                    zy = 2*zx*zy + cy
                    zx = xtemp
                    i += 1
                
                # Map iteration count to character set
                # Use a dense mapping
                if i == max_iter:
                    char = " "
                else:
                    # Non-linear mapping for visual interest
                    idx = int(math.sqrt(i / max_iter) * len(FractalWeaver.CHARS_DENSITY))
                    idx = min(idx, len(FractalWeaver.CHARS_DENSITY) - 1)
                    char = FractalWeaver.CHARS_DENSITY[idx]
                
                line += char
            output.append(line)
            
        return "\n".join(output)

    @staticmethod
    def evolve(interaction_count: int, unique_tabs: int, height: int = 16, seed_key: str = None, 
               z_score: float = 0.0, regime: str = "UNKNOWN", rsi: float = 50.0) -> str:
        """
        Public entry point. Returns a fractal string based on interaction metrics.
        The more interactions, the more 'evolved' (complex) the fractal.
        If seed_key (symbol) is provided, the fractal shape is deterministic for that key.
        """
        # Dimensions for Telegram message
        width = 40
        # height is now dynamic
        
        # Calculate complexity score (0-100)
        # Base on interactions + unique tabs
        score = min(100, (interaction_count * 2) + (unique_tabs * 10))
        
        # Use Hyper Fractal logic (Mandelbrot) for consistency
        try:
            from services.aesthetic_service import ASCIIArt
            import time
            import math
            import random
            import hashlib
            
            # Use seed to drive unique variations
            if seed_key:
                # Deterministic seed from symbol
                hash_input = seed_key.upper().encode('utf-8')
                hash_val = int(hashlib.sha256(hash_input).hexdigest(), 16)
                # Normalize to float
                seed = float(hash_val % 10000) / 10000.0
                
                # Dynamic shift based on time (slow rotation per hour) to make it "alive"
                # but "rooted" in the symbol identity
                hour_shift = (int(time.time()) // 3600) * 0.1
                seed += hour_shift
            else:
                seed = time.time()
                
            drift = (seed * 10.0) % (2 * math.pi)
            
            # COORDINATE MAPPING (The "Doubling as Indicator" Logic)
            # Different regimes map to different fractal valleys
            # Default: Seahorse Valley
            base_x, base_y = -0.745, 0.1
            
            if "JOY" in regime: # Bull Trend -> Elephant Valley (Stable, structured)
                 base_x, base_y = 0.275, 0.006 
            elif "SAD" in regime: # Bear Trend -> Scepter Valley (Spiky)
                 base_x, base_y = -1.36, 0.005
            elif "ANGER" in regime or "VOLATILE" in regime: # Chaos -> Triple Spiral
                 base_x, base_y = -0.088, 0.654
            
            # Z-Score drives dynamic zoom/drift intensity (The "Pulse")
            drift_radius = 0.05 + (abs(z_score) * 0.02)
            
            drift_x = base_x + (math.cos(drift) * drift_radius)
            drift_y = base_y + (math.sin(drift) * drift_radius)
            
            # Evolution: complexity drives zoom/iter
            # RSI modifies "Heat" (Complexity/Iterations)
            # High RSI (Overbought) -> More noise/details
            base_zoom = 1.0 + (score / 20.0)
            zoom = base_zoom + (abs(z_score) * 0.5) # Z-Score zooms in
            
            base_iters = 30 + int(score)
            rsi_mod = abs(rsi - 50) # Deviation from neutral
            iters = base_iters + int(rsi_mod * 0.5)
            
            return ASCIIArt.generate_mandelbrot(
                width=width, height=height, 
                iterations=iters, zoom=zoom, 
                center_x=drift_x, center_y=drift_y
            )
        except Exception as e:
            # Fallback
            return FractalWeaver.generate_consciousness_fractal(width, height, score, seed=time.time())

import time
