
import sqlite3
import pandas as pd
import numpy as np
import pickle
import random
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from arena.strategies.rat import TheRat
from arena.strategies.prophit_net import ProphitNetStrategy
from arena.api import Champion

def _validate_and_clean_data(df, max_crash_pct=0.30):
    """
    Remove outliers and validate price continuity.
    Also detects and validates crash scenarios.
    
    Thresholds are calibrated for minute-level data:
    - Max crash (30%): Realistic daily crashes, filters unrealistic data corruption
    - Crash detection (10%): Identifies significant market stress events
    - Max sequential jump (50%): Prevents unit mismatches (e.g., satoshis vs USD)
    - Max intrabar move (50%): Filters flash crashes and data errors
    
    Args:
        df: DataFrame with OHLCV data
        max_crash_pct: Maximum realistic crash percentage (default 30% for daily data)
    """
    if df.empty:
        return df
    
    initial_len = len(df)

    # Replace infinities and drop obvious NaNs in price columns
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna(subset=['open', 'high', 'low', 'close', 'volume'])

    # Remove duplicate timestamps if present (keeps first occurrence)
    if 'timestamp' in df.columns:
        df = df.drop_duplicates(subset='timestamp', keep='first')

    # Enforce absolute price sanity bounds to catch unit mismatches or corrupted feeds
    # Prices <= 1e-8 are effectively zero; prices > 1e7 are extremely unlikely for crypto/stock tickers in USD
    df = df[(df['close'] > 1e-8) & (df['close'] < 1e7) & (df['open'] > 0) & (df['high'] > 0) & (df['low'] > 0)]

    # Rolling z-score filter to remove isolated spikes that pass simple pct-change checks
    # Window and threshold are intentionally conservative to avoid removing legitimate volatility
    try:
        roll_mean = df['close'].rolling(window=50, min_periods=1).mean()
        roll_std = df['close'].rolling(window=50, min_periods=1).std().replace(0, np.nan)
        z = ((df['close'] - roll_mean) / roll_std).abs().fillna(0)
        df = df[z <= 10]  # keep values within 10 sigma (very permissive)
    except Exception:
        # If anything goes wrong with rolling stats, continue with remaining guards
        pass

    # Detect extreme intrabar moves (>50% for minute data)
    df['intrabar_pct'] = (df['high'] - df['low']) / df['low']
    df = df[df['intrabar_pct'] <= 0.5]

    # Detect extreme sequential jumps
    df['price_change_pct'] = df['close'].pct_change().abs()

    # Detect crash scenarios (large negative moves)
    df['is_crash'] = df['close'].pct_change() < -0.10  # >10% drop

    # Validate crash scenarios are realistic
    # For minute data, a realistic crash might be 5-15% per candle max
    # For daily data, 20-30% max
    # Anything beyond max_crash_pct is likely data corruption
    crash_mask = df['is_crash'] & (df['price_change_pct'].abs() > max_crash_pct)
    if crash_mask.any():
        crash_count = int(crash_mask.sum())
        print(f"[TRAIN] [WARN] Detected {crash_count} unrealistic crash scenarios (>{(max_crash_pct*100):.0f}% drop) - removing")
        df = df[~crash_mask]

    # Log realistic crash scenarios for audit
    realistic_crashes = df['is_crash'] & (df['price_change_pct'].abs() <= max_crash_pct)
    if realistic_crashes.any():
        crash_count = int(realistic_crashes.sum())
        crash_pcts = df.loc[realistic_crashes, 'price_change_pct'].abs() * 100
        avg_crash = float(crash_pcts.mean())
        max_crash = float(crash_pcts.max())
        print(f"[TRAIN] Detected {crash_count} realistic crash scenarios (avg: {avg_crash:.1f}%, max: {max_crash:.1f}%)")

    # Remove extreme sequential jumps (non-crash)
    df = df[df['price_change_pct'] <= 0.5]  # Max 50% sequential change

    removed = initial_len - len(df)
    if removed > 0:
        print(f"[TRAIN] Removed {removed} invalid/outlier candles ({removed/initial_len*100:.1f}%)")

    # Final defensive cleanup: reset index and ensure numeric dtypes
    try:
        df = df.reset_index(drop=True)
        for c in ['open','high','low','close','volume','intrabar_pct','price_change_pct']:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors='coerce')
    except Exception:
        pass

    # Drop any remaining non-finite rows
    df = df.replace([np.inf, -np.inf], np.nan).dropna(subset=['open', 'high', 'low', 'close', 'volume'])

    return df.reset_index(drop=True)

def load_data(limit=10000):
    try:
        import sqlite3
        from config.settings import get_settings
        settings = get_settings()
        
        db_path = getattr(settings, 'DB_PATH', 'market_data.db')
        conn = sqlite3.connect(db_path, timeout=5.0)
        
        # We need timestamp, open, high, low, close, volume
        query = f"SELECT timestamp, price as close, volume FROM market_ticks WHERE symbol='BTCUSDC' ORDER BY timestamp DESC LIMIT {limit}"
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            print("[TRAIN] Warning: SQLite returned empty DataFrame.")
            return pd.DataFrame()
            
        # Synthesize OHLC
        df['open'] = df['close']
        df['high'] = df['close']
        df['low'] = df['close']
            
        # Ensure timestamp sort
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # Data validation
        df = _validate_and_clean_data(df)
        return df
    except Exception as e:
        print(f"Data Load Error: {e}")
        return pd.DataFrame()

def calculate_thoth_oracle(df, horizon=5, resonance_range=(0.7, 1.0)):
    """
    Generate probabilistic oracle predictions.
    Varies resonance to prevent overfitting to perfect foresight.
    """
    predictions = []
    closes = df['close'].values
    
    for i in range(len(df)):
        if i + horizon >= len(df):
            predictions.append(None)
            continue
        
        # Base prediction (future price)
        future_price = closes[i + horizon]
        current_price = closes[i]
        
        # Add noise to prediction (5-15% variance)
        noise_factor = np.random.uniform(0.85, 1.15)
        predicted_price = future_price * noise_factor
        
        # Probabilistic resonance (varies between min and max)
        resonance = np.random.uniform(resonance_range[0], resonance_range[1])
        
        # Generate price sequence with noise
        price_sequence = []
        for j in range(horizon):
            if i + 1 + j < len(closes):
                # Add progressive noise
                step_noise = np.random.uniform(0.95, 1.05)
                price_sequence.append(closes[i + 1 + j] * step_noise)
            else:
                price_sequence.append(predicted_price)
        
        pred = {
            'prices': price_sequence,
            'resonance': resonance
        }
        predictions.append(pred)
        
    return predictions

def calculate_fitness(balance, initial_balance, trades, wins, returns_history, crash_trades=None):
    """
    Calculate robust fitness metric using log returns and risk-adjusted components.
    
    Args:
        balance: Final balance after simulation
        initial_balance: Starting balance
        trades: Total number of trades
        wins: Number of winning trades
        returns_history: List of per-trade returns
        crash_trades: List of booleans indicating if each trade was during a crash scenario
    """
    if trades < 5:
        return 0.0

    # Protect against runaway balances by capping the balance ratio before log
    try:
        ratio = max(balance / initial_balance, 1e-10)
        max_ratio = 1e6  # cap growth to prevent extreme fitness from single glitches
        capped_ratio = min(ratio, max_ratio)
        log_return = np.log(capped_ratio)
    except Exception:
        log_return = 0.0

    # Risk-adjusted component
    win_rate = wins / trades if trades > 0 else 0.0

    # Penalize extreme single-trade returns (data glitch indicator)
    # Threshold: 50% single trade return is unrealistic for normal market conditions
    # Penalty: -10.0 (significant but not catastrophic) - proportional to violation severity
    extreme_penalty = 0.0
    if returns_history:
        try:
            max_single_return = max(abs(r) for r in returns_history)
            if max_single_return > 0.5:  # >50% single trade (unrealistic)
                extreme_penalty = -10.0  # Heavy penalty for exploiting data glitches
        except Exception:
            pass

    # Crash scenario weighting
    # If crash_trades provided, weight crash performance less heavily
    # (we want good normal performance, not just crash exploitation)
    # Threshold: >50% of trades in crashes indicates over-reliance on extreme events
    # Penalty: -5.0 (moderate) - encourages balanced performance across market conditions
    crash_adjustment = 0.0
    if crash_trades and len(crash_trades) == len(returns_history):
        crash_trade_count = sum(crash_trades)
        if crash_trade_count > trades * 0.5:  # >50% of trades in crashes
            # Penalize if too many trades are in crash scenarios
            # (indicates bot is only good at exploiting crashes, not normal trading)
            crash_adjustment = -5.0
            print(f"[TRAIN] [WARN] {crash_trade_count}/{trades} trades in crash scenarios (imbalanced)")

    # Trade frequency bonus (reward consistent trading, max 5 points)
    # Encourages strategies that trade regularly, not just high returns on few trades
    trade_frequency_bonus = min(trades / 10.0, 5.0)  # 1 point per 10 trades, capped at 5

    # Win rate penalty for low win rates (below 50% is concerning)
    # Prevents strategies that exploit rare high-return events with poor consistency
    # Stronger penalty to ensure balanced strategies are preferred
    win_rate_penalty = 0.0
    if win_rate < 0.50:  # Below 50% win rate
        win_rate_penalty = -15.0 * (0.50 - win_rate)  # Stronger penalty scales with how far below 50%
        # Example: 40% WR → -15.0 * 0.10 = -1.5 penalty
        # Example: 30% WR → -15.0 * 0.20 = -3.0 penalty

    # Composite fitness: balanced weights for optimal strategy selection
    # Log returns (primary, 50x): Rewards profitability
    # Win rate (secondary, 40x): Rewards consistency (increased weight for better balance)
    # Trade frequency (bonus, max 5): Rewards activity
    # Win rate penalty: Discourages low-consistency strategies
    # Other penalties: Discourage data glitch exploitation and crash over-reliance
    fitness = (log_return * 50) + (win_rate * 40) + trade_frequency_bonus + win_rate_penalty + extreme_penalty + crash_adjustment

    # Cap fitness to a reasonable range to avoid extreme values from data glitches
    try:
        fitness = float(np.clip(fitness, -1e9, 1e9))
    except Exception:
        # If clipping fails for any reason, fall back to safe numeric conversion
        try:
            fitness = float(fitness)
        except Exception:
            fitness = 0.0

    return fitness

def train_generation(population, df, predictions):
    """
    Runs one generation of the Rat against the Thoth Oracle.
    """
    scores = []
    
    # Pre-calculate market features to speed up loop
    # We need z-score and velocity
    # Simple proxies
    closes = df['close']
    pct = closes.pct_change()
    roll_std = pct.rolling(20).std()
    z_scores = (pct / roll_std).fillna(0)
    velocities = (pct.diff() / roll_std).fillna(0) # Proxy for velocity
    
    # Detect crash scenarios (large negative moves >10%)
    df['is_crash_candle'] = pct < -0.10
    
    # Pre-fetch live cosmic state once per generation to simulate generic cosmic state
    try:
        from services.telemetry import get_cosmic_influence
        pre_fetched_cosmic = get_cosmic_influence()
    except Exception:
        pre_fetched_cosmic = {}
    
    for genome in population:
        # 1. Equip ProphitNet with Genome
        prophit = ProphitNetStrategy()
        prophit.skills.update(genome)
        
        balance = 1000.0
        initial_balance = 1000.0
        position = 0.0
        entry_price = 0.0
        
        trades = 0
        wins = 0
        returns_history = []  # Track per-trade returns for fitness calculation
        crash_trades = []  # Track whether each recorded trade occurred during a crash scenario
        
        # Run Simulation
        # Skip first 20 for rolling window
        for t in range(20, len(df)-5):
            price = closes[t]

            # Skip invalid prices early to avoid numeric blow-ups later
            if not np.isfinite(price) or price <= 0 or price > 1e7:
                print(f"[TRAIN] Skipping invalid price at t={t}: {price}")
                continue

            # [SOVEREIGN MANIFOLD INJECTION]
            # Use pre-fetched cosmic state for this training run to avoid 500,000 HTTP requests
            cosmic = pre_fetched_cosmic

            # Construct State with 18D Omniscience
            state = {
                'price': price,
                'z_score': z_scores[t],
                'velocity': velocities[t],
                'prediction': predictions[t], # THE ORACLE
                'trend_strength': 0.0,
                # Inject Space Features
                'bt': cosmic.get('bt', 5.0),
                'bz': cosmic.get('bz', 0.0),
                'speed': cosmic.get('speed', 400.0),
                'density': cosmic.get('density', 5.0),
                'flare_score': cosmic.get('flare_score', 1.0),
                'pressure': cosmic.get('pressure', 1.0),
                'shield_open': cosmic.get('shield_open', 0.0),
                # Inject Seismic Features
                'vibration': cosmic.get('vibration', 0.0),
                'seismic_energy': cosmic.get('seismic_energy', 0.0),
                'max_quake': cosmic.get('max_quake', 0.0),
                'soul_pred': predictions[t].get('resonance', 0.5) # Map Oracle to LGNN Soul Pred
            }
            
            # Get Signal
            signal = prophit.on_tick(state)
            
            # Execution Logic (Simple Backtest)
            threshold = prophit.skills.get('confidence_gate', 0.20)
            if abs(signal) >= threshold and position == 0.0:
                # Open Position
                position = 1.0 if signal > 0 else -1.0
                entry_price = price
                trades += 1
                
            elif position != 0.0:
                # Check Exit (Profit Target or Stop)
                pnl_pct = (price - entry_price) / entry_price * position
                
                # Early numeric clamping (before balance update)
                # Clamp to ±50% max per trade to prevent numeric blow-up
                pnl_pct = np.clip(pnl_pct, -0.5, 0.5)
                
                # Check for NaN/Inf
                if not np.isfinite(pnl_pct):
                    print(f"[TRAIN] Invalid pnl_pct at t={t}: {pnl_pct} (entry={entry_price}, price={price})")
                    pnl_pct = 0.0
                
                # Check ProphitNet's internal profit target and stop loss
                target = prophit.skills.get('profit_target', 0.02)
                stop = prophit.skills.get('stop_loss', 0.015)
                
                if pnl_pct >= target or pnl_pct <= -stop:
                    # Close position
                    # Track return for fitness calculation (ensure finite)
                    if np.isfinite(pnl_pct):
                        returns_history.append(float(pnl_pct))
                    else:
                        # Record a safe zero return for non-finite values
                        returns_history.append(0.0)
                    
                    # Check if this trade occurred during a crash scenario
                    was_crash = bool(df.loc[t, 'is_crash_candle']) if t < len(df) else False
                    crash_trades.append(was_crash)
                    
                    # Apply PnL to balance (multiplicative update with clamped value)
                    # Ensure pnl_pct is within safe bounds and use the clamped value
                    safe_pnl = float(np.clip(pnl_pct, -0.5, 0.5))
                    balance *= (1.0 + safe_pnl)
                    
                    # Cap balance to a reasonable range to avoid runaway fitness numbers
                    if not np.isfinite(balance) or balance > 1e12 or balance < 1e-6:
                        print(f"[TRAIN] Clamping balance at t={t}: {balance}")
                        balance = float(np.clip(balance, 1e-6, 1e12))
                    
                    position = 0.0
                    if safe_pnl > 0:
                        wins += 1
                    
        # Fitness Function (robust, numerically stable)
        fitness = calculate_fitness(balance, initial_balance, trades, wins, returns_history, crash_trades)
            
        scores.append((genome, fitness, trades, wins))
        
    return scores

def evolve():
    print("[TRAIN] Entering Hyperbolic Time Chamber...")
    
    # 1. Load Data
    df = load_data(limit=5000)
    if df.empty:
        print("Error: No data found.")
        return None, 0.0
    print(f"[TRAIN] Loaded {len(df)} candles.")
    
    # 2. Generate Oracle
    print("[TRAIN] Casting Prismatic Oracle (Simulating Thoth)...")
    predictions = calculate_thoth_oracle(df)
    
    # 3. Initialize Population
    population = []
    for _ in range(20):
        # ProphitNet Genome (Balancing LGNN vs Physics)
        genome = {
            'soul_pan': random.uniform(0.1, 0.9),
            'confidence_gate': random.uniform(0.1, 0.4),
            'physics_limit': random.uniform(2.0, 5.0),
            'profit_target': random.uniform(0.01, 0.05),
            'stop_loss': random.uniform(0.01, 0.03),
            'velocity_dampener': random.uniform(0.5, 0.95),
            'topology_trust_multiplier': random.uniform(1.0, 2.5),
            'chaos_immunity': random.uniform(1.5, 4.0),
            'dynamic_sizing_factor': random.uniform(0.2, 0.8)
        }
        population.append(genome)
        
    # 4. Evolution Loop (Short & Intense)
    generations = 5
    best_genome = None
    best_fitness = -99999.0

    def _format_money(x):
        """Format large fitness values safely for display."""
        try:
            if x is None:
                return "N/A"
            # Use scientific notation for extremely large numbers to avoid ugly full-digit prints
            if isinstance(x, (int,)) and abs(x) > 1e12:
                return f"{x:.2e}"
            if abs(float(x)) > 1e12:
                return f"{float(x):.2e}"
            return f"{float(x):,.2f}"
        except Exception:
            return str(x)
    
    for g in range(generations):
        print(f"\n[TRAIN] Generation {g+1}/{generations}")
        results = train_generation(population, df, predictions)
        
        # Sort by Fitness
        results.sort(key=lambda x: x[1], reverse=True)
        
        top_performer = results[0]
        if top_performer[1] > best_fitness:
            best_fitness = top_performer[1]
            best_genome = top_performer[0]
            
        print(f"   [BEST] Fitness: ${_format_money(top_performer[1])} (Trades: {top_performer[2]}, Wins: {top_performer[3]})")
        print(f"   [GENES] {top_performer[0]}")
        
        # Selection & Mutation
        survivors = results[:5] 
        population = []
        
        # Elitism
        population.append(survivors[0][0])
        
        # Offspring
        while len(population) < 20:
            parent = random.choice(survivors)[0]
            child = parent.copy()
            # Mutate
            key = random.choice(list(child.keys()))
            child[key] *= random.uniform(0.8, 1.2)
            population.append(child)
            
    # 5. Save Champion Versioned
    print("\n[TRAIN] Saving Champion to Checkpoint...")
    checkpoint_data = {
        'population': [Champion(best_genome)], 
        'generation': 4000
    }
    
    timestamp = int(__import__('time').time())
    auto_dir = os.path.join(os.getcwd(), 'checkpoints', 'auto')
    os.makedirs(auto_dir, exist_ok=True)
    
    versioned_filename = f"prophit_omniscient_v{timestamp}.pkl"
    save_path = os.path.join(auto_dir, versioned_filename)
    
    with open(save_path, 'wb') as f:
        pickle.dump(checkpoint_data, f)
        
    print(f"[TRAIN] Training Complete. Artifact: {save_path}")
    print("   ProphitNet has achieved equilibrium between Body and Soul.")
    
    # 6. Auto-Verify Strategy (Phase 3: Universal Regime Verification)
    print("\n[VERIFY] Auto-Verifying Strategy on All Regimes...")
    try:
        from arena.strategy_verifier import verify_strategy, save_metadata
        metadata = verify_strategy(save_path, data_limit=5000)
        if metadata:
            save_metadata(save_path, metadata)
            is_universal = metadata.get('is_universal', False)
            universal_score = metadata.get('universal_score', 0.0)
            optimal_regime = metadata.get('optimal_regime', 'unknown')
            print(f"   [OK] Verification complete.")
            print(f"   - Universal: {is_universal}")
            print(f"   - Universal Score: {universal_score:.3f}")
            print(f"   - Optimal Regime: {optimal_regime}")
        else:
            print(f"   [WARN] Verification failed or skipped")
    except ImportError as e:
        print(f"   [WARN] Verification module not available: {e}")
    except Exception as e:
        print(f"   [WARN] Verification error (non-fatal): {e}")
        import traceback
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Verification traceback: {traceback.format_exc()}")
    
    # Return path and fitness for validation
    return save_path, best_fitness

if __name__ == "__main__":
    evolve()
