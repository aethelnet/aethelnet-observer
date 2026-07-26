
import os
import sys
import asyncio
import json
from datetime import datetime

# Add project root
project_root = "/var/home/nhrlyn/Projects/auratic-systems-prime"
sys.path.insert(0, project_root)

async def run_biopsy():
    print("\n" + "="*60)
    print("      🦂 WEDNESDAY NIGHT SOVEREIGN STATUS REPORT 🦂")
    print("="*60)
    
    try:
        from services.tracker import get_performance_tracker
        tracker = get_performance_tracker()
        stats = tracker.get_stats()
        
        print(f"[*] Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"[*] Total PnL: {stats.get('total_pnl', 0.0):+.4f}")
        print(f"[*] Total Trades: {stats.get('total_trades', 0)}")
        print(f"[*] Win Rate: {stats.get('win_rate', 0.0):.2f}%")
        print(f"[*] Open Positions: {stats.get('open_positions', 0)}")
        print(f"[*] Max Drawdown: {stats.get('max_drawdown', 0.0):.4f}")
        print(f"[*] Current Equity: {stats.get('current_equity', 0.0):.4f}")
        
        # Validation Status
        win_rate = stats.get('win_rate', 0.0)
        trades = stats.get('total_trades', 0)
        
        print("\n[VALIDATION GATE]")
        print(f"  - 75 Trades: {'✅' if trades >= 75 else '❌'} ({trades})")
        print(f"  - 45% WinRate: {'✅' if win_rate >= 45.0 else '❌'} ({win_rate:.1f}%)")
        print(f"  - 8% Drawdown: {'✅' if abs(stats.get('max_drawdown', 0)) <= 8.0 else '⚠️'} (Logic needed)")
        
        if stats.get('open_positions', 0) > 0:
             print("\n[ACTIVE BATTLEFRONT]")
             print(f"  > System is currently ENGAGED in {stats.get('open_positions')} positions.")
        else:
             print("\n[BATTLEFRONT] Status: CLEAR (Searching for high-conviction entries).")

    except Exception as e:
        print(f"❌ Biopsy Failed: {e}")
        
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(run_biopsy())
