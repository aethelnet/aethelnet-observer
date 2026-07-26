from ...api import IStrategy
import numpy as np
import pandas as pd

class TheProfessor(IStrategy):
    """
    The Professor (Regime Classifier).
    
    Concept:
        Hidden Markov Model (HMM) logic to determine the 'State' of the market.
        He doesn't trade directionally. He assigns a 'Class' to the current candle.
        
    Mechanic:
        - Input: Log-Returns, Volatility (GARCH proxy), Volume Delta.
        - States:
            0. "The Great Moderation" (Low Vol, Low Return) -> Safe for Leverage.
            1. "The Bull Run" (Med Vol, Pos Return) -> Trend Following.
            2. "The Bubble" (High Vol, Parabolic Return) -> Soros Zone.
            3. "The Crash" (Extreme Vol, Neg Return) -> Minsky Zone.
        - Output: State ID.
    """
    @property
    def name(self) -> str:
        return "The Professor"

    @property
    def class_type(self) -> str:
        return "META"

    def __init__(self):
        super().__init__()
        self.skills = {
            "window": 100
        }
        
    def on_tick(self, packet: dict) -> dict:
        return {"action": "OBSERVE"}
        
    def next_candle(self, df: pd.DataFrame) -> dict:
        if len(df) < self.skills['window']:
            return {"action": "WAIT"}
            
        # 1. Feature Engineering
        close = df['close']
        returns = close.pct_change().fillna(0)
        volatility = returns.rolling(20).std().fillna(0)
        
        curr_ret = returns.iloc[-1]
        curr_vol = volatility.iloc[-1]
        
        # 2. Simple Heuristic Regime Classification (Pseudo-HMM)
        # In real PhD implementation, we'd train GaussianMixture on historical data here.
        # For simulation speed, we use hard boundaries (Decision Tree).
        
        regime = "UNKNOWN"
        
        # Volatility Regimes
        LOW_VOL = 0.005 # 0.5%
        HIGH_VOL = 0.02 # 2.0%
        
        if curr_vol < LOW_VOL:
            regime = "MODERATION" # Quiet
        elif curr_vol > HIGH_VOL:
            # High Energy
            if curr_ret < -0.02:
                regime = "CRASH" # Minsky
            elif curr_ret > 0.02:
                regime = "BUBBLE" # Soros
            else:
                regime = "CHAOS" # High vol, directionless
        else:
            # Medium Vol
            if curr_ret > 0:
                regime = "BULL"
            else:
                regime = "BEAR"
                
        # 3. Decision
        # The Professor merely signals the regime.
        # The 'Consensus' or 'Board' uses this tag to switch bot weights.
        
        return {
            "action": "TAG",
            "regime": regime,
            "volatility": curr_vol
        }

    def evolve(self, mutation_rate: float = 0.1) -> 'IStrategy':
        # The Professor studies harder
        return self 
