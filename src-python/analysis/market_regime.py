import logging
from typing import Dict, List, Optional
import pandas as pd

logger = logging.getLogger("Analysis.MarketRegime")

def analyze_universe(layers: Dict[str, List[str]], metrics_df: pd.DataFrame) -> Dict:
    """
    Analyze the classified universe to determine global market regime and physics.
    """
    core_symbols = layers.get('core', [])
    
    config = get_simulation_config(core_symbols, metrics_df)
    
    return {
        "regime": config['regime'],
        "physics": config
    }

def get_simulation_config(core_symbols: List[str], metrics_df: pd.DataFrame) -> Dict:
    """
    Determine the global physics parameters based on the market regime.
    """
    if metrics_df.empty or not core_symbols:
        # Default / Stagnant
        return {
            "gravity": 0.05,
            "friction": 0.9,
            "repulsion": 200,
            "regime": "Neutral"
        }

    # Filter metrics for Core symbols
    # We need to ensure metrics_df has 'symbol' column
    if 'symbol' not in metrics_df.columns:
            return {
            "gravity": 0.05,
            "friction": 0.9,
            "repulsion": 200,
            "regime": "Neutral"
        }

    core_metrics = metrics_df[metrics_df['symbol'].isin(core_symbols)]
    
    if core_metrics.empty:
            return {
            "gravity": 0.05,
            "friction": 0.9,
            "repulsion": 200,
            "regime": "Neutral"
        }

    avg_volatility = core_metrics['volatility'].mean()
    avg_momentum = core_metrics['momentum'].mean() if 'momentum' in core_metrics.columns else 0
    
    # Normalize Drift (-1 to 1)
    # Assuming momentum is roughly -100 to 100, we scale it down
    drift = max(-1.0, min(1.0, avg_momentum / 50.0))
    
    # Regime Logic
    config = {
        "drift": drift,
        "volatility": avg_volatility,
        "regime": "Neutral",
        "gravity": 0.05,
        "friction": 0.9,
        "repulsion": 200
    }

    if avg_volatility > 5.0: # Extreme Volatility
        config.update({
            "gravity": 0.01, # Weak gravity (Fracture)
            "friction": 0.5, # Low friction (Chaos)
            "repulsion": 800, # High repulsion (Scatter)
            "regime": "Crash/Panic"
        })
    elif avg_volatility > 2.0: # Active
        config.update({
            "gravity": 0.03,
            "friction": 0.8, # Medium friction
            "repulsion": 300,
            "regime": "Active"
        })
    else: # Stagnant
        config.update({
            "gravity": 0.08, # Strong gravity (Clumping)
            "friction": 0.95, # High friction (Frozen)
            "repulsion": 100,
            "regime": "Stagnant"
        })
        
    return config
