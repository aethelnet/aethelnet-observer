from ...api import IStrategy
import numpy as np
import pandas as pd

class TheLiquidityHole(IStrategy):
    """
    The Liquidity Hole (Flash Crash Exploiter).
    
    Concept:
        Market Depth protects against slippage. When Depth evaporates (Liquidity Hole), 
        small orders cause massive price dislocations (Flash Crash).
        
    Mechanic:
        - Detect Low Order Book Depth (Simulated via Volume/Range Ratio).
        - If Ratio drops (Thin Market) AND Volatility spikes (Panic):
            - Place Limit Bids way below market (-5%, -10%).
            - Place Limit Asks way above market (+5%, +10%).
        - "Fishing for Wicks."
    """
    @property
    def name(self) -> str:
        return "The Liquidity Hole"

    @property
    def class_type(self) -> str:
        return "ECONOMIST"

    def __init__(self):
        super().__init__()
        self.skills = {
            "depth_threshold": 0.5, # Relative liquidity check
            "panic_threshold": 0.03, # 3% move in 1 candle
            "fishing_depth": 0.08    # 8% away from price
        }
        
    def on_tick(self, packet: dict) -> dict:
        return {"action": "HOLD"}
        
    def next_candle(self, df: pd.DataFrame) -> dict:
        if len(df) < 20:
             return {"action": "HOLD"}
             
        # 1. Estimate Liquidity (Kyle's Lambda proxy)
        # Amivest measure: Volume / |Return|
        # High Value = Deep Market (Takes lots of vol to move price).
        # Low Value = Thin Market (Small vol moves price).
        
        close = df['close']
        volume = df['volume']
        
        returns = close.pct_change().abs()
        liquidity = volume / (returns + 0.0000001) # Avoid div/0
        
        # Normalize Liquidity against recent history (Z-Score)
        rolling_liq = liquidity.rolling(20).mean().iloc[-1]
        current_liq = liquidity.iloc[-1]
        
        liquidity_ratio = current_liq / rolling_liq if rolling_liq > 0 else 1.0
        
        # 2. Detect Panic
        current_ret = (close.iloc[-1] - close.iloc[-2]) / close.iloc[-2]
        
        is_thin = liquidity_ratio < self.skills['depth_threshold']
        is_panic = abs(current_ret) > self.skills['panic_threshold']
        
        action = "HOLD"
        limit_order = None
        
        if is_thin and is_panic:
            # THE HOLE IS OPEN.
            # If Panic is Down, we fish LOW.
            if current_ret < 0:
                target_price = close.iloc[-1] * (1.0 - self.skills['fishing_depth'])
                action = "BUY_LIMIT"
                limit_order = target_price
            else:
                # Panic Up (Short Squeeze)
                target_price = close.iloc[-1] * (1.0 + self.skills['fishing_depth'])
                action = "SELL_LIMIT"
                limit_order = target_price
                
        return {
            "action": action,
            "limit_price": limit_order,
            "liquidity_ratio": liquidity_ratio
        }

    def evolve(self, mutation_rate: float = 0.1) -> 'IStrategy':
        child = TheLiquidityHole()
        child.skills['fishing_depth'] = np.clip(self.skills['fishing_depth'] + np.random.normal(0, 0.01), 0.01, 0.20)
        return child
