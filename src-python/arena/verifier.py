import sys
import os
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta

# Ensure backend acts as root
sys.path.append(os.getcwd())

class DataVerifier:
    def __init__(self, db_path="sqlite:///market_data.db"):
        self.engine = create_engine(db_path)
        
    def verify_integrity(self, required_days=30):
        """
        Scans the DB for all symbols.
        Checks if they have enough 1m data for the requested days.
        """
        print(f"--- DATA VERIFIER (Target: {required_days} Days) ---")
        
        with self.engine.connect() as conn:
            # 1. Get Distinct Symbols
            symbols_query = text("SELECT DISTINCT symbol FROM ohlcv")
            symbols = [row[0] for row in conn.execute(symbols_query)]
            
            report = []
            
            print(f"Found {len(symbols)} symbols in DB.")
            
            for field in symbols:
                # Check 1m Data
                query = text(f"""
                    SELECT COUNT(*), MIN(timestamp), MAX(timestamp) 
                    FROM ohlcv 
                    WHERE symbol = '{field}' AND interval = '1m'
                """)
                result = conn.execute(query).fetchone()
                count, min_ts, max_ts = result
                
                if count == 0:
                    status = "EMPTY"
                    duration = 0
                else:
                    min_dt = datetime.strptime(min_ts, '%Y-%m-%d %H:%M:%S.%f') if isinstance(min_ts, str) else min_ts
                    max_dt = datetime.strptime(max_ts, '%Y-%m-%d %H:%M:%S.%f') if isinstance(max_ts, str) else max_ts
                    duration = (max_dt - min_dt).days
                    
                    if duration >= required_days:
                        status = "READY"
                    else:
                        status = f"PARTIAL ({duration}d)"
                
                print(f"  > {field}: {count} rows | {duration} days | Status: {status}")
                report.append({'symbol': field, 'status': status, 'days': duration})
                
        return pd.DataFrame(report)

if __name__ == "__main__":
    verifier = DataVerifier()
    verifier.verify_integrity()
