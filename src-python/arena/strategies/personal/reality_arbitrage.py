from arena.api import IStrategy
import pandas as pd
import numpy as np

class TheRealityArbitrage(IStrategy):
    """
    The Reality Arbitrage (Metashape vs Colmap).
    Gemini Seed #7.
    
    Logic Structure: PORTFOLIO_MANAGER (Case 1)
    Narrative: "Gambling between Solvers".
    - Metashape (Fast/Trend): Used when error (volatility) is low.
    - Colmap (Deep/Mean Reversion): Used when error (volatility) is high.
    - Switches dynamically based on 'Reprojection Error'.
    """

    @property
    def name(self) -> str:
        return "The Reality Arbitrage"

    @property
    def class_type(self) -> str:
        return "PORTFOLIO_MANAGER"

    def __init__(self):
        super().__init__()
        # Hyperparameters (The Skills)
        self.skills = {
            "error_tolerance": 0.015, # The volatility threshold (Reprojection Error)
            "metashape_speed": 10,    # Fast moving average (Trend)
            "colmap_depth": 50,       # Slow moving average (Deep Value)
            "colmap_threshold": 0.015, # [HARDENING] Required depth below MA to buy (1.5%)
            "solver_confidence": 0.8  # Max allocation size
        }

    def _get_metashape_signal(self, df: pd.DataFrame) -> float:
        """
        The 'Fast Solver'. Follows the immediate trend.
        Effective in clean, low-noise markets.
        """
        ma_fast = df['close'].tail(int(self.skills['metashape_speed'])).mean()
        if df['close'].iloc[-1] > ma_fast:
            return 1.0
        return -1.0

    def _get_colmap_signal(self, df: pd.DataFrame) -> float:
        """
        The 'Deep Solver'. Looks for mean reversion in noise.
        Effective in complex, high-volatility markets.
        [HARDENED] Now requires a minimum deviation to avoid falling knives.
        """
        ma_slow = df['close'].tail(int(self.skills['colmap_depth'])).mean()
        current_price = df['close'].iloc[-1]
        
        # Calculate deviation from mean
        deviation = (current_price - ma_slow) / ma_slow
        threshold = self.skills['colmap_threshold']
        
        # Only buy if significantly below mean
        if deviation < -threshold:
            return 1.0
        # Only sell if significantly above mean
        elif deviation > threshold:
            return -1.0
        return 0.0

    def on_tick(self, packet: dict) -> float:
        return 0.0

    def next_candle(self, df: pd.DataFrame) -> float:
        if len(df) < int(self.skills['colmap_depth']):
            return 0.0

        # 1. Calculate 'Reprojection Error' (Market Volatility)
        # [STABILITY] Increased lookback to 20 to reduce jitter
        reprojection_error = df['close'].pct_change().tail(20).std()
        
        # Handle NaN at start
        if np.isnan(reprojection_error): reprojection_error = 0.0

        # 2. The Allocation Gamble
        metashape_weight = 0.0
        colmap_weight = 0.0

        if reprojection_error < self.skills['error_tolerance']:
            # Low Error: The easy solver (Metashape) works best.
            # "Reality is clean." -> 80% Trend, 20% Value
            metashape_weight = 0.8
            colmap_weight = 0.2
        else:
            # High Error: The fast solver is failing (artifacts). 
            # Switch to the robust solver (Colmap).
            # "Reality is noisy." -> 20% Trend, 80% Value
            metashape_weight = 0.2
            colmap_weight = 0.8

        # 3. Calculate Weighted Signal
        signal_m = self._get_metashape_signal(df)
        signal_c = self._get_colmap_signal(df)
        
        # Output is the "Hedge Fund's" net position
        final_position = (signal_m * metashape_weight) + (signal_c * colmap_weight)
        
        # Clamp to max confidence
        return max(min(final_position, self.skills['solver_confidence']), -self.skills['solver_confidence'])

    def evolve(self, mutation_rate: float = 0.1) -> 'TheRealityArbitrage':
        child = TheRealityArbitrage()
        # Mutate the error tolerance (when to switch solvers)
        child.skills['error_tolerance'] = self.skills['error_tolerance'] * (1 + np.random.normal(0, mutation_rate))
        return child
