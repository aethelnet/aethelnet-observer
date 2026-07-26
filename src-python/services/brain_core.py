import numpy as np
import logging
import threading
from typing import Optional, Dict
from collections import deque
from core.logger import get_logger

logger = get_logger("BrainCore")

class BrainEngine:
    """
    The Core Brain Engine (Open Source Version).
    Provides basic market data tracking and RSI calculation.
    Does NOT contain proprietary decision models or signals.
    """
    
    def __init__(self, symbol: str = "BTCUSDC"):
        self.states: Dict[str, Dict] = {}
        self.current_symbol = symbol
        self.running_volatility = 0.0
        self.current_regime = "CORE_MODE"

    def _get_state(self, symbol: str) -> Dict:
        """Get or create state for a symbol."""
        if symbol not in self.states:
            self.states[symbol] = {
                'price_history': [],
                'volume_history': [],
                'timestamp_history': [],
                'regime': 'CORE_MODE'
            }
        return self.states[symbol]
        
    def ingest_candle(self, timestamp_ms: int, close_price: float, volume: float, symbol: str = "BTCUSDC"):
        """Ingest a new candle (Basic Tracker)."""
        try:
            self.current_symbol = symbol
            state = self._get_state(symbol)

            state['timestamp_history'].append(int(timestamp_ms))
            state['price_history'].append(float(close_price))
            state['volume_history'].append(float(volume))

            # Maintain history limit
            if len(state['price_history']) > 1000:
                state['price_history'] = state['price_history'][-1000:]
                state['volume_history'] = state['volume_history'][-1000:]
                state['timestamp_history'] = state['timestamp_history'][-1000:]
                
        except Exception as e:
            logger.error(f"Error ingesting candle for {symbol}: {e}")

    def ingest_sentiment(self, symbol: str, bias: float):
        """Ingest sentiment (Stub)."""
        pass

    def compute_projection(self, lookahead=1, symbol: str = None):
        """
        Compute market projection.
        In CORE mode, this returns a neutral signal.
        """
        return {
            "signal": 0.0, 
            "confidence": 0.0, 
            "regime": "CORE_MODE",
            "volatility": 0.0,
            "phase": 0.0,
            "target_price": 0.0,
            "stop_loss": 0.0,
            "take_profit": 0.0
        }

    def get_divine_metrics(self, symbol: str = None) -> Dict:
        """Return basic metrics."""
        return {
            "regime": "CORE_MODE",
            "symbol": symbol or self.current_symbol
        }

    def check_volume_support(self, symbol: str = None) -> bool:
        """
        Check if the current candle has volume support (Volume > Moving Average).
        Used as a safety filter to avoid 'fakeouts' (price moves on low volume).
        """
        try:
            if not symbol: symbol = self.current_symbol
            state = self._get_state(symbol)
            volumes = state['volume_history']
            
            if len(volumes) < 20: return True # Not enough data, default safe (allow) to avoid blocking startup
            
            # Simple Moving Average (20)
            avg_vol = sum(volumes[-21:-1]) / 20.0
            current_vol = volumes[-1]
            
            # Require volume to be at least 80% of average (tolerant) or strictly > average
            # Let's be moderately strict: > 80% of average
            return current_vol > (avg_vol * 0.8)
            
        except Exception:
            return True # Fail open to avoid paralysis

    def calculate_rsi(self, period: int = 14, symbol: str = None) -> float:
        """Standard RSI Calculation."""
        try:
            if not symbol:
                symbol = self.current_symbol
                
            state = self._get_state(symbol)
            prices = state['price_history']
            
            if len(prices) < period + 1:
                return 50.0

            arr = np.array(prices, dtype=float)
            deltas = np.diff(arr)
            gains = np.where(deltas > 0, deltas, 0.0)
            losses = np.where(deltas < 0, -deltas, 0.0)

            avg_gain = float(np.mean(gains[-period:])) if gains.size >= period else float(np.mean(gains))
            avg_loss = float(np.mean(losses[-period:])) if losses.size >= period else float(np.mean(losses))

            if avg_gain == 0 and avg_loss == 0: return 50.0
            if avg_loss == 0: return 100.0

            rs = avg_gain / avg_loss
            rsi = 100.0 - (100.0 / (1.0 + rs))
            return float(rsi)
        except Exception:
            return 50.0

    def load_historical_z_scores(self, symbol: str = "BTCUSDC", limit: int = 1000):
        """Stub."""
        return 0

    def warm_up(self, symbol: str, limit: int = 50):
        """Stub."""
        return 0

# Global instance
_engine_instance: Optional[BrainEngine] = None

def get_engine() -> BrainEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = BrainEngine()
        logger.info("[BRAIN] Core engine initialized (Open Source Mode)")
    return _engine_instance

class ButterflySensor:
    """Stub for compatibility."""
    def __init__(self):
        self.status = "nominal"
    def get_signal(self, data):
        return 0.0
