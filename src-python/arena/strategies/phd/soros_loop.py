from ...api import IStrategy
import numpy as np
import pandas as pd

class TheSorosLoop(IStrategy):
    """
    The Soros Loop (Reflexivity).
    
    Concept:
        George Soros' Theory of Reflexivity: Price can alter Fundamentals.
        In Crypto, this is true: Higher Unit Price = Higher Network Security/Adoption = Higher Price.
        This feedback loop creates self-reinforcing Bubbles.
        
    Mechanic:
        - Detect "Giffen Good" behavior:
            - Standard Goods: Price Up -> Demand (Volume) Down.
            - Reflexive Goods: Price Up -> Demand (Volume) UP.
        - Measures Correlation(DeltaPrice, DeltaVolume).
        - If Correlation > 0.8 (Positive Feedback Loop):
            - ENTER PARABOLIC LONG.
        - Exit when Correlation breaks (Negative Feedback returns).
    """
    @property
    def name(self) -> str:
        return "The Soros Loop"

    @property
    def class_type(self) -> str:
        return "ECONOMIST"

    def __init__(self):
        super().__init__()
        self.skills = {
            "window": 20, 
            "reflexivity_thresh": 0.7, # Correlation coeff
            "momentum_thresh": 0.02 # Min movement to filter noise
        }
        
    def on_tick(self, packet: dict) -> float:
        return 0.0
        
    def next_candle(self, df: pd.DataFrame) -> float:
        if len(df) < self.skills['window'] + 5:
            return 0.0
            
        close = df['close']
        volume = df['volume']
        
        # 1. Calculate Deltas (Percent Change)
        # We want to see if +Price => +Volume (Buying into strength)
        
        d_price = close.pct_change()
        d_vol = volume.pct_change()
        
        # 2. Measure Correlation over window
        window = int(self.skills['window'])
        
        # Rolling correlation
        corr = d_price.rolling(window).corr(d_vol).iloc[-1]
        
        # 3. Check for Momentum (Are we actually moving?)
        recent_move = (close.iloc[-1] - close.iloc[-window]) / close.iloc[-window]
        
        action = "HOLD"
        
        # If Price rising AND Volume rising (Corr > X) => BUBBLE INFLATING => BUY.
        # If Price falling AND Volume rising (Corr < -X?) => PANIC SELLING => SELL.
        # Soros focuses on the Bubble Up.
        
        is_reflexive = corr > self.skills['reflexivity_thresh']
        
        signal = 0.0

        if is_reflexive:
            if recent_move > self.skills['momentum_thresh']:
                # Positive Feedback Loop (Up)
                signal = 1.0
            elif recent_move < -self.skills['momentum_thresh']:
                # Positive Feedback Loop (Down) - Death Spiral
                signal = -1.0
                
        # What if Negative Correlation?
        # Price Up (+), Vol Down (-) => Divergence (Weakness) => standard tech analysis bearish dive.
        # Price Down (-), Vol Up (+) => Capitulation / Panic Sales.
        
        # Soros Strategy is purely surfing the Positive Correlation Wave.
        
        return signal

    def get_raw_reflexivity(self, df: pd.DataFrame) -> float:
        """Exposes the raw Price-Volume Correlation (tanh-saturated) for Neural Training."""
        if len(df) < self.skills['window'] + 5: return 0.0
        
        # Calculate Rolling Correlation
        d_price = df['close'].pct_change()
        d_vol = df['volume'].pct_change()
        
        window = int(self.skills['window'])
        corr = d_price.rolling(window).corr(d_vol).iloc[-1]
        
        if np.isnan(corr): return 0.0
        
        # Soft Saturation (tanh) to normalize gradient intensity
        # We also boost it slightly to make the 'reflexive' zone more distinct
        return float(np.tanh(corr * 1.5))

    def evolve(self, mutation_rate: float = 0.1) -> 'IStrategy':
        child = TheSorosLoop()
        child.skills['reflexivity_thresh'] = np.clip(self.skills['reflexivity_thresh'] + np.random.normal(0, 0.05), 0.1, 0.99)
        return child
