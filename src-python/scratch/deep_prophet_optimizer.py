#!/usr/bin/env python3
import sys
import os
import asyncio
import logging
import pandas as pd
import numpy as np
import sqlite3
import time
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.getcwd())

from services.brain_full import BrainEngine
from services.database import get_database

# Suppress logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger("ProphetOptimizer")

# Mock settings for Sovereign mode
class MockSettings:
    ORACLE_SOUL_PAN = 1.0
    NEURAL_CUBIC_SCALAR = 0.5
    DB_PATH = "market_data.db"

settings = MockSettings()

# Monkey-patch get_settings
import config
config.get_settings = lambda: settings
import services.brain_full
services.brain_full.get_settings = lambda: settings

async def run_deep_optimizer(days=3):
    print(f"--- DEEP PROPHET OPTIMIZER (Last {days} Days) ---")
    print("Initializing BrainEngine (The Prophet)...")
    
    engine = BrainEngine()
    db = get_database()
    
    # 1. Load Data
    print("Loading historical OHLCV data...")
    symbol = "BTCUSDC"
    with sqlite3.connect('market_data.db') as conn:
        sql = f"SELECT timestamp, open, high, low, close, volume FROM ohlcv WHERE symbol = '{symbol}' AND timestamp >= datetime('now', '-{days} days') ORDER BY timestamp ASC"
        df = pd.read_sql_query(sql, conn)
    
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    if df.empty:
        print("No data found!")
        return

    print(f"Loaded {len(df)} 1m candles.")
    
    # 2. Pre-calculate Signals
    print("Synthesizing Prophet signals...")
    signals = []
    prices = df['close'].tolist()
    
    warmup = 100
    for i in range(len(df)):
        ts_ms = int(df.iloc[i]['timestamp'].timestamp() * 1000)
        await engine.ingest_candle(ts_ms, df.iloc[i]['close'], df.iloc[i]['volume'], symbol)
        
        if i >= warmup:
            # Get metrics
            res = engine.get_latest_metrics(symbol)
            # In Sovereign mode, neural_signal is the fused soul signal
            sig = res.get('neural_signal', 0.0)
            ml_prob = res.get('ml_probability', 0.5)
            source = res.get('ml_source', 'UNKNOWN')
            
            signals.append({'price': prices[i], 'signal': sig})
            
            if i % 100 == 0:
                print(f"Candle {i}: Signal {sig:.2f} | Prob {ml_prob:.3f} | Source {source}")

    print(f"\nGenerated {len(signals)} Prophet signals.")

    # 3. Sweep Thresholds (Reflecting 0-5.0 scale)
    thresholds = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5]
    fee_pct = 0.0005 
    results = []

    for t in thresholds:
        capital = 1000.0
        position = None
        trades_count = 0
        wins = 0
        
        for i in range(len(signals)):
            s = signals[i]
            sig = s['signal']
            price = s['price']
            
            if position is None:
                if abs(sig) >= t:
                    side = "BUY" if sig > 0 else "SELL"
                    capital -= capital * fee_pct
                    position = {'side': side, 'price': price}
                    trades_count += 1
            
            elif position:
                pnl_pct = 0
                exit = False
                if position['side'] == "BUY":
                    pnl_pct = (price - position['price']) / position['price']
                    if sig < 0: exit = True
                else:
                    pnl_pct = (position['price'] - price) / position['price']
                    if sig > 0: exit = True
                
                if pnl_pct <= -0.015 or pnl_pct >= 0.04 or exit: # Tighter SL for 3 days
                    capital += capital * pnl_pct
                    capital -= capital * fee_pct
                    if pnl_pct > 0: wins += 1
                    position = None

        final_pnl = capital - 1000.0
        wr = (wins / trades_count * 100) if trades_count > 0 else 0
        results.append({'Threshold': t, 'PnL': final_pnl, 'Trades': trades_count, 'WinRate': wr})
        print(f"Threshold {t}: PnL ${final_pnl:>7.2f} | Trades: {trades_count:>4} | WinRate: {wr:>5.1f}%")

    res_df = pd.DataFrame(results)
    print("\n--- SOVEREIGN OPTIMIZATION TABLE ---")
    print(res_df.to_string(index=False))

if __name__ == "__main__":
    asyncio.run(run_deep_optimizer(days=3))
