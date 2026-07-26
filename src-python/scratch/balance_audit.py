import sys
import os
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime
import logging

# Setup Pathing
sys.path.append(os.getcwd())

from services.data_manager import get_data_manager
from services.brain_full import get_engine
from config import get_settings
from incubator.oracle import Oracle

async def run_balance_audit():
    print("\n" + "="*60)
    print("      ORACLE BALANCE SHEET: COMPONENT CONTRIBUTION AUDIT")
    print("="*60)

    settings = get_settings()
    dm = get_data_manager()
    engine = get_engine()
    oracle = Oracle()
    
    db_path = "market_data.db"
    import sqlalchemy
    local_engine = sqlalchemy.create_engine(f"sqlite:///{db_path}")
    
    symbol = "BTCUSDC"
    try:
        with local_engine.connect() as conn:
            query = sqlalchemy.text(f"SELECT * FROM ohlcv WHERE symbol='{symbol}' AND interval='1m' ORDER BY timestamp DESC LIMIT 1440")
            df = pd.read_sql(query, conn)
        df = df.iloc[::-1].reset_index(drop=True)
    except Exception as e:
        print(f"❌ DB ERROR: {e}")
        return

    contributions = {
        'swarm': [],
        'soul': [],
        'hindsight': []
    }
    
    trade_count = 0
    
    for i in range(50, len(df)):
        current_row = df.iloc[i]
        ts_dt = datetime.fromisoformat(current_row['timestamp']) if isinstance(current_row['timestamp'], str) else datetime.fromtimestamp(int(current_row['timestamp'])/1000)
        price = float(current_row['close'])
        
        await engine.ingest_candle(int(ts_dt.timestamp() * 1000), price, float(current_row['volume']), symbol=symbol)
        state = engine._get_state(symbol)
        state['symbol'] = symbol
        
        diag = oracle.calculate_truth_score_verbose(state)
        truth_score = diag['truth_score']
        
        if abs(truth_score) > settings.SIGNAL_THRESHOLD:
            trade_count += 1
            # Calculate absolute contribution of each pillar
            # We look at: current_weight * pillar_value
            # Note: verbose output doesn't directly give the final weighted value per pillar in a simple way, 
            # so we re-derive it from the diag output keys.
            
            # Simplified: we use the weights from oracle.weights and raw values from diag
            w_swarm = oracle.weights['swarm']
            w_soul = oracle.weights['soul']
            w_hind = oracle.weights['hindsight']
            
            v_swarm = diag['swarm']['raw']
            v_soul = diag['soul']['raw']
            v_hind = diag['hindsight']['raw']
            
            total_abs = abs(v_swarm * w_swarm) + abs(v_soul * w_soul) + abs(v_hind * w_hind)
            
            if total_abs > 0:
                contributions['swarm'].append(abs(v_swarm * w_swarm) / total_abs)
                contributions['soul'].append(abs(v_soul * w_soul) / total_abs)
                contributions['hindsight'].append(abs(v_hind * w_hind) / total_abs)

    print(f"\n[ANALYSIS] Processed {trade_count} trades for balance verification.")
    
    if trade_count > 0:
        avg_swarm = np.mean(contributions['swarm']) * 100
        avg_soul = np.mean(contributions['soul']) * 100
        avg_hind = np.mean(contributions['hindsight']) * 100
        
        print("\n--- PILLAR CONTRIBUTION BREAKDOWN ---")
        print(f"🏛️  SWARM (Physics)   : {avg_swarm:6.1f}%")
        print(f"👻  SOUL (ML)        : {avg_soul:6.1f}%")
        print(f"📜  HINDSIGHT (Mem)  : {avg_hind:6.1f}%")
        print("--------------------------------------")
        
        if max(avg_swarm, avg_soul, avg_hind) > 70:
            print("⚠️  WARNING: System is dominated by one pillar.")
        elif min(avg_swarm, avg_soul, avg_hind) < 10:
            print("⚠️  WARNING: One pillar is effectively silenced.")
        else:
            print("✅ BALANCE: The Oracle is synthesized harmoniously.")

    print("\n" + "="*60)

if __name__ == "__main__":
    asyncio.run(run_balance_audit())
