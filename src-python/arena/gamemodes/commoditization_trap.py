from arena.api import IGameMode
import pandas as pd
import numpy as np

class TheCommoditizationTrap(IGameMode):
    """
    SCENARIO DESIGN: The Commoditization Trap.
    Gemini Seed #5 Scenario.
    
    Narrative: "The Slow Bleed".
    Simulates the devaluation of technical skills (Down Trend) masked by 'AI Noise' (High Freq Jitter).
    Tests the Pilot's discipline to SIT STILL (Travel Mode).
    """

    @property
    def name(self) -> str:
        return "The Commoditization Trap"

    @property
    def description(self) -> str:
        return "A grinding, noisy bear market representing the devaluation of technical skills."

    def generate_scenario(self) -> pd.DataFrame:
        length = 5000
        start_price = 1000.0
        
        # 1. The Slow Bleed (The devaluation of the Master Technician)
        # Linear decay representing the commoditization of services over time.
        trend = np.linspace(0, -200, length) 
        
        # 2. The AI Noise (Generic Content Flood)
        # High frequency noise that makes it look like there is action, when there is none.
        noise = np.random.normal(0, 5, length)
        
        # 3. The "False Summits" (Hype Cycles)
        # Occasional sine waves that lure the pilot in, only to crash.
        hype_cycles = np.sin(np.linspace(0, 20 * np.pi, length)) * 20
        
        # 4. Synthesize Price
        price_action = start_price + trend + noise + hype_cycles
        
        # Ensure no negative prices
        price_action = np.maximum(price_action, 1.0)
        
        # Create DataFrame
        df = pd.DataFrame({
            'timestamp': pd.date_range(start='2025-01-01', periods=length, freq='h'),
            'close': price_action
        })
        
        # Synthesize OHLC based on 'close' to give it body
        df['open'] = df['close'].shift(1).fillna(start_price)
        df['high'] = df[['open', 'close']].max(axis=1) + (np.abs(np.random.random(length)) * 2)
        df['low'] = df[['open', 'close']].min(axis=1) - (np.abs(np.random.random(length)) * 2)
        df['volume'] = np.random.randint(100, 10000, length)
        
        return df
