
import sys
import os
import torch
import numpy as np
import pandas as pd
import time
from datetime import datetime

# Setup paths
sys.path.append("/var/home/nhrlyn/Projects/auratic-systems-prime")

from incubator.temporal_fusion import TemporalFusionEngine
from services.data_manager import get_data_manager
from services.brain import get_engine

def run_verification(symbol="BTCUSDC"):
    print(f"\n--- TFT FORENSIC AUDIT: {symbol} ---")
    
    # 1. Initialize Engine
    tft = TemporalFusionEngine()
    dm = get_data_manager()
    
    # 2. Fetch Historical 5m Data (Last 200 candles)
    print("Fetching 5m historical data...")
    df = dm.get_latest_ohlcv_df(symbol, "5m", limit=200)
    
    if df.empty or len(df) < 20:
        print("Error: Not enough data.")
        return
    
    # 3. Sliding Window Evaluation
    # We take 10 candles, predict next, compare to actual
    predictions = []
    actuals = []
    
    print(f"Running back-inference on {len(df)-11} windows...")
    
    for i in range(len(df) - 11):
        # Slice window
        window = df.iloc[i : i+10]
        target = df.iloc[i+10]['close']
        prev_close = df.iloc[i+9]['close']
        
        # Prepare Features (simplified version of beacon_service.py logic)
        features = []
        for _, row in window.iterrows():
            f = [
                row['open'], row['high'], row['low'], row['close'], row['volume'],
                0, 0, 0, 0, 0 # Padding velocity etc for now
            ]
            f.extend([0] * (20 - len(f)))
            features.append(f)
        
        dynamic_features = np.array(features)
        static_features = np.zeros(5) # [regime, gas, spike, conf, sig]
        
        # Predict
        preds, _ = tft.predict(dynamic_features, static_features)
        tft_signal = float(preds[1]) # Median
        
        # actual_move
        actual_move = (target - prev_close) / prev_close
        
        predictions.append(1 if tft_signal > 0 else -1)
        actuals.append(1 if actual_move > 0 else -1)
        
    # 4. Accuracy Calculation
    predictions = np.array(predictions)
    actuals = np.array(actuals)
    
    matches = (predictions == actuals)
    accuracy = np.mean(matches) * 100
    
    print(f"RESULTS for {symbol}:")
    print(f"Total Windows: {len(matches)}")
    print(f"Directional Accuracy: {accuracy:.2f}%")
    
    if 48 < accuracy < 52:
        print("STATUS: 🎲 RANDOM WALK (Weights are likely uninitialized/random)")
    elif accuracy > 55:
        print("STATUS: 📈 TRAINED (Model shows predictive alpha)")
    else:
        print("STATUS: 📉 INVERSE ALPHA (Model is worse than a coin flip)")

if __name__ == "__main__":
    run_verification("BTCUSDC")
    run_verification("ETHUSDC")
