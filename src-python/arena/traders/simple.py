from ..base_trader import BaseTrader
import random

class TitForTatTrader(BaseTrader):
    """
    Simple trader that copies the last market move.
    Momentum following strategy.
    """
    def __init__(self, name="TitForTat", initial_balance=50000.0):
        super().__init__(name, initial_balance)
        self.last_prices = {}  # ticker -> last_price

    def decide(self, galaxy_state):
        orders = []
        
        for ticker, state in galaxy_state.items():
            current_price = state['price']
            
            if ticker not in self.last_prices:
                self.last_prices[ticker] = current_price
                continue
                
            # Calculate price change
            last_price = self.last_prices[ticker]
            change = (current_price - last_price) / last_price
            
            # Follow momentum
            size = 5.0  # Fixed lot size
            
            if change > 0.002:  # Price went up significantly
                orders.append({'side': 'buy', 'size': size, 'ticker': ticker})
            elif change < -0.002:  # Price went down significantly
                orders.append({'side': 'sell', 'size': size, 'ticker': ticker})
                
            self.last_prices[ticker] = current_price
            
        return orders

class RiskAverseTrader(BaseTrader):
    """
    Conservative trader that avoids high volatility.
    Only trades during calm market conditions.
    """
    def __init__(self, name="RiskAverse", initial_balance=50000.0):
        super().__init__(name, initial_balance)
        self.price_histories = {}  # ticker -> price_history

    def decide(self, galaxy_state):
        orders = []
        
        for ticker, state in galaxy_state.items():
            current_price = state['price']
            volatility = state.get('volatility', 0.01)
            
            # Track price history
            if ticker not in self.price_histories:
                self.price_histories[ticker] = []
            self.price_histories[ticker].append(current_price)
            
            # Keep only recent history
            if len(self.price_histories[ticker]) > 50:
                self.price_histories[ticker].pop(0)
                
            # Only trade in low volatility environments
            if volatility < 0.02 and len(self.price_histories[ticker]) > 10:
                # Calculate recent trend
                recent_prices = self.price_histories[ticker][-10:]
                trend = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
                
                size = 3.0  # Conservative size
                
                if trend > 0.01:  # Uptrend in calm market
                    orders.append({'side': 'buy', 'size': size, 'ticker': ticker})
                elif trend < -0.01:  # Downtrend in calm market
                    orders.append({'side': 'sell', 'size': size, 'ticker': ticker})
                    
            # Panic sell in high volatility
            elif volatility > 0.05:
                current_position = self.inventory.get(ticker, 0)
                if current_position > 0:
                    orders.append({'side': 'sell', 'size': current_position, 'ticker': ticker})
                    
        return orders
