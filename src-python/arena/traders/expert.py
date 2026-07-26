from ..base_trader import BaseTrader
import random
import numpy as np

class HFTTrader(BaseTrader):
    """
    High Frequency Trader.
    Uses mean reversion on a very short timeframe.
    Provides liquidity but can be predatory.
    """
    def __init__(self, name="FlashBoy", initial_balance=50000.0):
        super().__init__(name, initial_balance)
        self.window = []
        self.window_size = 10

    def decide(self, market_state):
        price = market_state['price']
        self.window.append(price)
        if len(self.window) > self.window_size:
            self.window.pop(0)
            
        if len(self.window) < self.window_size:
            return {'side': 'hold', 'size': 0}
            
        avg = sum(self.window) / len(self.window)
        std = np.std(self.window)
        
        if std == 0: return {'side': 'hold', 'size': 0}
        
        z_score = (price - avg) / std
        
        # Mean Reversion: Sell if high, Buy if low
        size = 5.0 # Larger size
        
        if z_score > 1.5:
            return {'side': 'sell', 'size': size}
        elif z_score < -1.5:
            return {'side': 'buy', 'size': size}
            
        return {'side': 'hold', 'size': 0}

class ChaosTrader(BaseTrader):
    """
    The Joker.
    Wants to watch the world burn.
    Injects massive volume randomly to break correlations.
    """
    def __init__(self, name="EntropyAgent", initial_balance=100000.0):
        super().__init__(name, initial_balance)
        self.cooldown = 0

    def decide(self, market_state):
        if self.cooldown > 0:
            self.cooldown -= 1
            return {'side': 'hold', 'size': 0}
            
        # Randomly decide to attack
        if random.random() < 0.05: # 5% chance per tick
            side = 'buy' if random.random() > 0.5 else 'sell'
            # Massive size to cause impact
            size = random.randint(50, 200) 
            self.cooldown = 10 # Rest after attack
            return {'side': side, 'size': size}
            
        return {'side': 'hold', 'size': 0}
