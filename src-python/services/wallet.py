import time
import json
from typing import Dict, List, Optional, Any
import os
import logging
from core.failsafe import atomic_write

logger = logging.getLogger("OmniWallet")

class Wallet:
    """
    Represents a sub-wallet for a single exchange or account.

    Manages free/locked balances, a simple profit vault, and common operations
    (deposit, lock/unlock funds, credit/spend). Intended to be lightweight and
    used by PaperBroker and OmniWallet.
    """
    def __init__(self, name: str, initial_balance: float = 0.0, base_currency: str = "USDC"):
        """
        Initialize a sub-wallet.
        
        IMPORTANT: initial_balance defaults to 0.0 (not $10k) to prevent phantom money
        when broker connections fail. Real balances come from _reconcile_* methods.
        """
        self.name = name
        self.base_currency = base_currency
        self.balances = {
            base_currency: {"free": initial_balance, "locked": 0.0, "buying_power": initial_balance}
        }
        # THE VAULT (Secured Profits)
        self.vault = {
            base_currency: 0.0 
        }
        self.profit_secure_ratio = 0.5 # Default 50% of profits go to Vault
        self.initial_capital = initial_balance
        self.history = []
        # Provenance metadata (help trace where balances originated)
        # Possible values: 'unknown', 'primary', 'mother_vault_init', 'loaded', 'reconciled'
        self.source = "unknown"

    def get_balance(self, asset: str) -> Dict[str, float]:
        """Returns {free, locked} for an asset."""
        return self.balances.get(asset, {"free": 0.0, "locked": 0.0})

    def deposit(self, asset: str, amount: float):
        if asset not in self.balances:
            self.balances[asset] = {"free": 0.0, "locked": 0.0}
        self.balances[asset]["free"] += amount
        self._log("DEPOSIT", asset, amount)

    def lock_funds(self, asset: str, amount: float) -> bool:
        """Locks funds for an order."""
        if self.balances.get(asset, {}).get("free", 0) >= amount:
            self.balances[asset]["free"] -= amount
            self.balances[asset]["locked"] += amount
            return True
        return False

    def unlock_funds(self, asset: str, amount: float):
        """Unlocks funds (e.g. cancelled order)."""
        if self.balances.get(asset, {}).get("locked", 0) >= amount:
            self.balances[asset]["locked"] -= amount
            self.balances[asset]["free"] += amount

    def spend_locked(self, asset: str, amount: float):
        """Consumes locked funds (order filled)."""
        if self.balances.get(asset, {}).get("locked", 0) >= amount:
            self.balances[asset]["locked"] -= amount
        else:
            remaining = amount - self.balances[asset]["locked"]
            self.balances[asset]["locked"] = 0
            self.balances[asset]["free"] -= remaining

    def credit(self, asset: str, amount: float):
        """Adds to free balance (e.g. receiving asset from buy, or USDT from sell)."""
        if asset not in self.balances:
            self.balances[asset] = {"free": 0.0, "locked": 0.0}
        self.balances[asset]["free"] += amount

    def total_usd_value(self, prices: Dict[str, float]) -> float:
        """Estimates total portfolio value in USD based on provided current prices."""
        total = 0.0
        for asset, bal in self.balances.items():
            qty = bal["free"] + bal["locked"]
            # Treat all stablecoins as Cash (1.0)
            if asset in [self.base_currency, 'USDT', 'USDC', 'BUSD', 'DAI']:
                total += qty
            elif asset in prices:
                total += qty * prices[asset]
        return total

    def get_snapshot(self) -> Dict:
        """Returns a complete snapshot of the wallet state."""
        return {
            "name": self.name,
            "balances": self.balances,
            "vault": self.vault,
            "total_equity": self.total_usd_value({}), # Estimate
            "source": getattr(self, "source", "unknown")
        }

    def _log(self, action: str, asset: str, amount: float):
        self.history.append({
            "ts": time.time(),
            "action": action,
            "asset": asset,
            "amount": amount
        })
        # Cap history to last N entries to avoid unbounded memory growth
        if len(self.history) > 100:
            self.history = self.history[-100:]

    def reset(self):
        self.balances = {
            self.base_currency: {"free": self.initial_capital, "locked": 0.0}
        }
        self.history = []

    def to_dict(self):
        return {
            "name": self.name,
            "balances": self.balances,
            "vault": self.vault,
            "profit_secure_ratio": self.profit_secure_ratio,
            "history": self.history,
            "initial_capital": self.initial_capital,
            "base_currency": self.base_currency,
            "source": getattr(self, "source", "unknown")
        }

    def from_dict(self, data: Dict):
        self.name = data.get("name", self.name)
        self.balances = data.get("balances", self.balances)
        self.vault = data.get("vault", self.vault)
        self.profit_secure_ratio = data.get("profit_secure_ratio", 0.5)
        self.history = data.get("history", [])
        self.initial_capital = data.get("initial_capital", self.initial_capital)
        self.base_currency = data.get("base_currency", self.base_currency)
        self.source = data.get("source", "loaded")




class OmniWallet:
    """
    High-level wallet manager that aggregates multiple sub-wallets.

    Provides a primary wallet proxy for backward compatibility and an auto-finance
    'mother vault' to top up sub-wallets automatically when configured. Designed
    to avoid re-entrancy between financing and telemetry injection.
    """
    def __init__(self):
        self.wallets: Dict[str, Wallet] = {}
        self.connected = False
        self.last_error = {}
        self.last_debug = {}
        
        # Determine primary key based on trading mode (must match router expectations)
        # Router expects 'binance_spot' or 'binance_future' based on TRADING_MODE
        try:
            from config import get_settings
            settings = get_settings()
            if settings.TRADING_MODE.upper() == "FUTURES":
                self.primary_key = "binance_future"
            elif settings.TRADING_MODE.upper() == "DEFI":
                self.primary_key = "hyperliquid"
            else:
                # Default to spot (SPOT mode or unknown)
                self.primary_key = "binance_spot"
        except Exception:
            # Fallback to spot if settings unavailable
            self.primary_key = "binance_spot"
        
        self.mother_wallet_key = "mother_vault"
        
        # Auto-financing configuration
        self.auto_finance_enabled = True
        self.min_balance_threshold = 100.0  # Minimum balance before auto-finance triggers
        self.auto_finance_amount = 500.0    # Amount to transfer when financing
        self.max_auto_finance_per_day = 2000.0  # Daily limit for auto-financing
        self.daily_finance_used = 0.0
        self.last_finance_reset = time.time()
        
        # Reentrancy guard to prevent recursive auto-finance checks
        self._auto_finance_checking: set = set()
        
        # Initialize Primary and Mother Vault
        self.wallets[self.primary_key] = Wallet(self.primary_key)
        # provenance: primary created at init
        self.wallets[self.primary_key].source = "primary"
        # Mother Vault (Profit Silo)
        # Default to 0.0 for Real/Live modes to avoid confusion.
        self.wallets[self.mother_wallet_key] = Wallet(self.mother_wallet_key, initial_balance=0.0, base_currency="USDC")
        # provenance: mother vault seeded at init
        self.wallets[self.mother_wallet_key].source = "mother_vault_init"
        # Reconciliation bookkeeping: avoid hitting exchange too frequently
        self.last_reconcile = 0.0
        self.RECONCILE_INTERVAL = 300  # seconds between automatic reconciliations
        
        # Risk Tolerance Level (0-100 scale, stepped by 5)
        # 0=Ultra Conservative, 50=Moderate, 100=Ultra Aggressive
        self.risk_level = 50  # Default to moderate (50%)

    async def get_all_balances(self, force: bool = False) -> Dict[str, Dict[str, Dict[str, float]]]:
        """
        Returns latest balances. Reconciles if force=True or if cache is stale.
        """
        import asyncio
        import time
        
        # Avoid heavy reconciliation on every poll if it just happened
        if force or (time.time() - self.last_reconcile > 60):
            try:
                # Reconcile all providers with a hard timeout to prevent hangs
                await asyncio.wait_for(self.update(force), timeout=45.0)
            except asyncio.TimeoutError:
                logger.warning("[OmniWallet] Global reconciliation timeout")
            except Exception as e:
                logger.error(f"[OmniWallet] Global reconciliation failed: {e}")
        
        # Return current state (even if update failed/timed out, we show last known)
        return {k: w.balances for k, w in self.wallets.items()}

    async def get_sub_wallet_async(self, key: str) -> Wallet:
        """Async wrapper for get_sub_wallet to avoid blocking."""
        # For now, just call the sync version as it's just dict lookup/creation
        return self.get_sub_wallet(key)

    def get_sub_wallet(self, key: str) -> Wallet:
        """
        Returns a specific sub-wallet by ID.
        """
        if key not in self.wallets:
            # Try load from DB first
            if key.startswith("user_"):
                try:
                    from services.database import get_database
                    db = get_database()
                    uid = int(key.replace("user_", ""))
                    db_state = db.get_wallet_state(uid)
                    if db_state:
                         w = Wallet(key)
                         w.balances = db_state.get('balances', w.balances)
                         w.vault = db_state.get('vault', w.vault)
                         self.wallets[key] = w
                         return w
                except Exception as e:
                    logger.debug(f"[OmniWallet] Could not load user wallet {key} from DB: {e}")
            self.wallets[key] = Wallet(key)
        
        # Check if auto-financing is needed (with reentrancy guard)
        if self.auto_finance_enabled and key != self.mother_wallet_key:
            if key not in self._auto_finance_checking:
                self._auto_finance_checking.add(key)
                try:
                    self._check_and_finance(key)
                finally:
                    self._auto_finance_checking.discard(key)
        
        return self.wallets[key]

    def get_balance(self, asset: str) -> Dict[str, float]:
        """
        Aggregates balance for an asset across ALL sub-wallets (Binance + Alpaca + others).
        """
        total_free = 0.0
        total_locked = 0.0
        
        for w in self.wallets.values():
            bal = w.get_balance(asset)
            total_free += bal.get("free", 0.0)
            total_locked += bal.get("locked", 0.0)
            
        return {"free": total_free, "locked": total_locked}
    
    
    def get_snapshot(self) -> Dict:
        """Returns a snapshot of ALL sub-wallets."""
        # Fetch latest prices for accurate equity calculation
        prices = {}
        try:
            from services.data_manager import get_data_manager
            dm = get_data_manager()
            # Get latest price for all known symbols
            # We iterate wallets to find what assets we hold, then look them up
            all_assets = set()
            for w in self.wallets.values():
                all_assets.update(w.balances.keys())
            
            for asset in all_assets:
                if asset not in ["USDT", "USDC", "USD", "EUR", "BUSD", "DAI"]:
                    # Try catch all symbols that might contain this asset
                    # This is imperfect but good enough for estimation
                    # In reality, we should know the symbol (e.g. BTCUSDT) for the asset (BTC)
                    # For now, we rely on DataManager's cache
                    price = dm.get_latest_price(f"{asset}USDT") or dm.get_latest_price(f"{asset}USD")
                    if price is not None and price > 0:
                        prices[asset] = price
        except Exception as e:
            logger.warning(f"Failed to fetch prices for equity calc: {e}")

        return {
            "primary": self.primary_key,
            "wallets": {k: w.get_snapshot() for k, w in self.wallets.items()},
            "global_equity": sum(w.total_usd_value(prices) for w in self.wallets.values())
        }

    def allocate_budget(self, total_balance: float, settings) -> Dict[str, float]:
        """
        Allocate budget into reserve, whitelist pool, and auto-discovery pool.
        
        Example with 100 EUR:
        - Reserve (50%): 50 EUR
        - Trading Pool (50%): 50 EUR
          - Whitelist (50% of trading = 25 EUR)
          - Auto-Discovery (50% of trading = 25 EUR)
        
        Returns dict with allocated amounts.
        """
        reserve_pct = getattr(settings, 'RESERVE_PERCENTAGE', 0.5)
        auto_pct = getattr(settings, 'AUTO_DISCOVERY_BUDGET_PCT', 0.5)
        
        reserve = total_balance * reserve_pct
        trading_pool = total_balance - reserve
        
        whitelist_pool = trading_pool * (1 - auto_pct)
        auto_pool = trading_pool * auto_pct
        
        return {
            "reserve": reserve,
            "whitelist": whitelist_pool,
            "auto_discovery": auto_pool,
            "trading_pool": trading_pool
        }
    
    def get_trading_pool_balance(self, asset: str = "USDC") -> float:
        """
        Get available balance in the trading pool (total - reserve).
        This is the balance available for whitelist + auto-discovery trading.
        """
        try:
            from config import get_settings
            settings = get_settings()
            
            # Get total balance from primary wallet
            primary_wallet = self.wallets.get(self.primary_key)
            if not primary_wallet:
                return 0.0
            
            total = primary_wallet.get_balance(asset).get("free", 0.0)
            
            # Calculate trading pool (total - reserve)
            reserve_pct = getattr(settings, 'RESERVE_PERCENTAGE', 0.5)
            # Calculate trading pool (total - reserve)
            reserve_pct = getattr(settings, 'RESERVE_PERCENTAGE', 0.5)
            
            # LEVERAGE UPGRADE: Use Buying Power if available and safe
            # Alpaca returns explicit buying_power. Binance Futures uses balance * leverage.
            # We check if 'buying_power' key exists and is greater than free balance
            balance_info = primary_wallet.get_balance(asset)
            raw_balance = balance_info.get("free", 0.0)
            buying_power = balance_info.get("buying_power", raw_balance)
            
            # Use the larger of the two, but respect reserve
            # If using buying power, we still reserve a % of current equity (raw balance)
            # reserve_amount = raw_balance * reserve_pct
            # usable_buying_power = buying_power - reserve_amount
            # Simplified: Apply reserve factor to the relevant metric
            
            # If we have explicit buying power > raw balance, assume it's leveraged
            if buying_power > raw_balance * 1.1:
                 # Leveraged Trading Pool
                 start_capital = buying_power
            else:
                 # Cash Trading Pool
                 start_capital = raw_balance

            trading_pool = start_capital * (1 - reserve_pct)
            
            return trading_pool
        except Exception:
            return 0.0
    
    def get_auto_discovery_balance(self, asset: str = "USDC") -> float:
        """
        Get available balance in the auto-discovery pool.
        This is the budget allocated for automatic symbol discovery and trading.
        """
        try:
            from config import get_settings
            settings = get_settings()
            
            trading_pool = self.get_trading_pool_balance(asset)
            auto_pct = getattr(settings, 'AUTO_DISCOVERY_BUDGET_PCT', 0.5)
            
            return trading_pool * auto_pct
        except Exception:
            return 0.0
    
    def get_whitelist_balance(self, asset: str = "USDC") -> float:
        """
        Get available balance in the whitelist trading pool.
        This is the budget for normal trading on configured symbols.
        """
        try:
            from config import get_settings
            settings = get_settings()
            
            trading_pool = self.get_trading_pool_balance(asset)
            auto_pct = getattr(settings, 'AUTO_DISCOVERY_BUDGET_PCT', 0.5)
            
            return trading_pool * (1 - auto_pct)
        except Exception:
            return 0.0

    def get_available_balance(self, wallet_key: str, asset: str) -> float:
        """
        Read-only accessor for a wallet's available (free) balance without triggering
        any auto-finance behavior. This intentionally avoids calling get_sub_wallet()
        which can perform auto-finance and cause re-entrancy issues.
        """
        w = self.wallets.get(wallet_key)
        if not w:
            return 0.0
        bal = w.get_balance(asset)
        return float(bal.get("free", 0.0))

    def transfer(self, from_id: str, to_id: str, asset: str, amount: float) -> bool:
        """
        Virtually moves funds between sub-wallets.

        NOTE: Use direct wallet dict access here to avoid triggering get_sub_wallet()
        which performs auto-finance checks that in turn call transfer(), creating recursion.
        """
        # Validation
        if amount <= 0:
            logger.warning(f"[OmniWallet] Transfer Failed: Invalid amount {amount}")
            return False

        # Directly access wallets dict to avoid re-entrancy into auto-finance logic.
        source = self.wallets.get(from_id)
        if source is None:
            # If the source wallet doesn't exist, create it without triggering auto-finance.
            source = Wallet(from_id)
            self.wallets[from_id] = source

        # Ensure asset exists in source balances
        src_free = source.get_balance(asset).get("free", 0.0)
        if src_free < amount:
            logger.warning(f"[OmniWallet] Transfer Failed: Insufficient funds in {from_id} (have {src_free}, need {amount})")
            return False

        # Execute transfer to destination (also avoid triggering auto-finance)
        dest = self.wallets.get(to_id)
        if dest is None:
            dest = Wallet(to_id)
            self.wallets[to_id] = dest

        # Deduct and credit
        source.balances.setdefault(asset, {"free": 0.0, "locked": 0.0})
        dest.balances.setdefault(asset, {"free": 0.0, "locked": 0.0})

        source.balances[asset]['free'] -= amount
        dest.deposit(asset, amount)

        # Log
        source._log("TRANSFER_OUT", asset, amount)
        dest._log("TRANSFER_IN", asset, amount)

        from config import get_settings
        self.save_state(os.path.join(get_settings().DATA_DIR, "wallet_state.json"))
        return True

    def _check_and_finance(self, wallet_key: str):
        """
        Mother Wallet Auto-Financing System.
        Automatically transfers funds from mother vault when sub-wallet runs low.
        """
        # Safety check: ensure wallet exists (should be created by get_sub_wallet, but be defensive)
        if wallet_key not in self.wallets:
            return False
        
        # Reset daily limit if needed
        current_time = time.time()
        if current_time - self.last_finance_reset > 86400:  # 24 hours
            self.daily_finance_used = 0.0
            self.last_finance_reset = current_time

        # Check if we've hit daily limit
        if self.daily_finance_used >= self.max_auto_finance_per_day:
            logger.info(f"[MOTHER WALLET] Daily auto-finance limit reached for {wallet_key}.")
            return False

        wallet = self.wallets[wallet_key]
        mother = self.wallets[self.mother_wallet_key]
        
        # Check if wallet needs financing
        current_balance = wallet.get_balance(wallet.base_currency)['free']
        
        if current_balance < self.min_balance_threshold:
            # Check if mother vault has sufficient funds
            mother_balance = mother.get_balance(mother.base_currency)['free']
            
            if mother_balance >= self.auto_finance_amount:
                # Execute auto-financing
                success = self.transfer(
                    self.mother_wallet_key, 
                    wallet_key, 
                    mother.base_currency, 
                    self.auto_finance_amount
                )
                
                if success:
                    self.daily_finance_used += self.auto_finance_amount
                    logger.info(f"[MOTHER WALLET] 🏦 Auto-financed {wallet_key} with {self.auto_finance_amount} {mother.base_currency}")
                    logger.info(f"[MOTHER WALLET] Daily usage: {self.daily_finance_used}/{self.max_auto_finance_per_day}")
                    return True
            else:
                logger.warning(f"[MOTHER WALLET] Insufficient funds in mother vault for auto-financing {wallet_key}")
        
        return False

    def configure_auto_finance(self, enabled: bool = True, min_threshold: float = 100.0, 
                             finance_amount: float = 500.0, daily_limit: float = 2000.0):
        """
        Configure the auto-financing system parameters.
        """
        self.auto_finance_enabled = enabled
        self.min_balance_threshold = min_threshold
        self.auto_finance_amount = finance_amount
        self.max_auto_finance_per_day = daily_limit
        
        logger.info(f"[MOTHER WALLET] Auto-finance configured: enabled={enabled}, threshold={min_threshold}, amount={finance_amount}, daily_limit={daily_limit}")
        from config import get_settings
        self.save_state(os.path.join(get_settings().DATA_DIR, "wallet_state.json"))

    def get_mother_wallet_status(self) -> Dict[str, Any]:
        """
        Returns status of the mother wallet and auto-financing system.
        """
        mother = self.wallets[self.mother_wallet_key]
        return {
            "enabled": self.auto_finance_enabled,
            "mother_balance": mother.get_balance(mother.base_currency)['free'],
            "min_threshold": self.min_balance_threshold,
            "finance_amount": self.auto_finance_amount,
            "daily_limit": self.max_auto_finance_per_day,
            "daily_used": self.daily_finance_used,
            "remaining_daily": self.max_auto_finance_per_day - self.daily_finance_used,
            "source": getattr(mother, "source", "unknown")
        }

    def clear_mother_wallet(self) -> bool:
        """
        Zero-out the mother vault free & locked balances and persist state.
        Returns True on success, False otherwise.
        """
        try:
            mother = self.wallets.get(self.mother_wallet_key)
            if mother is None:
                logger.warning(f"[OmniWallet] No mother wallet found at key {self.mother_wallet_key}")
                return False
            mother.balances = {mother.base_currency: {"free": 0.0, "locked": 0.0}}
            mother.vault = {mother.base_currency: 0.0}
            # preserve provenance that we explicitly cleared it
            mother.source = "cleared_by_admin"
            from config import get_settings
            self.save_state(os.path.join(get_settings().DATA_DIR, "wallet_state.json"))
            logger.info("[OmniWallet] Mother wallet cleared and state saved.")
            return True
        except Exception as e:
            logger.error(f"[OmniWallet] Failed to clear mother wallet: {e}")
            return False

    def inject_telemetry(self, snapshot: Dict[str, Dict[str, Dict[str, float]]]):
        """
        Updates sub-wallets with real data from OmniRouter.

        Important: Do not call get_sub_wallet() here because that can trigger the
        auto-finance system while we're simply injecting telemetry. Updating wallets
        must be non-invasive and not change financing state.
        snapshot: { 'binance_spot': {'USDT': {'free': 100, 'locked': 0}}, ... }
        """
        for wallet_key, assets in snapshot.items():
            # Update or create wallet object directly to avoid triggering auto-finance.
            if wallet_key not in self.wallets:
                self.wallets[wallet_key] = Wallet(wallet_key)
            w = self.wallets[wallet_key]
            # Update balances (overwrite with latest telemetry)
            for asset, details in assets.items():
                w.balances[asset] = details

    # --- PROXY METHODS (Backward Compatibility) ---
    def __getattr__(self, name):
        """Delegate unknown attributes to the primary wallet."""
        return getattr(self.wallets[self.primary_key], name)

    # Explicit proxy for dunder methods or properties if needed, 
    # but __getattr__ handles methods and properties usually.
    # WARN: If Wallet has serialization logic, we need to handle that at Omni level.

    def increase_risk(self, step: int = 5) -> int:
        """Increase risk tolerance (max 100). Default step is 5%."""
        self.risk_level = min(100, self.risk_level + step)
        from config import get_settings
        self.save_state(os.path.join(get_settings().DATA_DIR, "wallet_state.json"))
        logger.info(f"[OmniWallet] Risk increased to {self.risk_level}%")
        return self.risk_level
    
    def decrease_risk(self, step: int = 5) -> int:
        """Decrease risk tolerance (min 0). Default step is 5%."""
        self.risk_level = max(0, self.risk_level - step)
        from config import get_settings
        self.save_state(os.path.join(get_settings().DATA_DIR, "wallet_state.json"))
        logger.info(f"[OmniWallet] Risk decreased to {self.risk_level}%")
        return self.risk_level
    
    def get_risk_params(self) -> dict:
        """
        Returns trading parameters based on current risk level (0-100).
        
        INVERTED SCALE (user preference):
        - 0 (LEFT) = SCALP MODE: Maximum trades, fast, aggressive
        - 100 (RIGHT) = WEALTH MODE: Minimum trades, only big moves, hold stable assets
        
        Uses logarithmic scaling for trade frequency to prevent extreme losses
        at the aggressive end while allowing meaningful wealth preservation at the other.
        """
        import math
        
        r = self.risk_level / 100.0  # Normalize to 0-1
        
        # INVERTED: Higher r = more patient/fewer trades
        # Logarithmic scaling for smooth transition at extremes
        
        # Threshold: 0.35 (aggressive) -> 0.95 (wealth mode)
        threshold = 0.35 + (r * 0.60)
        
        # Persistence: 1 (aggressive) -> 6 (wealth mode) 
        persistence = max(1, int(1 + (r * 5)))
        
        # Hold time: 15s (scalping) -> 3600s (hourly, wealth mode)
        # Use exponential curve so it ramps up smoothly
        hold_time = int(15 * math.exp(r * 5.5))  # 15s -> ~3600s
        hold_time = min(hold_time, 3600)  # Cap at 1 hour
        
        # Estimated trades per hour (logarithmic to cap extreme end)
        # At r=0: ~30/hr (scalping), at r=1: ~0.3/hr (few per day)
        if r < 0.1:
            est_trades_per_hour = 30 - (r * 100)  # 30 -> 20
        else:
            est_trades_per_hour = max(0.2, 20 * math.exp(-r * 4))
        est_trades_per_hour = round(est_trades_per_hour, 1)
        
        # Description based on position (calibration-focused naming)
        if r < 0.15:
            desc = "RAPID"
            icon = "▸▸"  # Fast arrows
        elif r < 0.35:
            desc = "SWIFT"
            icon = "▸"
        elif r < 0.65:
            desc = "TUNED"
            icon = "◆"  # Diamond = calibrated
        elif r < 0.85:
            desc = "STEADY"
            icon = "▪"  # Square = stable
        else:
            desc = "ANCHOR"
            icon = "◈"  # Diamond frame = locked in
        
        return {
            "threshold": round(threshold, 2),
            "persistence": persistence,
            "hold_time": hold_time,
            "description": desc,
            "icon": icon,
            "est_trades_per_hour": est_trades_per_hour,
            "slider_pos": self.risk_level  # For UI display
        }

    def save_state(self, filepath: str):
        """Saves ALL wallets to a single JSON file."""
        state = {
            "primary_key": self.primary_key,
            "mother_wallet_key": self.mother_wallet_key,
            "risk_level": self.risk_level,
            "auto_finance_config": {
                "enabled": self.auto_finance_enabled,
                "min_threshold": self.min_balance_threshold,
                "finance_amount": self.auto_finance_amount,
                "daily_limit": self.max_auto_finance_per_day,
                "daily_used": self.daily_finance_used,
                "last_reset": self.last_finance_reset
            },
            "wallets": {k: w.to_dict() for k, w in self.wallets.items()}
        }
        try:
            with atomic_write(filepath) as f:
                json.dump(state, f, indent=4)
        except Exception as e:
            logger.error(f"[OmniWallet] Failsafe Error: Could not save state: {e}")

    def load_state(self, filepath: str):
        if not os.path.exists(filepath):
            return False
        try:
            with open(filepath, 'r') as f:
                state = json.load(f)
            
            # Handle Legacy (Single Wallet) File Format
            if "wallets" not in state:
                # This is a legacy file. Load it into primary.
                logger.info("[OmniWallet] Legacy wallet file detected. Migrating...")
                self.wallets[self.primary_key].from_dict(state)
                # Save immediately to upgrade
                self.save_state(filepath)
                return True

            # Modern Format
            # Determine correct primary key based on TRADING_MODE (must match router expectations)
            try:
                from config import get_settings
                settings = get_settings()
                if settings.TRADING_MODE.upper() == "FUTURES":
                    desired_primary = "binance_future"
                else:
                    desired_primary = "binance_spot"
            except Exception:
                desired_primary = "binance_spot"
            
            # Load saved primary key, but migrate if it's an old name
            saved_primary = state.get("primary_key", "binance_paper")
            
            # Migration map: old names -> new names
            migration_map = {
                "binance_paper": "binance_spot",  # Old testnet name -> spot
                "binance": "binance_spot",  # Old live name -> spot
            }
            
            # If saved primary is an old name, migrate it
            if saved_primary in migration_map:
                migrated_name = migration_map[saved_primary]
                # If we're in futures mode, use futures instead
                if desired_primary == "binance_future":
                    migrated_name = "binance_future"
                saved_primary = migrated_name
                logger.info(f"[OmniWallet] Migrating primary key from old name to {saved_primary}")
            
            # Use desired_primary if it matches trading mode, otherwise use saved (after migration)
            if saved_primary in ("binance_spot", "binance_future", "hyperliquid"):
                self.primary_key = saved_primary if saved_primary == desired_primary else desired_primary
            else:
                self.primary_key = desired_primary
            
            # Special DEFI override
            try:
                from config import get_settings
                if get_settings().TRADING_MODE.upper() == "DEFI":
                    self.primary_key = "hyperliquid"
            except:
                pass
            
            self.mother_wallet_key = state.get("mother_wallet_key", "mother_vault")
            
            # Load auto-finance configuration
            auto_config = state.get("auto_finance_config", {})
            self.auto_finance_enabled = auto_config.get("enabled", True)
            self.min_balance_threshold = auto_config.get("min_threshold", 100.0)
            self.auto_finance_amount = auto_config.get("finance_amount", 500.0)
            self.max_auto_finance_per_day = auto_config.get("daily_limit", 2000.0)
            self.daily_finance_used = auto_config.get("daily_used", 0.0)
            self.last_finance_reset = auto_config.get("last_reset", time.time())
            
            # Load risk level (default to 3 = Moderate)
            self.risk_level = state.get("risk_level", 3)
            
            wallet_data = state.get("wallets", {})
            
            # Migrate old wallet names to new names when loading
            migrated_wallets = {}
            for key, data in wallet_data.items():
                # Migrate old wallet names
                if key in migration_map:
                    new_key = migration_map[key]
                    # If we're in futures mode and migrating from paper/binance, use futures
                    if self.primary_key == "binance_future" and new_key == "binance_spot":
                        new_key = "binance_future"
                    if new_key != key:
                        logger.info(f"[OmniWallet] Migrating wallet '{key}' -> '{new_key}'")
                    migrated_wallets[new_key] = data
                else:
                    migrated_wallets[key] = data
            
            for key, data in migrated_wallets.items():
                w = Wallet(key)
                w.from_dict(data)
                # provenance: mark wallets loaded from persisted state
                w.source = "loaded"
                self.wallets[key] = w
            
            # Ensure primary and mother vault exist
            if self.primary_key not in self.wallets:
                 self.wallets[self.primary_key] = Wallet(self.primary_key)
            
            if self.mother_wallet_key not in self.wallets:
                self.wallets[self.mother_wallet_key] = Wallet(self.mother_wallet_key, initial_balance=50000.0, base_currency="USDC")
            
            # --- SYNC WITH DB (New Source of Truth for Users) ---
            try:
                from services.database import get_database
                db = get_database()
                # Check known user wallets in this instance
                for key, w in self.wallets.items():
                    if key.startswith("user_"):
                        try:
                            uid = int(key.replace("user_", ""))
                            db_state = db.get_wallet_state(uid)
                            if db_state:
                                # DB overwrites JSON for balances (it's more atomic)
                                w.balances = db_state.get('balances', w.balances)
                                w.vault = db_state.get('vault', w.vault)
                        except ValueError:
                            pass # Not a user wallet
            except Exception as e:
                logger.warning(f"[OmniWallet] DB Sync Failed: {e}")

            return True
        except Exception as e:
            logger.error(f"[OmniWallet] Failed to load state: {e}")
            return False

    def _reconcile_from_exchange(self, force: bool = False):
        """
        PHOENIX PROTOCOL:
        Reconciles balances from Binance based on active TRADING_MODE (Spot/Futures).
        Ensures internal wallet state matches exchange reality.
        """
        try:
            now = time.time()
            if not force and (now - getattr(self, "last_reconcile", 0.0) < getattr(self, "RECONCILE_INTERVAL", 300)):
                return False
        except Exception:
            pass

        try:
            from binance.client import Client
            from config import get_settings
            settings = get_settings()

            is_testnet = getattr(settings, "BINANCE_TESTNET", True)
            trading_mode = getattr(settings, "TRADING_MODE", "SPOT").upper()

            # 1. Streamlined API Key Selection
            if is_testnet:
                api_key = getattr(settings, "BINANCE_TESTNET_API_KEY", None) or getattr(settings, "BINANCE_API_KEY", None)
                api_secret = getattr(settings, "BINANCE_TESTNET_SECRET_KEY", None) or getattr(settings, "BINANCE_SECRET_KEY", None)
            else:
                api_key = getattr(settings, "BINANCE_API_KEY", None)
                api_secret = getattr(settings, "BINANCE_SECRET_KEY", None)

            if not api_key or not api_secret:
                # [ALLEY-OOP] If Binance Keys missing, check for ALPACA keys
                alpaca_key = getattr(settings, "ALPACA_API_KEY", None)
                alpaca_secret = getattr(settings, "ALPACA_SECRET_KEY", None)
                
                if alpaca_key and alpaca_secret:
                    logger.info("[OmniWallet] PHOENIX: Binance Keys missing. Switching to ALPACA Reconciliation.")
                    return self._reconcile_alpaca(alpaca_key, alpaca_secret, settings)
                
                logger.warning(f"[OmniWallet] PHOENIX SKIPPED: No API keys in .env (Mode: {'TESTNET' if is_testnet else 'LIVE'})")
                return False

            # Extract raw strings from SecretStr if necessary and STRIP whitespace
            raw_key = (api_key.get_secret_value() if hasattr(api_key, "get_secret_value") else str(api_key)).strip()
            raw_secret = (api_secret.get_secret_value() if hasattr(api_secret, "get_secret_value") else str(api_secret)).strip()

            logger.info(f"[OmniWallet] PHOENIX INITIATED: Reconciling {trading_mode} ({'TESTNET' if is_testnet else 'LIVE'})")

            # 2. Advanced Client Setup with PROXY FAILSAFE
            requests_params = {}
            use_proxy = False
            if settings.EGRESS_PROXY_URL:
                logger.debug(f"[OmniWallet] PHOENIX Proxy: {settings.EGRESS_PROXY_URL}")
                requests_params['proxies'] = {
                    'http': settings.EGRESS_PROXY_URL,
                    'https': settings.EGRESS_PROXY_URL
                }
                requests_params['timeout'] = 10
                use_proxy = True

            try:
                client = Client(raw_key, raw_secret, testnet=is_testnet, requests_params=requests_params)
                
                # [FAILSAFE] Verify Proxy Connectivity if enabled
                if use_proxy:
                     # Probe Network (Public Endpoint) to verify Proxy is alive
                     client.ping()
                     
            except Exception as e:
                err = str(e).lower()
                is_proxy_issue = "timeout" in err or "proxy" in err or "connection" in err or "adapter" in err
                
                if use_proxy and is_proxy_issue:
                    logger.warning(f"[OmniWallet] ⚠️ PROXY INITIALIZATION FAILED: {e}")
                    logger.warning("[OmniWallet] 🔄 PROXY BYPASS ACTIVATED (Direct Connection Attempt)")
                    # Re-init Client without proxy
                    client = Client(raw_key, raw_secret, testnet=is_testnet, requests_params={'timeout': 30})
                else:
                    raise e # Not a proxy issue, or no proxy used - re-raise
            
            # Futures requires different base URLs even in PHOENIX
            if trading_mode == "FUTURES":
                if is_testnet:
                    client.FUTURES_URL = "https://testnet.binancefuture.com/fapi/v1"
                else:
                    client.FUTURES_URL = "https://fapi.binance.com/fapi/v1"

            # 3. Mode-Specific Reconciliation
            balances = []
            if trading_mode == "FUTURES":
                # Reconcile USD-M Futures
                acc_info = client.futures_account()
                raw_bal = acc_info.get('assets', [])
                for b in raw_bal:
                    asset = b.get('asset')
                    free = float(b.get('walletBalance', 0)) # Using wallet balance for futures
                    locked = float(b.get('maintMargin', 0)) # Using maintenance margin as 'locked' logic
                    if free > 0 or locked > 0:
                        balances.append({'asset': asset, 'free': free, 'locked': locked})
            else:
                # Reconcile Spot
                acc_info = client.get_account()
                balances = acc_info.get('balances', [])

            # 4. Inject Into Sub-Wallets
            # Use the correct primary key based on trading mode (binance_spot or binance_future)
            # This prevents duplicate wallet entries
            if self.primary_key in ("binance_spot", "binance_future"):
                target_key = self.primary_key
            elif trading_mode == "FUTURES":
                target_key = "binance_future"
            else:
                target_key = "binance_spot"
                
            if target_key not in self.wallets:
                self.wallets[target_key] = Wallet(target_key)
                
            target_wallet = self.wallets[target_key]
            target_wallet.source = "reconciled"
            target_wallet.balances = {}
            found = 0
            
            for b in balances:
                asset = b.get('asset')
                free = float(b.get('free', 0)) if 'free' in b else float(b.get('walletBalance', 0))
                locked = float(b.get('locked', 0)) if 'locked' in b else float(b.get('maintMargin', 0))
                
                if free > 0 or locked > 0:
                    target_wallet.balances[asset] = {"free": free, "locked": locked}
                    found += 1

            # Update initial capital estimate ONLY if Binance is Primary
            if self.primary_key in ("binance_spot", "binance_future"):
                for stable in ("USDT", "USDC", target_wallet.base_currency):
                    bal = target_wallet.balances.get(stable, {})
                    if bal.get("free", 0) > 0:
                        target_wallet.initial_capital = bal["free"] + bal.get("locked", 0)
                        target_wallet.base_currency = stable
                        break

            logger.info(f"[OmniWallet] PHOENIX SUCCESS: {found} assets reconciled into {target_key}.")
            self.connected = True
            from config import get_settings
            self.save_state(os.path.join(get_settings().DATA_DIR, "wallet_state.json"))
            self.last_reconcile = time.time()
            self.connected = True
            self.last_error = None
            return True

        except Exception as e:
            err_msg = str(e)
            if "-2015" in err_msg:
                self.last_error = {"binance": "Invalid API Key or IP Restriction"}
                logger.error(f"[OmniWallet] PHOENIX FAILURE: API Key Invalid for {trading_mode} mode.")
                logger.error("Suggestion: Ensure your API key has " + ("FUTURES" if trading_mode == "FUTURES" else "SPOT") + " permissions enabled.")
            else:
                self.last_error = {"binance": err_msg}
                logger.error(f"[OmniWallet] PHOENIX FAILURE: {err_msg}")
            self.connected = False
            return False

    def _reconcile_alpaca(self, api_key, secret_key, settings):
        """
        Specialized reconciliation for Alpaca to capture Buying Power.
        """
        try:
            import requests
            is_paper = getattr(settings, "ALPACA_PAPER", True)
            base_url = "https://paper-api.alpaca.markets" if is_paper else "https://api.alpaca.markets"
            endpoint = f"{base_url}/v2/account"
            
            headers = {
                "APCA-API-KEY-ID": api_key,
                "APCA-API-SECRET-KEY": secret_key
            }
            
            resp = requests.get(endpoint, headers=headers, timeout=10)
            if resp.status_code != 200:
                logger.error(f"[OmniWallet] Alpaca Reconcile Failed: {resp.text}")
                return False
                
            data = resp.json()
            
            # Extract Metrics
            # buying_power: Total purchasing power (inc. margin)
            # equity: Total cash + position value
            # cash: Free cash
            
            buying_power = float(data.get('buying_power', 0.0))
            equity = float(data.get('equity', 0.0))
            cash = float(data.get('cash', 0.0))
            
            target_wallet = self.wallets[self.primary_key]
            
            # Reset balances
            target_wallet.balances = {}
            
            # Store USD (Alpaca Base)
            # We treat 'cash' as free balance, but inject buying_power metadata
            target_wallet.balances["USD"] = {
                "free": cash, 
                "locked": equity - cash, # Approximate locked logic
                "buying_power": buying_power
            }
            # For compatibility with crypto-logic downstream that looks for USDC/USDT
            target_wallet.balances["USDC"] = target_wallet.balances["USD"]
            
            logger.info(f"[OmniWallet] ALPACA SYNC: Cash=${cash:.2f} | Equity=${equity:.2f} | Buying Power=${buying_power:.2f}")
            
            target_wallet.initial_capital = equity
            target_wallet.base_currency = "USD"
            
            self.last_reconcile = time.time()
            self.connected = True
            
            # Save State
            from config import get_settings
            self.save_state(os.path.join(get_settings().DATA_DIR, "wallet_state.json"))
            
            return True
            
        except Exception as e:
            logger.error(f"[OmniWallet] Alpaca Reconciliation Exception: {e}")
            return False

    async def _reconcile_alpaca(self):
        """
        Reconciles balances/positions from Alpaca (Stocks).
        Using Async CCXT logic directly.
        """
        try:
            from config import get_settings
            settings = get_settings()
            
            # Check if enabled
            if not getattr(settings, 'ALPACA_ENABLED', False):
                return

            api_key = getattr(settings, 'ALPACA_API_KEY', None)
            secret_key = getattr(settings, 'ALPACA_SECRET_KEY', None)
            
            if not api_key or not secret_key:
                return

            logger.info("[OmniWallet] Starting Alpaca Sync...")
            
            # Instantiate Broker Temporarily (lightweight)
            from brokers.alpaca import AlpacaBroker
            # In settings they might be SecretStr
            a_key = api_key.get_secret_value() if hasattr(api_key, 'get_secret_value') else str(api_key)
            s_key = secret_key.get_secret_value() if hasattr(secret_key, 'get_secret_value') else str(secret_key)
            
            # Determine if using paper trading for Alpaca
            is_alpaca_paper = getattr(settings, "ALPACA_PAPER", True)
            
            broker = AlpacaBroker(a_key, s_key, paper=is_alpaca_paper) # Pass paper flag
            
            try:
                import asyncio
                # Get Positions (with Timeout)
                try:
                    positions = await asyncio.wait_for(broker.get_all_positions(), timeout=10.0)
                except asyncio.TimeoutError:
                    logger.warning("[OmniWallet] Alpaca positions fetch timed out")
                    positions = []
                
                # Update 'alpaca' wallet
                wallet_key = "alpaca"
                if wallet_key not in self.wallets:
                    self.wallets[wallet_key] = Wallet(wallet_key)
                    self.wallets[wallet_key].source = "reconciled"
                
                target = self.wallets[wallet_key]
                # Reset balances (we rebuild from positions)
                target.balances = {} 
                
                # Alpaca also has 'Cash'. We should fetch balance.
                try:
                    usd_cash = await asyncio.wait_for(broker.get_balance('USD'), timeout=5.0)
                except asyncio.TimeoutError:
                    logger.warning("[OmniWallet] Alpaca cash balance fetch timed out - Preserving previous state if available")
                    # Try to preserve existing cash if we have it
                    if 'USD' in target.balances:
                        usd_cash = target.balances['USD']['free']
                    else:
                        usd_cash = 0.0

                if usd_cash > 0:
                    target.balances['USD'] = {'free': usd_cash, 'locked': 0.0}
                    target.base_currency = 'USD'
                    
                target.connected = True
                
                # Inject Positions as Assets
                count = 0
                for p in positions:
                    symbol = p['symbol']
                    qty = p['qty']
                    # We store stock positions as "free" balance in wallet for simple tracking
                    # The Tracker will pick this up as a "Position" because it has value > $1
                    target.balances[symbol] = {'free': qty, 'locked': 0.0}
                    count += 1
                
                logger.info(f"[OmniWallet] Alpaca Sync Complete: {count} assets, ${usd_cash:.2f} cash.")
            
            finally:
                await broker.close()

        except Exception as e:
            logger.warning(f"[OmniWallet] Alpaca Sync Warning: {e}")

    async def _reconcile_hyperliquid(self):
        """
        Reconciles balances/positions from Hyperliquid (DeFi).
        """
        try:
            from config import get_settings
            settings = get_settings()
            
            # Check if relevant
            # We reconcile if TRADING_MODE is DEFI or if we have keys (just in case)
            if settings.TRADING_MODE.upper() != "DEFI":
                # Only strictly required in DEFI mode, but let's check keys
                pass

            pk = getattr(settings, 'HYPERLIQUID_PRIVATE_KEY', None)
            if not pk:
                logger.warning("[OmniWallet] Skipping Hyperliquid Sync: 'HYPERLIQUID_PRIVATE_KEY' not found in settings.")
                return

            # Instantiate Broker Temporarily
            from brokers.hyperliquid import HyperliquidBroker
            
            # Key might be string or SecretStr
            _key = pk.get_secret_value() if hasattr(pk, 'get_secret_value') else str(pk)
            
            # Skip if dummy value
            if not _key or "placeholder" in _key:
                logger.warning("[OmniWallet] Skipping Hyperliquid Sync: Private Key appears to be a placeholder.")
                return

            broker = HyperliquidBroker(_key)
            
            try:
                if hasattr(broker, 'address'):
                    self.last_debug['hyperliquid_address'] = broker.address

                # 1. Get Balance (USDC)
                usdc_bal = await broker.get_balance("USDC")
                
                # 2. Get Positions
                positions = await broker.get_all_positions()
                
                # Update 'hyperliquid' wallet
                wallet_key = "hyperliquid"
                if wallet_key not in self.wallets:
                    self.wallets[wallet_key] = Wallet(wallet_key)
                    self.wallets[wallet_key].source = "reconciled"
                
                target = self.wallets[wallet_key]
                target.balances = {}
                target.base_currency = "USDC"
                
                # Store USDC (Cash + Margin)
                # Hyperliquid accountValue includes unrealized pnl, but get_balance returns 'withdrawable' usually?
                # Actually my HyperliquidBroker.get_balance returns accountValue (Equity).
                # Let's trust it as 'free' for now, or split if possible. 
                # Broker implementation: return float(summary['accountValue'])
                # So this is EQUITY.
                
                target.balances["USDC"] = {
                    "free": usdc_bal, 
                    "locked": 0.0,
                    "buying_power": usdc_bal * 50.0 # 50x assumption or fetch max leverage
                }

                # Inject Positions
                count = 0
                for p in positions:
                    # Broker adapter returns: {"symbol": "BTC", "qty": 0.1, "entryPrice": ..., "info": ...}
                    # Handle both old format (coin/szi) and new format (symbol/qty)
                    coin = p.get('symbol') or p.get('coin', 'UNKNOWN')
                    size = float(p.get('qty', p.get('szi', 0.0)))
                    if size == 0: continue
                    
                    symbol = coin
                    target.balances[symbol] = {'free': abs(size), 'locked': 0.0}
                    count += 1
                
                logger.info(f"[OmniWallet] HYPERLIQUID SYNC: Equity=${usdc_bal:.2f} | {count} Positions")
                
                # Detailed Debug Log for "Blindness" investigation
                if count > 0:
                    assets_str = ", ".join([f"{k}: {v['free']}" for k, v in target.balances.items() if k != "USDC"])
                    logger.info(f"[OmniWallet] HL ASSETS FOUND: {assets_str}")
                if usdc_bal > 0 or count > 0:
                    self.connected = True
                    from config import get_settings
                    self.save_state(os.path.join(get_settings().DATA_DIR, "wallet_state.json"))
                    
            finally:
                # No close method on HyperliquidBroker currently needed? 
                # It uses aiohttp session? My adapter creates `eth_account`. 
                # SDK manages session? 
                # My adapter `__init__` does `self.info = Info(...)` and `self.exchange = Exchange(...)`.
                # They don't typically need explicit close, but good practice if available.
                pass

        except Exception as e:
            logger.warning(f"[OmniWallet] Hyperliquid Sync Warning: {e}")
            self.last_error['hyperliquid'] = str(e)

    async def update(self, force: bool = False):
        """
        Async wrapper for synchronous reconciliation.
        Runs network calls in a thread to avoid blocking the event loop.
        """
        import asyncio
        loop = asyncio.get_running_loop()
        try:
             # 1. Binance (Sync via Thread)
             # Don't block if binance keys missing
             await loop.run_in_executor(None, self._reconcile_from_exchange, force)
             
             # 2. Alpaca (Async)
             await self._reconcile_alpaca()

             # 3. Hyperliquid (Async)
             await self._reconcile_hyperliquid()
             
        except Exception as e:
             logger.error(f"[OmniWallet] Update failed: {e}")

    async def get_all_positions(self) -> Dict[str, Dict[str, Any]]:
        """
        Returns aggregate positions from performance tracker (or wallet data if tracker missing).
        Currently delegates to trading service's tracker if available.
        """
        from services.tracker import get_performance_tracker
        tracker = get_performance_tracker()
        if tracker:
            return getattr(tracker, "positions", {})
        return {}

_wallet_instance = None
_wallet_initializing = False

def get_wallet() -> OmniWallet:
    global _wallet_instance, _wallet_initializing
    # Re-entrancy guard: if another call to get_wallet is already initializing the singleton,
    # return a lightweight temporary wallet to avoid import/initialization recursion.
    if _wallet_instance is None:
        if _wallet_initializing:
            # Return a minimal, non-financing stub that provides get_sub_wallet without auto-finance.
            class _ReentrantOmniWalletStub:
                def __init__(self):
                    self.wallets = {}
                    self.connected = False
                async def update(self, force=False):
                    pass
                    self.primary_key = "binance_spot"
                    self.mother_wallet_key = "mother_vault"
                    self.auto_finance_enabled = False
                    self.risk_level = 50  # Default risk level

                def get_sub_wallet(self, key: str) -> Wallet:
                    if key not in self.wallets:
                        self.wallets[key] = Wallet(key)
                    return self.wallets[key]

                def get_snapshot(self):
                    return {
                        "primary": self.primary_key,
                        "wallets": {k: w.get_snapshot() for k, w in self.wallets.items()},
                        "global_equity": sum(w.total_usd_value({}) for w in self.wallets.values())
                    }
                
                def get_risk_params(self) -> dict:
                    """Default risk params for stub."""
                    return {
                        'hold_time': 30,
                        'persistence': 3,
                        'threshold': 0.5,
                        'icon': '||',
                        'description': 'Default (Stub)'
                    }

                def __getattr__(self, name):
                    raise AttributeError(name)

            return _ReentrantOmniWalletStub()

        _wallet_initializing = True
        try:
            _wallet_instance = OmniWallet()
            # Try load state immediately (local file, fast)
            from config import get_settings
            settings = get_settings()
            _wallet_instance.load_state(os.path.join(settings.DATA_DIR, "wallet_state.json"))
            # NOTE: Reconcile is intentionally deferred to avoid blocking startup.
            # The WebSocket manager or periodic job will trigger reconcile when ready.
            logger.info("[OmniWallet] Initialized. Reconcile will happen on first trade or background job.")
        finally:
            _wallet_initializing = False

    return _wallet_instance
