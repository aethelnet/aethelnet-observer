import os
import sys
import numpy as np
import pandas as pd
import asyncio

# Ensure project root is in path
sys.path.append(os.getcwd())

from services.data_manager import get_data_manager

async def rat_live_probe():
    print("🦾⚔️🐀🛡️👑 RAT LIVE SIGMA PROBE 👑🛡️ Silvia-High-Mode 🦾")
    dm = get_data_manager()
    
    # Symbols to probe
    symbols = ["KPEPEUSDC", "KSHIBUSDC", "KETHUSDC", "KBTCUSDC", "KSOLUSDC"]
    
    print(f"{'SYMBOL':<15} | {'PRICE':<10} | {'SIGMA (11m)':<12} | {'STATUS':<20}")
    print("-" * 65)
    
    for symbol in symbols:
        try:
            # Fetch last 11 candles
            data = dm.get_data(symbol, '1m', limit=20)
            if not data or len(data) < 11:
                print(f"{symbol:<15} | {'N/A':<10} | {'N/A':<12} | {'Warm-up Needed':<20}")
                continue
                
            closes = np.array([float(d['close']) for d in data])
            current_price = closes[-1]
            
            # Rat Physics (Last 11)
            lookback = 11
            rolling_slice = closes[-lookback:]
            ma = np.mean(rolling_slice)
            std = np.std(rolling_slice)
            sigma = (current_price - ma) / std if std > 1e-6 else 0.0
            
            status = "SILENT PREDATOR"
            if abs(sigma) > 1.5: status = "ALERT"
            if abs(sigma) > 2.0: status = "CUSP APPROACHING"
            if abs(sigma) > 2.9: status = "SCORPIO STING! 🦂"
            
            print(f"{symbol:<15} | {current_price:<10.4f} | {sigma:<12.4f} | {status:<20}")
            
        except Exception as e:
            print(f"{symbol:<15} | ERROR: {str(e)}")

    print("\n[Audit] Threshold: 2.9 Sigma")
    print("🦾⚔️🐀🛡️👑 PROBE COMPLETE 👑🛡️🐀⚔️🦾")

if __name__ == "__main__":
    asyncio.run(rat_live_probe())
