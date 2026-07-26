import os
import sys
import asyncio
import json
import logging

# Ensure project root is in path
sys.path.append(os.getcwd())

from brokers.hyperliquid import HyperliquidBroker
from config import get_settings

async def diagnostic():
    settings = get_settings()
    hl_key = settings.HYPERLIQUID_PRIVATE_KEY
    if hasattr(hl_key, "get_secret_value"):
        hl_key = hl_key.get_secret_value()
        
    broker = HyperliquidBroker(hl_key)
    
    print(f"\n--- 🕵️‍♂️ HYPERLIQUID DEEP SCAN ---")
    print(f"Main Address: {broker.address}")
    
    # 1. Main Account State
    state = broker.info.user_state(broker.address)
    print("\n[MAIN] Margin Summary:")
    print(json.dumps(state.get("marginSummary"), indent=2))
    
    positions = state.get("assetPositions", [])
    print(f"\n[MAIN] Positions Found: {len(positions)}")
    for p in positions:
        pos = p if 'coin' in p else p.get('position', {})
        print(f"  - {pos.get('coin')}: {pos.get('szi')} (PnL: {pos.get('unrealizedPnl')})")
    
    # 2. Check for Vaults (The most likely hiding place)
    try:
        print("\n[SCAN] Checking for Vault memberships...")
        # Get all vaults to check if user is a leader or follower
        user_vaults = broker.info.user_vault_equities(broker.address)
        if user_vaults:
            print(f"Found {len(user_vaults)} Vault associations:")
            print(json.dumps(user_vaults, indent=2))
        else:
            print("No Vault associations found.")
    except Exception as e:
        print(f"Vault scan failed: {e}")

    # 3. Check Open Orders (Are we stuck in an exit?)
    orders = await broker.get_open_orders()
    print(f"\n[ORDERS] Open Orders: {len(orders)}")
    for o in orders:
        print(f"  - {o.get('symbol')}: {o.get('side')} {o.get('quantity')} @ {o.get('price')}")

    # 4. Final Verdict
    processed = await broker.get_all_positions()
    print("\n[VERDICT] Bot's internal vision sees:")
    for p in processed:
        print(f"  - {p['symbol']}: {p['side']} {p['qty']} (Broker: {p.get('broker', 'hl')})")

if __name__ == "__main__":
    asyncio.run(diagnostic())
