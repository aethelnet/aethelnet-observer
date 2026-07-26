import logging
import sys

logger = logging.getLogger("BrainProxy")

try:
    # 1. Try to load the Proprietary Brain (Private Plugin)
    from services.brain_full import BrainEngine, get_engine, ButterflySensor, ProphitEngine
    logger.info("[BRAIN][SYSTEM] Proprietary Engine LOADED (Mode: FULL)")
except ImportError:
    # 2. Fallback to Open Source Core (Public Interface)
    try:
        from services.brain_core import BrainEngine, get_engine, ButterflySensor
        ProphitEngine = BrainEngine # Alias for compatibility
        logger.info("[BRAIN][CORE] Open Source Core LOADED (Mode: CORE_ONLY)")
    except ImportError as e:
        logger.critical(f"Failed to load ANY Brain Engine: {e}")
        raise e

# Re-export key components
__all__ = ['BrainEngine', 'get_engine', 'ButterflySensor', 'ProphitEngine']
