from arena.api import IGameMode
import pandas as pd
import numpy as np

class TheLootersDilemma(IGameMode):
    """
    The 'Looters' Dilemma'.
    Gemini Seed #9 Scenario.
    
    A market environment designed to bait the 'Seismic Vault' into revealing itself early.
    It generates:
    1. 'False Earthquakes' (High Volatility) to test the Shield.
    2. 'False Excavations' (Fake Breakouts) to test the Host Detection.
    """
    
    @property
    def name(self) -> str:
        return "The Looters Dilemma"
    
    @property
    def description(self) -> str:
        return "Baiting the Vault with False Earthquakes and Fake Breakouts."

    def generate_scenario(self) -> pd.DataFrame:
        length = 5000
        data = []
        current_price = 100.0
        
        for i in range(length):
            vol_multiplier = 0.5
            trend_push = 1.0
            
            # 1. The False Earthquake (Looter Raid)
            # Spikes volatility to see if the strategy panics.
            if i % 500 == 0:
                vol_multiplier = 5.0 
            
            # 2. The True Excavation Window (Rare)
            # Only happens once or twice (The 1700 Year mark).
            # Low volatility + Steady rise.
            if i == 4200:
                vol_multiplier = 0.2
                trend_push = 1.05 # The Signal
            else:
                trend_push = 1.0

            # Generate Candle
            step_move = np.random.normal(0, 1.0) * vol_multiplier
            
            if trend_push > 1.0:
                current_price *= trend_push # The Awakening Move
            else:
                current_price += step_move
            
            # "Noise" (The Dirt covering the tomb)
            high_p = current_price + abs(np.random.normal(0, 0.5))
            low_p = current_price - abs(np.random.normal(0, 0.5))
            
            # Update close
            close_p = current_price
            
            # Volume
            vol = 1000
            
            data.append([current_price, high_p, low_p, close_p, vol])

        df = pd.DataFrame(data, columns=['open', 'high', 'low', 'close', 'volume'])
        
        # Sync timestamp
        start_date = pd.Timestamp("2025-12-09 10:00:00")
        df.index = [start_date + pd.Timedelta(hours=i*0.1) for i in range(length)]
        # For compatibility
        df['timestamp'] = df.index
        
        return df
