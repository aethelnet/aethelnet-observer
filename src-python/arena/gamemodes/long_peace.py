import pandas as pd
import numpy as np
from arena.api import IGameMode

class TheLongPeace(IGameMode):
    @property
    def name(self) -> str:
        return "The Long Peace (Sideways Chop)"

    @property
    def description(self) -> str:
        return "A low-volatility environment simulation (2014-style). Tests patience and churn."

    def generate_scenario(self) -> pd.DataFrame:
        # Generate 2000 ticks of boredom
        timestamps = pd.date_range(start="2014-01-01", periods=2000, freq="h")
        
        np.random.seed(42)
        # Mean Reverting Noise (Ornstein-Uhlenbeck style simple approx)
        price = 100.0
        prices = []
        
        for _ in range(2000):
            noise = np.random.normal(0, 0.5)
            # Pull back to 100
            pull = (100 - price) * 0.1 
            price = price + pull + noise
            prices.append(price)
        
        return pd.DataFrame({
            "timestamp": timestamps,
            "close": np.array(prices),
            "volume": np.random.randint(10, 100, 2000) # Low Volume
        })
