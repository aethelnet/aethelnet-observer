from ..base_trader import BaseTrader
from ...services.brain import ProphitEngine
import numpy as np
import random

# Try to import XGBoost, fallback if not available
try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

class PredatorTrader(BaseTrader):
    """
    Uses Machine Learning (XGBoost) to predict short-term price movements.
    Hunts for patterns created by other traders.
    """
    def __init__(self, name="Predator", initial_balance=50000.0):
        super().__init__(name, initial_balance)
        self.models = {}  # ticker -> XGBRegressor
        self.histories = {}  # ticker -> list of prices
        self.last_train = {}  # ticker -> int
        self.train_interval = 100  # Retrain every 100 ticks

    def decide(self, galaxy_state):
        orders = []
        
        for ticker, state in galaxy_state.items():
            price = state['price']
            
            if ticker not in self.histories:
                self.histories[ticker] = []
                self.last_train[ticker] = 0
                
            self.histories[ticker].append(price)
            history = self.histories[ticker]
            
            # Need enough data
            if len(history) < 30: continue
            
            # Feature Engineering (Simple lags)
            window = 20
            X = []
            y = []
            returns = np.diff(history)
            
            # Train Model (Retrain every 100 ticks)
            if HAS_XGB and len(history) - self.last_train[ticker] > 100:
                for i in range(len(returns) - window):
                    X.append(returns[i:i+window])
                    y.append(returns[i+window])
                    
                if len(X) > 10:
                    # GPU ACCELERATION & VRAM USAGE
                    try:
                        model = xgb.XGBRegressor(
                            n_estimators=500, 
                            max_depth=12, 
                            learning_rate=0.05,
                            verbosity=0, 
                            device='cuda',
                            tree_method='hist' 
                        )
                        model.fit(np.array(X), np.array(y))
                        self.models[ticker] = model
                    except Exception as e:
                        # Fallback to CPU if CUDA fails
                        # print(f"GPU Init Failed for {ticker}: {e}. Falling back to CPU.")
                        model = xgb.XGBRegressor(n_estimators=100, max_depth=6, verbosity=0, n_jobs=1)
                        model.fit(np.array(X), np.array(y))
                        self.models[ticker] = model
                        
                    self.last_train[ticker] = len(history)
            
            # Predict
            if ticker in self.models and len(returns) >= window:
                last_window = np.array([returns[-window:]])
                pred_return = self.models[ticker].predict(last_window)[0]
                
                if pred_return > 0.001:
                    orders.append({'side': 'buy', 'size': 10.0, 'ticker': ticker})
                elif pred_return < -0.001:
                    orders.append({'side': 'sell', 'size': 10.0, 'ticker': ticker})
                    
        return orders

class MathWizTrader(BaseTrader):
    """
    Uses FFT to find cycles.
    """
    def __init__(self, name="Fourier", initial_balance=50000.0):
        super().__init__(name, initial_balance)
        self.window_size = 256
        self.histories = {}

    def decide(self, galaxy_state):
        orders = []
        
        for ticker, state in galaxy_state.items():
            price = state['price']
            if ticker not in self.histories: self.histories[ticker] = []
            self.histories[ticker].append(price)
            
            history = self.histories[ticker]
            if len(history) < self.window_size: continue
            
            # FFT Logic
            data = np.array(history[-self.window_size:])
            # Detrend
            data_detrended = data - np.mean(data)
            fft_vals = np.fft.rfft(data_detrended)
            # Filter high freq noise
            fft_vals[int(len(fft_vals)*0.8):] = 0
            # Reconstruct
            reconstructed = np.fft.irfft(fft_vals, n=self.window_size)
            
            # Predict next step (slope at end)
            slope = reconstructed[-1] - reconstructed[-2]
            
            if slope > 0.1:
                orders.append({'side': 'buy', 'size': 5.0, 'ticker': ticker})
            elif slope < -0.1:
                orders.append({'side': 'sell', 'size': 5.0, 'ticker': ticker})
                
        return orders

class WhaleTrader(BaseTrader):
    """
    Accumulates slowly, then dumps.
    """
    def __init__(self, name="MobyDick", initial_balance=1000000.0):
        super().__init__(name, initial_balance)
        self.mode = 'accumulate'
        self.target_inventory = 1000
        self.count = 0

    def decide(self, galaxy_state):
        orders = []
        self.count += 1
        
        # Focus on CORE ticker for simplicity
        core_state = galaxy_state.get('CORE')
        if not core_state:
            return orders
            
        current_position = self.inventory.get('CORE', 0)
        
        if self.mode == 'accumulate':
            if current_position < self.target_inventory:
                # Buy small chunks to not spike price too much yet
                orders.append({'side': 'buy', 'size': 10.0, 'ticker': 'CORE'})
            else:
                self.mode = 'dump'
                self.count = 0
                
        elif self.mode == 'dump':
            # Dump hard to crash price
            if current_position > 0:
                orders.append({'side': 'sell', 'size': 50.0, 'ticker': 'CORE'})
            else:
                self.mode = 'wait'
                
        elif self.mode == 'wait':
            if self.count > 50:  # Wait for dust to settle
                self.mode = 'accumulate'
                
        return orders

class NemesisTrader(BaseTrader):
    """
    The Anti-Hero.
    Has the ProphitEngine but uses it for selfish gain.
    Knows the 'True Path' and front-runs it.
    """
    def __init__(self, name="Nemesis", initial_balance=50000.0):
        super().__init__(name, initial_balance)
        self.engine = ProphitEngine()
        # Nemesis has a well-tuned engine from the start
        self.config = {
            'decay': 0.741,
            'base_drag': 0.499,
            'base_spring': 0.0015
        }

    def decide(self, galaxy_state):
        orders = []
        
        # Focus on CORE ticker
        core_state = galaxy_state.get('CORE')
        if not core_state:
            return orders
            
        price = core_state['price']
        time = core_state['time']
        
        # Ingest
        volume = 100.0
        if core_state.get('history', {}).get('volume'):
            volume = core_state['history']['volume'][-1]
            
        self.engine.ingest_candle(time, price, volume)
        
        # Predict (using compute_projection which returns signal/confidence, not prices)
        projection = self.engine.compute_projection()
        
        if not projection:
            return orders
            
        signal = projection.get('signal', 0.0)
        confidence = projection.get('confidence', 0.0)
        
        # Aggressive Trading - lower threshold than Hero
        threshold = 0.002
        if abs(signal) > threshold and confidence > 0.3:
            side = 'buy' if signal > 0 else 'sell'
            size = 20.0  # Larger size
            orders.append({'side': side, 'size': size, 'ticker': 'CORE'})
            
        return orders
