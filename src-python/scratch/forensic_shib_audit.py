import asyncio
import os
import sys

# Add project root to sys.path
sys.path.append(os.getcwd())

from brokers.router import get_omni_router
from services.tracker import PerformanceTracker

async def forensic_audit():
    print("🚀 STARTING FORENSIC POSITION AUDIT...")
    
    # 1. Check Broker Reality
    router = get_omni_router()
    h_pos = await router.get_position('SHIBUSDC')
    print(f"\n[BROKER REALITY] Hyperliquid SHIBUSDC Position: {h_pos}")
    
    # 2. Check Tracker Memory
    tracker = PerformanceTracker()
    t_pos = tracker.get_position('SHIBUSDC')
    print(f"[TRACKER MEMORY] performance.json SHIBUSDC Position: {t_pos}")
    
    # 3. Analyze Desync
    if abs(h_pos) < 0.001 and not t_pos:
        print("\n✅ STATUS: CLEAN. No position on exchange, no position in tracker.")
    elif abs(h_pos) > 0.001 and t_pos:
        print(f"\n✅ STATUS: SYNCED. Position exists in both. Tracker Side: {t_pos.get('side')}")
    elif abs(h_pos) > 0.001 and not t_pos:
        print("\n🚨 STATUS: GHOST LONG! Exchange has a position that tracker is ignoring.")
    elif abs(h_pos) < 0.001 and t_pos:
        print("\n🚨 STATUS: GHOST TRACKER! Tracker thinks we have a position but exchange is flat.")
    
    print("\n[VERDICT] If Hyperliquid is > 0 and Tracker is Flat, the 'Rat Entry' was used to close an ancient ghost.")

if __name__ == "__main__":
    asyncio.run(forensic_audit())
