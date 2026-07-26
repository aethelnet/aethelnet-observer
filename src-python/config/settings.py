from functools import lru_cache
from typing import Any, ClassVar, Dict, List, Optional
import os

from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Canonical runtime settings for Auratic Systems Prime.

    Philosophy:
    - `settings.py` holds sane canonical defaults.
    - `.env` overrides environment-specific or operator-specific values.
    - Avoid duplicate field definitions and hidden fallback behavior.
    """

    _settings_dir: ClassVar[str] = os.path.dirname(os.path.abspath(__file__))
    _backend_dir: ClassVar[str] = os.path.dirname(_settings_dir)
    _project_root: ClassVar[str] = os.path.dirname(_backend_dir)
    _env_path: ClassVar[str] = os.path.join(_project_root, ".env")


    model_config = {
        "env_file": _env_path,
        "extra": "ignore",
    }

    # ---------------------------------------------------------------------
    # Core application
    # ---------------------------------------------------------------------
    APP_NAME: str = "Auratic Systems Backend"
    DEBUG_MODE: bool = False
    NODE_ID: str = "oracle-sovereign-core"
    NODE_PRIORITY: int = 1
    LGNN_ONLY: bool = False

    DATA_DIR: str = os.getenv("DATA_DIR", _project_root)
    DB_PROVIDER: str = "postgresql"
    DATABASE_URL: Optional[str] = (
        "postgresql://postgres.auojtmytnhehexcshdyw:"
        "wu8QBj7wnIApcfwn@aws-1-eu-west-1.pooler.supabase.com:6543/postgres"
    )
    DB_PATH: str = os.path.join(DATA_DIR, "market_data.db")
    KNOWLEDGE_STORE_PATH: str = os.path.join(DATA_DIR, "knowledge_index.pkl")

    PHYSICS_WINDOW_SIZE: int = 20000
    BROADCAST_INTERVAL: float = 0.10
    RESOURCE_MODE: str = "ELITE"
    WS_RING_BUFFER_SIZE: int = 1000

    # ---------------------------------------------------------------------
    # Operating mode / execution
    # ---------------------------------------------------------------------
    ENV_MODE: str = "development"
    EXECUTION_ENABLED: bool = False
    TRADING_MODE: str = "DEFI"
    REBALANCER_DRY_RUN: bool = False

    # ---------------------------------------------------------------------
    # Core trading profile
    # ---------------------------------------------------------------------
    MAX_POSITION_SIZE: float = 0.02
    MAX_POSITION_SIZE_USD: float = 100.0
    SIGNAL_THRESHOLD: float = 0.0
    SIGNAL_PERSISTENCE: int = 5
    ADAPTIVE_THRESHOLD_SCALAR: float = 10.0
    MIN_HOLD_TIME: int = 60
    MAX_POSITION_DURATION: int = 28800
    REBALANCE_COOLDOWN: float = 60.0
    MIN_REBALANCE_DELTA_USD: float = 1.0

    PROFIT_TARGET: float = 0.015
    STOP_LOSS: float = 0.05
    STOP_LOSS_ENABLED: bool = True
    TRAILING_STOP: bool = True
    TRAILING_STOP_PCT: float = 0.005
    SCALPING_MODE: bool = True
    
    # Simple Signal Decay Exit (Scalper Mode Bypass)
    SIGNAL_DECAY_EXIT_ENABLED: bool = True
    SIGNAL_DECAY_EXIT_PCT: float = 0.10  # Exit if signal drops 10% from entry
    
    TEMPORAL_FIBONACCI_SNAPPING: bool = False
    USE_CONFIDENCE_GATE: bool = True

    HYPERLIQUID_LEVERAGE: float = 20.0
    BINANCE_LEVERAGE: float = 3.0
    SCORPIO_SCALAR: float = 1.5
    HL_MARGIN_SAFE_THRESHOLD: float = 0.75
    MIN_ACCOUNT_VALUE: float = 0.0
    MAX_DAILY_LOSS: float = 1000.0
    BYPASS_DAILY_LOSS_LIMIT: bool = True
    
    # [SOVEREIGN TUNING] Neural Confidence Dampening
    # Higher = Smoother/Slower, Lower = More Twitchy/Aggressive
    NEURAL_CONFIDENCE_SCALE: float = 1.5 # Default 1.2 in code, increasing to 1.5 for stability
    NEURAL_CUBIC_SCALAR: float = 0.5
    TRACKER_PILLAR_SCALE: float = 2.0
    ORACLE_VALIDATION_OFFSET: float = 0.5
    ORACLE_VALIDATION_SCALAR: float = 1.618
    LAYER_PNL_SENSITIVITY: float = 5.0
    
    # --- [SOVEREIGN 4-PILLAR MANIFOLD] ---
    PILLAR_RAT_THRESHOLD: float = 1.5
    PILLAR_RAT_BLOOM: float = 0.5
    PILLAR_BRAIN_THRESHOLD: float = 1.2
    PILLAR_BRAIN_BLOOM: float = 0.5
    PILLAR_RHYME_THRESHOLD: float = 1.0
    PILLAR_RHYME_BLOOM: float = 0.5
    PILLAR_HINDSIGHT_THRESHOLD: float = 0.789
    PILLAR_HINDSIGHT_BLOOM: float = 0.25

    # [SVRGN LIVE]
    SIGNAL_HYSTERESIS: float = 0.10
    NEURAL_THRESHOLD: float = 2.5
    NEURAL_EXIT_THRESHOLD_PCT: float = 0.20
    SIGNAL_REVERSION: bool = False
    REBALANCER_REVERSION: bool = False
    USE_RAT_MEAN_REVERSION: bool = False
    EVOLUTION_ENABLED: bool = False

    # [SOVEREIGN EXPONENTIAL MANIFOLD]
    # Power curve for capital distribution across signals.
    # 0.0 = DISABLED (no global distribution, legacy per-symbol sizing)
    # 1.0 = Linear (proportional to conviction)
    # 2.0 = Squared (King gets 4x more than half-conviction)
    # 3.0 = Cubic  (extreme concentration in top signals)
    RECYCLER_EXPONENTIAL_POWER: float = 2.0

    # ---------------------------------------------------------------------
    # Execution features
    # ---------------------------------------------------------------------
    USE_SAFETY_ORDERS: bool = False
    SAFETY_STOP_LOSS_PCT: float = 0.08
    SAFETY_TAKE_PROFIT_PCT: float = 0.015
    REDUCE_ONLY_EXITS: bool = True

    LIMIT_ORDER_FIRST: bool = True
    REBALANCER_ORDER_TYPE: str = "market"
    DYNAMIC_BID_MAX_OFFSET: float = 0.015
    DYNAMIC_BID_SIGMOID_SENSITIVITY: float = 1.0
    LIMIT_ORDER_OFFSET_PCT: float = 0.001

    SMART_EXECUTION_ENABLED: bool = True
    SMART_EXECUTION_THRESHOLD: float = 1000.0
    SMART_EXECUTION_DEFAULT_SLICES: int = 10

    SWARM_EXECUTION_ENABLED: bool = True
    SIGNAL_WEIGHTED_SIZING: bool = True
    CASH_RESERVE_PCT: float = 0.10
    RESERVE_DEPLOY_THRESHOLD: float = 0.95
    MAX_CONCURRENT_TRADES: int = 40

    # ---------------------------------------------------------------------
    # Strategy architecture
    # ---------------------------------------------------------------------
    ORACLE_ENABLED: bool = False
    USE_STRATEGY_ENSEMBLE: bool = True
    LAYER_TRACKER_ENABLED: bool = True

    # ---------------------------------------------------------------------
    # Universe / discovery
    # ---------------------------------------------------------------------
    UNIVERSE_TAXONOMY: Dict[str, List[str]] = {
        "crypto": ["BTC", "ETH", "SOL", "ADA", "DOT", "AVAX", "MATIC", "LINK", "UNI", "LDO", "GAS", "IMX", "TIA", "SUI", "APT", "ARB", "OP", "RENDER", "HYPE", "PURR"],
        "tradfi": ["AAPL", "NVDA", "MSFT", "GOOGL", "AMZN", "TSLA", "^GSPC", "SPACEX"],
        "forex": ["EURUSD", "GBPUSD", "USDJPY"],
        "commodities": ["GC=F", "SI=F", "CL=F", "NG=F", "GOLD"],
    }
    SYMBOL_ALIASES: Dict[str, str] = {
        "BTC": "BTCUSDT",
        "ETH": "ETHUSDT",
        "SOL": "SOLUSDT",
        "XRP": "XRPUSDT",
        "LDO": "LDOUSDC",
        "GAS": "GASUSDC",
        "IMX": "IMXUSDC",
        "TIA": "TIAUSDC",
        "SUI": "SUIUSDC",
        "HYPE": "HYPEUSDC",
        "PURR": "PURRUSDC",
    }
    SYMBOLS_WHITELIST: Optional[str] = None
    SYMBOLS_ADDITIONAL: Optional[str] = None
    TRADING_SYMBOLS: str = "BTCUSDC,ETHUSDC,SOLUSDC,ADAUSDC,AVAXUSDC,MATICUSDC,LINKUSDC,UNIUSDC,DOTUSDC,SPACEX"
    trading_symbols: list = []

    OPEN_ECOSYSTEM_MODE: bool = True
    RESERVE_PERCENTAGE: float = 0.5
    AUTO_DISCOVERY_ENABLED: bool = False
    AUTO_DISCOVERY_BUDGET_PCT: float = 0.5
    AUTO_DISCOVERY_MAX_SYMBOLS: int = 5
    AUTO_DISCOVERY_MIN_SIGNAL: float = 0.75
    AUTO_DISCOVERY_DISCOVERY_INTERVAL_MINUTES: int = 60
    AUTO_DISCOVERY_REBALANCE_HOURS: int = 24
    MIN_DAILY_VOLUME_USD: float = 1_000_000
    MIN_LIQUIDITY_SCORE: float = 0.5

    # ---------------------------------------------------------------------
    # Shadow / validation layers
    # ---------------------------------------------------------------------
    SHADOW_ENGINE_ENABLED: bool = True
    SHADOW_MIN_HOLD_TIME: int = 10
    SHADOW_SIGNAL_THRESHOLD: float = 0.59
    SHADOW_POSITION_SIZE: float = 0.06
    SHADOW_MAX_POSITIONS: int = 10

    VALIDATION_MIN_TRADES: int = 20
    VALIDATION_MIN_WIN_RATE: float = 0.55
    VALIDATION_MAX_DRAWDOWN: float = 0.15
    VALIDATION_TARGET_HOURS: int = 48

    # ---------------------------------------------------------------------
    # External intelligence / reward systems
    # ---------------------------------------------------------------------
    # [DEPRECATED] Moved to .env and DB discovery
    EVOLUTION_ENABLED: bool = False

    OCEAN_NETWORK_URL: str = "https://sapphire.oasis.io"
    NUMERAI_MODEL_NAME: str = "ProphitEngine"

    # ---------------------------------------------------------------------
    # News / sentiment
    # ---------------------------------------------------------------------
    NEWS_SENTIMENT_ENABLED: bool = True
    EGRESS_PROXY_URL: Optional[str] = None

    # ---------------------------------------------------------------------
    # Secrets / API credentials
    DASHBOARD_PASSWORD: str = "auratic_admin"
    JWT_SECRET_KEY: str = "auratic_super_secret_key_change_in_prod"
        # ---------------------------------------------------------------------
    BINANCE_API_KEY: Optional[str] = None
    BINANCE_SECRET_KEY: Optional[str] = None
    BINANCE_TESTNET_API_KEY: Optional[str] = None
    BINANCE_TESTNET_SECRET_KEY: Optional[str] = None
    HYPERLIQUID_PRIVATE_KEY: Optional[str] = None
    HYPERLIQUID_WALLET_ADDRESS: Optional[str] = None
    ALPACA_API_KEY: Optional[str] = None
    ALPACA_SECRET_KEY: Optional[str] = None
    ALPACA_PAPER_API_KEY: Optional[str] = None
    ALPACA_PAPER_SECRET_KEY: Optional[str] = None
    ALPACA_BASE_URL: Optional[str] = None
    ALPACA_PAPER: bool = True
    ALPACA_ENABLED: bool = False
    HYPERLIQUID_TESTNET: bool = False
    BINANCE_TESTNET: bool = False
    ALPACA_EXTENDED_HOURS: bool = True
    ALPACA_SYMBOL_MAP: Dict[str, str] = {
        # Map Auratic global symbols to Alpaca-tradeable stock/ETF tickers
        "GOLD": "GLD",
        "SILVER": "SLV",
        "OIL": "USO",
        "SPX": "SPY",
        "SPXUSDC": "SPY",
        "BTC": "BITO",
        "BTCUSDC": "BITO",
        "ETHUSDC": "ETHE",
        "SPACEX": "SPACE", # Assuming the IPO ticker will be SPACE
    }

    ADMIN_TOKEN: Optional[str] = None
    ALPHA_KEY: Optional[str] = None
    ALPHA_OVERRIDE: bool = False
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    TELEGRAM_DONATION_URL: Optional[str] = None
    GITHUB_TOKEN: Optional[str] = None
    GITHUB_REPO: str = "ProphitEngine/ProphitEngine"
    CRYPTOPANIC_API_KEY: Optional[str] = None
    NEWSAPI_KEY: Optional[str] = None
    OCEAN_PRIVATE_KEY: Optional[str] = None
    NUMERAI_PUBLIC_ID: Optional[str] = None
    NUMERAI_SECRET_KEY: Optional[str] = None

    ETHICAL_TRADING_ENABLED: bool = False
    ETHICAL_ASSET_CONTEXT: Dict[str, Any] = {}

    INCIDENT_REPORTING_ENABLED: bool = False
    SENTINEL_ENABLED: bool = False
    ARENA_ENABLED: bool = False

    # ---------------------------------------------------------------------
    # Validators
    # ---------------------------------------------------------------------
    @model_validator(mode="before")
    def validate_signal_threshold(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        st = values.get("SIGNAL_THRESHOLD")
        if st is not None:
            try:
                st_float = float(st)
                if not (0.0 <= st_float <= 25.0):
                    raise ValueError(f"SIGNAL_THRESHOLD must be between 0.0 and 25.0, got {st!r}")
                values["SIGNAL_THRESHOLD"] = st_float
            except (ValueError, TypeError):
                raise ValueError(f"SIGNAL_THRESHOLD must be a number between 0.0 and 25.0, got {st!r}")
        return values

    @model_validator(mode="before")
    def normalize_trading_mode(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        tm = values.get("TRADING_MODE")
        if tm is not None:
            tm_str = str(tm).upper()
            aliases = {
                "LIVE": "DEFI",
                "HYPERLIQUID": "DEFI",
                "PAPER": "SPOT",
            }
            values["TRADING_MODE"] = aliases.get(tm_str, tm_str)
        return values

    @model_validator(mode="before")
    def normalize_env_mode(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        env_mode = values.get("ENV_MODE")
        if env_mode is not None:
            em = str(env_mode).lower()
            aliases = {
                "dev": "development",
                "live": "production",
                "prod": "production",
            }
            values["ENV_MODE"] = aliases.get(em, em)
        return values

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if name in ('SIGNAL_REVERSION', 'REBALANCER_REVERSION', 'USE_RAT_MEAN_REVERSION'):
            sync_val = bool(value)
            # prevent infinite recursion by checking current value
            for field in ('SIGNAL_REVERSION', 'REBALANCER_REVERSION', 'USE_RAT_MEAN_REVERSION'):
                if getattr(self, field, None) != sync_val:
                    super().__setattr__(field, sync_val)

@lru_cache()
def get_settings() -> Settings:
    return Settings()


def get_trading_symbols(settings: Settings = None) -> List[str]:
    """Get list of trading symbols from configuration."""
    if settings is None:
        settings = get_settings()

    default_symbols = [
        "BTCUSDC", "ETHUSDC", "SOLUSDC", "ADAUSDC", "AVAXUSDC",
        "MATICUSDC", "LINKUSDC", "UNIUSDC", "DOTUSDC", "ATOMUSDC",
    ]

    # [FIX] Prioritize the whitelist from .env if present
    env_symbols = getattr(settings, "SYMBOLS_WHITELIST", None) or getattr(settings, "TRADING_SYMBOLS", None)
    if env_symbols:
        if isinstance(env_symbols, str):
            return [s.strip() for s in env_symbols.split(",") if s.strip()]
        if isinstance(env_symbols, list):
            return env_symbols

    return default_symbols
