import logging
import sys

# 0. Global Setup
logger = logging.getLogger("BrainProxy")

# 1. Core Component Imports
try:
    # We import from the refactored 'brain_full'
    from services.brain_full import BrainEngine, get_engine
    
    # ButterflySensor lives in core.physics now
    from core.physics import ButterflySensor
    
    # ProphitEngine is the legacy alias for BrainEngine
    ProphitEngine = BrainEngine
    
    logger.info("[Brain] 🧠 Sovereign Engine LOADED.")
except ImportError as e:
    logger.critical(f"[Brain] 🚨 Failed to load BrainEngine: {e}")
    # We must have at least a fallback or re-raise
    raise e

# 2. Advanced Intelligence Modules (Lazy Proxies)
class TemporalFusionEngine:
    def __init__(self, *args, **kwargs):
        from services.temporal_fusion import TemporalFusionEngine as _TFE
        self._engine = _TFE(*args, **kwargs)
    def __getattr__(self, name):
        return getattr(self._engine, name)

class AdversarialGym:
    def __init__(self, *args, **kwargs):
        from services.adversarial_gym import AdversarialGym as _AG
        self._gym = _AG(*args, **kwargs)
    def __getattr__(self, name):
        return getattr(self._gym, name)

def get_conformal_predictor(*args, **kwargs):
    from services.conformal import get_conformal_predictor as _gcp
    return _gcp(*args, **kwargs)

def get_regime_detector(*args, **kwargs):
    from services.regime_detector import get_regime_detector as _grd
    return _grd(*args, **kwargs)

# Re-export clean interface
__all__ = ['BrainEngine', 'get_engine', 'ButterflySensor', 'ProphitEngine', 'TemporalFusionEngine', 'AdversarialGym']
