import numpy as np
import random
from enum import Enum

class MarketEra(Enum):
    NORMAL = "NORMAL"
    BOOM = "BOOM"
    CRASH = "CRASH"
    CHAOS = "CHAOS"
    STAGNATION = "STAGNATION"

class Market:
    def __init__(self, scenario=None, start_price=100.0):
        self.price = start_price
        self.initial_price = start_price
        self.time = 0
        self.scenario = scenario
        self.history = {'price': [], 'volume': [], 'volatility': []}
        
        # Order Book (Simplified)
        self.bids = []
        self.asks = []

    def step(self, orders):
        """
        Evolve market by one tick using Scenario data.
        """
        # Get conditions from Scenario
        conditions = {'volatility': 0.01, 'trend': 0.0, 'liquidity': 1000.0, 'inverted': False}
        if self.scenario:
            conditions = self.scenario.get_conditions(self.time)
            
        volatility = conditions['volatility']
        trend = conditions['trend']
        liquidity = conditions['liquidity']
        inverted = conditions.get('inverted', False)
        
        self.time += 1
        
        # 1. Calculate Net Order Flow
        net_volume = 0
        total_volume = 0
        
        for order in orders:
            size = order.get('size', 0)
            if order['side'] == 'buy':
                net_volume += size
            else:
                net_volume -= size
            total_volume += size

        # 2. Price Impact
        impact = 0
        if liquidity > 0:
            # Impact is proportional to Volatility too (thinner books in high vol)
            impact = (net_volume / liquidity) * self.price * (volatility * 10.0)
            
        # IRRATIONAL PHYSICS: Invert Impact
        if inverted:
            impact *= -2.0 # Reverse impact and amplify it (Chaos)
            
        # 3. Scenario Trend
        drift = trend * self.price
            
        # 4. Noise
        noise = np.random.normal(0, volatility * self.price)
            
        # Update Price
        self.price += drift + noise + impact
        self.price = max(0.01, self.price) 
        
        # Record History
        self.history['price'].append(self.price)
        self.history['volume'].append(total_volume)
        self.history['volatility'].append(volatility)
        
        return {
            'price': self.price,
            'volume': total_volume,
            'time': self.time,
            'volatility': volatility,
            'liquidity': liquidity
        }

    def get_state(self):
        return {
            'price': self.price,
            'time': self.time,
            'history': self.history
        }
