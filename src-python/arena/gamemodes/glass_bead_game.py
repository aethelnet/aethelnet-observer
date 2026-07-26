from arena.api import IGameMode
import pandas as pd
import numpy as np
import random
import math

class TheGlassBeadGame(IGameMode):
    """
    Scenario: The Glass Bead Game (Gemini Arena)
    Description:
        A synthetic environment explicitly designed to test the 'Gemini' strategy.
        It alternates between two distinct regimes to verify the strategy's State Machine:
        1. ORDER: Clean Sine Waves (Trend-Following friendly).
        2. CHAOS: White Noise / Random Walk (Mean-Reversion friendly).
        
        The transitions are sharp to test reaction time.
    """

    @property
    def name(self) -> str:
        return "The Glass Bead Game"

    @property
    def description(self) -> str:
        return "Synthetic Environment: Alternating Order (Sine) and Chaos (Noise)"

    def generate_scenario(self) -> pd.DataFrame:
        """
        Generates 2000 candles of synthetic data.
        """
        length = 2000
        data = []
        price = 100.0
        
        # Generator State
        t = 0
        regime = "ORDER" # Start with Order
        
        print(f"[{self.name}] Generating {length} beads of reality...")
        
        for i in range(length):
            # 1. Regime Switcher (Every 200 ticks)
            if i % 200 == 0:
                regime = "CHAOS" if regime == "ORDER" else "ORDER"
                # print(f"  > Tick {i}: Switched to {regime}")
            
            change = 0.0
            
            # 2. Logic based on Regime
            if regime == "ORDER":
                # Sine Wave + Small Noise
                # Trend: price follows a sine wave pattern
                # dy/dx of sin(t) is cos(t).
                # We simply set price = 100 + 10*sin(t)
                t += 0.05
                target_price = 100 + (20 * math.sin(t))
                # Move towards target
                change = (target_price - price) * 0.1
                change += np.random.normal(0, 0.2) # Small friction
                
            elif regime == "CHAOS":
                # Random Walk (Brownian Motion)
                # Volatility is high
                change = np.random.normal(0, 1.5)
            
            price += change
            if price <= 0: price = 1.0 # Floor
            
            data.append({
                "timestamp": pd.Timestamp.now() + pd.Timedelta(minutes=i),
                "open": price,
                "high": price + 0.5,
                "low": price - 0.5,
                "close": price,
                "volume": 1000 + np.random.randint(-500, 500)
            })
            
        return pd.DataFrame(data)

    def calculate_reward(self, trades: list) -> float:
        """
        Standard PnL Reward.
        """
        if not trades: return 0.0
        pnl = sum([t['pnl'] for t in trades])
        return pnl
