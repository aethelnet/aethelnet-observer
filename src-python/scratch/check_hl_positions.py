import os
import sys
import asyncio

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import get_settings
from brokers.hyperliquid import HyperliquidBroker

from dotenv import load_dotenv
load_dotenv()

async def main():
    settings = get_settings()
    pk = os.getenv("HYPERLIQUID_PRIVATE_KEY")
    if not pk:
        from services.keychain import get_keychain
        keys = get_keychain().get_keys('hyperliquid')
        if keys:
            pk = keys.get('secret_key') or keys.get('private_key')
        
    if hasattr(pk, 'get_secret_value'):
        pk = pk.get_secret_value()
        
    broker = HyperliquidBroker(pk)
    print(f"--- HYPERLIQUID LIVE POSITION CHECK ---")
    print(f"Wallet: {broker.address}")
    
    # Force fresh user state
    state = broker.info.user_state(broker.address)
    positions = state.get("assetPositions", [])
    
    if not positions:
        print("No open positions found.")
    else:
        for p in positions:
            pos = p.get("position", {})
            coin = pos.get("coin")
            size = pos.get("szi")
            entry = pos.get("entryPx")
            print(f"✅ POSITION: {coin:<10} | Size: {size:<10} | Entry: ${entry}")

if __name__ == "__main__":
    asyncio.run(main())
