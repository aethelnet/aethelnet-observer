from arena.api import IGameMode
import pandas as pd
import numpy as np

class TheXenonCrisis(IGameMode):
    """
    The Xenon Crisis (Resource Shock).
    Gemini Seed #4 Scenario.
    
    Structure:
    1. Resource Shortage: Slow grind down, low volatility (Kills Miners).
    2. Invasion: Massive volatility spike (Stress tests Reserve Capital).
    """
    @property
    def name(self) -> str:
        return "The Xenon Crisis"

    @property
    def description(self) -> str:
        return "Simulates a resource shortage (Liquidity Crisis) followed by a massive invasion (Volatility Spike)."

    def generate_scenario(self) -> pd.DataFrame:
        length = 5000
        prices = np.zeros(length)
        prices[0] = 1000
        
        # 1. The "Resource Shortage" (The Trap)
        # Price grinds slowly downwards with almost ZERO volatility.
        # This kills 'Miners' (nothing to mine) and bores 'Fighters'.
        # Indices 0 to 4000
        for i in range(1, 4000):
            # Slow bleed
            prices[i] = prices[i-1] - 0.05 + np.random.normal(0, 0.05)
            
        # 2. The "Invasion" (The Stress Test)
        # Suddenly, a Xenon I enters the sector. Massive volatility.
        # Indices 4000 to end
        for i in range(4000, length):
            shock = np.random.normal(0, 50.0) # Huge variance (Invasion)
            prices[i] = prices[i-1] + shock
            
        # Ensure positive
        prices = np.maximum(prices, 10.0)
            
        # Create DataFrame
        df = pd.DataFrame({
            'timestamp': pd.date_range(start='2025-01-01', periods=length, freq='min'),
            'close': prices
        })
        # Generate OHLC
        df['open'] = df['close'].shift(1).fillna(1000)
        df['high'] = df[['open', 'close']].max(axis=1) + 2.0
        df['low'] = df[['open', 'close']].min(axis=1) - 2.0
        df['volume'] = np.random.randint(100, 10000, length)
        
        return df
