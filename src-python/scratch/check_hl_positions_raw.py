import os
import json
import asyncio
from brokers.hyperliquid import HyperliquidBroker
from config import get_settings

def load_env(filepath):
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' not in line:
                continue
            key, value = line.split('=', 1)
            # Remove quotes
            value = value.strip('"').strip("'")
            os.environ[key] = value

async def main():
    load_env(".env")
    pk = os.getenv("HYPERLIQUID_PRIVATE_KEY")
    if not pk:
        print("Error: HYPERLIQUID_PRIVATE_KEY not found in environment.")
        return

    broker = HyperliquidBroker(private_key=pk)
    # No start() method needed
    
    print("Fetching Hyperliquid Positions...")
    try:
        positions = await broker.get_all_positions()
        
        if not positions:
            print("No open positions found on Hyperliquid.")
        else:
            print(f"Found {len(positions)} positions:")
            for p in positions:
                # Based on get_all_positions() returning a list of dicts
                print(f"  - {p.get('symbol')}: {p.get('qty')} (Entry: {p.get('entry_price')})")
    except Exception as e:
        print(f"Error fetching positions: {e}")
            
    # await broker.close() if it exists
    if hasattr(broker, 'close'):
        await broker.close()

if __name__ == "__main__":
    asyncio.run(main())
