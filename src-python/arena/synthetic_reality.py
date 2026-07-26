import numpy as np
import pandas as pd
from datetime import datetime, timedelta

class SyntheticReality:
    """
    The Studio (Mathematical Market Generator).
    Generates high-fidelity, tick-level market scenarios based on economic theories.
    Used for 'The PhD Defense' to prove strategy robustness in theoretical extremes.
    """
    
    def __init__(self):
        pass

    def _generate_time_index(self, duration_hours: int, freq: str = "1s") -> pd.DatetimeIndex:
        start = datetime(2025, 1, 1)
        periods = duration_hours * 3600 # seconds
        return pd.date_range(start=start, periods=periods, freq=freq)

    def generate_minsky_meltdown(self, duration_hours: int = 10) -> pd.DataFrame:
        """
        Scenario: The Great Moderation -> The Crash.
        Math: Wiener Process with decaying volatility (Stability) -> Jump Diffusion (Crash).
        """
        index = self._generate_time_index(duration_hours)
        n = len(index)
        
        # 1. The Buildup (Stability) - 80% of time
        # Low volatility drift upwards
        split = int(n * 0.8)
        
        # Random Walk (Brownian Motion)
        # dS = mu*dt + sigma*dW
        mu = 0.0001 # Slow drift up
        sigma_stable = 0.0005 # Very low vol
        
        returns = np.random.normal(mu, sigma_stable, split)
        
        # 2. The Moment (The Crash)
        # Massive Jump Diffusion
        sigma_crash = 0.02 # Huge vol
        crash_drift = -0.005 # Fast crash
        
        crash_returns = np.random.normal(crash_drift, sigma_crash, n - split)
        
        # Combine
        all_returns = np.concatenate([returns, crash_returns])
        price_path = 100 * np.exp(np.cumsum(all_returns))
        
        # Volume: Low during stability, Explodes during crash
        vol_stable = np.random.normal(100, 10, split)
        vol_crash = np.random.normal(5000, 1000, n - split)
        volume_path = np.concatenate([vol_stable, vol_crash])
        
        df = pd.DataFrame({
            "timestamp": index,
            "close": price_path,
            "volume": volume_path
        })
        
        # Feature Engineering (OHLC sim)
        df['open'] = df['close']
        df['high'] = df['close'] * 1.001
        df['low'] = df['close'] * 0.999
        
        return df

    def generate_soros_bubble(self, duration_hours: int = 10) -> pd.DataFrame:
        """
        Scenario: Reflexivity (Super-Exponential Growth).
        Math: Price change correlated with Volume change.
        """
        index = self._generate_time_index(duration_hours)
        n = len(index)
        
        # Exponential Growth Phase
        t = np.linspace(0, 10, n)
        # Price = e^(t) with some noise
        # This creates parabolic structure
        
        noise = np.random.normal(0, 0.5, n)
        price_path = 100 + np.exp(t * 0.5) + noise
        
        # Volume correlates with Price (Reflexivity)
        # Vol = Price * RandomFactor
        volume_path = price_path * np.random.uniform(0.8, 1.2, n) * 10
        
        df = pd.DataFrame({
            "timestamp": index,
            "close": price_path,
            "volume": volume_path
        })
        
        df['open'] = df['close']
        df['high'] = df['close'] + (df['close'] * 0.005)
        df['low'] = df['close'] - (df['close'] * 0.005)
        
        return df

    def generate_liquidity_vacuum(self, duration_hours: int = 5) -> pd.DataFrame:
        """
        Scenario: Flash Crash (Liquidity Hole).
        Math: Standard walk -> Volume Drop -> Price Gap.
        """
        index = self._generate_time_index(duration_hours)
        n = len(index)
        
        price = 1000.0
        prices = []
        volumes = []
        
        # Event happens in middle
        start_event = int(n * 0.45)
        end_event = int(n * 0.55)
        
        for i in range(n):
            if start_event < i < end_event:
                # VACUUM ZONE
                # Volume dies
                vol = np.random.uniform(1, 10) # Almost zero
                
                # Volatility explodes (Gaps)
                change = np.random.normal(0, 50.0) # Huge jumps
                price += change
            else:
                # Normal Market
                vol = np.random.uniform(1000, 5000)
                change = np.random.normal(0, 1.0)
                price += change
                
            prices.append(price)
            volumes.append(vol)
            
        df = pd.DataFrame({
            "timestamp": index,
            "close": prices,
            "volume": volumes
        })
        
        # WICK simulation
        df['open'] = df['close']
        df['high'] = df['close']
        df['low'] = df['close']
        
        return df

    def generate_choppy_normal(self, duration_hours: int = 12) -> pd.DataFrame:
        """
        Scenario: Choppy Normal (Mean-Reverting Boredom).
        Math: Ornstein-Uhlenbeck process with random volume spikes and fake breakouts.
        Designed to train strategies that survive 'boring normal' markets.
        """
        index = self._generate_time_index(duration_hours)
        n = len(index)
        
        # Ornstein-Uhlenbeck parameters (mean-reverting)
        theta = 0.3      # Speed of mean reversion
        mu = 0.0        # Long-term mean (no drift)
        sigma = 0.008   # Volatility (low but not zero)
        dt = 1 / 3600   # 1-second bars
        
        # Initialize price and volume paths
        price = 100.0
        prices = [price]
        volumes = []
        
        for i in range(1, n):
            # OU drift toward mean
            drift = theta * (mu - (price - 100.0) / 100.0)
            noise = np.random.normal(0, sigma)
            change = drift * dt + noise * np.sqrt(dt)
            
            # Random volume spikes without trend (whipsaw bait)
            if np.random.random() < 0.15:  # 15% chance of volume spike
                vol = np.random.uniform(8000, 12000)
                # Small fake breakout that reverts
                if np.random.random() < 0.5:
                    change += np.random.choice([-0.003, 0.003])
            else:
                vol = np.random.uniform(800, 3000)
            
            price += change
            prices.append(price)
            volumes.append(vol)
        
        # Pad first volume to match length
        volumes.insert(0, volumes[0] if volumes else 1500)
        
        df = pd.DataFrame({
            "timestamp": index,
            "close": prices,
            "volume": volumes
        })
        
        # Simulate OHLC
        df['open'] = df['close'].shift(1).fillna(df['close'])
        df['high'] = df[['open', 'close']].max(axis=1) * np.random.uniform(1.0, 1.002, len(df))
        df['low'] = df[['open', 'close']].min(axis=1) * np.random.uniform(0.998, 1.0, len(df))
        
        return df
