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
    print(f"--- HYPERLIQUID UNIVERSE CHECK ---")
    
    meta = broker.info.meta()
    universe = meta.get('universe', [])
    
    names = [asset['name'] for asset in universe]
    names.sort()
    
    print(f"Total Perp Assets: {len(names)}")
    print(f"First 20: {names[:20]}")
    
    # Check for KAS or kAS
    kas_matches = [n for n in names if 'KAS' in n.upper()]
    print(f"\nKAS related coins: {kas_matches}")

if __name__ == "__main__":
    asyncio.run(main())
