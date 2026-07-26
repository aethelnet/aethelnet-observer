#!/usr/bin/env python3
import sys
import os
import logging
import pandas as pd
import numpy as np

# Add project root to path
sys.path.insert(0, os.getcwd())

from scripts.test_component_impact import ComponentImpactTester
from config.test_configs import ALL_TEST_CONFIGS

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("ProfitOptimizer")

def run_sweep(days=3):
    print(f"--- SOVEREIGN PROFIT SWEEP (Last {days} Days) ---")
    print("Finding the path to maximum capital acceleration...")
    
    thresholds = [0.5, 0.8, 1.0, 1.2, 1.5, 1.8, 2.0, 2.2, 2.5, 2.8, 3.0, 3.2, 3.5]
    results = []

    # Base config for Sovereign mode
    base_config = {
        'name': 'sweep_temp',
        'description': 'Temporary sweep config',
        'SIGNAL_THRESHOLD': 0.8,
        'IGNORE_REGIME_FILTER': True,
        'USE_STRATEGY_ENSEMBLE': False,
        'USE_RAT_MEAN_REVERSION': False,
        'SIGNAL_PERSISTENCE': 2,
        'MAX_POSITION_SIZE': 0.15 # Use large relative size for small account simulation
    }

    for t in thresholds:
        # Create tester with custom threshold
        tester = ComponentImpactTester('baseline', days_back=days)
        tester.config = base_config.copy()
        tester.config['SIGNAL_THRESHOLD'] = t
        
        # Run simulation
        tester.run_simulation()
        
        m = tester.metrics
        results.append({
            'Threshold': t,
            'PnL_USD': m['total_pnl'],
            'Trades': m['total_trades'],
            'WinRate': m['win_rate'],
            'Sharpe': m['sharpe_ratio']
        })
        print(f"Tested Threshold {t:.1f}: PnL ${m['total_pnl']:>7.2f} | Trades: {m['total_trades']:>3} | WinRate: {m['win_rate']:>5.1f}%")

    df = pd.DataFrame(results)
    
    print("\n--- SWEEP RESULTS TABLE ---")
    print(df.to_string(index=False))
    
    best_pnl = df.loc[df['PnL_USD'].idxmax()]
    print(f"\n🏆 WINNER: Threshold {best_pnl['Threshold']:.2f}")
    print(f"Estimated Profit: ${best_pnl['PnL_USD']:.2f} (with {best_pnl['Trades']} trades)")
    print(f"Win Rate: {best_pnl['WinRate']:.1f}%")
    
    current_val = 0.809
    print(f"\nYour current value (0.809) vs Winner ({best_pnl['Threshold']:.2f}):")
    if best_pnl['Threshold'] < current_val:
        print("ADVICE: You could be MORE aggressive to capture more moves.")
    elif best_pnl['Threshold'] > current_val:
        print("ADVICE: You should be MORE selective to avoid noise.")
    else:
        print("ADVICE: Your value is mathematically OPTIMAL for the recent market.")

if __name__ == "__main__":
    run_sweep(days=3)
