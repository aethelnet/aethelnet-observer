import uuid

class BaseTrader:
    """
    Base class for all traders in the arena.
    Handles balance, positions, and basic trading operations.
    """
    def __init__(self, name, initial_balance=50000.0):
        self.id = str(uuid.uuid4())[:8]
        self.name = name
        self.balance = initial_balance
        self.initial_balance = initial_balance
        self.inventory = {} # Dict: ticker -> quantity
        self.pnl_history = [0.0]  # Start with 0 PnL
        self.is_bankrupt = False

    def decide(self, galaxy_state):
        """
        Input: galaxy_state = { 'CORE': {...}, 'TECH': {...} }
        Output: List of dicts [{'side': 'buy', 'size': 10, 'ticker': 'CORE'}, ...]
        Override this method in subclasses.
        """
        return []

    def update_portfolio(self, current_prices):
        """
        Update PnL based on current market prices.
        current_prices: dict {ticker: price}
        """
        # Calculate total equity (cash + positions)
        equity = self.balance
        for ticker, qty in self.inventory.items():
            price = current_prices.get(ticker, 0)
            equity += qty * price
            
        # Calculate PnL vs initial balance
        pnl = equity - self.initial_balance
        self.pnl_history.append(pnl)
        
        # Check bankruptcy
        if equity <= 0:
            self.is_bankrupt = True
            
        return equity

    def execute_trade(self, side, size, price, ticker='CORE'):
        """
        Execute a trade order.
        Returns True if successful, False if failed.
        """
        if self.is_bankrupt: 
            return False
        
        cost = size * price
        
        if side == 'buy':
            if self.balance >= cost:
                self.balance -= cost
                self.inventory[ticker] = self.inventory.get(ticker, 0) + size
                return True
            else:
                return False  # Insufficient funds
                
        elif side == 'sell':
            # Allow short selling (for simplicity)
            self.balance += cost
            self.inventory[ticker] = self.inventory.get(ticker, 0) - size
            return True
            
        return False

    def __repr__(self):
        current_pnl = self.pnl_history[-1] if self.pnl_history else 0
        return f"<{self.name} (${self.balance:.0f}, PnL: {current_pnl:.0f})>"
