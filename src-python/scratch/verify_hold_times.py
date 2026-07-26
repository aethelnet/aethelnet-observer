
import sqlite3
import pandas as pd
from datetime import datetime
import os

def analyze_hold_times():
    db_path = "/var/home/nhrlyn/Projects/auratic-systems-prime/market_data.db"
    if not os.path.exists(db_path):
        print("Database not found.")
        return

    conn = sqlite3.connect(db_path)
    query = "SELECT symbol, action, price, ts FROM trades ORDER BY ts ASC"
    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        print("No trade data to analyze.")
        return

    round_trips = []
    active_pos = {} # symbol -> {entry_price, entry_ts, side}

    for idx, row in df.iterrows():
        sym = row['symbol']
        action = row['action']
        ts = row['ts']
        price = row['price']

        # Simplify: BUY opens LONG, SELL closes LONG (or vice versa)
        # We look for opposite actions to close a round trip
        if sym in active_pos:
            entry = active_pos[sym]
            if action != entry['side']:
                # Closing position
                duration = (ts - entry['entry_ts']) / 60.0 # Minutes
                pnl = (price - entry['entry_price']) / entry['entry_price'] if entry['side'] == 'BUY' else (entry['entry_price'] - price) / entry['entry_price']
                round_trips.append({
                    'symbol': sym,
                    'duration': duration,
                    'pnl': pnl
                })
                del active_pos[sym]
        else:
            active_pos[sym] = {'entry_price': price, 'entry_ts': ts, 'side': action}

    if not round_trips:
        print("Could not reconstruct round-trips from logs.")
        return

    rt_df = pd.DataFrame(round_trips)
    print("\n=== RECONSTRUCTED ROUND-TRIP ANALYSIS ===")
    print(f"Total Completed Trades: {len(rt_df)}")
    print(f"Average Hold Time:      {rt_df['duration'].mean():.2f} min")
    print(f"Median Hold Time:       {rt_df['duration'].median():.2f} min")
    print(f"Max Hold Time:          {rt_df['duration'].max():.2f} min")
    print(f"Avg PnL per Trade:      {rt_df['pnl'].mean()*100:.2f}%")
    
    correlation = rt_df['duration'].corr(rt_df['pnl'])
    print(f"Hold Time vs PnL Corr:  {correlation:.4f}")

    conn.close()

if __name__ == "__main__":
    analyze_hold_times()
