from typing import List, Dict, Any
import numpy as np
import pandas as pd
from arena.api import IStrategy

class TheStigmergy(IStrategy):
    """
    The Stigmergy: Ant Colony Optimization.
    Price levels are 'paths'. 
    High Volume/Bounces leaves 'Pheromones'.
    We follow the strongest pheromone trails (Support/Resistance).
    """
    def __init__(self):
        super().__init__()
        # Skills: Ant Behavior
        self.skills = {
            "evaporation_rate": 0.95, # Pheromones decay over time
            "pheromone_strength": 1.0, # How much volume adds to a level
            "sensitivity": 0.02, # How close to a level counts as a 'visit' (2%)
            "colony_size": 100 # Virtual ants (not used directly, but scales logic)
        }
        # Digital Pheromone Map: {PriceLevel_Int: Strength}
        # We bin prices to integers or decimals for mapping
        self.pheromone_map = {} 

    @property
    def name(self) -> str:
        return "The Stigmergy"

    @property
    def class_type(self) -> str:
        return "BIOLOGIST"

    def on_tick(self, packet: Dict[str, Any]) -> float:
        return 0.0
        
    def _get_bin(self, price: float) -> int:
        # Bin to nearest 1% roughly? No, use integer for integers, 
        # or round to relevant precision.
        # Let's bin to 3 sig figs relative to price?
        # Simpler: Round to generic grid.
        return int(price)

    def next_candle(self, window_df: pd.DataFrame) -> float:
        # 1. Update Pheromones (Environment)
        closes = window_df['close'].values
        volumes = window_df['volume'].values if 'volume' in window_df.columns else np.ones(len(closes))
        
        current_price = closes[-1]
        last_bin = self._get_bin(current_price)
        
        # Evaporation (Global Decay)
        # Doing this every tick for map is expensive if map is huge.
        # We'll just decay the 'visited' ones or do lazy decay?
        # Lazy approach: Store timestamp.
        # Simple approach for backtest: Global decay x0.99
        for k in list(self.pheromone_map.keys()):
            self.pheromone_map[k] *= self.skills['evaporation_rate']
            if self.pheromone_map[k] < 0.1:
                del self.pheromone_map[k]
                
        # Deposit Pheromone
        # Volume acts as intensity
        volume_factor = np.log1p(volumes[-1]) # Log volume to dampen whales
        deposit = self.skills['pheromone_strength'] * volume_factor
        
        if last_bin in self.pheromone_map:
            self.pheromone_map[last_bin] += deposit
        else:
            self.pheromone_map[last_bin] = deposit
            
        # 2. Ant Decision (Follow Trail)
        # Look ahead: Is there a massive pheromone trail ABOVE or BELOW?
        
        # Scan levels near us
        scan_range = int(current_price * 0.05) # +/- 5%
        
        strongest_level = None
        max_p = 0
        
        for p_bin, strength in self.pheromone_map.items():
            # Check if within range
            if abs(p_bin - last_bin) <= scan_range:
                if strength > max_p:
                    max_p = strength
                    strongest_level = p_bin
                    
        # 3. Action
        if strongest_level:
            # If we are below strongest level -> It attracts us (Resistance acts as magnet then repel?)
            # Actually, Stigmergy usually implies following the path.
            # If path is higher, GO UP.
            if strongest_level > last_bin:
                return 1.0
            elif strongest_level < last_bin:
                return -1.0
                
        return 0.0

    def get_raw_pheromone_concentration(self, window_df: pd.DataFrame) -> float:
        """Exposes the normalized pheromone density (tanh-saturated) at current level."""
        closes = window_df['close'].values
        if len(closes) < 5: return 0.0
        
        current_price = closes[-1]
        p_bin = self._get_bin(current_price)
        
        strength = self.pheromone_map.get(p_bin, 0.0)
        # Saturate strength (which can grow large) into a manageable gradient
        return float(np.tanh(strength / 10.0))

    def evolve(self, mutation_rate: float = 0.1) -> 'TheStigmergy':
        child = TheStigmergy()
        for key, val in self.skills.items():
            change = 1.0 + np.random.uniform(-mutation_rate, mutation_rate)
            child.skills[key] = val * change
        return child
