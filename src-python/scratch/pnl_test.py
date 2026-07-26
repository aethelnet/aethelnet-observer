
import sys
import os
import pandas as pd
import asyncio

# Setup paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from arena.gauntlet import GauntletEngine
from services.data_manager import get_data_manager
from config import get_settings

class TestBot:
    def __init__(self):
        self.name = "PnL_Validator"
        self.class_type = "TEST"
    
    def on_tick(self, state):
        # High-conviction logic: follow the soul_signal
        soul = state.get('soul_signal', 0)
        if soul > 1.5:
            return 1.0
        elif soul < -1.5:
            return -1.0
        return 0.0

async def run_pnl_test():
    print(">>> STARTING PnL VALIDATION TEST <<<")
    settings = get_settings()
    dm = get_data_manager()
    
    # 1. Load Data
    print("  > Loading BTCUSDC data from local DB...")
    history = dm.get_latest_ohlcv_df("BTCUSDC", "1m", limit=1000)
    if history.empty:
        print("  [ERROR] No data found in local DB. Hydration might still be running.")
        return

    # 2. Setup Engine
    engine = GauntletEngine()
    bot = TestBot()
    
    # 3. Simulate
    print(f"  > Simulating {len(history)} ticks...")
    # Mock arena
    class MockArena:
        def __init__(self): self.name = "PnL_Chamber"
        def apply_handicap(self, s): return s
    
    result = engine._simulate_match(bot, MockArena(), history)
    
    # 4. Report
    abs_pnl = (result['pnl'] / 100.0) * 10000.0
    print("\n" + "="*40)
    print(f"PnL RESULT: {result['pnl']:+.2f}% (${abs_pnl:+.2f})")
    print(f"TRADES:     {result['trades']}")
    print(f"WIN RATE:   {result['win_rate']}%")
    print("="*40)

if __name__ == "__main__":
    asyncio.run(run_pnl_test())
