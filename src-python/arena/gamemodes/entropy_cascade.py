from arena.api import IGameMode
import pandas as pd
import numpy as np

class TheEntropyCascade(IGameMode):
    """
    The Entropy Cascade.
    A structural trap designed to punish switching between logic and intuition.
    User-Specific Scenario Gemini Seed #3.
    """
    @property
    def name(self) -> str:
        return "The Entropy Cascade"

    @property
    def description(self) -> str:
        return "A structural trap designed to punish switching between logic and intuition."

    def generate_scenario(self) -> pd.DataFrame:
        length = 5000
        
        # 1. Time Index
        timestamps = pd.date_range(start="2024-01-01", periods=length, freq="H")
        
        # 2. Base Structure: A seductive, gentle upward sine wave (The Mall)
        x = np.linspace(0, 50, length)
        trend = np.sin(x) * 100 + 1000 # Base price around 1000
        
        # 3. The Injection of Entropy
        noise = np.random.normal(0, 2, length) # Standard low noise
        
        # 4. The Trap (The "Fake Crash")
        # At index 3000, we simulate a structural break that looks like noise but isn't.
        # It drops fast, but KEEPS dropping (Trending Volatility).
        # The Alchemist will try to 'buy the dip' thinking it's just volatility, 
        # but the Architect won't react fast enough.
        
        shock_wave = np.zeros(length)
        for i in range(length):
            if i > 3000:
                # Exponential decay disguised as high variance
                # We add noise to the decay to mask it as 'Just Volatility'
                shock_wave[i] = -((i - 3000) * 0.5) + np.random.normal(0, 50) 
            
        prices = trend + noise + shock_wave
        
        # Ensure positive prices
        prices = np.maximum(prices, 10.0)

        # 5. Build OHLCV
        data = {
            'timestamp': timestamps,
            'close': prices,
            'open': prices + np.random.normal(0, 1, length),
            'high': prices + np.abs(np.random.normal(0, 2, length)),
            'low': prices - np.abs(np.random.normal(0, 2, length)),
            'volume': np.abs(np.random.randint(100, 10000, length))
        }
        
        return pd.DataFrame(data)
