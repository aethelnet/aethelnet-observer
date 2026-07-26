import pandas as pd
import numpy as np
from arena.api import IGameMode

class TheGreatWar(IGameMode):
    @property
    def name(self) -> str:
        return "The Great War (Synthetic Volatility)"

    @property
    def description(self) -> str:
        return "A simulated crash scenario with extreme volatility. Good for testing Rogues."

    def generate_scenario(self) -> pd.DataFrame:
        # Generate 5000 ticks of Chaos (5x more data for better learning)
        timestamps = pd.date_range(start="2025-01-01", periods=5000, freq="min")
        
        # Random Walk with High Variance
        # ✅ FIXED: Use time-based seed for different data each generation
        # This prevents overfitting to a single noise pattern
        seed = int(timestamps[0].timestamp()) % 10000
        np.random.seed(seed)
        
        # 2% Volatility per tick (realistic for crypto)
        returns = np.random.normal(0, 0.02, 5000)
        price = 100 * np.exp(np.cumsum(returns))
        
        # Add volume correlation (higher volume during volatile periods)
        volatility = np.abs(returns)
        volume = 1000 + (volatility * 50000)  # Volume increases with volatility
        
        return pd.DataFrame({
            "timestamp": timestamps,
            "close": price,
            "volume": volume.astype(int)
        })
