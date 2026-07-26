"""
Strategy Verification System
Tests strategies on multiple market regimes to identify universal vs regime-specific strategies.
"""

import sqlite3
import pandas as pd
import numpy as np
import pickle
import json
import os
import sys
from typing import Dict, Any, Optional, List, Tuple

# Add project root to path
sys.path.append(os.getcwd())

from arena.strategies.rat import TheRat
from arena.train_artifacts import (
    load_data, 
    calculate_fitness, 
    calculate_thoth_oracle,
    _validate_and_clean_data
)


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Average True Range (ATR) for volatility measurement.
    
    Args:
        df: DataFrame with OHLCV data (must have 'high', 'low', 'close' columns)
        period: Rolling window period for ATR calculation (default: 14)
    
    Returns:
        Series of ATR values as percentage of price
    """
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    # Convert to percentage of price
    atr_pct = (atr / close) * 100
    
    return atr_pct


def filter_regime_data(df: pd.DataFrame) -> Tuple[Dict[str, pd.DataFrame], Dict[str, pd.Series]]:
    """
    Split market data into different regimes and return index mappings.
    
    Returns:
        Tuple of (regime_dataframes, index_mappings)
        - regime_dataframes: Dict mapping regime name to filtered DataFrame
        - index_mappings: Dict mapping regime name to Series of original indices
    
    Regimes:
    - normal: Excludes >10% drops
    - crash: Only candles with >10% drops
    - high_volatility: ATR > 2%
    - low_volatility: ATR < 1%
    """
    # Calculate ATR
    df = df.copy()
    df['atr_pct'] = calculate_atr(df)
    
    # Calculate price change percentage
    df['pct_change'] = df['close'].pct_change()
    
    # Store original index before filtering
    df['original_index'] = df.index
    
    # Normal market (exclude crashes >10%)
    df_normal = df[df['pct_change'] >= -0.10].copy()
    df_normal = df_normal.reset_index(drop=True)
    idx_normal = df_normal['original_index'] if 'original_index' in df_normal.columns else pd.Series(dtype=int)
    
    # Crash market (only >10% drops)
    df_crash = df[df['pct_change'] < -0.10].copy()
    df_crash = df_crash.reset_index(drop=True)
    idx_crash = df_crash['original_index'] if 'original_index' in df_crash.columns else pd.Series(dtype=int)
    
    # High volatility (ATR > 2%)
    df_high_vol = df[df['atr_pct'] > 2.0].copy()
    df_high_vol = df_high_vol.reset_index(drop=True)
    idx_high_vol = df_high_vol['original_index'] if 'original_index' in df_high_vol.columns else pd.Series(dtype=int)
    
    # Low volatility (ATR < 1%)
    df_low_vol = df[df['atr_pct'] < 1.0].copy()
    df_low_vol = df_low_vol.reset_index(drop=True)
    idx_low_vol = df_low_vol['original_index'] if 'original_index' in df_low_vol.columns else pd.Series(dtype=int)
    
    # Remove helper column
    for df_regime in [df_normal, df_crash, df_high_vol, df_low_vol]:
        if 'original_index' in df_regime.columns:
            df_regime.drop(columns=['original_index'], inplace=True)
    
    regime_data = {
        'normal': df_normal,
        'crash': df_crash,
        'high_volatility': df_high_vol,
        'low_volatility': df_low_vol
    }
    
    index_mappings = {
        'normal': idx_normal,
        'crash': idx_crash,
        'high_volatility': idx_high_vol,
        'low_volatility': idx_low_vol
    }
    
    return regime_data, index_mappings


def _validate_dataframe(df: pd.DataFrame, min_rows: int = 25) -> bool:
    """Validate dataframe has sufficient data for testing."""
    if df is None or df.empty:
        return False
    if len(df) < min_rows:
        return False
    required_cols = ['close', 'high', 'low', 'open']
    if not all(col in df.columns for col in required_cols):
        return False
    return True


def _validate_predictions(predictions: List[Any], df_length: int) -> bool:
    """Validate predictions list matches dataframe length."""
    if predictions is None:
        return False
    if len(predictions) < df_length:
        return False
    return True


def _align_predictions_to_regime(
    predictions: List[Any], 
    original_indices: pd.Series
) -> List[Any]:
    """
    Align predictions list to regime dataframe using original indices.
    
    Args:
        predictions: Full predictions list indexed by original dataframe position
        original_indices: Series of original dataframe indices for this regime
    
    Returns:
        Filtered predictions list aligned to regime dataframe
    """
    if predictions is None or len(original_indices) == 0:
        return []
    
    regime_predictions = []
    for orig_idx in original_indices:
        if 0 <= orig_idx < len(predictions):
            regime_predictions.append(predictions[int(orig_idx)])
        else:
            regime_predictions.append(None)
    
    return regime_predictions


def test_strategy_on_regime(
    genome: Dict[str, Any], 
    df: pd.DataFrame, 
    predictions: List[Any]
) -> Dict[str, Any]:
    """
    Test a strategy genome on a specific regime dataset.
    
    Args:
        genome: Strategy genome (skills dict)
        df: Regime-filtered dataframe (must have reset index)
        predictions: Predictions list aligned to this regime dataframe
    
    Returns:
        Dict with keys: fitness, trades, wins, win_rate
    """
    # Validate inputs
    if not _validate_dataframe(df, min_rows=25):
        return {
            'fitness': 0.0,
            'trades': 0,
            'wins': 0,
            'win_rate': 0.0
        }
    
    if not _validate_predictions(predictions, len(df)):
        # If predictions don't match, use None for all (strategy will work without oracle)
        predictions = [None] * len(df)
    
    # Create Rat with genome
    rat = TheRat()
    rat.skills.update(genome)
    
    # Pre-calculate market features
    closes = df['close'].values
    pct = pd.Series(closes).pct_change()
    roll_std = pct.rolling(20).std()
    z_scores = (pct / roll_std).fillna(0).values
    velocities = (pct.diff() / roll_std).fillna(0).values
    
    # Initialize simulation state
    balance = 1000.0
    initial_balance = 1000.0
    position = 0.0
    entry_price = 0.0
    
    trades = 0
    wins = 0
    returns_history = []
    crash_trades = []  # Not used for regime-specific tests, but needed for fitness calc
    
    # Run simulation
    # Use integer indices since dataframe index was reset
    start_idx = 20  # Skip rolling window
    end_idx = len(df) - 5  # Leave room for predictions
    
    for i in range(start_idx, min(end_idx, len(df))):
        if i >= len(closes) or i < 0:
            continue
            
        price = closes[i]
        
        # Construct state
        state = {
            'price': price,
            'z_score': z_scores[i] if i < len(z_scores) else 0.0,
            'velocity': velocities[i] if i < len(velocities) else 0.0,
            'prediction': predictions[i] if i < len(predictions) else None,
            'trend_strength': 0.0
        }
        
        # Get signal
        try:
            signal = rat.on_tick(state)
        except Exception as e:
            # If strategy fails, skip this tick
            continue
        
        # Execution logic
        if signal != 0.0 and position == 0.0:
            # Open position
            position = signal
            entry_price = price
            trades += 1
            
        elif position != 0.0:
            # Check exit
            pnl_pct = (price - entry_price) / entry_price * position
            
            # Clamp to prevent numeric issues
            pnl_pct = np.clip(pnl_pct, -0.5, 0.5)
            
            if not np.isfinite(pnl_pct):
                pnl_pct = 0.0
            
            # Exit logic
            target = rat.skills.get('profit_target', 0.005)
            stop = target * 0.5
            
            if pnl_pct >= target or pnl_pct <= -stop:
                returns_history.append(pnl_pct)
                crash_trades.append(False)  # Not tracking crash for regime tests
                
                balance *= (1.0 + pnl_pct)
                
                if not np.isfinite(balance):
                    balance = initial_balance
                
                position = 0.0
                if pnl_pct > 0:
                    wins += 1
    
    # Calculate fitness
    fitness = calculate_fitness(balance, initial_balance, trades, wins, returns_history, crash_trades)
    win_rate = wins / trades if trades > 0 else 0.0
    
    return {
        'fitness': fitness,
        'trades': trades,
        'wins': wins,
        'win_rate': win_rate
    }


def calculate_regime_fitness(
    genome: Dict[str, Any], 
    regime_data: Dict[str, pd.DataFrame],
    index_mappings: Dict[str, pd.Series],
    all_predictions: List[Any]
) -> Dict[str, Dict[str, Any]]:
    """
    Calculate fitness for each regime with properly aligned predictions.
    
    Args:
        genome: Strategy genome (skills dict)
        regime_data: Dict mapping regime name to filtered DataFrame
        index_mappings: Dict mapping regime name to Series of original indices
        all_predictions: Full predictions list indexed by original dataframe position
    
    Returns:
        Dict with regime names as keys and performance metrics as values
    """
    results = {}
    
    for regime_name, df_regime in regime_data.items():
        # Get original indices for this regime
        original_indices = index_mappings.get(regime_name, pd.Series(dtype=int))
        
        # Align predictions to regime dataframe
        regime_predictions = _align_predictions_to_regime(all_predictions, original_indices)
        
        # Test strategy on this regime
        try:
            result = test_strategy_on_regime(genome, df_regime, regime_predictions)
            results[regime_name] = result
        except Exception as e:
            # If testing fails, return zero fitness
            print(f"[VERIFIER] ⚠️  Error testing {regime_name} regime: {e}")
            results[regime_name] = {
                'fitness': 0.0,
                'trades': 0,
                'wins': 0,
                'win_rate': 0.0
            }
    
    return results


def is_universal_strategy(
    regime_fitness: Dict[str, Dict[str, Any]], 
    threshold: float = 100.0
) -> bool:
    """
    Check if strategy performs above threshold in all regimes.
    
    Args:
        regime_fitness: Dict mapping regime names to performance metrics
        threshold: Minimum fitness required in each regime to be considered universal
    
    Returns:
        True if strategy meets threshold in all regimes, False otherwise
    """
    for regime_name, metrics in regime_fitness.items():
        fitness = metrics.get('fitness', 0.0)
        if fitness < threshold:
            return False
    return True


def calculate_universal_score(regime_fitness: Dict[str, Dict[str, Any]]) -> float:
    """
    Calculate normalized universal score (0-1) as average normalized fitness across all regimes.
    
    Args:
        regime_fitness: Dict mapping regime names to performance metrics
    
    Returns:
        Universal score between 0.0 and 1.0 (higher = more universal)
    """
    fitnesses = [metrics.get('fitness', 0.0) for metrics in regime_fitness.values()]
    
    if not fitnesses or all(f == 0 for f in fitnesses):
        return 0.0
    
    # Normalize each fitness to 0-1 range (assuming max reasonable fitness ~2000)
    max_fitness = max(fitnesses) if fitnesses else 1.0
    if max_fitness == 0:
        return 0.0
    
    normalized = [f / max_fitness for f in fitnesses]
    
    # Average normalized fitness
    return sum(normalized) / len(normalized)


def find_optimal_regime(regime_fitness: Dict[str, Dict[str, Any]]) -> str:
    """
    Find the regime where strategy performs best.
    
    Args:
        regime_fitness: Dict mapping regime names to performance metrics
    
    Returns:
        Name of the optimal regime (defaults to 'normal' if all have zero fitness)
    """
    best_regime = None
    best_fitness = -99999.0
    
    for regime_name, metrics in regime_fitness.items():
        fitness = metrics.get('fitness', 0.0)
        if fitness > best_fitness:
            best_fitness = fitness
            best_regime = regime_name
    
    return best_regime or 'normal'


def verify_strategy(checkpoint_path: str, data_limit: int = 10000) -> Optional[Dict[str, Any]]:
    """
    Verify a strategy checkpoint on all market regimes.
    
    Args:
        checkpoint_path: Path to .pkl checkpoint file
        data_limit: Number of candles to load for testing
    
    Returns:
        Metadata dict with verification results, or None if verification failed
    """
    print(f"[VERIFIER] Testing checkpoint: {checkpoint_path}")
    
    # Load checkpoint
    try:
        with open(checkpoint_path, 'rb') as f:
            data = pickle.load(f)
            population = data.get('population', [])
            
            if not population:
                print(f"[VERIFIER] ⚠️  Checkpoint has no population")
                return None
            
            # Get champion (first in population)
            champion = population[0]
            if hasattr(champion, 'skills'):
                genome = champion.skills
            elif isinstance(champion, dict):
                genome = champion
            else:
                print(f"[VERIFIER] ⚠️  Unknown champion format")
                return None
                
    except Exception as e:
        print(f"[VERIFIER] ❌ Failed to load checkpoint: {e}")
        return None
    
    # Load market data
    df = load_data(limit=data_limit)
    if df.empty:
        print(f"[VERIFIER] ❌ No market data available")
        return None
    
    # Generate predictions (Thoth Oracle)
    predictions = calculate_thoth_oracle(df)
    
    if not predictions or len(predictions) != len(df):
        print(f"[VERIFIER] ⚠️  Predictions length mismatch, generating fallback")
        predictions = [None] * len(df)
    
    # Filter into regimes (returns dataframes and index mappings)
    regime_data, index_mappings = filter_regime_data(df)
    
    # Test on each regime
    print(f"[VERIFIER] Testing on {len(regime_data)} regimes...")
    regime_fitness = calculate_regime_fitness(genome, regime_data, index_mappings, predictions)
    
    # Calculate metadata
    is_universal = is_universal_strategy(regime_fitness, threshold=100.0)
    universal_score = calculate_universal_score(regime_fitness)
    optimal_regime = find_optimal_regime(regime_fitness)
    
    # Build metadata
    checkpoint_name = os.path.basename(checkpoint_path)
    metadata = {
        'checkpoint': checkpoint_name,
        'verified': True,
        'regime_performance': regime_fitness,
        'optimal_regime': optimal_regime,
        'is_universal': is_universal,
        'universal_score': round(universal_score, 3)
    }
    
    # Print summary
    print(f"[VERIFIER] ✅ Verification complete:")
    print(f"  - Universal: {is_universal}")
    print(f"  - Universal Score: {universal_score:.3f}")
    print(f"  - Optimal Regime: {optimal_regime}")
    for regime, metrics in regime_fitness.items():
        print(f"  - {regime}: fitness={metrics['fitness']:.2f}, trades={metrics['trades']}, win_rate={metrics['win_rate']:.3f}")
    
    return metadata


def save_metadata(checkpoint_path: str, metadata: Dict[str, Any]) -> None:
    """
    Save metadata JSON file alongside checkpoint.
    
    Args:
        checkpoint_path: Path to checkpoint .pkl file
        metadata: Metadata dictionary to save
    
    Raises:
        IOError: If file cannot be written
    """
    checkpoint_dir = os.path.dirname(checkpoint_path)
    checkpoint_name = os.path.basename(checkpoint_path)
    
    # Replace .pkl with .metadata.json
    metadata_name = checkpoint_name.replace('.pkl', '.metadata.json')
    metadata_path = os.path.join(checkpoint_dir, metadata_name)
    
    try:
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        print(f"[VERIFIER] 💾 Saved metadata: {metadata_path}")
    except Exception as e:
        print(f"[VERIFIER] ❌ Failed to save metadata: {e}")


def load_metadata(checkpoint_path: str) -> Optional[Dict[str, Any]]:
    """Load metadata JSON file for a checkpoint."""
    checkpoint_dir = os.path.dirname(checkpoint_path)
    checkpoint_name = os.path.basename(checkpoint_path)
    
    metadata_name = checkpoint_name.replace('.pkl', '.metadata.json')
    metadata_path = os.path.join(checkpoint_dir, metadata_name)
    
    if not os.path.exists(metadata_path):
        return None
    
    try:
        with open(metadata_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"[VERIFIER] ⚠️  Failed to load metadata: {e}")
        return None


if __name__ == "__main__":
    # Test verification on a single checkpoint
    import glob
    
    checkpoints = glob.glob(os.path.join(os.getcwd(), "checkpoints", "auto", "*.pkl"))
    if checkpoints:
        test_checkpoint = checkpoints[0]
        metadata = verify_strategy(test_checkpoint)
        if metadata:
            save_metadata(test_checkpoint, metadata)
    else:
        print("[VERIFIER] No checkpoints found to test")
