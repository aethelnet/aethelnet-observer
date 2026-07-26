from .settings import Settings, get_settings

# --- THE DIVINE PROPORTIONS ---
try:
    from scipy.constants import golden as GOLDEN_RATIO
except ImportError:
    GOLDEN_RATIO = 1.618033988749895

INV_GOLDEN_RATIO = 1.0 / GOLDEN_RATIO
PHIDIA = INV_GOLDEN_RATIO # Shorthand for inverse phi
