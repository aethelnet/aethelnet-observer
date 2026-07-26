import os
import sys
import asyncio
import logging

# Ensure project root is in path
sys.path.append(os.getcwd())

from brokers.router import get_omni_router

async def debug_positions():
    print("🕵️‍♂️ ROHE BÖRSEN-DIAGNOSE 🕵️‍♂️")
    router = get_omni_router()
    
    try:
        # Get raw positions from the router
        positions = await router.get_all_positions()
        print(f"\nGefundene Positionen ({len(positions)}):")
        for p in positions:
            print(f"  - Symbol: {p.get('symbol')} | Side: {p.get('side')} | Qty: {p.get('qty')} | Broker: {p.get('broker')}")
            
        if not positions:
            print("  - KEINE POSITIONEN GEFUNDEN (Vielleicht falsche API-Keys oder leeres Konto?)")
            
    except Exception as e:
        print(f"Fehler bei der Diagnose: {e}")

if __name__ == "__main__":
    asyncio.run(debug_positions())
