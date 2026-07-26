from typing import Dict, Optional, List
from datetime import datetime
from incubator.physics import PhysicsCore, HydroFractalEngine
import numpy as np

# --- DOCUMENTATION REFERENCES ---
# Universe Manager: Market Brain/Backend/Universe Manager.md
# Fluid Dynamics:   Market Brain/Concepts/Fluid Dynamics.md
# --------------------------------

class UniverseManager:
    """
    Manages the 'universe' of tradable assets.

    Responsibilities:
    - Instantiate and route ticks to PhysicsCore engines per symbol.
    - Maintain recent price/volume history per symbol.
    - Compute simple global metrics (e.g. market return) and surface them to engines.
    """
    def __init__(self):
        self.engines: Dict[str, PhysicsCore] = {}
        self.active_symbol: str = "BTCUSDT"
        self.correlation_matrix = None
        self.simulation = SimulationManager()
        self.price_data: Dict[str, List[float]] = {}
        self.volume_data: Dict[str, List[float]] = {}
        
    def get_engine(self, symbol: str) -> PhysicsCore:
        """
        Get or create a PhysicsCore engine for a specific symbol.
        """
        if symbol not in self.engines:
            # Initialize new engine
            self.engines[symbol] = PhysicsCore()
            
        return self.engines[symbol]
        
    def set_active_symbol(self, symbol: str):
        self.active_symbol = symbol
        # Ensure engine exists
        self.get_engine(symbol)
        
    def get_active_engine(self) -> PhysicsCore:
        return self.get_engine(self.active_symbol)

    def ingest_tick(self, symbol: str, timestamp: float, price: float, volume: float, is_buyer_maker: bool):
        """
        Route incoming tick to the correct engine.
        """
        engine = self.get_engine(symbol)
        
        # Store price and volume data
        if symbol not in self.price_data:
            self.price_data[symbol] = []
            self.volume_data[symbol] = []
            
        self.price_data[symbol].append(price)
        self.volume_data[symbol].append(volume)
        
        # Keep only recent data (last 1000 points)
        if len(self.price_data[symbol]) > 1000:
            self.price_data[symbol] = self.price_data[symbol][-1000:]
            self.volume_data[symbol] = self.volume_data[symbol][-1000:]
        
        # Update Global Market Index
        self.update_market_index()
        
    def get_global_metrics(self):
        """
        Calculate global metrics across the universe.
        (Placeholder for v0.3)
        """
        return {
            "active_symbol": self.active_symbol,
            "universe_size": len(self.engines)
        }

    def update_market_index(self):
        """
        Calculate the 'Market Index' (Mean Return of all assets)
        and push it to all engines for Sympathy calculation.
        """
        returns = []
        for symbol in self.price_data:
            prices = self.price_data[symbol]
            if len(prices) >= 2:
                # Calculate last log return
                p_now = prices[-1]
                p_prev = prices[-2]
                if p_prev > 0:
                    ret = np.log(p_now / p_prev)
                    returns.append(ret)
        
        if returns:
            market_ret = np.mean(returns)
            # Store market return (could be used by engines later)
            self.market_return = market_ret

class SimulationManager:
    """
    Manages the simulation engine that advances "relativistic" simulation time.

    Handles volume-based sub-stepping and orchestrates the HydroFractalEngine to produce
    synthetic price steps without scaling the timestep (avoids numerical instability).
    """
    def __init__(self):
        self.clock = 0.0
        self.speed_multiplier = 1.0
        self.is_running = False
        self.dt = 0.01
        # The Engine (The "Matrix")
        self.engine = HydroFractalEngine()
        
    def tick(self, volume_intensity):
        """
        Advance simulation by one relativistic step.
        volume_intensity: 0.0 to 1.0 (Normalized Volume)
        """
        if not self.is_running: 
            return 0.0
        
        # RELATIVISTIC TIME DILATION (Corrected)
        # High Volume = High Gravity = More Events per Second (Sub-Stepping)
        # We do NOT scale dt (instability). We scale the NUMBER of steps.
        
        base_steps = 1
        # Map intensity 0..1 to 0..5 extra steps
        extra_steps = int(volume_intensity * 5.0)
        total_steps = base_steps + extra_steps
        
        last_price = 0.0
        for _ in range(total_steps):
            # Simple price simulation step
            last_price = self.simulate_price_step()
            self.clock += self.dt # Track simulation time
            
        return last_price
        
    def simulate_price_step(self):
        """Simple price simulation step."""
        # Basic random walk with some physics influence
        random_component = np.random.normal(0, 0.01)
        physics_component = self.engine.physics_core.mass * 0.001
        return random_component + physics_component

    def apply_regime(self, regime: str):
        """
        Apply Market Regime to Simulation Physics.
        Prophet -> Simulation Feedback Loop.
        """
        if regime == "TRENDING":
            # Low Friction, let it run
            self.engine.turbulence_factor = 0.02
            self.speed_multiplier = 1.5
        elif regime == "MEAN_REVERTING":
            # High Friction, rubber band
            self.engine.turbulence_factor = 0.2
            self.speed_multiplier = 0.8

# --- SINGLETON ACCESSOR ---
_universe_instance = None

def get_universe_manager():
    global _universe_instance
    if _universe_instance is None:
        _universe_instance = UniverseManager()
    return _universe_instance
