import pandas as pd
import numpy as np
from arena.api import IGameMode

class TheMoonshot(IGameMode):
    @property
    def name(self) -> str:
        return "The Moonshot (Parabolic Pump)"

    @property
    def description(self) -> str:
        return "An irrational exponential pump. Tests FOMO resistance and Top-Calling."

    def generate_scenario(self) -> pd.DataFrame:
        timestamps = pd.date_range(start="2021-01-01", periods=1000, freq="min")
        
        # Exponential Curve
        t = np.linspace(1, 10, 1000)
        price = np.exp(t/2) # Parabolic
        
        # Add noise
        noise = np.random.normal(0, price*0.02, 1000)
        price = price + noise
        
        return pd.DataFrame({
            "timestamp": timestamps,
            "close": price,
            "volume": np.random.randint(1000, 50000, 1000) * (t/2) # Volume creates price
        })
