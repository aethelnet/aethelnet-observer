from typing import Dict, Any
from arena.api import IStrategy

class TheTurtle(IStrategy):
    """
    The Follower.
    Slow. Steady.
    "Trend is friend."
    """
    @property
    def name(self) -> str:
        return "The Turtle"

    @property
    def class_type(self) -> str:
        return "Tank"

    def next_candle(self, df) -> float:
        # True Turtle: Buy 20-Day High, Sell 10-Day Low.
        # We assume 'df' has 'high', 'low', 'close'.
        
        if len(df) < 21: return 0.0
        
        # Donchian 20
        high_20 = df['high'].iloc[-21:-1].max()
        low_20 = df['low'].iloc[-21:-1].min()
        current_close = df['close'].iloc[-1]
        
        if current_close > high_20:
            return 1.0 # Breakout Long
        elif current_close < low_20:
            return -1.0 # Breakout Short
            
        # Exit logic could be 10-day, but for single-signal API:
        return 0.0

    def on_tick(self, market_state: Dict[str, Any]) -> float:
        # Fallback if no history (Tick-based)

        
        
        regime = market_state.get('regime', 'unknown')
        # [FIX] Use trend_strength from Brain (Standardized)
        trend_dir = market_state.get('trend_strength', 0.0) 
        
        # Accept 'Trending' string or Regime ID 2 (if used in legacy)
        # Also accept standard Brain regimes if they imply trend (JOY/SAD are handled by trend_strength != 0)
        
        if abs(trend_dir) > 0.1:
             return float(trend_dir) * 0.8 # Strong commitment
            
        # In chop, Turtle hides in shell
        return 0.0
