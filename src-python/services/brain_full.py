import numpy as np
import math
import logging
import time
import time
import threading
from concurrent.futures import ThreadPoolExecutor
# CACHE BUST 2026-01-17
from typing import List, Optional, Dict
from collections import deque
from incubator.physics import integrate
from incubator.topology import TopologyEngine
from services.opportunity_cache import get_opportunity_cache
from services.brain_exoskeleton import BrainExoskeleton
from core.logger import get_logger
from utils.airwindows_console import AirwindowsConsole


logger = get_logger("Brain")

# --- PHYSICS & AUDIO DSP UTILS ---
def ulaw_encode(x, u=255.0):
    """
    u-Law Companding (Airwindows Style).
    Increases resolution of small signals (Market Noise) while compressing whales.
    y = sign(x) * ln(1 + u|x|) / ln(1 + u)
    """
    if x == 0: return 0
    sign = 1 if x >= 0 else -1
    abs_x = abs(x)
    try:
        val = math.log(1 + u * abs_x) / math.log(1 + u)
        return sign * val
    except:
        return x

def tpdf_dither():
    """
    Triangular Probability Density Function (TPDF) Dither.
    Adds high-quality noise to prevent quantization artifacts (overfitting).
    """
    import random
    # High-pass dither? Or standard TPDF.
    # Standard TPDF is R1 - R2
    return (random.random() - random.random()) * 0.0001


class IncrementalStats:
    """Incremental mean/std over a sliding window (O(1) updates).
    Uses a deque for O(1) evictions and a threading.Lock to protect updates
    when the engine is accessed from multiple threads."""
    def __init__(self, window_size: int = 20):
        self.window_size = int(window_size)
        self.prices: deque = deque()
        self.sum = 0.0
        self.sum_sq = 0.0
        self._lock = threading.Lock()

    def add_price(self, price: float):
        price = float(price)
        with self._lock:
            # Evict oldest if at capacity (maintain window size)
            if len(self.prices) >= self.window_size:
                old = self.prices.popleft()
                self.sum -= old
                self.sum_sq -= old * old
            self.prices.append(price)
            self.sum += price
            self.sum_sq += price * price

    def get_mean(self) -> float:
        with self._lock:
            n = len(self.prices)
            return (self.sum / n) if n else 0.0

    def get_std(self) -> float:
        with self._lock:
            n = len(self.prices)
            if n < 2:
                return 0.0
            mean = (self.sum / n) if n else 0.0
            variance = (self.sum_sq / n) - (mean * mean)
            return math.sqrt(variance) if variance > 0 else 0.0


import pandas as pd
try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

try:
    import torch
    from core.neural import ProphitNet
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

class BrainEngine:
    """The core brain engine for market analysis and decision making."""
    
    def __init__(self, symbol: str = "BTCUSDC"):
        # Multi-Symbol State Manager
        # self.states[symbol] -> {
        #    'price_history': [], 
        #    'volume_history': [], 
        #    'z_score_history': [],
        #    'inc_stats': IncrementalStats(20)
        # }
        self.states: Dict[str, Dict] = {}
        
        # Legacy/Current pointer (for backward compat with simple calls)
        self.current_symbol = symbol

        self.live_manager = None
        self.topology = TopologyEngine()
        self.current_regime = "UNKNOWN"
        self.running_volatility = 0.0
        self.last_signal_ids: Dict[str, int] = {}
        # Airwindows Consoles (Multi-Flavor Setup)
        self.consoles_la: Dict[str, AirwindowsConsole] = {} # For SubTight filtering
        self.consoles_9: Dict[str, AirwindowsConsole] = {}  # For Golden Ratio summing
        # Cache for projections: (symbol, lookahead) -> (timestamp, result)
        # Cache for projections: (symbol, lookahead) -> (timestamp, result)
        self.projection_cache: Dict[tuple, tuple] = {}
        
        # [OPTIMIZATION] Thread Pool for I/O (Database Writes)
        # Replaces "Thread-per-Tick" pattern which causes resource exhaustion
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="BrainWorker")
        
        # Topology State
        self.last_topology_update = 0
        self.topology_data = {}
        
        # --- THE SOUL (ML Layer) ---
        self.soul_model = None
        if HAS_XGB:
            try:
                import os
                model_path = os.path.join("backend", "models", "soul_v2.json")
                if os.path.exists(model_path):
                    self.soul_model = xgb.Booster()
                    self.soul_model.load_model(model_path)
                    logger.info(f"[BRAIN] 👻 The Soul is Awake. Loaded {model_path}")
                else:
                    logger.warning("[BRAIN] 👻 Soul model not found. ML Layer inactive.")
            except Exception as e:
                logger.error(f"[BRAIN] Failed to load Soul model: {e}")

        # --- HEAVY ARTILLERY (Deep Learning Layer) ---
        self.heavy_model = None
        if HAS_TORCH:
            try:
                import os
                pt_path = os.path.join("backend", "models", "heavy_artillery.pt")
                meta_path = os.path.join("backend", "models", "heavy_artillery_meta.json")
                
                if os.path.exists(pt_path) and os.path.exists(meta_path):
                    import json
                    with open(meta_path, 'r') as f:
                        meta = json.load(f)
                    
                    self.heavy_model = ProphitNet(
                        input_size=meta.get('input_size', 5),
                        hidden_size=meta.get('hidden_size', 64),
                        num_layers=meta.get('num_layers', 2)
                    )
                    
                    # Load weights
                    device = torch.device("cpu") # Inference on CPU usually fine for single Item
                    self.heavy_model.load_state_dict(torch.load(pt_path, map_location=device))
                    self.heavy_model.eval()
                    logger.info(f"[BRAIN] 🚀 Heavy Artillery (ProphitNet) Initialized. Loaded {pt_path}")
                else:
                    logger.warning("[BRAIN] Heavy Artillery model not found. Deep Learning Layer inactive.")
            except Exception as e:
                logger.error(f"[BRAIN] Failed to load Heavy Artillery: {e}")

    def _get_state(self, symbol: str) -> Dict:
        """Get or create state for a symbol."""
        if symbol not in self.states:
            self.states[symbol] = {
                'price_history': [],
                'volume_history': [],
                'timestamp_history': [],
                'z_score_history': [],
                'inc_stats': IncrementalStats(window_size=20),
                'exoskeleton': BrainExoskeleton(),
                'regime_buffer': deque(maxlen=15),
                'regime': 'UNKNOWN',
                'divine_metrics': {}, # Phase, ESN, DMD, etc.
                'sentiment_bias': 0.0, # -1.0 to 1.0 (Leaderboard alignment)
                'butterfly': ButterflySensor() # Chaos Detector
            }
            
            # Initialize specialized Airwindows Consoles
            self.consoles_la[symbol] = AirwindowsConsole(flavor="consolela")
            self.consoles_9[symbol] = AirwindowsConsole(flavor="console9")
            # [BOOT-LOOP FIX] Skip synchronous DB loading during state creation.
            # Hydration is now handled by async warm_up_universe() on startup.
            pass
        return self.states[symbol]

    async def warm_up_universe(self, symbols: List[str]):
        """Parallel async hydration for the entire universe with progress tracking."""
        import asyncio
        total = len(symbols)
        logger.info(f"[BRAIN] 🌊 Universe Hydration Started for {total} symbols...")
        
        tasks = []
        for i, s in enumerate(symbols):
            # Use to_thread to keep the event loop alive during DB/Computation intensive warm-up
            tasks.append(self._async_hydrate_symbol(s))
            
        # Run in small batches to avoid DB connection exhaustion
        batch_size = 5
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i+batch_size]
            await asyncio.gather(*batch)
            progress = min(100, int((i + len(batch)) / total * 100))
            logger.info(f"[BRAIN] 🌊 Hydrating Universe... {progress}% COMPLETE ({i + len(batch)}/{total})")

        logger.info("[BRAIN] ✅ Universe Hydration Fully Stabilized.")

    async def _async_hydrate_symbol(self, symbol: str):
        """Individual symbol hydration wrapper."""
        import asyncio
        # First try historical Z-scores (Light)
        loaded = await asyncio.to_thread(self.load_historical_z_scores, symbol)
        # If still empty, warm up with raw prices (Heavy)
        if loaded < 20:
            await asyncio.to_thread(self.warm_up, symbol)
        
    def ingest_candle(self, timestamp_ms: int, close_price: float, volume: float, symbol: str = "BTCUSDC"):
        """Ingest a new candle into the brain for analysis and persist to database."""
        try:
            # keep active symbol in sync
            self.current_symbol = symbol
            state = self._get_state(symbol)

            # append raw histories
            state['timestamp_history'].append(int(timestamp_ms))
            state['price_history'].append(float(close_price))
            state['volume_history'].append(float(volume))

            # update incremental stats (maintains window)
            inc_stats = state['inc_stats']
            inc_stats.add_price(close_price)
            mean_price = inc_stats.get_mean()
            std_price = inc_stats.get_std()

            # compute z-score when we have enough data
            z_score = None
            if len(inc_stats.prices) >= inc_stats.window_size and std_price > 0:
                z_score = (float(close_price) - mean_price) / std_price
                state['z_score_history'].append(float(z_score))

                # [ARMADA FIX] Calculate Velocity & Trend for The Rat
                velocity = 0.0
                if len(state['price_history']) >= 2:
                    prev_p = state['price_history'][-2]
                    # Velocity as % change per tick
                    velocity = (close_price - prev_p) / (prev_p + 1e-9) * 100.0 
                
                state['velocity'] = velocity
                
                # Trend Mapping (Regime -> Strength)
                # We use the *current* regime buffer to estimate immediate trend
                # JOY = Bull (+1), SAD = Bear (-1)
                current_regime = state.get('regime', 'UNKNOWN')
                trend_map = {'JOY': 1.0, 'SAD': -1.0, 'PANIC': -2.0, 'EUPHORIA': 2.0}
                state['trend_strength'] = trend_map.get(current_regime, 0.0)

                # [ARCHITECT FIX] Calculate Support/Resistance Levels
                # Simple Donchian Channel (50-period)
                lookback = 50
                if len(state['price_history']) >= lookback:
                    recent_prices = state['price_history'][-lookback:]
                    support = min(recent_prices)
                    resistance = max(recent_prices)
                    state['levels'] = [support, resistance]
                else:
                    # Fallback to current price if history is short
                    state['levels'] = [close_price * 0.95, close_price * 1.05]

                # persist newly computed z-score asynchronously (best-effort) and signal metadata


                # persist newly computed z-score asynchronously (best-effort) and signal metadata
                db = None  # Initialize to prevent UnboundLocalError
                try:
                    from services.database import get_database
                    db = get_database()
                    payload = {
                        "z_score": float(z_score),
                        "price": float(close_price),
                        "volume": float(volume),
                        "mean_price": float(mean_price),
                        "std_price": float(std_price)
                    }

                    
                    # LINK TO RISK SETTINGS: Dynamic Thresholding
                    try:
                        from services.wallet import get_wallet
                        wallet_risk = get_wallet().get_risk_params()
                        user_threshold = wallet_risk.get('threshold', 0.5)
                        # Radar Offset: Brain sees 0.2 further than the Gun
                        BRAIN_CACHE_THRESHOLD = max(0.1, user_threshold - 0.2)
                    except Exception:
                        BRAIN_CACHE_THRESHOLD = 0.3 # Fallback default

                    # determine signal direction and confidence for persistence (non-blocking)
                    try:
                        # [ARMADA] Butterfly Effect Sensor (Chaos Detection)
                        state['butterfly'].update(close_price)
                        chaos_level = state['butterfly'].get_chaos_level()
                        state['entropy'] = chaos_level # [ALCHEMIST FIX] Persist for Strategy
                        
                        # Bucketed Confidence (Avoid false 100% precision)
                        abs_z = abs(float(z_score))
                        if abs_z >= 4.0: confidence = 0.99
                        elif abs_z >= 3.0: confidence = 0.95
                        elif abs_z >= 2.5: confidence = 0.90
                        elif abs_z >= 2.0: confidence = 0.80
                        elif abs_z >= 1.5: confidence = 0.65
                        else: confidence = max(0.1, abs_z / 3.0)
                        
                        # [ARMADA] Chaos Dampener: If chaos > 0.5, reduce confidence drastically
                        if chaos_level > 0.5:
                            confidence *= (1.0 - chaos_level)
                            # logger.debug(f"[BRAIN] {symbol} Chaos Dampener Active! (Level: {chaos_level:.2f})")
                        
                        # [ENHANCEMENT] Volume Confirmation (Backtest: +0.01 PF on BTC)
                        # Boost confidence when volume > average
                        try:
                            vol_history = state.get('volume_history', [])
                            if len(vol_history) >= 20:
                                avg_vol = sum(vol_history[-20:]) / 20
                                if volume > avg_vol * 1.0:  # Above average volume
                                    confidence *= 1.1  # 10% boost
                                    state['volume_confirmed'] = True
                                else:
                                    state['volume_confirmed'] = False
                        except Exception:
                            pass
                        
                        # [ENHANCEMENT] RSI Confirmation (Backtest: +0.05 PF on ETH)
                        # Boost confidence when RSI confirms extreme
                        try:
                            rsi = self.calculate_rsi(symbol=symbol)
                            if rsi is not None:
                                # RSI < 30 + BUY signal = strong confirmation
                                if z_score < 0 and rsi < 30:
                                    confidence *= 1.15  # 15% boost
                                    state['rsi_confirmed'] = True
                                # RSI > 70 + SELL signal = strong confirmation
                                elif z_score > 0 and rsi > 70:
                                    confidence *= 1.15  # 15% boost
                                    state['rsi_confirmed'] = True
                                else:
                                    state['rsi_confirmed'] = False
                        except Exception:
                            pass
                        
                        # Cap confidence at 0.99
                        confidence = min(0.99, confidence)
                    except Exception:
                        confidence = 0.0

                    SIGNAL_PERSISTENCE_THRESHOLD = 0.5
                    
                    # --- THE SOUL: ML INFERENCE ---
                    ml_prob = 0.5
                    if self.soul_model and len(state['price_history']) > 30:
                        try:
                            # Feature Engineering on the fly (Must match training!)
                            # Last 30 points
                            p_recent = pd.Series(state['price_history'][-30:])
                            
                            # Features: ['returns', 'log_returns', 'volatility', 'momentum', 'rsi']
                            feats = {}
                            feats['returns'] = float(p_recent.pct_change().iloc[-1])
                            feats['log_returns'] = float(np.log(p_recent / p_recent.shift(1)).iloc[-1])
                            feats['volatility'] = float(p_recent.pct_change().rolling(20).std().iloc[-1])
                            feats['momentum'] = float(p_recent.iloc[-1] - p_recent.shift(20).iloc[-1])
                            
                            # RSI (Reuse Brain Method)
                            rsi_val = self._compute_rsi(p_recent.tolist())
                            feats['rsi'] = rsi_val
                            
                            # LGNN Proxy Features (matching the V2 training data distributions)
                            vol = feats['volatility']
                            mean_vol = 0.002 # Baseline approx
                            feats['lgnn_mass'] = max(10.0, min(100.0, 100.0 - (vol / mean_vol) * 20.0))
                            feats['lgnn_entropy'] = abs(rsi_val - 50) / 50.0
                            feats['lgnn_resonance'] = (feats['momentum'] / max(0.001, abs(feats['momentum']))) * 100.0 # Normalized
                            
                            # Create DMatrix
                            df_live = pd.DataFrame([feats])
                            # Feature order MUST match V2 training
                            cols = ['returns', 'log_returns', 'volatility', 'momentum', 'rsi', 'lgnn_mass', 'lgnn_entropy', 'lgnn_resonance']
                            dtest = xgb.DMatrix(df_live[cols])
                            
                            # Predict
                            # Binary classification output: Probability of Class 1 (Up)
                            preds = self.soul_model.predict(dtest)
                            ml_prob = float(preds[0])
                            
                            # Store in State for Oracle
                            state['ml_probability'] = ml_prob
                            # logger.debug(f"[BRAIN] 👻 Soul Says: {ml_prob:.4f}")
                            
                        except Exception as e:
                            # logger.debug(f"[BRAIN] Soul failed to speak: {e}")
                            pass
                    
                    # --- HEAVY ARTILLERY: DEEP LEARNING INFERENCE ---
                    # Replaces or augments XGBoost
                    if self.heavy_model and len(state['price_history']) > 65:
                        try:
                            # Prepare Sequence (Last 60 candles)
                            # We need to construct the exact feature matrix used in training
                            # Features: ['returns', 'log_returns', 'volatility', 'momentum', 'rsi']
                            
                            p_seq = pd.Series(state['price_history'][-80:]) # Grab enough for rolling vars
                            
                            # Calculate features efficiently
                            # Using pandas rolling is easiest but slightly slow. 
                            # For single inference, it's negligible (ms).
                            
                            df_feat = pd.DataFrame({'close': p_seq})
                            df_feat['returns'] = df_feat['close'].pct_change()
                            df_feat['log_returns'] = np.log(df_feat['close'] / df_feat['close'].shift(1))
                            df_feat['volatility'] = df_feat['close'].pct_change().rolling(20).std()
                            df_feat['momentum'] = df_feat['close'] - df_feat['close'].shift(20)
                            
                            # RSI
                            # We can recompute or use sliding window logic
                            # self._compute_rsi expects list.
                            # Let's just do a rolling apply or manual loop if needed. 
                            # Or faster: use pandas_ta if available, otherwise simple manual.
                            # Re-using the manual logic for the whole window is safer for consistency.
                            
                            rsi_vals = []
                            closes = df_feat['close'].values
                            # We only need the valid ones at the end (last 60)
                            # But computing RSI requires lookback.
                            
                            # Optimization: Just compute RSI for the tail
                            # We actually need RSI for every step of the 60 inputs? 
                            # Training data had RSI as a column. So yes, each timestep has an RSI value.
                            # This implies we need RSI history, not just current RSI.
                            
                            # We don't track RSI history in state currently, only price/vol.
                            # So we must compute it on the fly.
                            
                            # Compute RSI vector
                            delta = df_feat['close'].diff()
                            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                            rs = gain / loss
                            df_feat['rsi'] = 100 - (100 / (1 + rs))
                            
                            # Drop NaNs
                            df_ready = df_feat.dropna().tail(60)
                            
                            if len(df_ready) == 60:
                                # Create Tensor
                                feats = df_ready[['returns', 'log_returns', 'volatility', 'momentum', 'rsi']].values
                                tensor_x = torch.FloatTensor(feats).unsqueeze(0) # (1, 60, 5)
                                
                                # Inference
                                with torch.no_grad():
                                    out = self.heavy_model(tensor_x)
                                    # Output is now logits, apply sigmoid for probability
                                    dl_prob = float(torch.sigmoid(out).item())
                                    
                                # Use Deep Learning Probability as the primary ML Probability
                                state['ml_probability'] = dl_prob
                                # logger.debug(f"[BRAIN] 🚀 Heavy Artillery Fired: {dl_prob:.4f}")
                                
                        except Exception as e:
                            logger.error(f"[BRAIN] Heavy Artillery Jammed: {e}")
                    
                    if z_score is None:
                        direction = "HOLD"
                        strength = 0.0
                    else:
                        # Incorporate ML into direction?
                        # No, let Oracle handle the synthesis. BrainEngine just reports the Physics Signal (Z-Score).
                        # But we CAN enhance confidence.
                        
                        if float(z_score) > SIGNAL_PERSISTENCE_THRESHOLD:
                            direction = "BUY"
                        elif float(z_score) < -SIGNAL_PERSISTENCE_THRESHOLD:
                            direction = "SELL"
                        else:
                            direction = "HOLD"
                        strength = abs(float(z_score))

                    signal_payload = {
                        "direction": direction,
                        "strength": float(strength),
                        "confidence": float(confidence),
                        "regime": state['regime']
                    }

                    def _write(db):
                        try:
                            # 1. DB: Insert Analysis (Z-Score)
                            try:
                                db.insert_analysis(symbol, timestamp_ms / 1000.0, "z_score", payload)
                            except Exception:
                                # Fallback signatures
                                try:
                                    db.insert_analysis(timestamp_ms / 1000.0, "z_score", payload)
                                except Exception:
                                    pass

                            # 2. DB: Insert Signal (if supported)
                            if hasattr(db, "insert_signal"):
                                try:
                                    # Try standard signature first
                                    try:
                                        sid = db.insert_signal(symbol, timestamp_ms / 1000.0, direction, signal_payload)
                                    except TypeError:
                                        # Fallback signatures
                                        try:
                                            sid = db.insert_signal(symbol=symbol, ts=timestamp_ms / 1000.0, signal=direction, params=signal_payload)
                                        except Exception:
                                            sid = None
                                    
                                    if sid:
                                        self.last_signal_ids[symbol] = sid
                                except Exception:
                                    pass

                            # 3. Cache Opportunity (Debounced)
                            now = time.time()
                            last_cached = self.last_signal_ids.get(f"CACHE_{symbol}", 0)
                            
                            cache_time_threshold = 300
                            if (now - last_cached > cache_time_threshold) and (signal_payload['direction'] != "HOLD" and signal_payload['strength'] > BRAIN_CACHE_THRESHOLD):
                                try:
                                    import uuid
                                    opp_id = str(uuid.uuid4())
                                    opp = {
                                        "id": opp_id,
                                        "symbol": symbol,
                                        "opportunity_type": direction,
                                        "z_score": float(z_score or 0.0),
                                        "confidence": float(confidence),
                                        "score": int(confidence * 100),
                                        "created_at": timestamp_ms / 1000.0,
                                        "expires_at": (timestamp_ms / 1000.0) + (3600 * 4),
                                        "factors": [
                                            f"Statistical Deviation: {float(z_score or 0):.2f}σ",
                                            f"Regime: {state.get('regime', 'UNKNOWN')}",
                                            f"RSI: {self.calculate_rsi(symbol=symbol):.1f}"
                                        ]
                                    }
                                    
                                    cache = get_opportunity_cache()
                                    cache.invalidate_for_symbol(symbol)
                                    cache.cache_opportunity(opp)
                                    self.last_signal_ids[f"CACHE_{symbol}"] = now
                                    logger.info(f"[BRAIN][SIGNAL] Cached Opportunity: {symbol} {direction} (Z={z_score:.2f})")
                                except Exception as e:
                                    logger.warning(f"Failed to cache opportunity: {e}")

                            # 4. Exoskeleton V2 (Background)
                            # Only if history sufficient
                            if len(state['z_score_history']) > 20:
                                try:
                                    # Ensure Exoskeleton initialized
                                    if 'exoskeleton' in state:
                                        metrics = state['exoskeleton'].analyze(
                                            state['price_history'][-200:], 
                                            state['volume_history'][-200:],
                                            state['z_score_history'][-200:]
                                        )
                                        state['divine_metrics'] = metrics
                                        
                                        # [GEN2 PERSISTENCE] Save features for training
                                        try:
                                            from services.database import get_database
                                            train_db = get_database()
                                            
                                            # 1. Compute BTC Correlation (if enough data)
                                            btc_corr = 0.0
                                            if s != "BTCUSDT" and s != "BTCUSDC":
                                                btc_h = self.states.get("BTCUSDC", {}).get("price_history", [])
                                                sym_h = state['price_history']
                                                if len(btc_h) > 50 and len(sym_h) > 50:
                                                    min_len = min(len(btc_h), len(sym_h))
                                                    # Simple correlation on last 50 candles
                                                    import numpy as np
                                                    c = np.corrcoef(btc_h[-min_len:], sym_h[-min_len:])[0, 1]
                                                    if not np.isnan(c):
                                                        btc_corr = float(c)
                                            
                                            # 2. Persist Payload
                                            payload = {
                                                "phase": float(metrics.get("phase", 0.0)),
                                                "entropy": float(metrics.get("entropy", 0.0)),
                                                "btc_corr": btc_corr,
                                                "ulaw_z": float(state.get("neural_signal", 0.0))
                                            }
                                            train_db.insert_analysis(s, time.time(), "gen2_features", payload)
                                        except Exception:
                                            pass # Non-critical feature logging
                                        
                                        # Neural Synthesis Logic - ROLE SEPARATION
                                        # Based on validation: Z=72-76% win rate, Hilbert=55% (BTC), DMD=broken
                                        current_raw_z = state['z_score_history'][-1]
                                        phase = metrics.get('phase', 0.0)
                                        
                                        # --- ROLE 1: Z-SCORE = ENTRY TRIGGER (Primary) ---
                                        # Z-Score is the dominant signal (validated at 72-76% win rate)
                                        entry_signal = current_raw_z
                                        
                                        # --- ROLE 2: HILBERT PHASE = POSITION SIZING ---
                                        # Favorable phase: BUY when phase < -1.0 (cycle bottom)
                                        #                  SELL when phase > 1.0 (cycle top)
                                        phase_favorable = False
                                        if current_raw_z > 0 and phase > 1.0:  # SELL signal + cycle top
                                            phase_favorable = True
                                        elif current_raw_z < 0 and phase < -1.0:  # BUY signal + cycle bottom
                                            phase_favorable = True
                                        
                                        # Size multiplier: 1.3x if phase confirms, 1.0x otherwise
                                        size_mult = 1.3 if phase_favorable else 1.0
                                        
                                        # --- ROLE 3: DMD = DISABLED (validation showed 0% accuracy) ---
                                        # Keeping code for future debugging, but not using
                                        dmd_price = metrics.get('dmd_forecast', 0.0)
                                        target_price = None
                                        if dmd_price > 0 and close_price > 0:
                                            # For now, use fixed % target instead of broken DMD
                                            default_target_pct = 0.02  # 2%
                                            if current_raw_z > 0:  # SELL signal
                                                target_price = close_price * (1 - default_target_pct)
                                            else:  # BUY signal
                                                target_price = close_price * (1 + default_target_pct)
                                        
                                        # Store role-separated signals
                                        state['entry_signal'] = entry_signal
                                        state['size_multiplier'] = size_mult
                                        state['target_price'] = target_price
                                        
                                        # Keep neural_signal for backwards compatibility
                                        # But now Z dominates (70%) with minor phase influence (30%)
                                        phase_pressure = (phase / math.pi) * -1.0  # Reduced from -2.5
                                        
                                        # [AIRWINDOWS v4 - FINANCIAL CALIBRATION]
                                        # Financial signals (Z-Scores) are way too "loud" for audio DSP.
                                        # We map them to Audio Headroom (-1.0 to 1.0) so the saturators work properly.
                                        headroom = 10.0
                                        audio_z = current_raw_z / headroom
                                        audio_phase = phase_pressure / headroom
                                        
                                        # 1. Summing Bus: Console9 (Divine Golden Ratio Synthesis)
                                        # We skip ConsoleLA SubTight here because Z-Scores ARE low-frequency DC drift,
                                        # and SubTight would filter the actual trading signal out.
                                        console_9 = self.consoles_9[s]
                                        enc_z = console_9.encode(audio_z)
                                        enc_phase = console_9.encode(audio_phase)
                                        
                                        # Summing in the encoded (saturated) space to give "Punch"
                                        bus_sum = (enc_z * 0.7) + (enc_phase * 0.3)
                                        
                                        # 2. Master Desk: Decode + ClipOnly3 Mastering
                                        decoded_sum = console_9.decode(bus_sum)
                                        mastered_audio = console_9.master_desk(decoded_sum)
                                        
                                        # 3. Expand back to Financial Scale
                                        state['neural_signal'] = mastered_audio * headroom
                                except Exception:
                                    pass

                        except Exception as e:
                            logger.error(f"[BRAIN] Write thread error: {e}")

                    if db is not None:
                        # [OPTIMIZATION] Use Thread Pool instead of spawning new thread
                        self.executor.submit(_write, db)
                except Exception as e:
                    logger.debug(f"Failed to persist z-score/signal to database asynchronously: {e}")

                # Improved regime update with smoothing (majority vote over buffer)
                try:
                    # Mapping Lore: EQUI (Range), JOY (Bull Trend), SAD (Bear Trend), ANGER (Extreme)
                    raw_current = "EQUI"
                    if z_score > 3.0 or z_score < -3.0:
                        raw_current = "ANGER"
                    elif z_score > 1.5:
                        raw_current = "JOY"
                    elif z_score < -1.5:
                        raw_current = "SAD"
                    
                    state['regime_buffer'].append(raw_current)
                    
                    # Compute Majority (Smoothing)
                    from collections import Counter
                    counts = Counter(state['regime_buffer'])
                    state['regime'] = counts.most_common(1)[0][0]
                except Exception:
                    pass

                # Fallback for young assets (Immediate return)
                if not state.get('neural_signal'):
                     if state['z_score_history']:
                        state['neural_signal'] = state['z_score_history'][-1]

            # [PHYSICS] Periodically Update Topology (Every 5 mins)
            now = time.time()
            if now - self.last_topology_update > 300:
                # Run in background to avoid blocking ingest
                self.executor.submit(self._update_topology)
                self.last_topology_update = now

            # Keep only recent history (last 1000 candles)
            if len(state['price_history']) > 1000:
                state['price_history'] = state['price_history'][-1000:]
                state['volume_history'] = state['volume_history'][-1000:]
                state['timestamp_history'] = state['timestamp_history'][-1000:]
                state['z_score_history'] = state['z_score_history'][-1000:]

        except Exception as e:
            logger.error(f"Error ingesting candle for {symbol}: {e}")

    def ingest_sentiment(self, symbol: str, bias: float):
        """
        Ingest external intelligence bias (from top traders/leaderboards).
        Bias should be normalized between -1.0 (Bearish) and 1.0 (Bullish).
        """
        try:
            state = self._get_state(symbol)
            # Simple alpha blending for smoothing bias
            current = state.get('sentiment_bias', 0.0)
            state['sentiment_bias'] = (current * 0.8) + (float(bias) * 0.2)
            logger.debug(f"[BRAIN] Sentiment updated for {symbol}: {state['sentiment_bias']:.2f}")
        except Exception as e:
            logger.error(f"Sentiment ingest error for {symbol}: {e}")
            
    def _update_topology(self):
        """
        Updates the Galaxy Topology (Correlation Graph + Volume Gravity).
        Runs periodically (expensive).
        """
        try:
            # 1. Gather Data
            data = {}
            volumes = {}
            min_len = 999999
            
            valid_symbols = [s for s in self.states if len(self.states[s]['price_history']) > 50]
            if len(valid_symbols) < 2: return # Need at least 2 stars for a galaxy
            
            for s in valid_symbols:
                # Use last 100 candles for correlation
                ph = self.states[s]['price_history'][-100:]
                data[s] = ph
                min_len = min(min_len, len(ph))
                
                # Use Volume (Mass) - Average of last 20 candles
                vh = self.states[s]['volume_history'][-20:]
                if vh:
                    volumes[s] = sum(vh) / len(vh)
                else:
                    volumes[s] = 1.0

            # 2. Align Data (Truncate to min length)
            aligned_data = {}
            for s in valid_symbols:
                aligned_data[s] = data[s][-min_len:]
                
            # 3. Compute Correlation
            df = pd.DataFrame(aligned_data)
            corr_matrix = df.corr().values
            tickers = list(df.columns)
            
            # 4. Update Topology Engine (Gravity)
            result = self.topology.update(corr_matrix, tickers, volumes)
            self.topology_data = result
            
            # [GEN2 PREPARATION] Persist Topology Physics to DB for Future Training
            # We need history of "Gravity" to train the Sharpshooter to use it.
            try:
                from services.database import get_database
                db = get_database()
                timestamp = time.time()
                
                centrality = result.get('centrality', {})
                # Extract edges to find "Net Gravity" on a node? 
                # For now, Centrality is the best proxy for "Gravitational Pull"
                
                for s in valid_symbols:
                    if s in centrality:
                        # Physics Packet
                        physics_payload = {
                            "centrality": float(centrality[s]),
                            "mass": float(volumes.get(s, 1.0)), # Raw Volume as proxy
                            "log_mass": float(np.log10(max(1.0, volumes.get(s, 1.0))))
                        }
                        # Save as "physics" analysis type
                        db.insert_analysis(s, timestamp, "physics", physics_payload)
                        
            except Exception as e:
                logger.warning(f"[BRAIN] Failed to persist Gen2 Physics data: {e}")
            
            # [GEN2.5] Persist Astrological Data (Global, not per-symbol)
            try:
                from services.astro_service import get_astro_packet_sync
                astro = get_astro_packet_sync()
                
                # Save as "astro" analysis type under a global key
                astro_payload = {
                    "moon_phase": astro["moon_phase"],
                    "moon_illumination": astro["moon_illumination"],
                    "kp_index": astro["kp_index"],
                    "sunspot": astro["sunspot"],
                    "day_of_year": astro["day_of_year"],
                    "hour_of_day": astro["hour_of_day"],
                    "day_of_week": astro["day_of_week"]
                }
                db.insert_analysis("_GLOBAL_", timestamp, "astro", astro_payload)
                logger.debug(f"[BRAIN] 🌙 Astro data archived: Moon={astro['moon_phase']:.2f}")
                
            except Exception as e:
                logger.warning(f"[BRAIN] Failed to persist Astro data: {e}")
            
            logger.info(f"[BRAIN] 🌌 Galaxy Topology Updated & Archived ({len(valid_symbols)} stars).")
            
        except Exception as e:
            logger.error(f"[BRAIN] Topology Update Failed: {e}")

    async def analyze(self, symbol: str) -> float:
        """Compatibility method for Trading Service."""
        metrics = self.get_latest_metrics(symbol)
        return float(metrics.get('neural_signal', 0.0))

    def get_sovereign_signal(self, history, symbol: str = None) -> float:
        """Compatibility method for Rebalancer."""
        metrics = self.get_latest_metrics(symbol)
        return float(metrics.get('neural_signal', 0.0))
        
    def get_sovereign_metadata(self, symbol: str = None) -> Dict:
        """Compatibility method for Rebalancer."""
        return {'is_scorpio': False}

    def get_latest_metrics(self, symbol: str, lookback: float = 0.0) -> Dict:
        """Retrieve the latest metrics for a symbol (for BeaconService)."""
        try:
            state = self._get_state(symbol)
            # Extract key values for beacon broadcasting
            z_history = state.get('z_score_history', [])
            z_score = z_history[-1] if z_history else 0.0
            
            return {
                'neural_signal': state.get('neural_signal', z_score),
                'z_score': z_score,
                'confidence': state.get('stability', 0.5),
                'price': state.get('price_history', [0])[-1] if state.get('price_history') else 0,
                'divine_metrics': state.get('divine_metrics', {})
            }
        except Exception:
            return {}
            
    def compute_projection(self, lookahead=1, symbol: str = None):
        """Compute market projection for broadcast loop."""
        try:
            if not symbol:
                symbol = self.current_symbol
                
            # --- CACHE CHECK ---
            # Lazy Init for Hot-Reload Safety
            if not hasattr(self, "projection_cache"):
                self.projection_cache = {}

            # Stable Snapshot Logic: Prevent rapid flipping on refresh
            now = time.time()
            cache_key = (symbol, lookahead)
            
            # Determine TTL based on horizon magnitude
            # Short (minutes): 30s cache
            # Medium (hours): 5m cache
            # Long (days): 15m cache
            ttl = 30 # Default 30s
            if lookahead >= 24: ttl = 900 # 15m for daily+
            elif lookahead >= 4: ttl = 300 # 5m for 4H
            elif lookahead >= 1: ttl = 60 # 1m for 1H
            
            if cache_key in self.projection_cache:
                ts, cached_result = self.projection_cache[cache_key]
                if now - ts < ttl:
                    return cached_result

            state = self._get_state(symbol)
            z_history = state['z_score_history']
            p_history = state['price_history']
            regime = state['regime']

            if not z_history:
                return {
                    "signal": 0.0, 
                    "confidence": 0.0, 
                    "regime": regime,
                    "phase": 0.0
                }
                
            # STABILIZATION: Average recent Z-scores to prevent "twitchy" forecasts.
            # Window scales with lookahead to filter noise for longer timeframes.
            # Base window 5, +1 per hour of lookahead roughly
            smoothing = max(5, int(math.log1p(lookahead) * 7))
            recent_z = z_history[-smoothing:]
            
            # Weighted average (linear decay) to favor recent data slightly but maintain smoothness
            # If we have very few data points, the weights will be shorter.
            weights = np.linspace(0.5, 1.0, len(recent_z))
            raw_z_signal = np.average(recent_z, weights=weights)

            # --- OPERATION NEURAL LINK: THE EXOSKELETON WIRING ---
            # We assume the Exoskeleton (Echo State Network, DMD, Hilbert) has run in the background.
            # Now we allow it to VETO or BOOST the raw statistical Z-score.
            
            metrics = state.get('divine_metrics', {})
            neural_signal = raw_z_signal
            
            if metrics:
                # 1. Hilbert Phase (Cyclical Pressure)
                # Phase ranges -PI (Bottom) to +PI (Top).
                # Negative Phase Pressure means we should SELL at Tops (+PI) and BUY at Bottoms (-PI).
                # Logic: Invert Phase to get Directional Pressure.
                phase = metrics.get('phase', 0.0)
                phase_pressure = (phase / math.pi) * -2.5 # Scale to approx +/- 2.5 Z-score equivalents
                
                # 2. DMD Forecast (Predictive Vector)
                # Where does the fluid dynamics model think price is going next 5 steps?
                dmd_price = metrics.get('dmd_forecast', 0.0)
                dmd_vector = 0.0
                last_price = p_history[-1]
                if dmd_price > 0 and last_price > 0:
                    pct_diff = (dmd_price - last_price) / last_price
                    # Scale: 1% predicted move = 2.0 Z-score strength
                    dmd_vector = pct_diff * 200.0 
                    
                # 3. SYNTHESIS (The "Divine" Signal)
                # Weights: 
                # - 70% Raw Statistics (Robust) - UPGRADED from 40% to fix signal dampening
                # - 30% Cyclical Phase (Timing)
                # - 0% Predictive DMD (Disabled)
                neural_signal = (raw_z_signal * 0.7) + (phase_pressure * 0.3)

                # --- SWARM INTELLIGENCE FUSION ---
                # Integrating Satellite Data (Hetzner Nodes)
                if 'swarm_z_score' in state:
                    try:
                        swarm_z = float(state.get('swarm_z_score', 0))
                        # If Swarm agrees with Neural, boost signal
                        # If Swarm disagrees, dampen signal (Consensus Mechanism)
                        swarm_weight = 0.2
                        neural_signal = (neural_signal * (1.0 - swarm_weight)) + (swarm_z * swarm_weight)
                    except: pass
                
                # Check Swarm Chaos (External Entropy)
                swarm_chaos = float(state.get('swarm_chaos', 0))
                if swarm_chaos > 0.5:
                     # High external chaos -> Reduce confidence/signal magnitude
                     dampener = max(0.2, 1.0 - (swarm_chaos * 0.5))
                     neural_signal *= dampener

            # Assign Synthesized Signal
            current_signal = neural_signal
            
            # Bucketed Confidence (Consistent with Ingest)
            abs_z = abs(float(current_signal))
            if abs_z >= 4.0: confidence = 0.99
            elif abs_z >= 3.0: confidence = 0.95
            elif abs_z >= 2.5: confidence = 0.90
            elif abs_z >= 2.0: confidence = 0.80
            elif abs_z >= 1.5: confidence = 0.65
            else: confidence = max(0.1, abs_z / 3.0)
            
            # --- EXTERNAL INTELLIGENCE LAYER ---
            # Factor in top trader sentiment bias
            s_bias = state.get('sentiment_bias', 0.0)
            if abs(s_bias) > 0.1:
                # If sentiment aligns with ML signal, boost confidence
                # If they diverge, dampen it.
                if (current_signal > 0 and s_bias > 0) or (current_signal < 0 and s_bias < 0):
                    confidence = min(1.0, confidence * (1.0 + abs(s_bias)))
                else:
                    confidence = confidence * (1.0 - abs(s_bias) * 0.5)

            # Simple phase calculation
            phase = 0.0
            if len(p_history) > 10:
                recent_prices = p_history[-10:]
                price_range = max(recent_prices) - min(recent_prices)
                if price_range > 0:
                    current_pos = (p_history[-1] - min(recent_prices)) / price_range
                    phase = (current_pos - 0.5) * math.pi
            
            # --- TARGET PRICE CALCULATION (Standard Deviation Projection) ---
            # We don't use new AI models, just standard statistical projection.
            
            # 1. Calculate Volatility (Std Dev of Price)
            # We use the recent incremental stats or calculate from history if needed
            volatility = 0.01 # Default 1%
            mean_price = state['inc_stats'].get_mean()
            std_price = state['inc_stats'].get_std()
            
            if mean_price > 0:
                volatility = std_price / mean_price
            
            # 2. Scale by Timeframe (Square Root of Time Rule)
            # lookahead is in "hours" (approximate units)
            # Volatility scales with sqrt(time)
            time_scaler = math.sqrt(lookahead) if lookahead > 0 else 1.0
            projected_vol = volatility * time_scaler
            
            last_price = p_history[-1]
            target_price = last_price
            
            # 3. Projection Logic
            # If Z-Score is extreme (> 2.0), we project MEAN REVERSION (Back to Average)
            # If Z-Score is moderate (0.5 - 1.5), we project MOMENTUM (Continuation)
            
            z = float(current_signal)
            
            if abs(z) > 2.0:
                # Mean Reversion: Target is closer to the Mean
                # We expect it to correct by half the deviation over the timeframe
                correction = (mean_price - last_price) * 0.5 * min(1.0, time_scaler/24.0)
                target_price = last_price + correction
            elif abs(z) > 0.5:
                # Momentum: Price is moving away from mean
                # Project continuation in direction of Z
                # Target = Price * (1 + (Z * Volatility * Scaler))
                drift = (z * 0.5) * projected_vol # Dampened drift
                target_price = last_price * (1 + drift)
            else:
                 # Noise / Chop: Target is effectively flat or slightly mean reverting
                 target_price = last_price

            # --- EXECUTION PARAMETERS (MT5 PRESET) ---
            # SL = Volatility based (ATR multiplier equivalent)
            # TP = Target Price
            risk_mult = 1.5
            sl_dist = projected_vol * risk_mult * last_price
            
            stop_loss = 0.0
            if target_price > last_price:
                # LONG
                stop_loss = last_price - sl_dist
            else:
                # SHORT
                stop_loss = last_price + sl_dist
            
            result = {
                "signal": float(current_signal),
                "confidence": float(confidence),
                "regime": regime,
                "volatility": float(volatility),
                "phase": float(phase),
                "drift": float(drift) if 'drift' in locals() else 0.0,
                "target_price": float(target_price),
                "stop_loss": float(stop_loss),
                "take_profit": float(target_price)
            }
            
            # Update Cache
            self.projection_cache[cache_key] = (now, result)
            return result
        except Exception as e:
            logger.error(f"Error computing projection for {symbol}: {e}")
            return {
                "signal": 0.0, 
                "confidence": 0.0, 
                "regime": "ERROR",
                "phase": 0.0
            }

    def get_divine_metrics(self, symbol: str = None) -> Dict:
        """
        Retrieves high-tier analytical data (Phase, DMD Forecast, Stability)
        for a specific symbol.
        """
        target = symbol or self.current_symbol
        state = self._get_state(target)
        
        metrics = state.get('divine_metrics', {}).copy()
        
        # SELF-HEALING: If no metrics exist, compute them on-demand
        if not metrics or not metrics.get('stability'):
            # 1. Ensure we have data
            if len(state['price_history']) < 50:
                self.warm_up(target)
            
            # 2. Run Exoskeleton Analysis
            if len(state['z_score_history']) > 20:
                try:
                    logger.debug(f"[BRAIN] Triggering On-Demand Exoskeleton for {target}")
                    computed = state['exoskeleton'].analyze(
                        state['price_history'][-200:],
                        state['volume_history'][-200:],
                        state['z_score_history'][-200:]
                    )
                    state['divine_metrics'] = computed
                    metrics = computed.copy()
                except Exception as e:
                    logger.error(f"On-Demand Exoskeleton failed for {target}: {e}")
        
        # Enrich with Centrality if available from Topology
        try:
            centrality = self.topology.get_centrality() if hasattr(self.topology, 'get_centrality') else {}
            metrics['centrality'] = centrality.get(target, 0.0)
        except:
            metrics['centrality'] = 0.0
            
        # Add sentiment context
        metrics['sentiment_bias'] = state.get('sentiment_bias', 0.0)
        metrics['regime'] = state.get('regime', 'UNKNOWN')
        metrics['symbol'] = target
        
        return metrics

    def get_metrics_for_timeframe(self, symbol: str, timeframe: str) -> Dict:
        """
        Fetch ad-hoc metrics (RSI, Volatility) for a specific timeframe.
        Fetches fresh data from DataManager instead of using internal cache.
        """
        try:
            # Map timeframe to DataManager interval
            # Bot uses: 15M, 1H, 4H, 1D, 1W
            # DM expects: 15m, 1h, 4h, 1d, 1w
            interval = timeframe.lower()
            
            from services.data_manager import get_data_manager
            dm = get_data_manager()
            
            # Fetch enough candles for RSI(14) + buffer
            candles = dm.get_data(symbol, interval, limit=50)
            
            # Allow calculation with as few as 5 candles (for new/sparse assets)
            if not candles or len(candles) < 5:
                # Fallback to internal state if fetch fails
                return {
                    "rsi": self.calculate_rsi(symbol=symbol),
                    "volatility": 0.0 # internal volatility is harder to isolate
                }
                
            prices = [float(c['close']) for c in candles]
            
            # 1. Compute RSI
            rsi = self._compute_rsi(prices)
            
            # 2. Compute Volatility (StdDev / Mean)
            arr = np.array(prices)
            mean = np.mean(arr)
            std = np.std(arr)
            # Return as Percentage (e.g. 0.01 -> 1.0%)
            vol = (std / mean * 100.0) if mean > 0 else 0.0
            
            return {
                "rsi": rsi,
                "volatility": vol
            }
        except Exception as e:
            logger.error(f"Ad-hoc metrics failed for {symbol} {timeframe}: {e}")
            return {"rsi": 50.0, "volatility": 0.0}

    def _compute_rsi(self, prices: List[float], period: int = 14) -> float:
        """Pure logic for RSI calculation."""
        if len(prices) < 2: # Minimal check
            return 50.0

        arr = np.array(prices, dtype=float)
        deltas = np.diff(arr)
        gains = np.where(deltas > 0, deltas, 0.0)
        losses = np.where(deltas < 0, -deltas, 0.0)

        # Use simple moving average of last `period` deltas for a robust estimate.
        avg_gain = float(np.mean(gains[-period:])) if gains.size >= period else float(np.mean(gains))
        avg_loss = float(np.mean(losses[-period:])) if losses.size >= period else float(np.mean(losses))

        if avg_gain == 0 and avg_loss == 0:
            return 50.0
        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100.0 - (100.0 / (1.0 + rs))
        return float(rsi)

    def calculate_rsi(self, period: int = 14, symbol: str = None) -> float:
        """
        Calculate RSI (Relative Strength Index) from the internal price_history.
        Legacy wrapper for backward compatibility.
        """
        try:
            if not symbol and hasattr(self, 'current_symbol'):
                symbol = self.current_symbol
            elif not symbol:
                symbol = "BTCUSDC" # Default fallback
                
            state = self._get_state(symbol)
            prices = state['price_history']
            
            return self._compute_rsi(prices, period)
        except Exception:
            return 50.0

    def load_historical_z_scores(self, symbol: str = "BTCUSDC", limit: int = 1000):
        """Load recent z-scores from database on startup."""
        try:
            state = self._get_state(symbol)
            
            from services.database import get_database
            db = get_database()
            analyses = db.get_analyses(symbol=symbol, analysis_type="z_score", limit=limit)

            if not analyses:
                return 0

            # analyses are returned newest-first; iterate in reverse for chronological insertion
            loaded = 0
            for a in reversed(analyses):
                payload = a.get("payload") or {}
                z = payload.get("z_score")
                price = payload.get("price")
                ts = a.get("ts")
                if z is None:
                    continue

                # restore chronological histories
                if float(z) not in state['z_score_history']:
                    state['z_score_history'].append(float(z))
                
                if price is not None:
                    p = float(price)
                    if p not in state['price_history']:
                        state['price_history'].append(p)
                        # seed incremental stats with restored price
                        try:
                            state['inc_stats'].add_price(p)
                            # [FIX] Feed Butterfly Sensor (Fixes Chaos 0 on DB Load)
                            state['butterfly'].update(p)
                        except Exception:
                            pass
                if 'volume' in payload and payload['volume'] is not None:
                    state['volume_history'].append(float(payload['volume']))
                if ts is not None:
                    try:
                        # DB stores seconds; convert to ms for internal history
                        ms = int(float(ts) * 1000)
                        if ms not in state['timestamp_history']:
                            state['timestamp_history'].append(ms)
                    except Exception:
                        pass
                loaded += 1

            logger.info(f"Loaded {loaded} z-scores for {symbol} from DB")
            return loaded
        except Exception:
            logger.exception(f"Error loading historical z-scores for {symbol}")
            return 0

    def warm_up(self, symbol: str, limit: int = 200):
        """
        Seed the brain with raw price history if pre-computed analysis is missing.
        Ensures stats like Z-Score and RSI are available immediately.
        """
        try:
            from services.data_manager import get_data_manager
            dm = get_data_manager()
            
            state = self._get_state(symbol)
            
            # Fetch 1H data for robust baseline
            # get_data returns chronological order
            raw_data = dm.get_data(symbol, "1h", limit=limit)
            
            if not raw_data:
                # Try 1m if 1h is empty
                raw_data = dm.get_data(symbol, "1m", limit=limit)
                
            if not raw_data:
                return 0
                
            count = 0
            for candle in raw_data:
                # Hybrid Handling (Dict vs ORM Object)
                if hasattr(candle, 'close'):
                    price = float(candle.close)
                    ts_val = candle.timestamp
                else:
                    price = float(candle['close'])
                    ts_val = candle['timestamp']
                
                # Deduplicate
                if price in state['price_history']:
                    continue
                    
                state['price_history'].append(price)
                # Handle volume safely
                vol = float(candle.volume) if hasattr(candle, 'volume') else float(candle.get('volume', 0))
                state['volume_history'].append(vol)
                
                try:
                    # Timestamp Handling (Datetime obj vs ISO String vs Int)
                    if isinstance(ts_val, (int, float)):
                        state['timestamp_history'].append(int(ts_val))
                    elif hasattr(ts_val, 'timestamp'): # datetime object
                        state['timestamp_history'].append(int(ts_val.timestamp() * 1000))
                    elif isinstance(ts_val, str):
                        dt = datetime.fromisoformat(ts_val.replace('Z', '+00:00'))
                        state['timestamp_history'].append(int(dt.timestamp() * 1000))
                except Exception:
                    pass
                    
                state['inc_stats'].add_price(price)
                # [FIX] Feed Butterfly Sensor during Warm-Up (Fixes Chaos 0)
                state['butterfly'].update(price)
                
                # Compute historical Z-Score for the baseline (Stabilization)
                mean = state['inc_stats'].get_mean()
                std = state['inc_stats'].get_std()
                if len(state['inc_stats'].prices) >= state['inc_stats'].window_size and std > 0:
                    z = (price - mean) / std
                    state['z_score_history'].append(z)
                
                count += 1
            
            # Compute Initial Regime
            if state['z_score_history']:
                last_z = state['z_score_history'][-1]
                raw_current = "EQUI"
                if last_z > 3.0 or last_z < -3.0: raw_current = "ANGER"
                elif last_z > 1.5: raw_current = "JOY"
                elif last_z < -1.5: raw_current = "SAD"
                state['regime'] = raw_current
                
            logger.info(f"[BRAIN][WARM-UP] Seeded {count} candles for {symbol} baseline (Internal Z-History: {len(state['z_score_history'])}).")
            # [SOVEREIGN PARALLELISM] Skip expensive exoskeleton analysis during boot
            # to prevent the 60-second watchdog timeout. The first tick will handle this.
            return count
            
            if False:
                try:
                    # 1. Run Exoskeleton
                    state['divine_metrics'] = state['exoskeleton'].analyze(
                        state['price_history'][-200:],
                        state['volume_history'][-200:],
                        state['z_score_history'][-200:]
                    )
                    
                    # 2. Update Butterfly (Chaos)
                    if state['price_history']:
                        # Feed last 20 prices to butterfly
                        for p in state['price_history'][-20:]:
                             state['butterfly'].update(p)
                    
                    # 3. Synthesize Signal (Copied from ingest_candle logic)
                    metrics = state['divine_metrics']
                    last_z = state['z_score_history'][-1]
                    
                    phase = metrics.get('phase', 0.0)
                    phase_pressure = (phase / math.pi) * -2.5
                    
                    dmd_price = metrics.get('dmd_forecast', 0.0)
                    dmd_vector = 0.0
                    last_price = state['price_history'][-1]
                    if dmd_price > 0 and last_price > 0:
                        pct = (dmd_price - last_price) / last_price
                        dmd_vector = pct * 200.0
                        
                    neural_val = (last_z * 0.4) + (phase_pressure * 0.3) + (dmd_vector * 0.3)
                    state['neural_signal'] = neural_val
                    
                    logger.info(f"[BRAIN][WARM-UP] Exoskeleton Active for {symbol}: Neural={neural_val:.2f} (Z={last_z:.2f})")
                except Exception as e:
                    logger.warning(f"[BRAIN][WARM-UP] Exoskeleton Pre-Heat Failed: {e}")

            return count
        except Exception as e:
            logger.error(f"Warm-up failed for {symbol}: {e}")
            return 0

    def extract_features_df(self, prices, volumes, feature_list):
        """
        Public interface for 33D Manifold extraction from raw arrays.
        Used by both Live Bot and Academy for Sovereign Alignment.
        """
        import pandas as pd
        import numpy as np
        
        # Convert to pandas for vectorized physics
        df = pd.DataFrame({'close': prices, 'volume': volumes})
        df['returns'] = df['close'].pct_change()
        df['volatility'] = df['close'].pct_change().rolling(20).std()
        df['momentum'] = df['close'] - df['close'].shift(20)
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-9)
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Expert Signals & Fractal Swarm
        experts = getattr(self, 'experts', {})
        current_window = df.tail(1000)
        
        for name in feature_list:
            if name in df.columns:
                continue
                
            if name in experts:
                strat = experts[name]
                if strat:
                    try:
                        sig = strat.next_candle(current_window)
                        if isinstance(sig, dict): sig = sig.get("action", 0.0)
                        df[name] = float(sig or 0.0)
                    except:
                        df[name] = 0.0
                else:
                    df[name] = 0.0
            elif name.startswith('z_') and name != 'z_velocity':
                try:
                    period = int(name.split('_')[-1])
                    v_arr = df['close'].tail(period).values
                    if len(v_arr) >= 2:
                        df[name] = (df['close'] - v_arr.mean()) / (v_arr.std() + 1e-9)
                    else:
                        df[name] = 0.0
                except:
                    df[name] = 0.0
            elif name == 'volume_z':
                v_arr = df['volume'].tail(20).values
                v_mean = v_arr.mean()
                v_std = v_arr.std()
                df[name] = (df['volume'] - v_mean) / (v_std + 1e-9)
            else:
                df[name] = 0.0
                
        return df[feature_list]

    def extract_features(self, tick_data):
        """
        Extracts a single tick feature vector (33D) from a DataFrame.
        Used by the Academy Gauntlet for real-time strategy testing.
        """
        if not hasattr(self, 'heavy_features') or not self.heavy_features:
            # Fallback to metadata if brain instance is fresh
            try:
                import json
                import os
                meta_path = os.path.join("backend", "models", "champion_meta.json")
                with open(meta_path, 'r') as f:
                    meta = json.load(f)
                self.heavy_features = meta.get('feature_cols', [])
            except:
                self.heavy_features = []

        if len(tick_data) < 10:
             return {f: 0.0 for f in self.heavy_features}

        prices = tick_data['close'].values
        volumes = tick_data['volume'].values
        
        df_full = self.extract_features_df(prices, volumes, self.heavy_features)
        
        # Return last row as dict
        if not df_full.empty:
            return df_full.iloc[-1].to_dict()
        return {f: 0.0 for f in self.heavy_features}


# Global engine instance
_engine_instance: Optional[BrainEngine] = None

def get_engine() -> BrainEngine:
    """Get the global brain engine instance."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = BrainEngine()
        logger.info("Brain engine initialized")
    return _engine_instance

# Removed unused physics functions - these were never called and are dead code
# If needed, use services.physics instead



class ButterflySensor:
    """
    Butterfly Effect Sensor: Detects Sensitive Dependence on Initial Conditions (Chaos).
    Uses simplified Lyapunov Exponent estimation.
    """
    def __init__(self, window=20):
        self.window = window
        self.history = []
        
    def update(self, price):
        self.history.append(float(price))
        if len(self.history) > self.window * 2:
            self.history.pop(0)
            
    def get_chaos_level(self) -> float:
        """
        Returns a chaos score (0.0 to 1.0).
        High chaos means market is unpredictable (Sensitivity to Initial Conditions).
        """
        if len(self.history) < self.window: return 0.0
        
        try:
            # Simple Lyapunov Proxy: Average Divergence Rate
            # Compare trajectory of first half vs second half
            mid = len(self.history) // 2
            dists = []
            
            for i in range(mid - 1):
                p1 = self.history[i]
                p2 = self.history[i+1]
                
                shifted_p1 = self.history[mid + i]
                shifted_p2 = self.history[mid + i + 1]
                
                # Divergence
                div_initial = abs(p1 - shifted_p1)
                div_final = abs(p2 - shifted_p2)
                
                if div_initial > 0.0001:
                    # Add small epsilon to prevent explosion on tiny initial distances
                    expansion = math.log((div_final + 1e-8) / (div_initial + 1e-8))
                    dists.append(expansion)
            
            if not dists: return 0.0
            
            avg_lambda = sum(dists) / len(dists)
            
            # Normalize: Lambda > 0.5 is heavily chaotic
            # MULTIPLIER reduced from 5.0 to 1.0 for better range
            chaos = math.tanh(max(0, avg_lambda) * 1.0) 
            return chaos
        except:
            return 0.0

# Alias for compatibility with arena system
ProphitEngine = BrainEngine




# Alias for compatibility with arena system
ProphitEngine = BrainEngine
