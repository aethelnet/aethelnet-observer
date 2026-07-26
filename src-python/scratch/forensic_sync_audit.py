import os
import sys
import asyncio
import logging

# Ensure project root is in path
sys.path.append(os.getcwd())

from brokers.router import get_omni_router
from services.symbol_normalizer import get_symbol_normalizer
from services.tracker import PerformanceTracker

async def forensic_sync_audit():
    print("🕵️‍♂️🏛️ FORENSISCHER SYNC-AUDIT 🏛️🕵️‍♂️")
    router = get_omni_router()
    sn = get_symbol_normalizer()
    tracker = PerformanceTracker()
    
    print("\n--- 1. ROUTER DATA ---")
    raw_positions = await router.get_all_positions()
    for p in raw_positions:
        asset = p.get('symbol')
        broker = p.get('broker')
        system_name = sn.to_system(asset)
        print(f"Raw: {asset} | Broker: {broker} | Normalizer -> {system_name}")
        
    print("\n--- 2. TRACKER MEMORY ---")
    for key, pos in tracker.positions.items():
        print(f"Key: {key} | Side: {pos.get('side')} | Qty: {pos.get('quantity')} | Broker: {pos.get('broker')}")

    print("\n--- 3. MATCHING LOGIC SIMULATION ---")
    # Build real_positions map like tracker.sync_with_wallet does
    real_positions = {}
    for pos in raw_positions:
        asset = pos.get('symbol')
        broker_name = pos.get('broker', 'unknown')
        sym = sn.to_system(asset)
        unique_id = f"{sym}@{broker_name}"
        real_positions[unique_id] = pos
        print(f"Mapped Real ID: {unique_id}")

    print("\n--- 4. GHOST DETECTION SIMULATION ---")
    for key in list(tracker.positions.keys()):
        pos = tracker.positions[key]
        pos_broker = pos.get('broker', 'unknown')
        pos_sym = pos.get('symbol', key)
        
        found = False
        lookup_key = key if "@" in key else f"{pos_sym}@{pos_broker}"
        if lookup_key in real_positions:
            found = True
            print(f"✅ Found exact: {lookup_key}")
        
        if not found and pos_sym in real_positions:
            found = True
            print(f"✅ Found symbol fallback: {pos_sym}")
            
        if not found:
            prefix = f"{pos_sym}@"
            for rid in real_positions:
                if rid.startswith(prefix):
                    found = True
                    print(f"✅ Found prefix match: {rid}")
                    break
        
        if not found:
            print(f"❌ GHOST DETECTED: {key} (Lookup: {lookup_key})")

if __name__ == "__main__":
    asyncio.run(forensic_sync_audit())
