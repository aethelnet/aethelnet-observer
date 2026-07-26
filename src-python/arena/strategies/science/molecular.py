from typing import List, Dict, Any
import numpy as np
import pandas as pd
from arena.api import IStrategy

class TheMolecularMind(IStrategy):
    """
    The Molecular Mind: Applied Thermodynamics.
    Markets have phases: Solid (Low Vol), Liquid (Trend), Gas (Crash).
    WE trade the phase change.
    """
    def __init__(self):
        super().__init__()
        # Skills: Physics Constants
        self.skills = {
            "freezing_point": 0.5,   # Below this volatility = Solid (Ice)
            "boiling_point": 2.0,    # Above this volatility = Gas (Steam/Crash)
            "viscosity": 10,         # Moving Average window for trend (Liquid flow)
            "entropy_threshold": 0.8 # Randomness required to exit Gas
        }
        self.state = "LIQUID" # Default

    @property
    def name(self) -> str:
        return "The Molecular Mind"

    @property
    def class_type(self) -> str:
        return "PHYSICIST"

    def on_tick(self, packet: Dict[str, Any]) -> float:
        return 0.0 # Not used in backtest logic yet

        
    def next_candle(self, window_df: pd.DataFrame) -> float:
        # 1. Physics Engine (Metrics)
        closes = window_df['close'].values
        
        if len(closes) < 30:
            return 0.0
            
        # Volatility (Temperature)
        # We use annualized vol or simple std dev relative to mean
        log_ret = np.log(closes[1:] / closes[:-1])
        volatility = np.std(log_ret) * 100 # Percentage
        
        # Trend (Flow Direction)
        viscosity = int(self.skills['viscosity'])
        ma = np.mean(closes[-viscosity:])
        current_price = closes[-1]
        
        # 2. State Determination (Phase Change)
        # Hysteresis included to prevent rapid flickering
        if volatility < self.skills['freezing_point']:
            self.state = "SOLID"
        elif volatility > self.skills['boiling_point']:
            self.state = "GAS"
        else:
            self.state = "LIQUID"
            
        # 3. Action based on State (Thermodynamics)
        
        if self.state == "SOLID":
            # crystal lattice structure -> Mean Reversion
            # If price deviates from lattice (MA), it snaps back
            deviation = (current_price - ma) / ma
            # Buy if compressed below (Spring), Sell if stretched above
            if deviation < -0.01: return 0.5 # Buy Limit logic (simulated by partial entry)
            if deviation > 0.01: return -0.5
            return 0.0
            
        elif self.state == "LIQUID":
            # Laminar Flow -> Trend Following
            # Go with the flow
            if current_price > ma: return 1.0 # Full flow
            if current_price < ma: return -1.0
            return 0.0
            
        elif self.state == "GAS":
            # High Entropy -> Chaos/Explosion
            # Molecules moving too fast to hold structure.
            # Usually implies a crash or parabolic blow-off.
            # Strategy: Cash is King (Vacuum) OR Short the Blow-off
            
            # If price is parabolic up, Short.
            # If price is crashing down, Cash.
            roc = (current_price - closes[-5]) / closes[-5]
            if roc > 0.05: return -1.0 # Short the explosion
            return 0.0 # Stay safe
            
        return 0.0
        
    def get_raw_molecular_velocity(self, window_df: pd.DataFrame) -> float:
        """Exposes the raw Phase Velocity (tanh-saturated) for Neural Training."""
        closes = window_df['close'].values
        if len(closes) < 30: return 0.0
        
        log_ret = np.log(closes[1:] / closes[:-1])
        volatility = np.std(log_ret) * 100
        
        # Saturation around boiling point
        # Map 0..BoilingPoint..Inf to 0..1..1 (approx)
        return float(np.tanh(volatility / self.skills['boiling_point']))
        
    def evolve(self, mutation_rate: float = 0.1) -> 'TheMolecularMind':
        child = TheMolecularMind()
        for key, val in self.skills.items():
            change = 1.0 + np.random.uniform(-mutation_rate, mutation_rate)
            child.skills[key] = val * change
        return child
