import os
import sys
import asyncio
import json

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import get_settings
from brokers.hyperliquid import HyperliquidBroker

async def main():
    settings = get_settings()
    pk = os.getenv("HYPERLIQUID_PRIVATE_KEY")
    if hasattr(pk, 'get_secret_value'):
        pk = pk.get_secret_value()
        
    broker = HyperliquidBroker(pk)
    print(f"--- HYPERLIQUID FILL HISTORY ---")
    
    # Get user fills
    fills = broker.info.user_fills(broker.address)
    
    # Show last 10 fills
    for f in fills[:10]:
        coin = f.get("coin")
        side = f.get("side")
        sz = f.get("sz")
        px = f.get("px")
        time = f.get("time")
        print(f"Fill: {coin:<10} | {side:<5} | {sz:<10} @ ${px:<10} | Time: {time}")

if __name__ == "__main__":
    asyncio.run(main())
