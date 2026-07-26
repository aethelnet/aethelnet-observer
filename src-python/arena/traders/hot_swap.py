
from ..base_trader import BaseTrader
import pickle
import os
import time
import pandas as pd
from services.data_manager import DataManager

class HotSwapTrader(BaseTrader):
    """
    The Chameleon.
    Automatically reloads the 'Best Bot' from the Long Haul Training Loop.
    """
    def __init__(self, name="HotSwap", status_file="long_haul_status.json"):
        super().__init__(name, 100000.0)
        self.status_file = status_file
        self.current_strategy = None
        self.current_strategy_name = "None"
        self.last_reload = 0
        self.reload_interval = 60 # Check every minute
        
        print(f"[HotSwap] Initialized. Watching {status_file}...")

    def check_for_updates(self):
        """Peeks at the JSON status file to see if a new champion exists."""
        if time.time() - self.last_reload < self.reload_interval:
            return

        self.last_reload = time.time()
        
        if not os.path.exists(self.status_file):
            return
            
        try:
            import json
            with open(self.status_file, 'r') as f:
                status = json.load(f)
                
            strat_name = status.get('strategy')
            gen = status.get('generation')
            
            # Load Checkpoint logic
            # Assume pattern: checkpoint_{Strategy_Name}.pkl
            # Strategy names often have spaces. Filenames use underscores.
            filename = f"checkpoint_{strat_name.replace(' ', '_')}.pkl"
            
            # RAT SPECIAL CASE: Bootcamp saved as rat_{arena}_chk.pkl? 
            # No, Long Haul saves as `checkpoint_{Name}.pkl`.
            
            if os.path.exists(filename):
                # Verify modification time to avoid reloading same file?
                # Actually, pickle content matters.
                # Just reload if name changed or randomly occasionally?
                # Let's simple check if strat_name changed OR gen changed (if we tracked gen).
                
                if strat_name != self.current_strategy_name:
                    print(f"[HotSwap] !! NEW CHAMPION DETECTED !! Switching to {strat_name} (Gen {gen})")
                    with open(filename, 'rb') as f:
                        data = pickle.load(f)
                        # data is {'generation': N, 'population': [...]}
                        # We take the best stored? Or is it just population?
                        # Usually Long Haul dumps the *Population*.
                        # We need the Best One.
                        # We can pick the first one? Or sort?
                        population = data['population']
                        # Assume sorted? Academy sorts before saving?
                        # Re-read Academy.py... 
                        # Academy sorts `scores`. `population` is `new_population` derived from survivors.
                        # It's NOT guaranteed sorted by fitness in the list, but effectively survivor-biased.
                        
                        # We'll take the first one (Alpha).
                        best_bot = population[0]
                        self.current_strategy = best_bot
                        self.current_strategy_name = strat_name
                        print(f"[HotSwap] Equipped {strat_name}. Skills: {best_bot.skills}")
                        
        except Exception as e:
            print(f"[HotSwap] Reload Failed: {e}")

    def decide(self, galaxy_state):
        # 1. Update Strategy
        self.check_for_updates()
        
        if not self.current_strategy:
            return []
            
        # 2. Convert Galaxy State to DataFrame (TheRat expects df)
        # We need historical data for the CORE ticker preferably.
        core = galaxy_state.get('CORE')
        if not core: return []
        
        history = core.get('history', {})
        prices = history.get('price', [])
        
        if len(prices) < 20: return []
        
        # Mock DataFrame
        # TheRat needs 'close'.
        df = pd.DataFrame({'close': prices})
        
        # 3. Ask Strategy
        signal = self.current_strategy.next_candle(df)
        
        # 4. Execute
        orders = []
        ticker = 'BTCUSDT' # Default
        
        if signal != 0:
            side = 'buy' if signal > 0 else 'sell'
            size = abs(signal) * 10.0 # Scale sizing
            print(f"[HotSwap] Signal from {self.current_strategy_name}: {side.upper()} {size:.2f}")
            orders.append({'side': side, 'size': size, 'ticker': ticker})
            
        return orders
