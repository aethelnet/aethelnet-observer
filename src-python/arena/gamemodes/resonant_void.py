from arena.api import IGameMode
import pandas as pd
import numpy as np

class TheResonantVoid(IGameMode):
    """
    SCENARIO DESIGN: The Resonant Void.
    Gemini Seed #6 Scenario.
    
    Narrative: "ECLIPSE Simulation".
    A hollow market of grey noise and arrhythmia designed to starve the Alchemist.
    Includes 'False Scars' (Drops that don't bounce) and Time Shifting.
    """

    @property
    def name(self) -> str:
        return "The Resonant Void"

    @property
    def description(self) -> str:
        return "A hollow market of grey noise and arrhythmia. Designed to starve the Alchemist."

    def generate_scenario(self) -> pd.DataFrame:
        length = 5000
        
        # 1. Base Layer: "The Grey Noise" (The Copy)
        # Extremely low volatility random walk.
        # This targets "God Mode" (which needs volatility) and "Architect" (needs trend).
        returns = np.random.normal(0, 0.0005, length) # Tiny standard deviation
        price_path = 100 * np.exp(np.cumsum(returns))
        
        # 2. Event: "The Arrhythmia" (Disrupting the Cycle)
        # Nika relies on a 24h cycle. The Void shifts time.
        # We inject periods where price freezes, effectively "skipping" hours.
        
        data = []
        current_price = 100.0
        
        for i in range(length):
            # 3. The Anomaly: "The Null Scar"
            # Instead of a sharp drop (which the Alchemist loves), 
            # we create a "False Scar" - a drop that never recovers (The Trap).
            if i == 2000 or i == 4000:
                 current_price *= 0.85 # 15% drop
                 # But we kill volatility immediately after, trapping the liquidity
                 vol_multiplier = 0.0
            else:
                 vol_multiplier = 1.0

            # 4. Generate Candle
            step_move = np.random.normal(0, 1.0) * vol_multiplier
            
            # Apply "Suffocation" (Low Vol) occasionally
            if 1000 < i < 1500:
                step_move *= 0.1
                
            open_p = current_price
            close_p = current_price + step_move
            high_p = max(open_p, close_p) + abs(np.random.normal(0, 0.5))
            low_p = min(open_p, close_p) - abs(np.random.normal(0, 0.5))
            
            # Update current
            current_price = close_p
            
            # Volume is high during the "False Scars", low otherwise (Ghost volume)
            vol = 1000 if vol_multiplier > 0 else 100
            
            data.append([open_p, high_p, low_p, close_p, vol])

        df = pd.DataFrame(data, columns=['open', 'high', 'low', 'close', 'volume'])
        
        # Create a time index to simulate the 24h cycle
        # We start at 10:00 (Ground Protocol)
        start_date = pd.Timestamp("2025-12-09 10:00:00")
        df.index = [start_date + pd.Timedelta(hours=i*0.1) for i in range(length)]
        
        # Since IGameMode usually returns 'timestamp' column, let's ensure it exists
        df['timestamp'] = df.index
        
        return df
