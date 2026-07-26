import sys
import os
import asyncio
import pandas as pd
import numpy as np

# Add project root
sys.path.append(os.getcwd())

from services.data_manager import get_data_manager
from services.layer_tracker import get_layer_tracker

async def measure_resonance_thresholds():
    print("--- 🕵️ FORENSIC BAROMETER: RESONANCE MEASUREMENT ---")
    
    dm = get_data_manager()
    tracker = get_layer_tracker()
    
    symbols = ["BTCUSDC", "ETHUSDC", "SOLUSDC"]
    all_max_confs = []
    
    for symbol in symbols:
        print(f"Measuring {symbol}...")
        df = dm.get_latest_ohlcv_df(symbol, interval="1m", limit=500)
        if df is None or len(df) < 100:
            continue
            
        for i in range(len(df) - 100, len(df)):
            # Simulating market state for tracker
            # We use a slight variation to see how KNN reacts to different Z-scores
            for z_test in [0.5, 1.5, 2.5]:
                weights = tracker.get_dynamic_weights(current_z=z_test, current_volatility=0.02, current_entropy=0.5)
                if weights:
                    max_c = max(weights.values())
                    all_max_confs.append(max_c)
                    
    if not all_max_confs:
        print("No data collected.")
        return

    all_max_confs.sort()
    
    print("\n--- 📊 RESONANCE DISTRIBUTION (MAX CONFIDENCE) ---")
    print(f"Sample Size: {len(all_max_confs)} points")
    print(f"Absolute Max: {max(all_max_confs):.4f}")
    print(f"99th Percentile (Elite): {np.percentile(all_max_confs, 99):.4f}")
    print(f"95th Percentile (Strong): {np.percentile(all_max_confs, 95):.4f}")
    print(f"90th Percentile (Active): {np.percentile(all_max_confs, 90):.4f}")
    print(f"75th Percentile (Normal): {np.percentile(all_max_confs, 75):.4f}")
    print(f"Median: {np.percentile(all_max_confs, 50):.4f}")
    
    print("\n--- ⚖️ RECOMMENDED THRESHOLDS ---")
    p95 = np.percentile(all_max_confs, 95)
    print(f"For 'Rare/Elite' Signals (Top 5%): Set to {p95:.3f}")
    p90 = np.percentile(all_max_confs, 90)
    print(f"For 'Active' Signals (Top 10%):  Set to {p90:.3f}")

if __name__ == "__main__":
    asyncio.run(measure_resonance_thresholds())
