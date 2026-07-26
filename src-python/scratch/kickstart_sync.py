import os
import sys
import asyncio

# Ensure project root is in path
sys.path.append(os.getcwd())

from services.data_manager import get_data_manager

async def manual_kickstart():
    print("🦾⚔️🐀🛡️👑 SOVEREIGN KICKSTART INITIATED 👑🛡️🐀⚔️🦾")
    dm = get_data_manager()
    
    # We call the logic directly to fill the gap
    # Note: We don't call the perpetual loop here, just the sync logic
    # because this script will terminate.
    
    from config.settings import get_settings
    from services.data_manager import get_trading_symbols
    from binance import Client
    
    settings = get_settings()
    symbols = get_trading_symbols(settings)
    
    print(f"[Kickstart] Restoring vision for {len(symbols)} symbols...")
    
    for symbol in symbols:
        try:
            print(f"[Syncing] {symbol}...")
            # We fetch the last 1 day to ensure we bridge the 4-hour gap
            await dm.fetch_and_store(symbol, "1m", lookback_days=1)
            print(f"[SUCCESS] {symbol} Vision Restored.")
        except Exception as e:
            print(f"[FAILED] {symbol}: {e}")
            
    print("\n🦾⚔️🐀🛡️👑 KICKSTART COMPLETE. THE RAT CAN SEE. 👑🛡️🐀⚔️🦾")

if __name__ == "__main__":
    asyncio.run(manual_kickstart())
