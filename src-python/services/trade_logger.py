"""
      .  : .
  .  [__?RECORD__]  .   T H E _ A R C H I V E
    / : : : : : \      [MEMORY_PERSISTENCE]
   | : : :!: : : |
   | : : : : : : |     [LAYER]:     PERSISTENCE
    \ :_:_:_:_: /      [FREQUENCY]: EVENT_DRAW
     '---------'       [AUTHORITY]: SYSTEM_R00T
       |  |  |         [PHASE]:     26 (GLITCH_II)
      
"""

from datetime import datetime, timezone
import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger("TradeLogger")

class TradeLogger:
    def __init__(self, data_dir: str = "./data/archive"):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.trades_file = os.path.join(self.data_dir, "trades.jsonl")
        self.thoughts_file = os.path.join(self.data_dir, "thoughts.jsonl")
        
        logger.info(f"Archive System Initialized at {self.data_dir}")

    def log_trade(self, trade: Dict[str, Any]):
        """Append trade to immutable record."""
        try:
            # Ensure timestamp
            if 'timestamp' not in trade:
                trade['timestamp'] = int(time.time() * 1000)
            
            # Format: JSON Line
            line = json.dumps(trade) + "\n"
            
            with open(self.trades_file, "a") as f:
                f.write(line)
                
            logger.info(f"Trade Archived: {trade.get('symbol')} {trade.get('side')}")
            
        except Exception as e:
            logger.error(f"Failed to archive trade: {e}")

    def log_thought(self, thought: Dict[str, Any]):
        """Append thought process to record."""
        try:
             # Ensure timestamp
            if 'timestamp' not in thought:
                thought['timestamp'] = int(time.time() * 1000)
                
            line = json.dumps(thought) + "\n"
            
            with open(self.thoughts_file, "a") as f:
                f.write(line)
        except Exception:
            pass # Fail silently for thoughts to preserve speed

    def get_recent_trades(self, limit: int = 50) -> list:
        """Retrieve recent trades from Truth Source (DataManager DB)."""
        try:
            from services.data_manager import get_data_manager
            from sqlalchemy import text
            
            dm = get_data_manager()
            engine = dm.engine
            
            # Fetch closed positions from DB
            query = text("SELECT symbol, side, entry_price, exit_price, quantity, pnl, exit_time FROM positions WHERE status='CLOSED' ORDER BY exit_time DESC LIMIT :limit")
            
            trades = []
            with engine.connect() as conn:
                result = conn.execute(query, {"limit": limit})
                rows = result.fetchall()
                
                for r in rows:
                    # SQLAlchemy rows are accessible by index or key
                    # r[0]=symbol, r[1]=side, r[6]=exit_time
                    trades.append({
                        'symbol': r[0],
                        'side': r[1],
                        'entry_price': float(r[2]) if r[2] is not None else 0.0,
                        'exit_price': float(r[3]) if r[3] is not None else 0.0,
                        'quantity': float(r[4]) if r[4] is not None else 0.0,
                        'pnl': float(r[5]) if r[5] is not None else 0.0,
                        'timestamp': datetime.fromtimestamp(float(r[6]), tz=timezone.utc).isoformat() if r[6] else "N/A",
                        'exit_time': r[6]
                    })
            
            return trades
        except Exception as e:
            logger.error(f"Failed to query DataManager DB: {e}")
            # Fallback to disk is risky if file is stale, but better than crash
            return self._get_from_disk(limit)

    def _get_from_disk(self, limit: int) -> list:
        trades = []
        if not os.path.exists(self.trades_file):
            return []
        try:
            with open(self.trades_file, "r") as f:
                lines = f.readlines()
                for line in reversed(lines[-limit:]):
                    try:
                        t = json.loads(line)
                        # Patch timestamp for formatter
                        if 'timestamp' in t and isinstance(t['timestamp'], (int, float)):
                             from datetime import datetime, timezone
                             # Assume ms if broad, but safely handle
                             try:
                                 val = float(t['timestamp'])
                                 # dynamic check for ms vs sec
                                 if val > 1e11: val /= 1000.0
                                 t['timestamp'] = datetime.fromtimestamp(val, tz=timezone.utc).isoformat()
                             except:
                                 t['timestamp'] = str(t['timestamp'])
                        trades.append(t)
                    except:
                        continue
            return trades
        except Exception:
            return []

# Singleton
_archive = None

def get_archive() -> TradeLogger:
    global _archive
    if _archive is None:
        _archive = TradeLogger()
    return _archive
