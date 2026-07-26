from arena.api import IGameMode
import pandas as pd
import numpy as np

class TheCourtOfHuoGuang(IGameMode):
    """
    The Nemesis: The Rigid Bureaucracy.
    Gemini Seed #8 Scenario.
    
    Represents the 'System of Sameness' (Mao / Huo Guang).
    It tries to starve the 'Emperor' by providing no volatility (Boredom),
    and then creating 'Fake Scandals' (False Crashes) to trigger the deposition.
    """
    
    @property
    def name(self) -> str:
        return "The Court of Huo Guang"

    @property
    def description(self) -> str:
        return "A oppressive, low-volatility regime with sudden 'Political Purges' (Traps)."

    def generate_scenario(self) -> pd.DataFrame:
        length = 5000
        data = []
        current_price = 100.0
        
        # The 'Bureaucracy' starts rigid.
        vol_regime = 0.05 
        
        for i in range(length):
            
            # 1. The Political Trap (The Deposition)
            # Suddenly drops the price to trigger the Emperor's 'Scar Hunting' instinct,
            # but then freezes the price so the resentment has nowhere to go.
            if i == 2000 or i == 3500:
                 current_price *= 0.80 # 20% Drop (The Deposition)
                 vol_regime = 0.001    # The Exile (Absolute Silence)
            
            # 2. The 'Berlin' Phase (The K-Hole)
            # Random periods of dissociation where price drifts aimlessly.
            elif 1000 < i < 1500:
                vol_regime = 0.01
            
            # 3. The Revolution (Rare moments where the system breaks)
            elif i > 4500:
                vol_regime = 2.0 # Chaos
                
            # Generate the candle
            step_move = np.random.normal(0, 1.0) * vol_regime
            
            open_p = current_price
            close_p = current_price + step_move
            
            # The Court suppresses high highs (Tall Poppy Syndrome)
            high_p = max(open_p, close_p) + (abs(np.random.normal(0, 0.1)) * 0.5)
            low_p = min(open_p, close_p) - abs(np.random.normal(0, 0.1))
            
            current_price = close_p
            
            # Volume: High during Purges, Low during Bureaucracy
            vol = 10000 if vol_regime > 1.0 else 100
            
            data.append([open_p, high_p, low_p, close_p, vol])

        df = pd.DataFrame(data, columns=['open', 'high', 'low', 'close', 'volume'])
        
        # Sync to Nika's time
        start_date = pd.Timestamp("2025-12-09 10:00:00")
        df.index = [start_date + pd.Timedelta(hours=i*0.1) for i in range(length)]
        
        return df
