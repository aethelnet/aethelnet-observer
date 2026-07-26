import os
import sys
import asyncio
import logging
import time
from datetime import datetime

# Ensure project root is in path
sys.path.append(os.getcwd())

# CONFIGURE LOGGING
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S'
)
logger = logging.getLogger("ForceMirrorSync")

from services.tracker import PerformanceTracker
from brokers.router import get_omni_router
from services.symbol_normalizer import get_symbol_normalizer

async def run_ritual():
    logger.info("🦾⚔️ starting the GREAT PURGE AND RE-ADOPTION RITUAL... ⚔️🦾")
    
    # 1. Check Router Health
    router = get_omni_router()
    logger.info(f"Router Brokers: {list(router.brokers.keys())}")
    
    if 'hyperliquid' not in router.brokers:
        logger.warning("❌ Hyperliquid NOT found in Router! Attempting Force Reload...")
        router.reload()
        logger.info(f"Router Brokers after Reload: {list(router.brokers.keys())}")
        
    if 'hyperliquid' not in router.brokers:
        logger.error("🔴 CRITICAL: Hyperliquid STILL NOT INITIALIZED. Check .env and API keys!")
        # Let's try to see if the env var is even there
        logger.info(f"HL_KEY Present in OS Env: {bool(os.getenv('HYPERLIQUID_PRIVATE_KEY'))}")
        return

    # 2. Perform Sync
    tracker = PerformanceTracker()
    
    logger.info("--- Phase 1: Purging Ghosts and Adopting Reality ---")
    await tracker.sync_with_wallet()
    
    logger.info("--- Phase 2: Final Verification ---")
    # Force a second sync just to be absolutely sure the adoption stuck
    await tracker.sync_with_wallet()
    
    print("\n[Result] New internal state after Ritual:")
    if not tracker.positions:
        print("  - NO POSITIONS TRACKED (Clean Slate)")
    else:
        for key, pos in tracker.positions.items():
            broker = pos.get('broker', 'unknown')
            print(f"  - {key}: {pos.get('side')} (Qty: {pos.get('quantity')}, Broker: {broker})")

    logger.info("🦾⚔️🐀🛡️👑 RITUAL COMPLETE. THE MIRROR IS SHATTERED. 👑🛡️🐀⚔️🦾")

if __name__ == "__main__":
    asyncio.run(run_ritual())
