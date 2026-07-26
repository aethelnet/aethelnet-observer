
import os
import sys
import asyncio
import json
from datetime import datetime

# Add project root
project_root = "/var/home/nhrlyn/Projects/auratic-systems-prime"
sys.path.insert(0, project_root)

async def run_cloud_audit():
    print("\n" + "="*60)
    print("      🦂 WEDNESDAY NIGHT CLOUD POSITION AUDIT 🦂")
    print("="*60)
    
    try:
        from services.database import get_database
        db = get_database()
        
        # 1. Fetch Positions
        try:
            sql = "SELECT symbol, quantity, avg_price, metadata FROM positions WHERE quantity != 0"
            rows = db.execute_read(sql)
            
            if rows:
                print(f"✅ FOUND {len(rows)} ACTIVE POSITIONS IN CLOUD:")
                for row in rows:
                    symbol, qty, avg_price, meta_json = row
                    meta = json.loads(meta_json) if meta_json else {}
                    side = meta.get('side', 'LONG' if qty > 0 else 'SHORT')
                    print(f"  > {symbol} | {side} | Qty: {qty} | AvgPrice: {avg_price}")
            else:
                print("[*] Status: No open positions found in positions table.")
        except Exception as e:
            print(f"⚠️ Positions check failed: {e}")

        # 2. Fetch Wallets
        try:
            sql = "SELECT balances, updated_ts FROM wallets"
            rows = db.execute_read(sql)
            print("\n[WALLET SNAPSHOT]")
            if rows:
                for row in rows:
                    balances_json, ts = row
                    balances = json.loads(balances_json)
                    print(f"  - Last Update: {datetime.fromtimestamp(ts).strftime('%H:%M:%S')}")
                    for asset, val in balances.items():
                        if isinstance(val, dict):
                             print(f"    {asset}: ${val.get('equity', 0.0):.2f}")
                        else:
                             print(f"    {asset}: {val}")
            else:
                print("  - No wallet data found in Cloud.")
        except Exception as e:
            print(f"⚠️ Wallet check failed: {e}")

    except Exception as e:
        print(f"❌ Audit Failed: {e}")
        
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(run_cloud_audit())
