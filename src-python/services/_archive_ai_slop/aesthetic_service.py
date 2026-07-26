"""
Aesthetic Service: Clinical ASCII Art & Terminal Aesthetics
Provides standardized ASCII assets for the Auratic terminal interface.
"""

class ASCIIArt:
    # --- HEADERS ---
    import random

    SYSTEM_HEADER = """
[ AURATIC SYSTEMS : MARKET INTELLIGENCE UNIT ]
══════════════════════════════════════════════
"""
    
    # --- CYCLE / MOON PHASES (ASCII) ---
    # Legend: ( ) = Full, ( . ) = New, ( / ) = Waxing, ( \ ) = Waning
    
    PHASE_VOID = (
        "     .     \n"
        r"     .     " "\n"
        r"    . .    " "\n"
        r"     .     "
    )
    
    PHASE_RISE = (
        r"    /|     " "\n"
        r"   / |     " "\n"
        r"  /  |     "
    )
    
    PHASE_FALL = (
        r"     |\    " "\n"
        r"     | \   " "\n"
        r"     |  \  "
    )
    
    PHASE_TOP = (
        r"   .---.   " "\n"
        r"  /     \  " "\n"
        r"  |     |  "
    )
    
    PHASE_BOT = (
        r"  |     |  " "\n"
        r"  \     /  " "\n"
        r"   '---'   "
    )

    # ==========================================================================
    # CHARACTER PALETTES FOR MATHEMATICAL DATA VISUALIZATION
    # ==========================================================================
    # Organized by semantic meaning and visual density for fractal rendering
    # All characters from well-supported Unicode blocks (graceful degradation)
    # NO EMOJIS - only geometric/mathematical symbols
    # ==========================================================================

    # --- DENSITY GRADIENTS (for intensity/value mapping) ---
    # Each gradient goes from empty (0.0) to solid (1.0)
    
    # Ultra-smooth 32-level gradient using Braille
    DENSITY_BRAILLE = " ⠀⠁⠂⠃⠄⠅⠆⠇⡀⡁⡂⡃⡄⡅⡆⡇⣀⣁⣂⣃⣄⣅⣆⣇⣠⣡⣤⣥⣦⣧⣿"
    
    # Classic block gradient (4 levels - fast rendering)
    DENSITY_BLOCKS = " ░▒▓█"
    
    # Dot density gradient (8 levels)
    DENSITY_DOTS = " ·∴∵⁘⁙⁛⁜※"
    
    # Circle fill gradient (6 levels)
    DENSITY_CIRCLES = " ◌○◎●◉⬤"
    
    # Square fill gradient (6 levels)  
    DENSITY_SQUARES = " □▢▣▤▦■"
    
    # Hexagon gradient (for honeycomb patterns)
    DENSITY_HEXAGONS = " ⬡⬢⬣"

    # --- DIRECTIONAL INDICATORS (for trend/momentum) ---
    
    # Vertical momentum (bullish/bearish)
    ARROW_UP = "↑⇑▲△"      # Bullish / Rising
    ARROW_DOWN = "↓⇓▼▽"    # Bearish / Falling
    ARROW_FLAT = "→⇒▶▷"    # Neutral / Sideways
    
    # Diagonal trends
    ARROW_UP_RIGHT = "↗⬈"   # Bullish momentum
    ARROW_DOWN_RIGHT = "↘⬊" # Bearish momentum
    ARROW_UP_LEFT = "↖⬉"    # Reversal up
    ARROW_DOWN_LEFT = "↙⬋"  # Reversal down
    
    # Bidirectional (volatility/range)
    ARROW_VERTICAL = "↕⇕"   # High volatility
    ARROW_HORIZONTAL = "↔⇔" # Ranging/consolidation

    # --- INTENSITY SCALES (for magnitude/strength) ---
    
    # Star intensity (5 levels - confidence/quality)
    INTENSITY_STARS = "☆✧✦★✪"
    
    # Diamond intensity (4 levels - value/price)
    INTENSITY_DIAMONDS = "◇◈◆❖"
    
    # Cross intensity (4 levels - crossover signals)
    INTENSITY_CROSSES = "×⊕⊗⊛"

    # --- MATHEMATICAL OPERATORS (for calculations/formulas) ---
    
    # Basic operators
    MATH_BASIC = "+-×÷=≠≈"
    
    # Comparisons
    MATH_COMPARE = "≤≥∝∞"
    
    # Set theory (for confluence/overlap)
    MATH_SETS = "∈∉∩∪⊂⊃⊆⊇"
    
    # Calculus (for derivatives/integrals)
    MATH_CALCULUS = "∂∆∇∑∏∫√"
    
    # Logic (for conditions)
    MATH_LOGIC = "∀∃¬∧∨⊥⊤"

    # --- BOX DRAWING (for structure/borders) ---
    
    # Single line
    BOX_SINGLE = "─│┌┐└┘├┤┬┴┼"
    
    # Double line
    BOX_DOUBLE = "═║╔╗╚╝╠╣╦╩╬"
    
    # Mixed (for hierarchy)
    BOX_MIXED = "╒╓╕╖╘╙╛╜╞╟╡╢╤╥╧╨╪╫"

    # --- HALF/QUARTER BLOCKS (for sub-character resolution) ---
    
    BLOCK_HALVES = "▀▄▌▐"           # Half blocks
    BLOCK_QUARTERS = "▖▗▘▙▚▛▜▝▞▟"   # Quarter blocks (high resolution)

    # --- PHASE INDICATORS (for cycle position) ---
    
    # Moon phases (market cycles)
    PHASE_CIRCLES = "◐◑◒◓◔◕"
    
    # Rotation indicators
    PHASE_ROTATION = "◜◝◞◟◠◡"

    # ==========================================================================
    # COMPOSITE CHARSETS FOR SPECIFIC USE CASES
    # ==========================================================================
    
    # Standard fractal rendering (smooth gradient)
    # Standard fractal rendering (smooth gradient)
    # The "Kryptos" Palette: Curated, Interleaved, Non-Blocky.
    # Light -> Heavy gradient, mixing scripts to prevent "banding" and enhance mystery.
    # Refined 2025: Removed ALL Latin/Standard chars to prevent "reading artifacts".
    FRACTAL_CHARSET = (
        " ·.,`'~-:;^°"  # Dust/Void (Allowed minimal punctuation for texture)
        + "∫∬∮∭" + "ᛠᛡᛢᛣᛤᛥ" + "ⴰⴱⴳⴷ"      # Low Density (Math/Runes/Tifinagh)
        + "🜁🜂🜃🜄" + "ᚠᚢᚦᚩᚪ" + "ⴹⴻⴼⴽ"      # Med-Low (Elements/Runes/Tifinagh)
        + "☤☥☧☨☫" + "🜅🜆🜇🜈" + "ⵀⵃⵄⵅ"      # Medium (Esoteric/Alchemy/Tifinagh)
        + "ᚫᚬᚭᚮᚯ" + "🜉🜊🜋🜌" + "ⵇⵉⵊⵍ"      # Med-High (Runes/Alchemy/Tifinagh)
        + "🜍🜎🜏🜐" + "ሀለሐመ" + "❖⬡⬢"      # High (Alchemy/Ethiopic/Geo)
        + "🜔🜕🜖🜗" + "ሠረሰሸ" + "∞∆∇"       # Density (Heavy Alchemy/Ethiopic/Math)
    )
    
    # High-contrast fractal (for small displays)
    FRACTAL_CHARSET_BOLD = " .·:" + DENSITY_BLOCKS[1:] + "●◉⬤■⬡⬢∞★"
    
    # Value indicator charset (for price/metric display)
    VALUE_CHARSET = DENSITY_CIRCLES + INTENSITY_DIAMONDS + "∞"
    
    # Momentum charset (for trend indicators)
    MOMENTUM_CHARSET = ARROW_DOWN + "─" + ARROW_UP + INTENSITY_STARS
    
    # Volatility charset (for range/volatility)
    VOLATILITY_CHARSET = " " + DENSITY_BLOCKS + ARROW_VERTICAL + "⬡⬢"
    
    # Legacy combined charset (backward compatibility)
    CHARSET = " ·.,'`~-_=+:;!?*^\"|/\\()[]{}░▒▓○●◎◉⬤▢▣■□▪▫◆◇◈❖⬡⬢✧✦★▀▄█▌▐∞∆∇⊕⊗"

    # ==========================================================================
    # SEMANTIC CHARACTER SELECTION HELPERS
    # ==========================================================================

    @staticmethod
    def get_density_char(value: float, style: str = "braille") -> str:
        """
        Maps a 0.0-1.0 value to a density character.
        Styles: braille, blocks, dots, circles, squares, hexagons
        """
        palettes = {
            "braille": ASCIIArt.DENSITY_BRAILLE,
            "blocks": ASCIIArt.DENSITY_BLOCKS,
            "dots": ASCIIArt.DENSITY_DOTS,
            "circles": ASCIIArt.DENSITY_CIRCLES,
            "squares": ASCIIArt.DENSITY_SQUARES,
            "hexagons": ASCIIArt.DENSITY_HEXAGONS,
        }
        chars = palettes.get(style, ASCIIArt.DENSITY_BLOCKS)
        idx = int(min(max(value, 0.0), 1.0) * (len(chars) - 1))
        return chars[idx]

    @staticmethod
    def get_momentum_char(momentum: float) -> str:
        """
        Maps momentum (-1.0 to +1.0) to a directional character.
        -1.0 = strong bearish, 0.0 = neutral, +1.0 = strong bullish
        """
        if momentum > 0.7:
            return "⇑"  # Strong bullish
        elif momentum > 0.3:
            return "↑"  # Bullish
        elif momentum > 0.1:
            return "△"  # Slight bullish
        elif momentum < -0.7:
            return "⇓"  # Strong bearish
        elif momentum < -0.3:
            return "↓"  # Bearish
        elif momentum < -0.1:
            return "▽"  # Slight bearish
        else:
            return "─"  # Neutral

    @staticmethod
    def get_volatility_char(volatility: float) -> str:
        """
        Maps volatility (0.0 to 1.0) to a visual indicator.
        0.0 = calm, 1.0 = extreme volatility
        """
        if volatility > 0.8:
            return "⇕"  # Extreme
        elif volatility > 0.6:
            return "↕"  # High
        elif volatility > 0.4:
            return "▓"  # Elevated
        elif volatility > 0.2:
            return "▒"  # Moderate
        else:
            return "░"  # Low

    @staticmethod
    def get_confidence_char(confidence: float) -> str:
        """
        Maps confidence (0.0 to 1.0) to a star intensity.
        """
        stars = ASCIIArt.INTENSITY_STARS  # "☆✧✦★✪"
        idx = int(min(max(confidence, 0.0), 1.0) * (len(stars) - 1))
        return stars[idx]

    @staticmethod
    def get_phase_char(phase_degrees: float) -> str:
        """
        Maps market cycle phase (0-360 degrees) to a phase indicator.
        0° = bottom, 90° = rising, 180° = top, 270° = falling
        """
        phases = ASCIIArt.PHASE_CIRCLES  # "◐◑◒◓◔◕"
        normalized = (phase_degrees % 360) / 360.0
        idx = int(normalized * (len(phases) - 1))
        return phases[idx]

    @staticmethod
    def create_value_bar(value: float, width: int = 10, style: str = "blocks") -> str:
        """
        Creates a horizontal bar representing a value (0.0 to 1.0).
        Returns a string of specified width showing the fill level.
        """
        filled = int(value * width)
        remaining = width - filled
        
        if style == "blocks":
            return "█" * filled + "░" * remaining
        elif style == "circles":
            return "●" * filled + "○" * remaining
        elif style == "squares":
            return "■" * filled + "□" * remaining
        else:
            return "#" * filled + "-" * remaining




    @staticmethod
    def _get_dithered_char(intensity: float, chars: str) -> str:
        """
        Maps 0.0-1.0 intensity to a character using Airwindows TPDF Dithering.
        (Triangular Probability Density Function).
        """
        from random import random
        # TPDF Noise: (random() - random()) -> Triangular dist [-1, 1]
        # This eliminates quantization distortion (banding) in the gradient.
        noise = random() - random()
        
        max_idx = len(chars) - 1
        raw_idx = intensity * max_idx
        
        # Apply Dither (Amplitude 0.5 to 1.0 LSB)
        # Using 0.7 for a balance of smoothness and texture
        dithered_idx = raw_idx + (noise * 0.7)
        
        idx = int(round(dithered_idx))
        idx = max(0, min(idx, max_idx))
        return chars[idx]

    @staticmethod
    def generate_mandelbrot(width: int = 40, height: int = 20, iterations: int = 15, 
                           zoom: float = 1.0, center_x: float = -0.0, center_y: float = 0.0) -> str:
        """
        Generates a clinical ASCII Mandelbrot fractal.
        Classic orientation with cardioid bulb shape.
        """
        chars = ASCIIArt.FRACTAL_CHARSET


        
        output = []
        for y in range(height):
            row = ""
            for x in range(width):
                # Map x,y to complex plane - CLASSIC orientation
                # x maps to real axis, y maps to imaginary axis
                zx = (x - width / 2) * 3.5 / (zoom * width) + center_x
                zy = (y - height / 2) * 2.0 / (zoom * height) + center_y
                
                cx, cy = zx, zy
                i = 0
                while zx * zx + zy * zy < 4 and i < iterations:
                    tmp = zx * zx - zy * zy + cx
                    zy = 2.0 * zx * zy + cy
                    zx = tmp
                    i += 1
                
                intensity = i / iterations
                row += ASCIIArt._get_dithered_char(intensity, chars)

            output.append(row)
        
        return "\n".join(output)


    @staticmethod
    def generate_julia(width: int = 40, height: int = 12, iterations: int = 20,
                      zoom: float = 1.0, c_real: float = -0.7, c_imag: float = 0.27) -> str:
        """
        Generates a Julia set fractal - a cousin of Mandelbrot with fixed c parameter.
        Creates more spiral/organic patterns. c_real and c_imag control the shape.
        Classic values: c = -0.7 + 0.27i (spirals), c = -0.8 + 0.156i (dendrites)
        """
        chars = ASCIIArt.FRACTAL_CHARSET

        
        output = []
        for y in range(height):
            row = ""
            for x in range(width):
                # Map to complex plane
                zx = 3.0 * (x - width / 2) / (zoom * width)
                zy = 2.0 * (y - height / 2) / (zoom * height)
                
                i = 0
                while zx * zx + zy * zy < 4 and i < iterations:
                    tmp = zx * zx - zy * zy + c_real
                    zy = 2.0 * zx * zy + c_imag
                    zx = tmp
                    i += 1
                
                intensity = i / iterations
                row += ASCIIArt._get_dithered_char(intensity, chars)

            output.append(row)
        
        return "\n".join(output)

    @staticmethod
    def generate_burning_ship(width: int = 40, height: int = 12, iterations: int = 20,
                              zoom: float = 1.0, center_x: float = -0.4, center_y: float = -0.6) -> str:
        """
        Generates a Burning Ship fractal - creates flame-like asymmetric patterns.
        Uses absolute values in the iteration, producing ship-hull shapes.
        """
        chars = ASCIIArt.FRACTAL_CHARSET

        
        output = []
        for y in range(height):
            row = ""
            for x in range(width):
                # Map to complex plane (inverted Y for proper orientation)
                zx = 3.5 * (x - width / 2) / (zoom * width) + center_x
                zy = 2.0 * (height - 1 - y - height / 2) / (zoom * height) + center_y
                
                cx, cy = zx, zy
                i = 0
                while zx * zx + zy * zy < 4 and i < iterations:
                    # Key difference: absolute values create the "burning" effect
                    tmp = zx * zx - zy * zy + cx
                    zy = abs(2.0 * zx * zy) + cy
                    zx = abs(tmp)
                    i += 1
                
                intensity = i / iterations
                row += ASCIIArt._get_dithered_char(intensity, chars)

            output.append(row)
        
        return "\n".join(output)

    @staticmethod
    def get_phase_totem(degree: float) -> str:
        """Returns a clinical ASCII phase indicator based on degree (0-360)"""
        d = degree % 360
        if 0 <= d < 45: return ASCIIArt.PHASE_RISE
        elif 45 <= d < 135: return ASCIIArt.PHASE_TOP
        elif 135 <= d < 225: return ASCIIArt.PHASE_FALL
        elif 225 <= d < 315: return ASCIIArt.PHASE_BOT
        else: return ASCIIArt.PHASE_VOID

    # Micro charset for tiny indicators (8 chars: space to solid)
    MICRO_CHARS = " ·░▒▓█●⬤"

    @staticmethod
    def generate_micro_fractal(width: int = 13, height: int = 2, 
                               value: float = 0.5, intensity: float = 0.5) -> str:
        """
        Generates a tiny micro-fractal indicator (1-2 lines, up to 13 chars).
        
        Args:
            width: Character width (up to 13)
            height: Line height (1-2 recommended)  
            value: 0-1 position value (affects horizontal focus, e.g. RSI/100)
            intensity: 0-1 intensity (affects zoom/detail, e.g. volatility)
        """
        chars = ASCIIArt.MICRO_CHARS
        
        # Map value to center_x range (-1.5 to 0.5)
        center_x = -1.5 + (value * 2.0)
        # Map intensity to zoom (0.5 to 2.0)
        zoom = 0.5 + (intensity * 1.5)
        iterations = 6 + int(intensity * 10)
        
        output = []
        for y in range(height):
            row = ""
            for x in range(width):
                zx = 1.5 * (x - width / 2) / (0.5 * zoom * width) + center_x
                zy = 1.0 * (y - height / 2) / (0.5 * zoom * height)
                
                cx, cy = zx, zy
                i = 0
                while zx * zx + zy * zy < 4 and i < iterations:
                    tmp = zx * zx - zy * zy + cx
                    zy = 2.0 * zx * zy + cy
                    zx = tmp
                    i += 1
                
                intensity = i / iterations
                row += ASCIIArt._get_dithered_char(intensity, chars)

            output.append(row)
        
        return "\n".join(output) if height > 1 else output[0]

    @staticmethod
    def colorize(text: str, sentiment: str = "neutral") -> str:
        """
        Adds a sentiment indicator prefix to text.
        sentiment: "bullish", "bearish", "neutral", "hot", "cold", "alert"
        """
        indicators = {
            "bullish": "▲",
            "bearish": "▼", 
            "neutral": "■",
            "hot": "◆",
            "cold": "◇",
            "alert": "⚡",
        }
        indicator = indicators.get(sentiment, "■")
        return f"{indicator}{text}"

    @staticmethod
    def metric_indicator(name: str, value: float, max_val: float = 100, 
                        reverse: bool = False) -> str:
        """
        Creates a metric indicator with micro-fractal and sentiment coloring.
        
        Args:
            name: Metric name (e.g., "RSI", "VOL")
            value: Current value
            max_val: Maximum value for normalization
            reverse: If True, high values are bearish (like RSI > 70)
        """
        normalized = min(1.0, max(0.0, value / max_val))
        
        # Determine sentiment
        if reverse:
            sentiment = "bearish" if normalized > 0.7 else ("bullish" if normalized < 0.3 else "neutral")
        else:
            sentiment = "bullish" if normalized > 0.7 else ("bearish" if normalized < 0.3 else "neutral")
        
        # Generate tiny fractal (13 chars wide, 1 line)
        micro = ASCIIArt.generate_micro_fractal(
            width=13, height=1, 
            value=normalized, 
            intensity=abs(normalized - 0.5) * 2
        )
        
        colored = ASCIIArt.colorize(micro, sentiment)
        return f"<code>{colored}</code> {name}: {value:.1f}"


    # --- INDICATORS ---
    INDICATOR_UP = "[UP]"
    INDICATOR_DOWN = "[DOWN]"
    INDICATOR_NEUTRAL = "[---]"
    
    GAUGE_MARKER = "[#]"
    ALERT_MARKER = "[ALERT]"
    SUCCESS_MARKER = "[OK]"
    ERROR_MARKER = "[FAIL]"

def get_ascii_factory():
    return ASCIIArt
