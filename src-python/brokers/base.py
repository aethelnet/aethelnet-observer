from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseBroker(ABC):
    """
    Abstract interface for brokers.

    Implementations (Binance, Alpaca, PaperBroker, etc.) must provide a consistent async API
    used by OmniRouter and higher-level services:

      - get_balance(asset) -> float
      - get_position(symbol) -> float | None
      - place_order(symbol, side, order_type, quantity, params) -> order object or None
      - cancel_all_orders(symbol) -> bool
      - close() -> cleanly close connections

    Keep implementations resilient: return None/0.0 for non-fatal failures and populate
    a broker-local _last_error string when appropriate to aid diagnostics.
    """

    async def connect(self) -> bool:
        """
        Optional async connection/hydration step. 
        Returns True if successful, False otherwise.
        """
        return True

    @abstractmethod
    async def get_balance(self, asset: str) -> float:
        """Return free balance of specific asset."""
        pass
        
    @abstractmethod
    async def get_position(self, symbol: str) -> float:
        """Return signed position size (Positive=Long, Negative=Short)."""
        pass
        
    @abstractmethod
    async def place_order(self, symbol: str, side: str, order_type: str, quantity: float, price: float = None, params: Dict = {}) -> Any:
        """Execute an order. Return order object or ID."""
        pass
        
    @abstractmethod
    async def cancel_all_orders(self, symbol: str) -> bool:
        """Cancel all open orders for a symbol."""
        pass
        
    @abstractmethod
    async def close(self):
        """Cleanly close connection."""
        pass
    
    async def get_max_leverage(self, symbol: str) -> float:
        """Return maximum allowable leverage for a symbol (Default: 1.0)"""
        return 1.0
    
    async def get_margin_state(self) -> Dict[str, float]:
        """
        Returns margin state for the account.
        
        This method provides margin utilization metrics needed for accurate
        position sizing that accounts for already-used margin.
        
        Returns:
            Dict with keys:
                - 'account_value': Total account equity (USD/USDC/USDT)
                - 'margin_used': Margin currently locked in positions
                - 'available_margin': Free margin available for new positions
                - 'utilization': Margin usage ratio (0.0 to 1.0)
        
        Default implementation returns zeros (for spot-only brokers).
        Override in margin-trading brokers (Hyperliquid, Binance Futures).
        """
        return {
            'account_value': 0.0,
            'margin_used': 0.0,
            'available_margin': 0.0,
            'utilization': 0.0
        }
