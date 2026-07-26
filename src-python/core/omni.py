"""
[ 99 ] O M N I _ P R O T O C O L
==================================
LAYER:     ORCHESTRATION
STATUS:    ASCENDED
AUTHORITY: GOD_MODE
PHASE:     99 (THE_ASCENSION)
"""

import asyncio
import logging
from typing import Dict, Any

# Core Services
from services.data_manager import get_data_manager
from services.brain import get_engine
from services.websocket_manager import get_websocket_manager
from routers.stream import broadcast_loop
from services.trading_service import run_trading_service
# from arena.manager import LiveStrategyManager # Bypass legacy manager

from services.beacon import BeaconListener

# Enhanced Services (The New Wave)
try:
    from services.trade_logger import get_archive
except ImportError:
    get_archive = None

try:
    from services.messenger import get_messenger
except ImportError:
    get_messenger = None

logger = logging.getLogger("Omni")

class Omni:
    """
    The Alpha and The Omega.
    Orchestrates the startup, lifecycle, and shutdown of all Sub-Systems.
    """
    _instance = None
    
    def __init__(self):
        self.status = "INITIALIZING"
        self.services = {}
        
        # --- PHASE 99: GOD MODE UNLOCKED ---
        self.god_mode = True # Live Capital Authorized
        self.environment = "PRODUCTION"

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = Omni()
        return cls._instance

    async def genesis(self):
        """
        The Spark of Life.
        Initializes the entire ecosystem in dependency order.
        """
        logger.info(">>> OMNI PROTOCOL: GENESIS SEQUENCE INITIATED <<<")
        logger.critical("!!! WARNING: GOD MODE IS ACTIVE. REAL CAPITAL IS AT RISK. !!!")
        self.status = "BOOT_SEQUENCE"

        try:
            # 1. FOUNDATION (Data & Network)
            logger.info("[OMNI] 1. Initializing Foundation...")
            self.services['data'] = get_data_manager()
            self.services['websocket'] = get_websocket_manager()
            await self.services['websocket'].start()
            
            # Sync Universe (Async Background)
            asyncio.create_task(self.services['data'].sync_universe(), name="universe_sync")

            # 2. INTELLIGENCE (Brain & Logic)
            logger.info("[OMNI] 2. Awakening Intelligence...")
            self.services['brain'] = get_engine()
            # self.services['logic'] = LiveStrategyManager() # Bypass legacy manager
            # self.services['brain'].live_manager = self.services['logic'] # Link Brain to Logic

            
            # PHASE 99 INJECTION: Pass God Mode to Manager
            if hasattr(self.services['logic'], 'set_god_mode'):
                self.services['logic'].set_god_mode(self.god_mode)
            
            # 3. MEMORY & VOICE (Persistent Layers)
            logger.info("[OMNI] 3. Restoring Memory & Voice...")
            if get_archive:
                self.services['archive'] = get_archive()
            if get_messenger:
                self.services['messenger'] = get_messenger()
                await self.services['messenger'].send_message(">>> OMNI SYSTEM: ASCENDED (LIVE CAPITAL ONLINE) <<<")

            # 4. CIRCULATION (Stream & Beacon)
            logger.info("[OMNI] 4. Starting Circulation...")
            asyncio.create_task(broadcast_loop(), name="broadcast_pulse")
            
            beacon = BeaconListener()
            beacon.start_background()
            self.services['beacon'] = beacon

            # 5. ACTION (Trading Loop)
            logger.info("[OMNI] 5. Engaging Engines...")
            asyncio.create_task(run_trading_service(), name="trading_core")

            # 6. EVOLUTION (The Dreamer)
            from services.dreamer import Dreamer
            logger.info("[OMNI] 6. Starting The Dreamer...")
            self.services['dreamer'] = Dreamer(interval_hours=4)
            self.services['dreamer'].start()
            
            # 7. TOPOLOGY (The Map)
            from services.topology import TopologyEngine
            self.services['brain'].topology_engine = TopologyEngine()

            self.status = "ONLINE"
            logger.info(">>> OMNI PROTOCOL: GENESIS COMPLETE. SYSTEM STABLE. <<<")
            
            return True

        except Exception as e:
            logger.critical(f"OMNI GENESIS FAILED: {e}")
            self.status = "CRITICAL_FAILURE"
            return False

    async def shutdown(self):
        """
        The Great Sleep.
        """
        logger.info(">>> OMNI PROTOCOL: SHUTDOWN SEQUENCE <<<")
        
        if 'websocket' in self.services:
            await self.services['websocket'].stop()
            
        if 'messenger' in self.services and get_messenger:
            await self.services['messenger'].send_message(">>> OMNI SYSTEM: OFFLINE <<<")
            
        logger.info(">>> SYSTEM HALTED <<<")

# Singleton Accessor
def get_omni():
    return Omni.get_instance()
