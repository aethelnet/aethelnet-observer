from arena.api import IStrategy
import pandas as pd
import numpy as np
import math

class TheEntropyStrategy(IStrategy):
    """
    Metaphor: The Alchemist of Chaos
    Context Case: 3 (Alchemist / Chaos / Biology)
    Logic Structure: STATE_MACHINE
    
    Description:
        This strategy acts as an Alchemist, analyzing the 'elemental' composition 
        of the market using Shannon Entropy. It operates as a State Machine with 
        two primary states:
        1. ORDER (Gold): Low Entropy. The market is structured. We Follow Trends.
        2. CHAOS (Lead): High Entropy. The market is random noise. We Mean Revert.
        
        The strategy dynamically transmutes its logic based on the detected regime.
    """

    @property
    def name(self) -> str:
        return "The Alchemist of Chaos"

    @property
    def class_type(self) -> str:
        return "CUSTOM"

    def __init__(self):
        super().__init__()
        # Hyperparameters (The Alchemist's Formulas)
        # These are the 'genes' that will be mutated by the evolutionary loop.
        self.skills = {
            "lookback_window": 50,      # The sample size for entropy calculation
            "entropy_threshold": 0.65,  # The tipping point between Order and Chaos (0.0 to 1.0)
            "risk_tolerance": 0.8,      # Base allocation size
            "volatility_sensitivity": 1.5
        }
        self.current_state = "INITIALIZING"

    def _calculate_shannon_entropy(self, close_prices: pd.Series) -> float:
        """
        Calculates the Shannon Entropy of the return distribution over the lookback window.
        
        Formula: H(X) = - Sum( p(x) * log2(p(x)) )
        
        Returns:
            float: Normalized Entropy between 0.0 (Pure Order) and 1.0 (Max Chaos)
        """
        if len(close_prices) < 2:
            return 1.0
            
        # 1. Calculate Logarithmic Returns to standardize the data
        returns = np.log(close_prices / close_prices.shift(1)).dropna()
        
        # 2. Discretize the returns into bins (Histogram)
        # We use a fixed number of bins (10) to ensure consistency in entropy range.
        try:
            hist, _ = np.histogram(returns, bins=10, density=True)
        except ValueError:
            return 1.0 # Default to max entropy if calculation fails (safety fallback)
            
        # 3. Calculate Probabilities (normalize the histogram)
        probs = hist / np.sum(hist)
        
        # 4. Filter out zero probabilities to avoid log(0) errors
        probs = probs[probs > 0]
        
        # 5. Compute Shannon Entropy
        entropy = -np.sum(probs * np.log2(probs))
        
        # 6. Normalize Entropy to [0, 1] range
        # The maximum entropy for N bins is log2(N). For 10 bins, log2(10) approx 3.32
        max_entropy = np.log2(10)
        normalized_entropy = entropy / max_entropy
        
        return max(0.0, min(1.0, normalized_entropy))

    def next_candle(self, df: pd.DataFrame) -> float:
        """
        Logic Structure: STATE_MACHINE (Case 3)
        
        Behavior:
            1. Detect Regime (Order vs Chaos) via Entropy.
            2. Switch internal State.
            3. Execute logic specific to that State.
        """
        # Data sufficiency check
        if len(df) < self.skills['lookback_window']:
            return 0.0

        # --- PHASE 1: REGIME DETECTION (The Transmutation) ---
        # Extract the window for analysis
        window = df['close'].iloc[-self.skills['lookback_window']:]
        
        # Calculate the Entropy of the current market window
        entropy = self._calculate_shannon_entropy(window)
        
        # Determine the Mental State based on the threshold
        if entropy < self.skills['entropy_threshold']:
            self.current_state = "ORDER"
        else:
            self.current_state = "CHAOS"
            
        # --- PHASE 2: STATE EXECUTION ---
        
        # CASE A: ORDER (The Golden State)
        # Hypothesis: Trends are persistent. Momentum is valid.
        # Logic: Trend Following (Exponential Moving Average Crossover)
        if self.current_state == "ORDER":
            # Calculate EMA (Exponential Moving Average)
            ema = df['close'].ewm(span=20, adjust=False).mean().iloc[-1]
            current_price = df['close'].iloc[-1]
            
            # If Price is above average, we assume a Bullish Trend -> LONG
            if current_price > ema:
                return self.skills['risk_tolerance']
            # If Price is below average, we assume a Bearish Trend -> SHORT
            elif current_price < ema:
                return -self.skills['risk_tolerance']
                
        # CASE B: CHAOS (The Lead State)
        # Hypothesis: Moves are random noise. Extremes will revert to the mean.
        # Logic: Mean Reversion (Bollinger Bands)
        elif self.current_state == "CHAOS":
            # Calculate Bollinger Bands
            rolling_mean = df['close'].rolling(window=20).mean().iloc[-1]
            rolling_std = df['close'].rolling(window=20).std().iloc[-1]
            upper_band = rolling_mean + (2 * rolling_std)
            lower_band = rolling_mean - (2 * rolling_std)
            current_price = df['close'].iloc[-1]
            
            # If Price > Upper Band, it's an overextension (Noise) -> SHORT
            if current_price > upper_band:
                # In Chaos, we reduce position size (0.5x) as risk is higher
                return -0.5 * self.skills['risk_tolerance']
            # If Price < Lower Band, it's an overextension (Noise) -> LONG
            elif current_price < lower_band:
                return 0.5 * self.skills['risk_tolerance']
        
        # Default neutral position
        return 0.0

    def on_tick(self, df: pd.DataFrame) -> float:
        """
        Required by IStrategy interface.
        For The Entropy Strategy, we treat ticks same as candles for now, or just return 0.
        """
        return self.next_candle(df)

    def evolve(self, mutation_rate: float = 0.1):
        """
        Genetic Evolution Hook.
        Creates a new 'Child' strategy with slightly mutated perception of Entropy.
        """
        child = TheEntropyStrategy()
        
        # Mutate the Entropy Threshold
        # A higher threshold makes the Alchemist see "Order" more easily (more aggressive).
        # A lower threshold makes the Alchemist see "Chaos" everywhere (more defensive).
        mutation = np.random.normal(0, 0.05)
        new_threshold = self.skills['entropy_threshold'] + mutation
        
        # Clamp values to safe ranges
        child.skills['entropy_threshold'] = max(0.1, min(0.9, new_threshold))
        
        # Mutate Risk Tolerance
        risk_mutation = np.random.normal(0, 0.05)
        child.skills['risk_tolerance'] = max(0.1, min(1.0, self.skills['risk_tolerance'] + risk_mutation))
        
        return child


