import ccxt.async_support as ccxt
import asyncio
import logging
import statistics
import time
from typing import Dict, Optional, List

logger = logging.getLogger("Watchtower")

class Watchtower:
    """
    The Hydra (Phase 46).
    Aggregates data from 5+ exchanges to form a Consensus Reality.
    Now with TTL caching to reduce API calls.
    """
    # Cache TTL in seconds (30s for crypto, 60s for stocks)
    CRYPTO_TTL = 30
    STOCK_TTL = 60
    
    def __init__(self):
        self.exchanges = {
            'kraken': ccxt.kraken(),
            'coinbase': ccxt.coinbase(),
            'okx': ccxt.okx(),
            'bybit': ccxt.bybit(),
            'kucoin': ccxt.kucoin(),
            'gateio': ccxt.gateio()
        }
        # Multi-Market Adaptor
        from services.yahoo_connector import YahooConnector
        self.yahoo = YahooConnector()

        self.latest_snapshot: Dict[str, Dict[str, float]] = {} # {symbol: {exchange: price}}
        self.cache_timestamps: Dict[str, float] = {}  # {symbol: last_fetch_time}
        self.consensus_cache: Dict[str, float] = {}   # {symbol: consensus_price}
        self.outliers: List[str] = []
        self.fracture_index: float = 0.0
        
        # [GHOST CANDLE] Price history for momentum prediction
        self.price_history: Dict[str, List[float]] = {}  # {symbol: [last N prices]}
        self.GHOST_LOOKBACK = 10  # How many candles to use for velocity calc
        self.anomaly_log: List[Dict] = []  # Recent anomalies for debugging
        
        # [GHOST ERROR] Confidence Scaling Parameters
        self.error_history: Dict[str, List[float]] = {}  # {symbol: [last N errors as %]}
        self.ERROR_WINDOW = 20  # Rolling window for error average
        self.MIN_CONFIDENCE_MULT = 0.8   # Conservative: Never bet less than 80%
        self.MAX_CONFIDENCE_MULT = 1.2   # Conservative: Never bet more than 120%
        self.WARMUP_SAMPLES = 20         # Don't scale until we have this many samples

    def _update_price_history(self, symbol: str, price: float):
        """Track price history for Ghost Candle generation."""
        if symbol not in self.price_history:
            self.price_history[symbol] = []
        
        self.price_history[symbol].append(price)
        
        # Keep only last N prices
        if len(self.price_history[symbol]) > self.GHOST_LOOKBACK * 2:
            self.price_history[symbol] = self.price_history[symbol][-self.GHOST_LOOKBACK:]

    def generate_ghost(self, symbol: str) -> tuple:
        """
        [GHOST CANDLE] Generates a predicted 'Ghost Price' based on momentum.
        Returns: (ghost_price, (low_band, high_band))
        """
        history = self.price_history.get(symbol, [])
        
        if len(history) < 3:
            # Not enough data - return neutral (no prediction)
            last = history[-1] if history else 0
            return last, (0, float('inf'))
        
        # Use last N prices
        window = history[-self.GHOST_LOOKBACK:]
        
        # 1. Calculate Velocity (Linear Regression Slope)
        # Simple: (last - first) / n
        n = len(window)
        velocity = (window[-1] - window[0]) / n if n > 1 else 0
        
        # 2. Calculate Volatility (Standard Deviation)
        if len(window) >= 2:
            sigma = statistics.stdev(window)
        else:
            sigma = 0
        
        # 3. Ghost Price = Last + Velocity
        ghost_price = window[-1] + velocity
        
        # 4. Expected Band = Ghost ± 2*Sigma (95% confidence)
        # Add a floor to prevent zero-width bands
        band_width = max(sigma * 2, ghost_price * 0.005)  # At least 0.5% band
        low_band = ghost_price - band_width
        high_band = ghost_price + band_width
        
        return ghost_price, (low_band, high_band)

    def detect_anomaly(self, symbol: str, real_price: float) -> Dict:
        """
        [GHOST CANDLE] Compare reality vs prediction.
        Returns anomaly info if price is outside expected band.
        Also tracks ALL errors for confidence scaling.
        """
        ghost, (low, high) = self.generate_ghost(symbol)
        
        if ghost == 0 or high == float('inf'):
            return {"anomaly": False, "reason": "insufficient_data"}
        
        # [GHOST ERROR] Calculate error regardless of anomaly status
        error_pct = abs(real_price - ghost) / ghost if ghost > 0 else 0
        
        # Track error history for confidence scaling
        if symbol not in self.error_history:
            self.error_history[symbol] = []
        self.error_history[symbol].append(error_pct)
        
        # Trim to window size
        if len(self.error_history[symbol]) > self.ERROR_WINDOW * 2:
            self.error_history[symbol] = self.error_history[symbol][-self.ERROR_WINDOW:]
        
        # [DB PERSIST] Save error for Gen3 training (async, non-blocking)
        try:
            from services.database import get_database
            db = get_database()
            db.insert_analysis(symbol, time.time(), "ghost_error", {
                "error_pct": round(error_pct * 100, 4),
                "ghost": round(ghost, 4),
                "actual": round(real_price, 4)
            })
        except Exception:
            pass  # Non-critical
        
        # Check if real price is outside expected band
        if real_price < low or real_price > high:
            anomaly_info = {
                "anomaly": True,
                "type": "OUT_OF_BAND",
                "symbol": symbol,
                "expected": ghost,
                "expected_range": (round(low, 4), round(high, 4)),
                "actual": real_price,
                "divergence_pct": round(error_pct * 100, 2),
                "timestamp": time.time()
            }
            
            # Log for debugging
            self.anomaly_log.append(anomaly_info)
            if len(self.anomaly_log) > 100:
                self.anomaly_log = self.anomaly_log[-50:]
            
            logger.warning(f"[GHOST] 👻 ANOMALY: {symbol} expected ${ghost:.2f} [{low:.2f}-{high:.2f}], got ${real_price:.2f} ({error_pct*100:.1f}% off)")
            
            return anomaly_info
        
        return {"anomaly": False, "error_pct": round(error_pct * 100, 4)}

    def get_confidence_multiplier(self, symbol: str) -> float:
        """
        [GHOST ERROR] Returns confidence-based position size multiplier.
        
        Logic:
        - Low error = High predictability = Bet MORE (up to 1.2x)
        - High error = Chaos = Bet LESS (down to 0.8x)
        
        Returns 1.0 during warmup period.
        """
        errors = self.error_history.get(symbol, [])
        
        # Warmup: Not enough data to be confident
        if len(errors) < self.WARMUP_SAMPLES:
            return 1.0
        
        # Calculate rolling average error
        recent_errors = errors[-self.ERROR_WINDOW:]
        avg_error = sum(recent_errors) / len(recent_errors) if recent_errors else 0
        current_error = errors[-1] if errors else 0
        
        # Prevent division by zero
        if avg_error < 0.0001:
            avg_error = 0.0001
        
        # Ratio: How does current error compare to baseline?
        # ratio < 1 → Better than average → High confidence
        # ratio > 1 → Worse than average → Low confidence
        ratio = current_error / avg_error
        
        # Invert: Low ratio = High multiplier
        # Map: ratio 0.5 → mult 1.2, ratio 2.0 → mult 0.8
        # Formula: multiplier = 1.0 + (1.0 - ratio) * 0.2
        raw_multiplier = 1.0 + (1.0 - ratio) * 0.2
        
        # Clamp to safety bounds
        multiplier = max(self.MIN_CONFIDENCE_MULT, min(self.MAX_CONFIDENCE_MULT, raw_multiplier))
        
        return round(multiplier, 2)

    def get_cached_price(self, symbol: str) -> Optional[float]:
        """
        Returns cached consensus price if fresh, None if stale/missing.
        This should be called BEFORE fetch_price to avoid unnecessary API calls.
        """
        if symbol not in self.cache_timestamps:
            return None
            
        age = time.time() - self.cache_timestamps.get(symbol, 0)
        ttl = self.CRYPTO_TTL if self._is_crypto(symbol) else self.STOCK_TTL
        
        if age < ttl:
            return self.consensus_cache.get(symbol)
        return None
    
    def _is_crypto(self, symbol: str) -> bool:
        """Determine if symbol is crypto or TradFi."""
        if symbol.endswith("USDT") or symbol.endswith("USDC") or symbol.endswith("BUSD"):
            return True
        if "BTC" in symbol or "ETH" in symbol:
            return True
        return False

    async def fetch_price(self, symbol: str) -> Optional[float]:
        """
        Polymorphic Fetch. Fires requests to all heads of the Hydra.
        Supports Stock Symbols via Yahoo.
        Returns consensus price or None.
        """
        # CHECK CACHE FIRST - avoid unnecessary API calls
        cached = self.get_cached_price(symbol)
        if cached is not None:
            return cached
            
        is_crypto = self._is_crypto(symbol)

        if not is_crypto:
            # STOCK MODE (Cyclops - One Eye for now, Yahoo)
            loop = asyncio.get_running_loop()
            price = await loop.run_in_executor(None, self.yahoo.get_latest_price, symbol)
            if price > 0:
                self.latest_snapshot[symbol] = {'yahoo': price}
                self._compute_consensus(symbol)
                return self.consensus_cache.get(symbol)
            return None

        # CRYPTO MODE (Hydra - Many Heads)
        self.latest_snapshot[symbol] = {}
        
        tasks = []
        ccxt_symbol = symbol.replace("USDT", "/USDT").replace("BUSD", "/BUSD") if "/" not in symbol else symbol
        
        for name, exchange in self.exchanges.items():
            tasks.append(self._fetch_single(name, exchange, ccxt_symbol, symbol))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        self._compute_consensus(symbol)
        return self.consensus_cache.get(symbol)

    async def _fetch_single(self, name: str, exchange, ccxt_symbol: str, original_symbol: str):
        try:
            ticker = await exchange.fetch_ticker(ccxt_symbol)
            price = ticker.get('last', 0.0)
            if price > 0:
                if original_symbol not in self.latest_snapshot:
                    self.latest_snapshot[original_symbol] = {}
                self.latest_snapshot[original_symbol][name] = price
        except Exception:
            pass  # Individual heads can fail silently

    def _compute_consensus(self, symbol: str):
        if symbol not in self.latest_snapshot:
            return
        
        prices = list(self.latest_snapshot[symbol].values())
        if not prices:
            return

        # 1. Consensus Price (Median)
        consensus = statistics.median(prices)
        
        # --- SANITY CHECK (The "ARKK" Defense) ---
        # Prevent 30,000% hallucinations (e.g. Stock -> BTC leakage)
        last_known = self.consensus_cache.get(symbol, 0.0)
        if last_known > 0:
            pct_diff = abs(consensus - last_known) / last_known
            if pct_diff > 3.0: # > 300% change
                # [FIX] Recovery Mode: If old price was practically zero (bad init) and new price is substantial,
                # we assume the old price was the hallucination/error and accept the new reality.
                # Threshold: Old < $5.0 and New > $100.0 (e.g. ^GSPC 0.67 -> 6900)
                if last_known < 5.0 and consensus > 100.0:
                    logger.warning(f"[WATCHTOWER] ⚠️ Correction Accepted: {symbol} ${consensus} (Was ${last_known}). Assuming bad initialization.")
                else:
                    logger.error(f"[WATCHTOWER] 🛑 HALLUCINATION BLOCKED: {symbol} ${consensus} (Was ${last_known}) | Delta: {pct_diff*100:.1f}%")
                    return 

        # 2. Update cache
        self.consensus_cache[symbol] = consensus
        self.cache_timestamps[symbol] = time.time()
        
        # [GHOST CANDLE] Check for anomaly BEFORE updating history
        # This compares new price against prediction from OLD history
        anomaly = self.detect_anomaly(symbol, consensus)
        
        # [GHOST CANDLE] Update history for next prediction
        self._update_price_history(symbol, consensus)
        
        # 3. Identify Outliers (>0.5% deviation)
        self.outliers = []
        for name, p in self.latest_snapshot[symbol].items():
            deviation = abs(p - consensus) / consensus
            if deviation > 0.005:
                self.outliers.append(name)


    def compare(self, symbol: str, primary_price: float) -> Dict:
        """
        Compares Primary Price (Binance) vs Consensus (Hydra Median).
        """
        consensus = self.consensus_cache.get(symbol, 0)
        
        if consensus == 0:
            return {
                "delta": 0.0,
                "fracture_index": 0.0,
                "consensus_price": 0.0,
                "outliers": [],
                "sources": 0
            }
        
        delta = primary_price - consensus
        fracture_pct = (abs(delta) / consensus) * 100.0
        
        return {
            "delta": delta,
            "fracture_index": fracture_pct,
            "consensus_price": consensus,
            "outliers": self.outliers,
            "sources": len(self.latest_snapshot.get(symbol, {}))
        }


    async def close(self):
        for ex in self.exchanges.values():
            await ex.close()

# Singleton
_tower = None
def get_watchtower():
    global _tower
    if _tower is None:
        _tower = Watchtower()
    return _tower
