from arena.api import IStrategy
import pandas as pd
import numpy as np

# ==========================================
# THE STRATEGY: The Fleet Commander
# ==========================================

class TheFleetCommander(IStrategy):
    """
    Nika: Fleet Command (Resource Allocation).
    Gemini Seed #4 (Final Form).
    
    Concept:
    - Does not trade directly. Manages a budget (Equity).
    - Scans the Sector (Market Condition).
    - Deploys 'Miners' (Mean Reversion) or 'Fighters' (Trend Following) based on conditions.
    """
    @property
    def name(self) -> str:
        return "The Fleet Commander"

    @property
    def class_type(self) -> str:
        return "PORTFOLIO_MANAGER"

    def __init__(self):
        super().__init__()
        # Resource Management Settings
        self.fleet_composition = {
            "miners": 0.0,   # % of capital allocated to Mean Reversion
            "fighters": 0.0, # % of capital allocated to Trend Following
            "reserve": 1.0   # % of capital held in Cash (The "Shipyard" fund)
        }
        
        # Personnel Settings (Risk Parameters)
        self.personnel_skill = {
            "reaction_time": 5,      # Ticks to react (Simulating pilot skill)
            "discipline": 0.95       # Probability of respecting Stop Loss
        }

    def on_tick(self, packet: dict) -> float:
        return 0.0

    def next_candle(self, df: pd.DataFrame) -> float:
        # --- PHASE 1: SECTOR SCAN (Market Analysis) ---
        # Instead of deciding "Buy/Sell", we decide "What is the Sector State?"
        
        if len(df) < 20: return 0.0

        volatility = df['close'].tail(20).std()
        trend_strength = abs(df['close'].iloc[-1] - df['close'].iloc[-20])
        
        # High Volatility + Low Trend = "Asteroid Field" (Good for Miners)
        # High Volatility + High Trend = "Xenon Invasion" (Good for Fighters)
        # Low Volatility = "Empty Space" (Dock and wait)
        
        # --- PHASE 2: RESOURCE ALLOCATION (Buying Ships) ---
        # Dynamic re-balancing of the fleet based on the scan.
        
        target_miners = 0.0
        target_fighters = 0.0
        
        if volatility > 1.0 and trend_strength < 5.0:
            # "Rich Asteroid Field Detected. Deploying Drills."
            target_miners = 0.8
            target_fighters = 0.0
        elif trend_strength > 10.0:
            # "Enemy Capital Ship Detected. Scramble Fighters."
            target_miners = 0.0
            target_fighters = 1.0 # Full aggression
        else:
            # "Sector Empty. Return to Shipyard."
            target_miners = 0.2
            target_fighters = 0.0

        # Smoothly adjust fleet size (Simulating "Build Time")
        self.fleet_composition['miners'] = (self.fleet_composition['miners'] * 0.9) + (target_miners * 0.1)
        self.fleet_composition['fighters'] = (self.fleet_composition['fighters'] * 0.9) + (target_fighters * 0.1)

        # --- PHASE 3: FLEET EXECUTION ---
        # Run the logic for the deployed ships
        
        # Miner Logic (Mean Reversion: Buy Low)
        # Simplistic logic: If Price > Avg -> Sell, Else Buy.
        avg = df['close'].tail(20).mean()
        miner_signal = -1.0 if df['close'].iloc[-1] > avg else 1.0
        
        # Fighter Logic (Trend Follow: Buy High)
        fighter_signal = 1.0 if df['close'].iloc[-1] > df['close'].iloc[-2] else -1.0
        
        # Combine signals based on Fleet Composition
        # This is the "Net Output" of your empire
        total_signal = (miner_signal * self.fleet_composition['miners']) + \
                       (fighter_signal * self.fleet_composition['fighters'])
                       
        return np.clip(total_signal, -1.0, 1.0)

    def evolve(self, mutation_rate: float = 0.1) -> 'TheFleetCommander':
        child = TheFleetCommander()
        # Evolution: Maybe we hire better personnel? (Improve discipline)
        # Or faster reaction time?
        if np.random.random() < mutation_rate:
            child.personnel_skill['discipline'] = min(1.0, self.personnel_skill['discipline'] + 0.01)
            
        return child
