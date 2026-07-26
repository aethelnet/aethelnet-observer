from functools import lru_cache
from services.universe import UniverseManager
from services.connection_manager import ConnectionManager
from services.market_data_service import MarketDataService
from config import get_settings

settings = get_settings()

@lru_cache()
def get_universe_manager():
    return UniverseManager()

@lru_cache()
def get_connection_manager():
    return ConnectionManager()

@lru_cache()
def get_market_data_service():
    universe = get_universe_manager()
    manager = get_connection_manager()
    return MarketDataService(universe, manager)
