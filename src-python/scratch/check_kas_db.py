import sqlite3
import pandas as pd
from datetime import datetime

paths = [
    "/var/home/nhrlyn/Projects/auratic-systems-prime/auratic.db",
    "/var/home/nhrlyn/Projects/auratic-systems-prime/backend/data/auratic.db",
    "/var/home/nhrlyn/Projects/auratic-systems-prime/backend/data/market_data.db",
    "/var/home/nhrlyn/Projects/auratic-systems-prime/backend/market_data.db"
]

for db_path in paths:
    try:
        conn = sqlite3.connect(db_path)
        # Check if ohlcv table exists
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ohlcv'")
        if not cursor.fetchone():
            print(f"Table 'ohlcv' not found in {db_path}")
            conn.close()
            continue

        query = "SELECT count(*), min(timestamp), max(timestamp) FROM ohlcv WHERE symbol = 'KASUSDC'"
        df = pd.read_sql_query(query, conn)
        print(f"\nKASUSDC Stats in {db_path}:")
        print(df)
        conn.close()
    except Exception as e:
        print(f"Error checking {db_path}: {e}")
