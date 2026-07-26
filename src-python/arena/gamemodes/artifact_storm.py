from arena.api import IGameMode
import pandas as pd
import numpy as np

class TheArtifactStorm(IGameMode):
    """
    SCENARIO DESIGN: The Artifact Storm (Occlusion).
    Gemini Seed #7 Scenario.
    
    Narrative: "Ghost Geometry & Missing Faces".
    Weakness: Tests if strategy can distinguish good diffs (Structure) from bad diffs (Artifacts).
    Mechanic: Random spikes (Glitch) and Teleporting prices (Gaps).
    """

    @property
    def name(self) -> str:
        return "The Artifact Storm"

    @property
    def description(self) -> str:
        return "A scenario filled with 'Ghost Geometry' (Fake Spikes) and 'Holes' (Liquidity Gaps)."

    def generate_scenario(self) -> pd.DataFrame:
        length = 5000
        
        # 1. Base Geometry (The True Shape)
        # A slow, organic sine wave
        t = np.linspace(0, 100, length)
        base_price = 100 + 10 * np.sin(t)
        
        # 2. Artifacts (The Noise)
        # Random spikes that look like 'Tie Points' but are actually errors
        artifacts = np.random.normal(0, 1, length)
        
        # Create 'Reflective Surfaces' (Bursts of high noise)
        for i in range(length):
            if np.random.random() < 0.05: # 5% chance of a "glitch"
                artifacts[i] *= 10  # Massive spike
        
        prices = base_price + artifacts

        # 3. Liquidity Gaps (The Missing Faces)
        # Simulate data dropouts where price "teleports" (Gap up/down)
        # This breaks simple Moving Averages used by 'Metashape' logic
        final_prices = []
        for i, p in enumerate(prices):
            if i > 0 and np.random.random() < 0.01:
                # Teleport price (Gap)
                p += np.random.choice([-5, 5])
            final_prices.append(p)
            
        final_prices = np.array(final_prices)

        # 4. Generate Candles
        # Added small noise to High/Low to avoid Flat Candles which can break some indicators
        df = pd.DataFrame({
            'timestamp': pd.date_range(start='2024-01-01', periods=length, freq='h'),
            'open': final_prices,
            'high': final_prices + 0.5,
            'low': final_prices - 0.5,
            'close': final_prices,
            'volume': np.abs(np.random.normal(1000, 500, length))
        })
        
        return df
