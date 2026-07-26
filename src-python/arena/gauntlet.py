import pandas as pd
import numpy as np
import time
from typing import List, Dict
from arena.loader import StrategyLoader
from services.brain import ProphitEngine

class GauntletEngine:
    """
    The Tournament Director.
    Runs every Recruited Strategy against every Open Arena.
    """
    
    def __init__(self):
        self.loader = StrategyLoader()
        self.strategies = list(self.loader.discover_strategies().values()) 
        # Gauntlet needs a list of classes or instances. 
        # discover_strategies returns {name: instance}.
        # Gauntlet original code seemed to expect Classes but verify_rat uses instances?
        # Let's check how load_strategies was implemented.
        # Assuming we can just use the instances. 
        
        # Original: self.strategies = DojoLoader.load_strategies()
        # verify_rat.py probably instantiates GauntletEngine.
        
        # Wait, Gauntlet iterates: `for StrategyClass in self.strategies: strategy = StrategyClass()`
        # So it expects CLASSES.
        # StrategyLoader instantiates them.
        
        # I should adapt Gauntlet to use the instances directly if possible, OR
        # modify StrategyLoader to return classes?
        # StrategyLoader returns INSTANCES.
        
        # Let's Modify Gauntlet loop below.
        
        self.strategies = list(self.loader.discover_strategies().values()) 
        
        # --- ARENAS (REAL) ---
        self.gamemodes = self.loader.discover_gamemodes()
        
        if not self.gamemodes:
            # Fallback if empty
            class BasicArena:
                 def __init__(self): self.name = "The Sandbox"
                 def generate_scenario(self):
                     # Simple Sine Wave
                     return pd.DataFrame({'close': [100]*100, 'volume': [100]*100})
                 def apply_handicap(self, s): return s
            self.gamemodes = [BasicArena]
        self.results = []

    def run_tournament(self):
        print(f"--- BEGINNING TOURNAMENT ---")
        print(f"Contestants: {len(self.strategies)}")
        print(f"Arenas: {len(self.gamemodes)}")
        
        for ArenaClass in self.gamemodes:
            arena = ArenaClass()
            print(f"\n[ARENA] Opening: {arena.name}...")
            
            # Generate the Environment (Data)
            scenario_data = arena.generate_scenario()
            
            for strategy_instance in self.strategies:
                # StrategyLoader provides instances.
                # Ideally we clone or reset?
                # For now, use as is.
                strategy = strategy_instance
                # print(f"  > Fighter: {getattr(strategy, 'name', 'Unknown')} entering...")
                
                score = self._simulate_match(strategy, arena, scenario_data)
                self.results.append({
                    "Arena": arena.name,
                    "Fighter": strategy.name,
                    "Class": strategy.class_type,
                    "PnL": score['pnl'],
                    "Trades": score['trades'],
                    "WinRate": score['win_rate']
                })
                
        return pd.DataFrame(self.results)

    def _simulate_match(self, strategy, arena, data):
        """
        Runs the simulation loop for one pair.
        """
        # Simulation State
        capital = 10000.0
        position = 0.0
        entry_price = 0.0
        trades = 0
        wins = 0
        
        history_prices = []
        
        # Walk through the ticks
        # We assume data has ['open', 'high', 'low', 'close', 'volume', 'timestamp']
        # But our simple generators returned ['close', 'volume', 'timestamp'] which is fine
        
        closes = data['close'].values
        volumes = data['volume'].values
        
        # --- SOVEREIGN NEURAL INTEGRATION ---
        # Initialize Brain for 33D Manifold awareness during backtest
        from services.brain_full import BrainEngine
        brain = BrainEngine(no_hydrate=True)
        
        # Simple backtest loop
        # Optimization: Don't create DF every tick if possible, but for PhD bots we must.
        # We need a window size. Let's assume 100 default.
        window_size = 100
        
        for i in range(1, len(closes)):
            current_price = closes[i]
            tick_data = data.iloc[max(0, i - window_size) : i+1]
            
            # 1. Ask Strategy for Signal
            raw_signal = 0.0
            
            if i == 1:
                print(f"  [DEBUG] Starting first tick simulation...")
            
            # --- SOVEREIGN INJECTION ---
            start_time = time.time()
            soul_signal = brain.get_sovereign_signal(tick_data)
            duration = (time.time() - start_time) * 1000
            
            if i % 100 == 0:
                print(f"  [TICK {i}] Neural Signal: {soul_signal:.4f} ({duration:.1f}ms)")
            
            # Inject into strategy for next_candle path
            strategy._last_soul = soul_signal

            # Prefer 'next_candle' for complex bots
            try:
                # Slice window
                response = strategy.next_candle(tick_data)
            except Exception:
                # Fallback to on_tick (Augmented with 33D features)
                
                # --- GAUNTLET METRICS ENGINE (Augmented) ---
                # Construct State Object with full Manifold awareness
                # Calculate features (Input for strategy physics)
                features = brain.extract_features(tick_data)
                
                state = features.copy() # Start with the 33 dimensions
                state.update({
                    "price": current_price,
                    "volume": volumes[i],
                    "prev_price": closes[i-1],
                    "soul_signal": soul_signal,
                    "target_symbol": "BTCUSDT" 
                })
                response = strategy.on_tick(state)

            # 2. Parse Response (Dict to Float)
            if isinstance(response, dict):
                action = response.get("action", "HOLD")
                if action == "BUY":
                    raw_signal = 1.0
                elif action == "SELL":
                    raw_signal = -1.0
                elif action == "BUY_LIMIT":
                    # Simple assumption: Limit hits if price crosses? 
                    # For now treat as Market Buy for simplicity of 'Press Play'
                    raw_signal = 0.5 
                elif action == "SELL_LIMIT":
                    raw_signal = -0.5
                else:
                    raw_signal = 0.0
            else:
                # Assume float
                raw_signal = float(response)
            
            # 3. Apply Arena Handicap (Lag/Slip)
            final_signal = arena.apply_handicap(raw_signal)
            
            # 4. Execution Logic (Simple Reversal System)
            # Signal 1.0 = Max Long, -1.0 = Max Short
            # Scale size based on signal strength?
            # PhD bots give 1.0 or -1.0 usually
            
            target_position = final_signal * 1000.0 # $1000 max size
            
            # If position changes sign or size, we trade
            # Simple assumption: Instant execution at Close
            
            if target_position != position:
                # Close existing
                if position != 0:
                    # Calculate PnL percentage of the trade
                    # (Exit - Entry) / Entry * Side * Size
                    # Wait, simplified PnL logic:
                    trade_pnl = (current_price - entry_price) * (1 if position > 0 else -1)
                    # This is raw dollar PnL per unit?
                    # Position is in DOLLARS ($1000). 
                    # Units = $1000 / EntryPrice.
                    units = abs(position) / entry_price
                    realized_pnl = (current_price - entry_price) * units * (1 if position > 0 else -1)
                    
                    capital += realized_pnl
                    trades += 1
                    if realized_pnl > 0: wins += 1
                
                # Open new
                position = target_position
                entry_price = current_price
                
        # Close final position
        if position != 0:
            units = abs(position) / entry_price
            realized_pnl = (closes[-1] - entry_price) * units * (1 if position > 0 else -1)
            capital += realized_pnl
            
        win_rate = (wins / trades * 100) if trades > 0 else 0
        pnl_pct = (capital - 10000.0) / 10000.0 * 100
        
        return {
            "pnl": round(pnl_pct, 2),
            "trades": trades,
            "win_rate": round(win_rate, 1)
        }
