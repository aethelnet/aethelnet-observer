import pandas as pd
import numpy as np
import random
from arena.api import IGameMode

class TheOnebro(IGameMode):
    """
    Hard Mode.
    Simulates:
    1. Lag (Data arrives late).
    2. Slippage (Execution is worse than quote).
    3. Low Capital (Simulated via signal handicap).
    """
    @property
    def name(self) -> str:
        return "The Onebro (Hardcore)"

    @property
    def description(self) -> str:
        return "Lag + Slippage + Low Liquidity. If you survive here, you are God Tier."

    def generate_scenario(self) -> pd.DataFrame:
        # Standard Scenario Data (can be anything, let's use a nice trend)
        timestamps = pd.date_range(start="2024-01-01", periods=1500, freq="min")
        
        # Clean Trend
        t = np.linspace(0, 10, 1500)
        price = 100 + t**2 + np.sin(t*5)*5
        
        return pd.DataFrame({
            "timestamp": timestamps,
            "close": price,
            "volume": np.random.randint(500, 2000, 1500)
        })

    def apply_handicap(self, signal: float, lag_ms: int = 0) -> float:
        # 1. Input Lag (Simulated by 'forgetting' the signal occasionally)
        if random.random() < 0.1: # 10% Packet Loss
            return 0.0
            
        # 2. Execution Handicap (Slippage)
        # If signal is weak, Onebro can't afford the fees/slip, so we kill it.
        # Must have STRONG conviction (> 0.8) to execute.
        if abs(signal) < 0.8:
            return 0.0
            
        return signal
