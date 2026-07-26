from arena.api import IGameMode
from services.data_manager import get_data_manager
import pandas as pd
import logging

logger = logging.getLogger("SovereignPulse")

class SovereignPulse(IGameMode):
    """
    Sovereign Pulse (Real-Time Hydration).
    The ultimate training arena. 
    Uses the last 2000 real-world candles from the local DataManager cache.
    Ensures that the 18D brain learns on real price action paired with real cosmic/seismic telemetry.
    """
    
    @property
    def name(self) -> str:
        return "Sovereign Pulse"

    @property
    def description(self) -> str:
        return "Real-world market hydration. The bridge between the Manifold and the Truth."

    def generate_scenario(self) -> pd.DataFrame:
        """
        Pulls the latest real-world data from the local repository.
        """
        try:
            dm = get_data_manager()
            # Fetch the latest 2000 minutes of BTCUSDC (approx 33 hours)
            df = dm.get_latest_ohlcv_df("BTCUSDC", "1m", limit=2000)
            
            if df.empty:
                logger.warning("[Pulse] Local repository is empty for BTCUSDC. Falling back to synthetic noise.")
                # Fallback to a basic sine wave to prevent Academy crash
                import numpy as np
                length = 1000
                price = 100 * np.exp(np.cumsum(np.random.normal(0, 0.01, length)))
                return pd.DataFrame({
                    "timestamp": pd.date_range(start="2025-01-01", periods=length, freq="1min"),
                    "close": price,
                    "volume": [1000]*length
                })
            
            logger.info(f"[Pulse] Successfully hydrated {len(df)} real-world candles for training.")
            return df
            
        except Exception as e:
            logger.error(f"[Pulse] Hydration failed: {e}")
            return pd.DataFrame()
