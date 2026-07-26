import pandas as pd
import numpy as np
from arena.api import IGameMode

class TheWinter(IGameMode):
    @property
    def name(self) -> str:
        return "The Winter (Slow Bleed)"

    @property
    def description(self) -> str:
        return "Death by 1000 cuts. Slow, grinding downtrend with fakeout pumps."

    def generate_scenario(self) -> pd.DataFrame:
        timestamps = pd.date_range(start="2022-01-01", periods=1500, freq="h")
        
        price = 100.0
        prices = []
        
        np.random.seed(13)
        for _ in range(1500):
            # Drift is negative (Bleed)
            drift = -0.05 
            shock = np.random.normal(0, 0.5)
            
            # Occasional Fakeout Pump
            if np.random.random() > 0.98:
                shock += 5.0
            
            price = price + drift + shock
            if price < 1: price = 1
            prices.append(price)
            
        return pd.DataFrame({
            "timestamp": timestamps,
            "close": np.array(prices),
            "volume": np.random.randint(10, 50, 1500) # Dead volume
        })
