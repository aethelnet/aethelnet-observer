import sys
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Probe")

logger.info("Starting Brain Import...")
try:
    from services.brain_full import BrainEngine, get_engine
    logger.info("Import Success. Initializing Engine...")
    engine = get_engine()
    logger.info("Engine Initialized Successfully.")
except Exception as e:
    logger.error(f"Failed: {e}")
except BaseException as be:
    logger.error(f"Critical Failure (likely hang/timeout): {be}")
