import asyncio
import logging
import time
import sys
import os
from unittest.mock import MagicMock

# Force backend paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Setup Logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] [%(name)s] %(message)s')
logger = logging.getLogger("ForensicScorpio")

# Properly load settings singleton
from config import get_settings
app_settings = get_settings()
# Officially registered in Settings model
setattr(app_settings, 'SCORPIO_SCALAR', 1.5)
app_settings.ORACLE_ENABLED = True
app_settings.USE_STRATEGY_ENSEMBLE = False
app_settings.SIGNAL_THRESHOLD = 0.75

async def test_scorpio_sting_consensus():
    logger.info("Starting Sovereign Consensus Forensic Test...")
    
    from services.position_sizer import PositionSizer
    sizer = PositionSizer(app_settings)
    
    # Rat Intensity (S_rat) logic: min(2.0, SCORPIO_SCALAR * intensity)
    # With SCORPIO_SCALAR = 1.5 and intensity = 1.35 (Max Rat Intensity), S_rat = 2.0
    
    # -------------------------------------------------------------
    # CASE 1: SOVEREIGN CONSENSUS (Monarch Agrees)
    # -------------------------------------------------------------
    print("\n--- CASE 1: SOVEREIGN CONSENSUS (Rat BUY + Monarch BUY) ---")
    # conviction = (0.95 - 0.5) * 2 * 1 = 0.9.  Bloom = tanh(0.9 * 1.618) * 0.5 ~= 0.45
    # final = 2.0 + 0.45 = 2.45x
    sizer.calculate(
        symbol='BTCUSDT',
        side='BUY',
        capital=1000.0,
        price=65000.0,
        signal=1.0,
        is_scorpio=True,
        intensity=1.35, # Max Rat Intensity
        ml_prob=0.95    # Monarch Agrees
    )

    # -------------------------------------------------------------
    # CASE 2: RAT SOVEREIGNTY (Monarch Disagrees)
    # -------------------------------------------------------------
    print("\n--- CASE 2: RAT SOVEREIGNTY (Rat BUY + Monarch SELL) ---")
    # conviction = (0.05 - 0.5) * 2 * 1 = -0.9.  Bloom = 0.0 (Floor)
    # final = 2.0 + 0.0 = 2.0x
    sizer.calculate(
        symbol='BTCUSDT',
        side='BUY',
        capital=1000.0,
        price=65000.0,
        signal=1.0,
        is_scorpio=True,
        intensity=1.35, # Max Rat Intensity
        ml_prob=0.05    # Monarch Disagrees
    )

    # -------------------------------------------------------------
    # CASE 3: MONARCH CALM (Monarch Neutral)
    # -------------------------------------------------------------
    print("\n--- CASE 3: MONARCH CALM (Rat BUY + Monarch 0.50) ---")
    # conviction = 0.0. Bloom = 0.0
    # final = 2.0x
    sizer.calculate(
        symbol='BTCUSDT',
        side='BUY',
        capital=1000.0,
        price=65000.0,
        signal=1.0,
        is_scorpio=True,
        intensity=1.35,
        ml_prob=0.50
    )

    print("\n✅ TEST COMPLETE.")

if __name__ == "__main__":
    asyncio.run(test_scorpio_sting_consensus())
