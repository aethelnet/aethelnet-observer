from ...api import IStrategy
import numpy as np
import pandas as pd

class TheMinskyMoment(IStrategy):
    """
    The Minsky Moment (Crisis Detector).
    
    Concept:
        "Stability breeds Instability." - Hyman Minsky.
        Long periods of low volatility encourage leverage buildup.
        When the trend inevitably breaks, the unwind is violent (The Moment).
        
    Mechanic:
        - Detect "Stability Regime": Low Volatility (ATR) + Low ADX (Consolidation) for > N bars.
        - Measure "Leverage Proxy": Since we don't have Open Interest in this simple sim, we use 
          Volume/Volatility Divergence. (High Vol, Low Volatility = Hidden Leverage).
        - Trigger: Sudden deviation > 2 Sigma (The Crack).
        - Action: Aggressive SHORT.
    """
    @property
    def name(self) -> str:
        return "The Minsky Moment"

    @property
    def class_type(self) -> str:
        return "ECONOMIST"

    def __init__(self):
        super().__init__()
        self.skills = {
            "stability_window": 50, # How long must it be quiet?
            "volatility_threshold": 0.02, # Max ATR% to consider "Stable"
            "crack_sensitivity": 2.5, # Sigma deviation to trigger crash
            "leverage_buildup": 0.0 # Internal tracking var
        }
        
    def on_tick(self, packet: dict) -> dict:
        return {"action": "HOLD"}
        
    def next_candle(self, df: pd.DataFrame) -> dict:
        if len(df) < self.skills['stability_window'] + 5:
            return {"action": "HOLD"}
            
        # 1. Measure Stability (Rolling Volatility)
        close = df['close'].values
        volume = df['volume'].values
        log_rets = np.log(close[1:] / close[:-1])
        
        window = int(self.skills['stability_window'])
        vol_series = pd.Series(log_rets).rolling(window=window).std()
        current_vol = vol_series.iloc[-1]
        
        # 2. Leverage Divergence (Volume vs Volatility)
        # High volume during low volatility indicates massive hidden accumulation/leverage.
        avg_vol = pd.Series(volume).rolling(window=window).mean().iloc[-1]
        vol_z = (volume[-1] - avg_vol) / (pd.Series(volume).rolling(window=window).std().iloc[-1] + 1e-9)
        
        # Stability check (< 0.02% move per bar)
        is_stable = current_vol < (self.skills['volatility_threshold'] / 100.0)
        
        # 3. The "Great Moderation" Buildup (EMA based for the Champion)
        # We increase buildup faster if volume is high during stability (Divergence)
        alpha = 0.1
        increment = (1.5 if vol_z > 1.0 else 1.0) if is_stable else -2.0
        self.skills['leverage_buildup'] = max(0, min(window, self.skills['leverage_buildup'] + increment))
        
        # 4. The Crack (Minsky Moment)
        if self.skills['leverage_buildup'] > (window * 0.4): # Threshold reached
            mean = close[-window:].mean()
            std = close[-window:].std()
            z_score = (close[-1] - mean) / (std + 1e-9)
            
            if z_score < -self.skills['crack_sensitivity']:
                return {"action": "SELL", "confidence": "HIGH", "reason": "MINSKY_MOMENT_DOWN"}
                
        return {
            "action": "HOLD", 
            "stability": current_vol, 
            "buildup": self.skills['leverage_buildup'] / window, # Normalized for logs
            "divergence": vol_z if is_stable else 0.0
        }

    def get_raw_instability(self, df: pd.DataFrame) -> float:
        """Exposes the raw Leverage Buildup (normalized) for Neural Training."""
        if len(df) < self.skills['stability_window'] + 5: return 0.0
        
        closes = df['close'].values
        volume = df['volume'].values
        log_rets = np.log(closes[1:] / closes[:-1])
        window = int(self.skills['stability_window'])
        
        vol_series = pd.Series(log_rets).rolling(window=window).std()
        avg_vol_series = pd.Series(volume).rolling(window=window).mean()
        std_vol_series = pd.Series(volume).rolling(window=window).std()
        
        buildup = 0
        thresh = self.skills['volatility_threshold'] / 100.0
        
        # Replay the logic through the window for accurate training features
        # Note: In production, we use the stateful self.skills['leverage_buildup'].
        # For training data (Hindsight), we must reconstruct it.
        for i in range(window, len(vol_series)):
            v = vol_series.iloc[i]
            vol_z = (volume[i] - avg_vol_series.iloc[i]) / (std_vol_series.iloc[i] + 1e-9)
            
            is_stable = v < thresh
            increment = (1.5 if vol_z > 1.0 else 1.0) if is_stable else -2.0
            buildup = max(0, min(window, buildup + increment))
            
        return float(min(1.0, buildup / window))

    def evolve(self, mutation_rate: float = 0.1) -> 'IStrategy':
        child = TheMinskyMoment()
        child.skills['stability_window'] = int(self.skills['stability_window'] * np.random.normal(1, mutation_rate))
        return child
