import numpy as np
from .market import Market
from .scenarios import ScenarioGenerator

class MarketGalaxy:
    """
    Simulates a galaxy of interconnected markets with correlations.
    """
    def __init__(self, scenario_gen=None, config=None):
        self.config = config if config else {}
        self.contagion_factor = self.config.get('contagion_factor', 1.0)
        
        self.tickers = ['CORE', 'TECH', 'ENERGY', 'GOLD', 'CRYPTO']
        self.markets = {}
        
        # Initialize Markets
        for ticker in self.tickers:
            # Each market gets its own scenario instance (or shared?)
            # For now, let's give them slightly different flavors of the same scenario
            if scenario_gen:
                scenario = scenario_gen(duration=2000)
                self.markets[ticker] = Market(scenario=scenario)
            else:
                self.markets[ticker] = Market()
                
        # Correlation Matrix (Target)
        # CORE, TECH, ENERGY, GOLD, CRYPTO
        self.correlation_matrix = np.array([
            [1.0,  0.8,  0.4, -0.3,  0.2], # CORE
            [0.8,  1.0,  0.3, -0.4,  0.6], # TECH
            [0.4,  0.3,  1.0,  0.1,  0.1], # ENERGY
            [-0.3,-0.4,  0.1,  1.0,  0.2], # GOLD
            [0.2,  0.6,  0.1,  0.2,  1.0]  # CRYPTO
        ])
        
        # Cholesky Decomposition for correlated noise generation
        self.L = np.linalg.cholesky(self.correlation_matrix)
        
    def get_state(self):
        """
        Returns the state of the entire galaxy.
        """
        galaxy_state = {}
        for ticker, market in self.markets.items():
            galaxy_state[ticker] = market.get_state()
        print(f"GALAXY STATE: {list(galaxy_state.keys())}")
        return galaxy_state
        
    def step(self, orders):
        """
        Evolve the galaxy.
        orders: List of dicts, each must have 'ticker'
        """
        # 1. Distribute Orders
        market_orders = {t: [] for t in self.tickers}
        for order in orders:
            ticker = order.get('ticker', 'CORE') # Default to CORE
            if ticker in market_orders:
                market_orders[ticker].append(order)
                
        # 2. Generate Correlated Noise (The "Vibe" of the market)
        # Generate uncorrelated random noise
        uncorrelated_noise = np.random.normal(0, 0.005, len(self.tickers))
        # Apply Cholesky matrix to get correlated noise
        correlated_noise = np.dot(self.L, uncorrelated_noise)
        
        # 3. Apply Contagion / Cosmic Weather
        # Check if any market is crashing (e.g. CORE drops > 2%)
        core_return = correlated_noise[0] # CORE is index 0
        
        contagion_factor = 1.0
        if core_return < -0.02: # CORE Crash
            print(f"!!! GALAXY CONTAGION DETECTED !!! Core Return: {core_return:.4f}")
            contagion_factor = 2.0 # Panic multiplier
            # Force TECH and CRYPTO down
            correlated_noise[1] -= 0.01 # TECH hit
            correlated_noise[4] -= 0.03 # CRYPTO nuke
            # Flight to safety
            correlated_noise[3] += 0.01 # GOLD pump
            
        # 4. Step Each Market
        for i, ticker in enumerate(self.tickers):
            market = self.markets[ticker]
            
            # Inject the correlated drift into the market
            # We need to update Market.step to accept this external drift
            # For now, we'll hack it by modifying the price directly before step
            # Or better, pass it as a parameter if we modify market.py
            
            # Applying drift directly to price for now (simplest integration)
            market.price *= (1 + correlated_noise[i] * contagion_factor)
            
            market.step(market_orders[ticker])
            
        return self.get_state()
