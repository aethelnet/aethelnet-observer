import sys
import os
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# Setup Pathing
sys.path.append(os.getcwd())

from dotenv import load_dotenv
load_dotenv()

from services.data_manager import get_data_manager
from services.brain_full import get_engine
from services.tracker import get_performance_tracker
from config import get_settings
from incubator.oracle import Oracle

async def run_sovereign_audit():
    print("\n" + "="*60)
    print("      SOVEREIGN HARMONY & PROFIT AUDIT (V2)")
    print("="*60)

    settings = get_settings()
    dm = get_data_manager()
    engine = get_engine()
    oracle = Oracle()
    tracker = get_performance_tracker()
    
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

    # Simulation State
    balance = 10000.0 
    position_size = 1000.0 
    fee_rate = 0.0002 
    
    trades = []
    active_position = None
    contributions = {'swarm': [], 'soul': [], 'hindsight': []}
    
    print(f"\n[1/3] Warming up the BrainEngine (1000 candles)...")
    for i in range(1000):
        current_row = df.iloc[i]
        ts_dt = datetime.fromisoformat(current_row['timestamp']) if isinstance(current_row['timestamp'], str) else datetime.fromtimestamp(int(current_row['timestamp'])/1000)
        price = float(current_row['close'])
        await engine.ingest_candle(int(ts_dt.timestamp() * 1000), price, float(current_row['volume']), symbol=symbol)
        
    print(f"\n[2/3] Simulating remaining {len(df)-1000}m with Dynamic Signal Decay Exits...")

    for i in range(1000, len(df)):
        current_row = df.iloc[i]
        ts_dt = datetime.fromisoformat(current_row['timestamp']) if isinstance(current_row['timestamp'], str) else datetime.fromtimestamp(int(current_row['timestamp'])/1000)
        price = float(current_row['close'])
        
        # A. Neural Processing
        await engine.ingest_candle(int(ts_dt.timestamp() * 1000), price, float(current_row['volume']), symbol=symbol)
        
        # B. Manually build the state
        state = tracker._collect_oracle_signals(symbol, price, engine, settings)
        
        # DEBUG: Check first candle for Rat signals
        if i == 1000:
            print(f"DEBUG: Rat signal check (i=1000):")
            for k in state:
                if 'rat' in k:
                    print(f"  {k}: {state[k]:.4f}")
        
        diag = oracle.calculate_truth_score_verbose(state)
        truth_score = diag['truth_score']
        
        # C. Exit Logic
        if active_position:
            entry_truth = active_position['entry_truth']
            decayed = abs(truth_score) < (abs(entry_truth) * 0.25)
            opposite = (active_position['type'] == 'BUY' and truth_score < 0) or \
                       (active_position['type'] == 'SELL' and truth_score > 0)
            timeout = (i - active_position['entry_idx']) > 240
            
            if decayed or opposite or timeout:
                entry_price = active_position['entry_price']
                pnl_pct = (price - entry_price) / entry_price if active_position['type'] == 'BUY' else (entry_price - price) / entry_price
                pnl_usd = (position_size * pnl_pct) - (position_size * fee_rate * 2)
                balance += pnl_usd
                trades.append({'pnl_usd': pnl_usd, 'type': active_position['type']})
                active_position = None

        # D. Entry Logic
        if not active_position and abs(truth_score) > settings.SIGNAL_THRESHOLD:
            active_position = {
                'type': 'BUY' if truth_score > 0 else 'SELL',
                'entry_price': price,
                'entry_idx': i,
                'entry_truth': truth_score
            }
            
            # Record Balance
            w_swarm, w_soul, w_hind = oracle.weights['swarm'], oracle.weights['soul'], oracle.weights['hindsight']
            v_swarm, v_soul, v_hind = diag['swarm']['raw'], diag['soul']['raw'], diag['hindsight']['raw']
            
            print(f"\n[TRADE TRIGGERED] Index: {i}, Price: {price}")
            print(f"  Truth Score : {truth_score:.4f}")
            print(f"  Swarm Raw   : {v_swarm:.4f}")
            print(f"  Soul Raw    : {v_soul:.4f}")
            
            total_abs = abs(v_swarm * w_swarm) + abs(v_soul * w_soul) + abs(v_hind * w_hind)
            if total_abs > 0:
                contributions['swarm'].append(abs(v_swarm * w_swarm) / total_abs)
                contributions['soul'].append(abs(v_soul * w_soul) / total_abs)
                contributions['hindsight'].append(abs(v_hind * w_hind) / total_abs)

    # Results
    total_pnl = balance - 10000.0
    wins = [t for t in trades if t['pnl_usd'] > 0]
    win_rate = (len(wins) / len(trades) * 100) if trades else 0
    
    print(f"\n[2/3] PERFORMANCE RESULTS:")
    print("-" * 30)
    print(f"Total Trades        : {len(trades)}")
    print(f"Win Rate            : {win_rate:.1f}%")
    print(f"Total PnL ($)       : ${total_pnl:+.2f}")
    print("-" * 30)

    if trade_count := len(contributions['swarm']):
        print(f"\n[3/3] PILLAR BALANCE SHEET:")
        print("-" * 30)
        print(f"🏛️  SWARM (Physics)   : {np.mean(contributions['swarm'])*100:6.1f}%")
        print(f"👻  SOUL (ML)        : {np.mean(contributions['soul'])*100:6.1f}%")
        print(f"📜  HINDSIGHT (Mem)  : {np.mean(contributions['hindsight'])*100:6.1f}%")
        print("-" * 30)
        print("✅ SYNTHESIS HARMONIOUS." if max(np.mean(list(contributions.values()), axis=1)) < 0.7 else "⚠️ DOMINANCE DETECTED.")

    print("\n" + "="*60)

if __name__ == "__main__":
    asyncio.run(run_sovereign_audit())
