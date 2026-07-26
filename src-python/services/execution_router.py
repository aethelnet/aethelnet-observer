
"""
Execution Router
Handles trade execution logic for various styles (CORE, WARREN, QUANT).
Currently operates in 'Paper Sovereign' mode (Simulated Execution),
but records trades to the persistent Tracker database.
"""
import logging
import asyncio
from typing import Dict, Optional
from datetime import datetime
from services.tracker import get_tracker
from services.data_manager import get_data_manager
from dataclasses import dataclass

logger = logging.getLogger("ExecutionRouter")

@dataclass
class Trade:
    symbol: str
    side: str
    quantity: float
    entry_price: float
    exit_price: float
    pnl: float
    status: str
    strategy: str
    timestamp: datetime

class ExecutionRouter:
    def __init__(self):
        self.tracker = get_tracker()
        self.dm = get_data_manager()

    async def execute_order(self, user_id: int, symbol: str, side: str, quantity: float, style: str = "CORE") -> Dict:
        """
        Executes a trade order based on the user's style.
        Returns a 'Trade Ticket' dictionary.
        """
        from services.risk_manager import get_risk_manager
        
        symbol = symbol.upper()
        side = side.upper()
        risk = get_risk_manager()
        
        # 1. Price Check (Simulated Exchange)
        market_data = await self.dm.get_ticker_snapshot(symbol)
        price = market_data.get('price', 0)
        
        if price <= 0:
            return {"success": False, "error": "No Liquidity (Price 0)"}

        # 2. Risk Management Check (Safety First)
        risk_check = risk.check_trade_risk(symbol, side, quantity, price)
        if not risk_check['allowed']:
             logger.warning(f"Trade BLOCKED by RiskManager: {risk_check['reason']}")
             return {"success": False, "error": risk_check['reason']}

        # 3. Execution Logic
        execution_note = "Market Order"
        avg_price = price
        
        if style == "WARREN":
            discount = price * 0.001 
            avg_price = price - discount if side == "BUY" else price + discount
            execution_note = "Limit Fill (Value Optimization)"
            
        elif style == "QUANT":
            execution_note = "TWAP Algo Execution"

        # 4. Record Trade (Tracker Persistence)
        try:
            # We map "BUY" to OPEN and "SELL" to CLOSE for simplicity in this model
            # In proper systems, SELL could be Short Open or Long Close.
            # Here we assume we are opening or closing 'positions'.
            
            if side == "BUY":
                self.tracker.open_position(symbol, side, avg_price, quantity)
            elif side == "SELL":
                # Close existing if exists
                self.tracker.close_position(symbol, avg_price)
            
            # Log it
            logger.info(f"EXECUTED {side} {symbol} @ {avg_price} ({style})")
            
            return {
                "success": True,
                "ticket_id": f"ORD-{int(datetime.utcnow().timestamp())}",
                "symbol": symbol,
                "side": side,
                "price": avg_price,
                "quantity": quantity,
                "style": style,
                "note": execution_note,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Execution Failed: {e}")
            return {"success": False, "error": str(e)}

_router = None

def get_execution_router():
    global _router
    if not _router:
        _router = ExecutionRouter()
    return _router
