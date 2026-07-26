from arena.api import IGameMode
import pandas as pd
import numpy as np

class TheSuperTyphoon(IGameMode):
    """
    The Super Typhoon (T10).
    Gemini Seed #10 Scenario.
    
    A scenario designed to test 'The Typhoon Sanctuary'.
    It generates massive volatility spikes (Typhoons) that would liquidate normal bots,
    testing if the HK Concrete holds and if the German Interior can scalp the noise.
    """
    
    @property
    def name(self) -> str:
        return "The Super Typhoon"

    @property
    def description(self) -> str:
        return "Massive volatility bursts testing structural integrity."

    def generate_scenario(self) -> pd.DataFrame:
        length = 5000
        data = []
        current_price = 100.0
        
        for i in range(length):
            vol_multiplier = 0.8
            
            # The Typhoon Cycle
            # Every 1000 ticks, a Category 10 storm hits.
            cycle_pos = i % 1000
            
            if 400 < cycle_pos < 600:
                # THE EYE WALL
                vol_multiplier = 8.0 # Extreme volatility
            elif 480 < cycle_pos < 520:
                # THE EYE (Calm center)
                vol_multiplier = 0.1
            
            # Generate Candle
            step_move = np.random.normal(0, 1.0) * vol_multiplier
            
            open_p = current_price
            close_p = current_price + step_move
            
            # Wicks are insane during Typhoon
            high_p = max(open_p, close_p) + abs(np.random.normal(0, 0.5) * vol_multiplier)
            low_p = min(open_p, close_p) - abs(np.random.normal(0, 0.5) * vol_multiplier)
            
            current_price = close_p
            vol = 1000 * vol_multiplier
            
            data.append([open_p, high_p, low_p, close_p, vol])

        df = pd.DataFrame(data, columns=['open', 'high', 'low', 'close', 'volume'])
        
        # Sync timestamp
        start_date = pd.Timestamp("2025-12-09 10:00:00")
        df.index = [start_date + pd.Timedelta(hours=i*0.1) for i in range(length)]
        # For compatibility
        df['timestamp'] = df.index
        
        return df
