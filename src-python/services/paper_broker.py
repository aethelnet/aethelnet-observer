import time
import uuid
import random
import logging
import os
import json
from typing import Dict, List, Optional, Tuple
from services.wallet import Wallet
from services.database import get_database

logger = logging.getLogger("PaperBroker")

class PaperBroker:
    """
    Simulates a Centralized Exchange (CEX) like Binance.
    Handles Orders, Matching, Fees, and Latency.
    """
    def __init__(self, wallet: Wallet, fee_rate: float = 0.001, slippage_std: float = 0.0002, latency_ms: int = 50):
        from config import get_settings
        self.settings = get_settings()
        self.wallet = wallet
        # Execution Configuration (Tunable)
        self.execution_params = {
            "slippage_std": slippage_std, # Standard Deviation for price slippage
            "latency_ms": latency_ms,      # Network lag simulation
            "fee_rate": fee_rate
        }
        
        # Order Books (Per Symbol)
        # For Paper Trading, we don't fully simulate L2/L3 books.
        # We just store our own open orders and match against incoming OHLCV ticks.
        # Per-User State
        # Per-User State
        # self.open_orders[symbol][order_id] -> order_dict (contains user_id)
        self.open_orders: Dict[str, Dict[str, dict]] = {}
        # self.filled_orders[user_id] = [order, ...]
        self.filled_orders: Dict[int, List[dict]] = {}
        # self.positions[user_id][symbol] = {avg_price, quantity}
        self.positions: Dict[int, Dict[str, dict]] = {}
        # Caps to prevent unbounded memory growth in long-running sessions
        self.MAX_FILLED_HISTORY = 1000
        # Rate-limit state saves to reduce disk churn (seconds)
        self._last_save = 0.0
        self._save_interval = 5.0

    def place_order(self, user_id: int, symbol: str, side: str, order_type: str, quantity: float, price: Optional[float] = None) -> str:
        """
        Places a new order for a specific user.
        """
        # 1. Get User Wallet
        user_wallet = self.wallet
        if hasattr(self.wallet, "get_sub_wallet"):
            user_wallet = self.wallet.get_sub_wallet(f"user_{user_id}")
            # Ensure initial balance for new virtual users
            if not user_wallet.balances:
                user_wallet.balances = {"USDT": {"free": 10000.0, "locked": 0.0}}

        quote_asset = getattr(user_wallet, "base_currency", "USDT")
        base_asset = symbol.replace(quote_asset, "")
        
        required_funds = 0.0
        required_asset = ""
        
        if side == 'BUY':
            # Need USDT
            if order_type == 'MARKET':
                # Estimate cost (We don't know exact price yet, assume infinite until match?)
                # Paper Trading: We check funds at Execution time for Market Orders roughly?
                # Or block 100% of portfolio?
                # Let's verify 'free' balance exists > 0 at least.
                required_asset = quote_asset
                # For Market Buy, we rely on Execution to fail if insufficient.
            elif order_type == 'LIMIT':
                if price is None: raise ValueError("Limit Order requires price")
                required_funds = price * quantity
                required_asset = quote_asset
                
        elif side == 'SELL':
            # Need Base Asset (BTC, etc.)
            required_funds = quantity
            required_asset = base_asset

        # Lock Funds for LIMIT orders
        if order_type == 'LIMIT':
            if not user_wallet.lock_funds(required_asset, required_funds):
                raise ValueError(f"Insufficient {required_asset} for Limit Order")

        # 2. Create Order Object
        order_id = str(uuid.uuid4())
        order = {
            "id": order_id,
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
            "price": price, # None for Market
            "status": "NEW",
            "created_at": time.time(),
            "locked_funds": required_funds if order_type == 'LIMIT' else 0.0,
            "locked_asset": required_asset if order_type == 'LIMIT' else None
        }
        
        # 3. Simulate Latency
        latency_sec = self.execution_params.get('latency_ms', 50) / 1000.0
        order['activation_time'] = time.time() + latency_sec
        
        if symbol not in self.open_orders:
            self.open_orders[symbol] = {}
        
        order['user_id'] = user_id
        self.open_orders[symbol][order_id] = order
        
        return order_id

    def cancel_order(self, symbol: str, order_id: str) -> bool:
        if symbol in self.open_orders and order_id in self.open_orders[symbol]:
            order = self.open_orders[symbol].pop(order_id)
            # Unlock funds
            if order['type'] == 'LIMIT':
                self.wallet.unlock_funds(order['locked_asset'], order['locked_funds'])
            order['status'] = 'CANCELLED'
            # Keep cancelled orders in short history to aid debugging, but cap size
            self.filled_orders.append(order)
            if len(self.filled_orders) > self.MAX_FILLED_HISTORY:
                # Trim oldest entries
                self.filled_orders = self.filled_orders[-self.MAX_FILLED_HISTORY:]
            return True
        return False

    def _update_unrealized_pnl(self, symbol: str, current_price: float):
        """
        Calculates unrealized PnL for active positions.
        """
        if symbol in self.positions:
            pos = self.positions[symbol]
            qty = pos.get('quantity', 0.0)
            avg = pos.get('avg_price', 0.0)
            
            if abs(qty) > 0:
                if qty > 0: # Long
                    unrealized = (current_price - avg) * qty
                else: # Short
                    unrealized = (avg - current_price) * abs(qty)
                
                # Store it in the position dict for UI/Logic to see
                pos['unrealized_pnl'] = unrealized
                pos['current_price'] = current_price

                # --- SL / TP MONITORING ---
                self._check_risk_levels(symbol, current_price, pos)

    def _check_risk_levels(self, symbol: str, current_price: float, pos: dict):
        """
        Checks if SL or TP have been triggered.
        """
        sl = pos.get('sl')
        tp = pos.get('tp')
        qty = pos.get('quantity', 0.0)
        entry = pos.get('avg_price', 0.0)
        
        if qty == 0: return

        def parse_target(target, entry, is_tp, is_long):
            if not target: return None
            try:
                if target.endswith('%'):
                    pct = float(target[:-1]) / 100.0
                    # For SL: Long SL is below (entry - pct*entry), Short SL is above (entry + pct*entry)
                    # For TP: Long TP is above (entry + pct*entry), Short TP is below (entry - pct*entry)
                    if is_tp:
                        return entry * (1 + pct) if is_long else entry * (1 - pct)
                    else:
                        return entry * (1 - pct) if is_long else entry * (1 + pct)
                return float(target)
            except:
                return None

        is_long = qty > 0
        sl_price = parse_target(sl, entry, is_tp=False, is_long=is_long)
        tp_price = parse_target(tp, entry, is_tp=True, is_long=is_long)

        triggered = False
        reason = ""

        if sl_price:
            if is_long and current_price <= sl_price:
                triggered = True
                reason = f"STOP LOSS HIT @ {current_price:.2f}"
            elif not is_long and current_price >= sl_price:
                triggered = True
                reason = f"STOP LOSS HIT @ {current_price:.2f}"

        if not triggered and tp_price:
            if is_long and current_price >= tp_price:
                triggered = True
                reason = f"TAKE PROFIT HIT @ {current_price:.2f}"
            elif not is_long and current_price <= tp_price:
                triggered = True
                reason = f"TAKE PROFIT HIT @ {current_price:.2f}"

        if triggered:
            logger.info(f"[RISK] {symbol}: {reason} for user {user_id}. Closing position.")
            self.close_position(user_id, symbol, current_price)


    def on_tick(self, symbol: str, tick: dict):
        """
        Process incoming market data (Tick/Candle) to match orders.
        tick: {'open', 'high', 'low', 'close', 'timestamp'}
        We assume this is a 1m candle or 'tick' aggregate.
        """
        logger.info(f"[TICK] Received Price: {tick['close']:.2f}")
        if symbol not in self.open_orders: return
        
        # Copy to avoid concurrently modifying loop
        current_orders = list(self.open_orders[symbol].values())
        
        current_time = time.time() # Or use tick timestamp?
        # Using tick timestamp is better for backtesting, but current time for 'Paper Trading' live?
        # If 'Paper Trading' is running alongside live feed, use system time.
        
        current_price = tick['close']
        # --- UNREALIZED PnL UPDATE --- 
        self._update_unrealized_pnl(symbol, current_price)
        logger.info(f"[PNL DEBUG] Current Price for {symbol}: {current_price:.2f}")
        high = tick['high']
        low = tick['low']
        
        for order in current_orders:
            if current_time < order.get('activation_time', 0):
                continue # Latency simulation
            
            executed = False
            fill_price = 0.0
            
            # --- MARKET ORDERS ---
            if order['type'] == 'MARKET':
                # Slippage Model: Random walk around 'close'
                std_dev = self.execution_params.get('slippage_std', 0.0002)
                slippage = random.gauss(0, std_dev) * current_price
                if order['side'] == 'BUY':
                    fill_price = current_price + abs(slippage) # Pay more
                else:
                    fill_price = current_price - abs(slippage) # Sell less
                
                executed = True

            # --- LIMIT ORDERS ---
            elif order['type'] == 'LIMIT':
                limit_price = order['price']
                if order['side'] == 'BUY':
                    # Buy if Low <= Limit
                    if low <= limit_price:
                        # Assuming we fill at Limit Price (or better if gapped?)
                        # Optimistic: Fill at Limit.
                        fill_price = limit_price
                        executed = True
                elif order['side'] == 'SELL':
                    # Sell if High >= Limit
                    if high >= limit_price:
                        fill_price = limit_price
                        executed = True

            # --- EXECUTION ---
            if executed:
                self._execute_fill(order, fill_price)

    def _execute_fill(self, order: dict, price: float):
        """Finalizes the trade, updates wallet and positions per user."""
        user_id = order.get('user_id', 0)
        symbol = order['symbol']
        side = order['side']
        qty = order['quantity']
        
        # Get User Wallet context
        user_wallet = self.wallet
        if hasattr(self.wallet, "get_sub_wallet"):
            user_wallet = self.wallet.get_sub_wallet(f"user_{user_id}")
            
        cost = abs(price * qty)
        fee = cost * self.execution_params.get('fee_rate', 0.001)
        quote_asset = getattr(user_wallet, "base_currency", "USDT")
        
        # Deduct Fee
        user_wallet.deduct_balance(quote_asset, fee)
        
        # Release Locks if Limit
        if order['type'] == 'LIMIT':
             user_wallet.unlock_funds(quote_asset, order['locked_funds'])

        # Update Position State
        if user_id not in self.positions:
            self.positions[user_id] = {}
            
        current_pos = self.positions[user_id].get(symbol, {'quantity': 0.0, 'avg_price': 0.0})
        curr_qty = current_pos['quantity']
        curr_avg = current_pos['avg_price']
        
        side_mult = 1.0 if side == 'BUY' else -1.0
        signed_fill_qty = qty * side_mult
        
        new_qty = curr_qty + signed_fill_qty
        new_avg = curr_avg
        
        pnl = 0.0
        # Logic: 
        # 1. Increasing Position (Open/Add): Update Avg Entry.
        # 2. Decreasing Position (Close/Reduce): Realize PnL. Keep Avg Entry same.
        
        # Case A: Same Sign or Zero (Increasing exposure)
        if (curr_qty == 0) or (curr_qty > 0 and signed_fill_qty > 0) or (curr_qty < 0 and signed_fill_qty < 0):
            total_val = (abs(curr_qty) * curr_avg) + (qty * price)
            total_qty = abs(curr_qty) + qty
            new_avg = total_val / total_qty
            
        # Case B: Opposite Sign (Closing / Flipping)
        else:
            closed_qty = min(abs(curr_qty), qty)
            if curr_qty > 0: # Closing Long
                pnl = (price - curr_avg) * closed_qty
            else: # Closing Short
                pnl = (curr_avg - price) * closed_qty
                
            # Credit PnL to Wallet
            if pnl > 0:
                ratio = getattr(user_wallet, 'profit_secure_ratio', 0.5)
                pool_share = pnl * (1.0 - ratio)
                user_wallet.credit(quote_asset, pool_share)
                logger.info(f"[GAME] User {user_id} WIN! +{pnl:.2f} USDT.")
            else:
                user_wallet.credit(quote_asset, pnl)
                logger.info(f"[GAME] User {user_id} LOSS. {pnl:.2f} USDT.")

            order['pnl'] = pnl
            if qty > abs(curr_qty):
                new_avg = price # Flip entry
        
        # Manage Entry Time (for Hold Time calc)
        new_entry_time = current_pos.get('entry_time', time.time())
        if curr_qty == 0:
            new_entry_time = time.time() # Fresh position
        elif (curr_qty > 0 and new_qty < 0) or (curr_qty < 0 and new_qty > 0):
             new_entry_time = time.time() # Flip position

        if abs(new_qty) < 1e-6:
            # [DUST SWEEP] Quantity is effectively zero. Remove from memory.
            if symbol in self.positions[user_id]:
                del self.positions[user_id][symbol]
            new_qty = 0.0 
        else:
            self.positions[user_id][symbol] = {
                'quantity': new_qty, 
                'avg_price': new_avg,
                'sl': order.get('sl'),
                'tp': order.get('tp'),
                'entry_time': new_entry_time
            }
        
        # Logging
        order['status'] = 'FILLED'
        order['fill_price'] = price
        order['filled_at'] = time.time()
        
        if user_id not in self.filled_orders:
            self.filled_orders[user_id] = []
        self.filled_orders[user_id].append(order)
        
        if symbol in self.open_orders and order['id'] in self.open_orders[symbol]:
            del self.open_orders[symbol][order['id']]

        # --- PERSIST TO DB ---
        try:
            db = get_database()
            meta = {k: v for k, v in order.items() if k not in ["symbol", "filled_at", "created_at", "side", "fill_price", "price", "quantity", "user_id"]}
            db.insert_trade(symbol, order['filled_at'], side, price, qty, user_id=user_id, metadata=meta)
            db.upsert_position(symbol, new_qty, user_id=user_id, avg_price=new_avg, metadata={"updated_at": order['filled_at']})
            # Wallet Sync
            db.upsert_wallet(user_id, user_wallet.balances, user_wallet.vault)
        except Exception as e:
            logger.error(f"Failed to persist trade/position/wallet to DB: {e}")
        
        self.save_state_debounced()

    def get_open_orders(self, symbol: str) -> List[dict]:
        # logger.info(f"[TICK] Received Price: {tick['close']:.2f}") - REMOVE spurious log
        if symbol not in self.open_orders: return []
        return list(self.open_orders[symbol].values())

    def save_state_debounced(self):
        """Rate-limited save to disk."""
        now = time.time()
        if (now - self._last_save) >= self._save_interval:
            try:
                state_path = os.path.join(self.settings.DATA_DIR, "broker_state.json")
                self.save_state(state_path)
                self._last_save = now
            except Exception as e:
                logger.error(f"Failed to save broker state: {e}")

    def get_trade_history(self, user_id: int, limit: int = 100) -> List[dict]:
        """
        Returns list of filled orders from DB for a specific user.
        """
        try:
            db = get_database()
            db_trades = db.get_trades(user_id=user_id, limit=limit)
            orders = []
            for t in db_trades:
                order = {
                    "id": t.get("id"),
                    "symbol": t.get("symbol"),
                    "side": t.get("action"),
                    "fill_price": t.get("price"),
                    "quantity": t.get("quantity"),
                    "filled_at": t.get("ts"),
                    "status": "FILLED"
                }
                if t.get("metadata"):
                    order.update(t["metadata"])
                orders.append(order)
            return orders
        except Exception as e:
            logger.error(f"Failed to get trade history from DB: {e}")
            return sorted(self.filled_orders.get(user_id, []), key=lambda x: x.get('filled_at', 0), reverse=True)

    def get_positions(self, user_id: int) -> Dict[str, dict]:
        """
        Returns all active positions for a user.
        """
        return self.positions.get(user_id, {})

    def get_position(self, user_id: int, symbol: str) -> float:
        """
        Returns quantity for specific symbol and user.
        """
        user_pos = self.positions.get(user_id, {})
        pos = user_pos.get(symbol, {})
        return pos.get('quantity', 0.0)

    def save_state(self, filepath: str):
        # Positions and Filled Orders are now primarily in SQL, 
        # but we keep a small JSON cache for fast startup/non-persistent environments.
        state = {
            "open_orders": self.open_orders,
            "filled_orders": {uid: orders[:10] for uid, orders in self.filled_orders.items()},
            "positions": self.positions
        }
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=4)

    def load_state(self, filepath: str):
        if not os.path.exists(filepath):
            return False
        try:
            with open(filepath, 'r') as f:
                state = json.load(f)
            
            # State recovery with type casting for keys (JSON keys are always strings)
            raw_orders = state.get("open_orders", {})
            self.open_orders = {s: {oid: o for oid, o in orders.items()} for s, orders in raw_orders.items()}
            
            raw_filled = state.get("filled_orders", {})
            self.filled_orders = {int(uid): orders for uid, orders in raw_filled.items()}
            
            raw_pos = state.get("positions", {})
            self.positions = {int(uid): pos for uid, pos in raw_pos.items()}
            
            # --- SYNC WITH DB ---
            try:
                db = get_database()
                db_positions = db.get_positions() # All users
                if db_positions:
                    for p in db_positions:
                        uid = p.get('user_id', 0)
                        if uid not in self.positions: self.positions[uid] = {}
                        self.positions[uid][p['symbol']] = {
                            'quantity': p['quantity'], 
                            'avg_price': p['avg_price'],
                            'sl': p.get('metadata', {}).get('sl') if p.get('metadata') else None,
                        }
            except Exception as e:
                logger.error(f"Failed to sync positions from DB: {e}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            return False

    def reset_account(self, user_id: int):
        """Wipes all positions and orders for a SPECIFIC user, resets virtual wallet."""
        self.positions[user_id] = {}
        if user_id in self.filled_orders:
            self.filled_orders[user_id] = []
            
        # Clear specific user's open orders across all symbols
        for symbol in self.open_orders:
            to_remove = [oid for oid, order in self.open_orders[symbol].items() if order.get('user_id') == user_id]
            for oid in to_remove:
                del self.open_orders[symbol][oid]
        
        # Reset Wallet
        user_wallet = self.wallet
        if hasattr(self.wallet, "get_sub_wallet"):
            user_wallet = self.wallet.get_sub_wallet(f"user_{user_id}")
            
        quote_asset = getattr(user_wallet, "base_currency", "USDT")
        user_wallet.balances = {quote_asset: {"free": 10000.0, "locked": 0.0}}
        
        # Clear User from DB
        try:
            db = get_database()
            with db._connect() as conn:
                conn.execute("DELETE FROM trades WHERE user_id = ?", (user_id,))
                conn.execute("DELETE FROM positions WHERE user_id = ?", (user_id,))
                conn.execute("DELETE FROM wallets WHERE user_id = ?", (user_id,))
                conn.commit()
        except:
            pass

        self.save_state_debounced()
        return True

    def get_balance(self, user_id: int) -> float:
        """Get Quote Balance (Free) for a specific user."""
        user_wallet = self.wallet
        if hasattr(self.wallet, "get_sub_wallet"):
            user_wallet = self.wallet.get_sub_wallet(f"user_{user_id}")
            
        quote_asset = getattr(user_wallet, "base_currency", "USDT")
        bal_data = user_wallet.get_balance(quote_asset)
        if isinstance(bal_data, dict):
            return float(bal_data.get("free", 0.0))
        return float(bal_data)
        
    def get_position_detailed(self, user_id: int, symbol: str) -> Optional[Dict]:
        """
        Returns rich position data for UI. 
        """
        symbol = symbol.upper()
        user_pos = self.positions.get(user_id, {})
        if symbol in user_pos:
            pos = user_pos[symbol]
            if pos.get('quantity', 0) == 0: return None
            return {
                "entry_price": pos.get('avg_price', 0.0),
                "size": pos.get('quantity', 0.0),
                "sl": pos.get('sl'),
                "tp": pos.get('tp'),
                "unrealized_pnl": pos.get('unrealized_pnl', 0.0)
            }
        return None

    def open_position(self, user_id: int, symbol: str, quantity: float, price: float, sl: Optional[str] = None, tp: Optional[str] = None) -> Tuple[bool, str]:
        """Instant Market Execution."""
        try:
            side = "BUY" if quantity > 0 else "SELL"
            order = {
                "id": f"game_{int(time.time()*1000)}",
                "user_id": user_id,
                "symbol": symbol,
                "side": side,
                "type": "MARKET",
                "quantity": abs(quantity),
                "status": "FILLED",
                "created_at": time.time(),
                "filled_at": time.time(),
                "sl": sl,
                "tp": tp
            }
            
            # Funds Check
            cost = abs(quantity) * price
            bal = self.get_balance(user_id)
            if side == "BUY" and bal < cost:
                return False, f"Insufficient Funds. Need ${cost:.2f}"
            
            self._execute_fill(order, price)
            return True, "Executed"
        except Exception as e:
            logger.error(f"Open Pos Error: {e}")
            return False, str(e)

    def close_position(self, user_id: int, symbol: str, price: float) -> Tuple[bool, str]:
        """Instant Close."""
        try:
            user_pos = self.positions.get(user_id, {})
            if symbol not in user_pos or user_pos[symbol]['quantity'] == 0:
                return False, "No Position"
            
            qty = user_pos[symbol]['quantity']
            side = "SELL" if qty > 0 else "BUY"
            
            order = {
                "id": f"game_close_{int(time.time()*1000)}",
                "user_id": user_id,
                "symbol": symbol,
                "side": side,
                "type": "MARKET",
                "quantity": abs(qty),
                "status": "FILLED",
                "created_at": time.time(),
                "filled_at": time.time()
            }
            
            self._execute_fill(order, price)
            return True, "Closed"
        except Exception as e:
            return False, str(e)

_broker_instance = None

def get_broker(wallet: Optional[Wallet] = None) -> PaperBroker:
    global _broker_instance
    if _broker_instance is None:
        if wallet is None:
            from services.wallet import get_wallet
            wallet = get_wallet()
        _broker_instance = PaperBroker(wallet)
        from config import get_settings
        settings = get_settings()
        _broker_instance.load_state(os.path.join(settings.DATA_DIR, "broker_state.json"))
    return _broker_instance
