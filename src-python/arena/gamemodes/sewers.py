from arena.api import IGameMode
import pandas as pd
import numpy as np
import random

class TheSewers(IGameMode):
    """
    Scenario: The Sewers (Inefficient Market)
    Description:
        A dirty, noisy environment simulating clumsy order flow.
        Features:
        1. Random 'Fat Finger' wicks (sudden 3-5% spikes that revert).
        2. High Noise (Random Walk).
        3. Stuttering (Flat periods).
    """

    @property
    def name(self) -> str:
        return "The Sewers"

    @property
    def description(self) -> str:
        return "Inefficient Market: High Noise, Fat Fingers, Panic Wicks."

    def generate_scenario(self) -> pd.DataFrame:
        """
        Generates 2000 candles of garbage data.
        """
        length = 2000
        data = []
        price = 100.0
        
        print(f"[{self.name}] Flushing the pipes (Generating data)...")
        
        for i in range(length):
            # Base Movement: Random Walk (Noise)
            change = np.random.normal(0, 0.5)
            
            # Event: Fat Finger / Panic Wick (1% chance)
            if random.random() < 0.01:
                # Sudden massive spike
                spike = np.random.choice([-3.0, 3.0]) * np.random.uniform(1.0, 2.0)
                price += spike
                # The Rat should catch this reversal next candle
            else:
                price += change
            
            # Sanity Floor
            if price <= 10: price = 10.0
            
            # Create a 'Wick' within the candle
            # High/Low are exaggerated to show volatility
            vol = np.random.uniform(0.1, 2.0)
            
            data.append({
                "timestamp": pd.Timestamp.now() + pd.Timedelta(minutes=i),
                "open": price, # Gap open?
                "high": price + vol,
                "low": price - vol,
                "close": price + np.random.normal(0, 0.1), # Close slightly off
                "volume": np.random.randint(100, 5000)
            })
            
        return pd.DataFrame(data)

    def apply_handicap(self, signal: float, lag_ms: int = 0) -> float:
        """
        Simulate Execution Lag.
        In The Sewers, sometimes your order just doesn't fill or slips.
        """
        # 10% chance of 'Slip' (Signal reduced)
        if random.random() < 0.10:
            return signal * 0.5
        return signal
