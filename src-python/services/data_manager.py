import asyncio
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd
import numpy as np
import pandas_ta as ta
from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, UniqueConstraint, select, inspect, Text
from sqlalchemy.orm import sessionmaker, declarative_base
from binance.client import Client
from binance.exceptions import BinanceAPIException
from config.settings import get_trading_symbols
from config import get_settings
from services.yahoo_connector import YahooConnector
from services.data.schema import Base, OHLCV, SymbolRegistry
from services.data.calibration import UniverseCalibrator
from core.logger import get_logger
from services.symbol_normalizer import get_symbol_normalizer

logger = get_logger("DataManager")
settings = get_settings()


import time
import random

# STEALTH: Common User-Agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
]


class DataManager:
    def __init__(self):
        # 1. LOCAL ENGINE (Always SQLite - for high bandwidth OHLCV/Ticks)
        db_abspath = os.path.abspath(settings.DB_PATH)
        self.local_db_url = f"sqlite:///{db_abspath}"
        self.local_engine = create_engine(self.local_db_url, connect_args={"check_same_thread": False})
        self.LocalSession = sessionmaker(autocommit=False, autoflush=False, bind=self.local_engine)
        logger.info(f"DataManager: Local Engine initialized (SQLite) for OHLCV @ {db_abspath}")

        # 2. CLOUD ENGINE (Postgres/Supabase - for User Settings, Trades, Registry)
        db_url = getattr(settings, 'DATABASE_URL', None) or os.getenv("DATABASE_URL")
        if db_url:
            self.cloud_db_url = db_url
            if self.cloud_db_url.startswith("postgres://"):
                self.cloud_db_url = self.cloud_db_url.replace("postgres://", "postgresql://", 1)
            self.cloud_engine = create_engine(self.cloud_db_url, pool_pre_ping=True, pool_size=10, max_overflow=20)
            logger.info("DataManager: Cloud Engine initialized (Supabase/Postgres) for Strategic State.")
        else:
            self.cloud_db_url = self.local_db_url
            self.cloud_engine = self.local_engine
            logger.warning("DataManager: ⚠️ No DATABASE_URL found. Strategic state will be LOCAL-ONLY.")

        self.CloudSession = sessionmaker(autocommit=False, autoflush=False, bind=self.cloud_engine)
        
        # Legacy compat for get_db() and other callers
        self.engine = self.cloud_engine
        self.SessionLocal = self.CloudSession
        
        # --- THREAD SAFETY ---
        # SQLite with check_same_thread=False REQUIRES application-level locking 
        # for concurrent writes to prevent "Database is locked" errors or corruption.
        import threading
        self.db_lock = threading.Lock()
        
        # CACHE: Track symbols that are NOT on Binance (TradFi) so we don't ask again
        self.TRADFI_CACHE = set() 
        
        # STATS CACHE: {symbol: {'data': stats, 'ts': timestamp}}
        self._stats_cache = {}
        self._cache_ttl = 30 # Seconds
        
        # SCHEMA: Ensure tables exist!
        try:
            # 1. Cloud Tables (Registries)
            cloud_tables = ['symbol_registry']
            Base.metadata.create_all(self.cloud_engine, tables=[Base.metadata.tables[t] for t in cloud_tables if t in Base.metadata.tables])
            
            # 2. Local Tables (OHLCV)
            local_tables = ['ohlcv']
            Base.metadata.create_all(self.local_engine, tables=[Base.metadata.tables[t] for t in local_tables if t in Base.metadata.tables])
            
            logger.info("DataManager: Hybrid Database Schema Verification Complete.")
        except Exception as e:
            logger.error(f"DataManager: Schema Creation Failed: {e}")
        
        # Initialize Binance Client
        # STEALTH: Pass custom requests_params if supported, else we handle jitter manually before calls
        # Initialize Binance Client
        # STEALTH: Pass custom requests_params including timeout and headers
        stealth_headers = {"User-Agent": random.choice(USER_AGENTS)}
        
        # PROXY FAILSAFE:
        requests_params = {"timeout": 15}
        use_proxy = False
            
        try:
            # Init Client (Attempts Ping by default)
            self.client = Client(requests_params=requests_params)
            
            # Additional Probe if client init didn't ping (defensive)
            if use_proxy:
                self.client.ping()
                
        except Exception as e:
            if use_proxy: # Only try bypass if we were using a proxy
                 err = str(e).lower()
                 if "timeout" in err or "proxy" in err or "connection" in err or "adapter" in err:
                     logger.warning(f"DataManager: ⚠️ PROXY INITIALIZATION FAILED: {e}")
                     logger.warning("DataManager: 🔄 ACTIVATING PROXY BYPASS (Direct Connection)")
                     # Fallback to direct
                     self.client = Client(requests_params={'timeout': 30})
                 else:
                     raise e # Re-raise if not a proxy issue
            else:
                 raise e # Re-raise if no proxy involved
        self.client.session.headers.update(stealth_headers)

        
        # Initialize Yahoo Connector (TradFi)
        self.yahoo = YahooConnector()
        self.sn = get_symbol_normalizer()
        
        # Run migrations BEFORE init_db
        self._ensure_columns_exist()
        
        self.init_db()
        
        # Time Synchronization
        self.time_offset = 0
        self.sync_time_with_server()

    def _ensure_columns_exist(self):
        """Ensures required columns exist in user_bot_settings table (Database Migration)."""
        pass

    def sync_time_with_server(self):
        """Calculate offset between Local System Time and Binance Server Time."""
        try:
            server_time_ms = self.client.get_server_time()['serverTime']
            local_time_ms = int(time.time() * 1000)
            self.time_offset = server_time_ms - local_time_ms
            
            # Log status
            server_dt = datetime.utcfromtimestamp(server_time_ms / 1000)
            local_dt = datetime.utcfromtimestamp(local_time_ms / 1000)
            logger.info(f"Time Sync | Local: {local_dt} | Server: {server_dt} | Offset: {self.time_offset}ms")
            
            if abs(self.time_offset) > 1000 * 60 * 60: # > 1 Hour drift
                logger.warning("[WARN] CRITICAL TIME DRIFT DETECTED. Adjusting requests to match Server Time.")
        except Exception as e:
            logger.error(f"Failed to sync time with Binance: {e}")

    def _fetch_yfinance_fallback(self, symbol: str, interval: str, limit: int = 100):
        """
        Fallback to Yahoo Finance for symbols not found on Binance (e.g. MSTR, COIN).
        Returns list of OHLCV dicts or empty list.
        """
        try:
            import yfinance as yf
            
            # Check In-Memory Cache first to avoid Rate Limits
            cache_key = f"{symbol}_{interval}"
            now = datetime.utcnow()
            
            if not hasattr(self, '_yfinance_cache'):
                self._yfinance_cache = {}
                
            cached = self._yfinance_cache.get(cache_key)
            if cached:
                # 15 minute cache for TradFi fallback
                if (now - cached['ts']).total_seconds() < 900: 
                    return cached['data']
            
            # Map Binance interval to YF interval
            # 1m, 1h, 1d -> 1m, 1h, 1d (mostly same)
            yf_interval = interval
            
            # Calculate start date based on limit roughly
            # This is an estimation; YF fetch is better by period
            period_map = {
                "1m": "5d", # Always use 5d to handle weekends/holidays for 1m candles
                "1h": "1mo" if limit < 200 else "3mo",
                "4h": "3mo",
                "1d": "1y"
            }
            period = period_map.get(interval, "1mo")
            
            # Use Ticker with auto_adjust=True for accurate prices
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=yf_interval)
            
            if df.empty:
                logger.warning(f"[YFinance] No data found for {symbol}")
                return []
                
            # Convert to standard OHLCV dict format (same as Binance)
            ohlc_data = []
            for ts, row in df.iterrows():
                # YF timestamps are timezone-aware (usually UTC or localized)
                # We normalize to naive UTC timestamp (ms) for consistency
                if hasattr(ts, 'tz_convert'):
                    ts_utc = ts.tz_convert('UTC').replace(tzinfo=None)
                else:
                    ts_utc = ts.to_pydatetime()
                    
                ohlc_data.append({
                    'timestamp': int(ts_utc.timestamp() * 1000),
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': float(row['Volume']),
                })
                
            # Limit to requested amount
            result_data = ohlc_data[-limit:]
            
            # Update Cache
            self._yfinance_cache[cache_key] = {
                'ts': datetime.utcnow(),
                'data': result_data
            }
            
            return result_data
            
        except Exception as e:
            msg = str(e)
            if "Too Many Requests" in msg or "429" in msg:
                logger.warning(f"[YFinance] Rate Limited for {symbol}. Using stale cache if available.")
                # Try to return stale cache
                if hasattr(self, '_yfinance_cache') and cache_key in self._yfinance_cache:
                    return self._yfinance_cache[cache_key]['data']
                return []
            
            logger.error(f"YFinance fallback failed for {symbol}: {e}")
            return []


    def init_db(self):
        """Initialize database and PURGE FUTURE GHOSTS."""
        try:
            # FIX: Do NOT call create_all(bind=self.engine) here to avoid creating OHLCV in Cloud.
            # Schema separation is handled in __init__.
            logger.info("[DataManager] [OK] Hybrid Schema verified (Cloud vs Local split).")
            
            # Verify specific tables exist (in Cloud)
            # Only check for critical cloud tables
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
            logger.info(f"[DataManager] Cloud tables: {tables}")
            
            if 'ohlcv' in tables:
                logger.warning("[DataManager] ⚠️ 'ohlcv' table detected in CLOUD DB. This may cause high egress if queried!")
            
            # CLEANUP: Delete any data from the future (e.g., > Jan 1, 2030)
            # We do this on Local DB for OHLCV
            try:
                with self.local_engine.connect() as conn:
                     from sqlalchemy import text
                     # Nuke anything after Jan 1 2030 just to be safe (future proof)
                     conn.execute(text("DELETE FROM ohlcv WHERE timestamp > '2030-01-01'"))
                     conn.commit()
            except Exception as e:
                logger.warning(f"Failed to prune local future ghosts: {e}")
                    
            # --- AUTO-MIGRATION: Ensure user_bot_settings has all columns (CLOUD) ---
            try:
                with self.engine.connect() as cloud_conn:
                    from sqlalchemy import text
                    columns_to_add = [
                        ("active_style", "VARCHAR DEFAULT 'ALL'"),
                        ("simple_mode", "INTEGER DEFAULT 1")
                    ]
                    
                    for col_name, col_type in columns_to_add:
                        try:
                            # Check if column exists
                            cloud_conn.execute(text(f"SELECT {col_name} FROM user_bot_settings LIMIT 1"))
                        except Exception:
                            logger.info(f"DataManager: Adding missing column {col_name} to user_bot_settings...")
                            try:
                                cloud_conn.execute(text(f"ALTER TABLE user_bot_settings ADD COLUMN {col_name} {col_type}"))
                                cloud_conn.commit()
                            except Exception as alter_err:
                                logger.error(f"Failed to add column {col_name}: {alter_err}")
            except Exception as e:
                logger.warning(f"Auto-migration check failed: {e}")

            logger.info("Database initialized and sanitized.")
                
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")

    def get_db(self):
        """Standard dependency for Cloud/Strategic state."""
        db = self.CloudSession()
        try:
            yield db
        finally:
            db.close()

    def get_local_session(self):
        """Explicitly get a session for Local/OHLCV data."""
        return self.LocalSession()

    async def update_symbol_registry(self):
        """Fetch all trading USDT pairs from Binance and include Whitelisted TradFi; update registry."""
        logger.info("Updating symbol registry with sector tagging...")
        try:
            settings = get_settings()
            taxonomy = settings.UNIVERSE_TAXONOMY
            
            # 1. Binance Crypto Data
            exchange_info = await asyncio.to_thread(self.client.get_exchange_info)
            binance_symbols = exchange_info['symbols']
            
            db = self.SessionLocal()
            count = 0
            
            # Helper to get tags
            def get_tags(sym):
                cat = "CRYPTO"
                sect = "UNKNOWN"
                # Check Categories (Explicit or Prefix)
                for c, members in taxonomy.get("CATEGORIES", {}).items():
                    if any(sym.startswith(m) for m in members):
                        cat = c
                        break
                
                # Check Prefixes explicitly
                for c, prefs in taxonomy.get("PREFIXES", {}).items():
                    if any(sym.startswith(p) for p in prefs):
                        cat = c
                        break

                # Check Sectors
                for s, members in taxonomy.get("SECTORS", {}).items():
                    if any(sym.startswith(m) for m in members):
                        sect = s
                        break
                
                # Heuristic Fallbacks
                if cat == "CRYPTO" and sect == "UNKNOWN":
                    if sym.endswith("USDT") or sym.endswith("USDC"): sect = "ALT"
                if cat == "GLOBAL" and sect == "UNKNOWN":
                    if sym.startswith("XAU"): sect = "COMMODITY"
                    if sym.startswith(("EUR", "GBP", "JPY")): sect = "MACRO"
                
                return cat, sect

            whitelist = settings.trading_symbols
            whitelist_set = set(whitelist)

            for s in binance_symbols:
                if s['status'] == 'TRADING' and s['quoteAsset'] in ['USDT', 'USDC']:
                    if s['symbol'] not in whitelist_set:
                        continue
                        
                    cat, sect = get_tags(s['symbol'])
                    symbol_entry = SymbolRegistry(
                        symbol=s['symbol'],
                        base_asset=s['baseAsset'],
                        quote_asset=s['quoteAsset'],
                        category=cat,
                        sector=sect,
                        status=s['status'],
                        last_updated=datetime.utcnow()
                    )
                    db.merge(symbol_entry)
                    count += 1
                    
            # 2. Whitelisted TradFi/Yahoo/Commodity Assets
            for s in whitelist:
                # If definitely a Global/TradFi asset (Binance assets processed above)
                is_binance = any(s.endswith(q) for q in ['USDT', 'USDC'])
                if is_binance: continue

                cat, sect = get_tags(s)
                symbol_entry = SymbolRegistry(
                    symbol=s,
                    base_asset=s.split('=')[0] if '=' in s else s,
                    quote_asset="USD", # Default for TradFi
                    category=cat,
                    sector=sect,
                    status="TRADING",
                    last_updated=datetime.utcnow()
                )
                db.merge(symbol_entry)
                count += 1
            
            with self.db_lock:
                db.commit()
            logger.info(f"[SUCCESS] Symbol registry updated. Total indexed identifiers: {count}.")
            db.close()
            return count
        except Exception as e:
            logger.error(f"Failed to update symbol registry: {e}")
            db.close()
            return 0

    def get_available_symbols(self) -> List[str]:
        """Return list of symbols currently in the registry."""
        db = self.SessionLocal()
        try:
            symbols = db.query(SymbolRegistry.symbol).filter(SymbolRegistry.status == 'TRADING').all()
            return [s[0] for s in symbols]
        finally:
            db.close()

    async def fetch_and_store(self, symbol: str, interval: str, lookback_days: int = 90):
        """Fetch historical data from Binance and store in SQLite (Performance Optimized & Time-Synced)."""
        normalizer = get_symbol_normalizer()
        
        # 1. Sanitize Input
        s_clean = normalizer.sanitize(symbol)
        if not s_clean:
            return # Silent fail for garbage

        # BLOCKLIST: Ignore known metadata keys to prevent API spam
        if s_clean.upper() in ["GLOBAL", "CRYPTO", "FOREX", "STOCKS", "COMMODITIES", "UNKNOWN", "SECTOR", "TOTAL"]:
            return

        # 2. Normalize Dialect (e.g. GOLD -> GC=F)
        symbol = normalizer.normalize(s_clean)
        
        logger.info(f"Fetching {interval} data for {symbol} (Last {lookback_days} days)...")
        
        # STEALTH: Network Jitter
        # Sleep randomly between 0.2s and 0.8s to break rhythmic patterns
        # Use asyncio.sleep to avoid blocking the event loop.
        jitter = random.uniform(0.2, 0.8)
        await asyncio.sleep(jitter)

        
        # 1. Calculate Start/End based on SERVER TIME (Real World) to avoid Local Clock drift
        now_ms = int(time.time() * 1000) + self.time_offset
        start_ms = now_ms - (lookback_days * 24 * 60 * 60 * 1000)
        
        try:
            # 2. Routing Logic: Crypto vs TradFi
            is_tradfi = False
            binance_symbol = normalizer.to_binance(symbol)
            
            # If no valid Binance symbol, or explicitly marked as TradFi
            if not binance_symbol or "^" in symbol or "=" in symbol:
                is_tradfi = True
            
            if is_tradfi:
                # Yahoo Header
                yahoo_symbol = normalizer.to_yahoo(symbol)
                
                # Date formatted via YFinance (handled inside connector)
                # Yahoo Connector Logic
                s_dt = datetime.utcfromtimestamp(start_ms / 1000)
                e_dt = datetime.utcfromtimestamp(now_ms / 1000)
                
                klines = await asyncio.to_thread(
                    self.yahoo.get_historical_klines,
                    yahoo_symbol,
                    interval,
                    s_dt.strftime("%Y-%m-%d"),
                    e_dt.strftime("%Y-%m-%d")
                )
            else:
                # Binance
                klines = await asyncio.to_thread(
                    self.client.get_historical_klines, 
                    binance_symbol, # Use safe Binance format 
                    interval, 
                    start_ms,
                    now_ms
                )
            
            if not klines:
                logger.warning(f"No data found for {symbol} {interval} (Range: {start_ms} - {now_ms})")
                return

            db = self.LocalSession()
            
            # DYNAMIC DIALECT DETECTION
            dialect = self.engine.dialect.name
            if dialect == 'postgresql':
                from sqlalchemy.dialects.postgresql import insert
            else:
                from sqlalchemy.dialects.sqlite import insert

            new_records = []
            
            # GUARDRAIL: Define "The Future" (e.g., anything > 24 hours from real now)
            # Use server time (now_ms) to define the cutoff
            real_now_dt = datetime.utcfromtimestamp(now_ms / 1000)
            cutoff_dt = real_now_dt + timedelta(hours=24)

            for k in klines:
                # Binance kline: [open_time, open, high, low, close, volume, ...]
                ts = datetime.utcfromtimestamp(k[0] / 1000)
                
                # 1. TIME TRAVEL FILTER
                if ts > cutoff_dt:
                    continue # Skip future data
                
                record = {
                    'symbol': symbol,
                    'interval': interval,
                    'timestamp': ts,
                    'open': float(k[1]),
                    'high': float(k[2]),
                    'low': float(k[3]),
                    'close': float(k[4]),
                    'volume': float(k[5])
                }
                new_records.append(record)

            # 2. BATCH INSERT (Fixes "too many terms" error)
            BATCH_SIZE = 500
            if new_records:
                # Offload DB write-heavy work to a worker thread to avoid blocking the event loop
                await asyncio.to_thread(self._store_records, new_records, BATCH_SIZE)
            else:
                logger.info(f"No new records to store for {symbol} {interval}")
            
            db.close()

        except BinanceAPIException as e:
            logger.error(f"Binance API error for {symbol}: {e}")
        except Exception as e:
            logger.error(f"Error fetching/storing data for {symbol}: {e}")

    def _store_records(self, records, batch_size=500):
        """Synchronous helper to store OHLCV records in chunks under the DB lock."""
        try:
            # FIX: Use Local Engine dialect for Local Storage (always SQLite)
            # self.engine might be Cloud (Postgres), which would break SQLite inserts
            dialect = self.local_engine.dialect.name
            if dialect == 'postgresql':
                from sqlalchemy.dialects.postgresql import insert
            else:
                from sqlalchemy.dialects.sqlite import insert

            db = self.LocalSession()
            total = 0
            for i in range(0, len(records), batch_size):
                chunk = records[i : i + batch_size]
                stmt = insert(OHLCV).values(chunk)
                
                # Dialect-specific UPSERT logic
                if dialect == 'postgresql':
                    # Postgres requires ON CONFLICT DO NOTHING
                    do_nothing_stmt = stmt.on_conflict_do_nothing(
                        index_elements=['symbol', 'interval', 'timestamp']
                    )
                else:
                    # SQLite works similarly but we ensure consistency
                    do_nothing_stmt = stmt.on_conflict_do_nothing(
                        index_elements=['symbol', 'interval', 'timestamp']
                    )

                with self.db_lock:
                    try:
                        db.execute(do_nothing_stmt)
                        db.commit()
                    except Exception:
                        db.rollback()
                total += len(chunk)
            # Silent Success - limit logging for background tasks
        except Exception:
            logger.exception("Error storing OHLCV records in background thread")
        finally:
            try:
                db.close()
            except Exception:
                pass

    async def calibrate_universe(self, lookback_days: int = 2) -> Dict[str, List[str]]:
        """
        Calibrate the universe asynchronously.
        Returns dictionary with tiers: {'core': [], 'momentum': [], 'speculative': []}
        """
        return await asyncio.to_thread(self._calibrate_logic, lookback_days)

    def _calibrate_logic(self, lookback_days: int) -> Dict[str, List[str]]:
        """
        Synchronous logic for calibration (Heavy CPU/IO).
        """
        logger.info(f"Calibrating Universe (Lookback: {lookback_days}d)...")
        symbols = self.get_available_symbols()
        
        tier_1 = [] # Core (High Liq)
        tier_2 = [] # Momentum (High Vol, Med Liq)
        tier_3 = [] # Speculative (Low Liq)
        
        start_dt = datetime.utcnow() - timedelta(days=lookback_days)
        
        results = []

        for symbol in symbols:
            # Get 1H data (Synchronous DB Call)
            data = self.get_data(symbol, "1h", start=start_dt)
            if len(data) < 24: # Need at least a day of data
                continue

            df = pd.DataFrame(data)
            
            # Calculate Metrics
            try:
                df['quote_vol'] = df['volume'] * df['close']
                daily_vol = df['quote_vol'].sum() 
                
                # Check for division by zero
                avg_daily_vol = daily_vol / lookback_days if lookback_days > 0 else 0
                
                # Volatility: ATR(14)
                atr = ta.atr(df['high'], df['low'], df['close'], length=14)
                
                # Check if ATR is empty or has no valid values
                if atr is None or atr.empty or len(atr) == 0:
                    current_atr = 0.0
                    volatility_pct = 0.0
                else:
                    try:
                        current_atr_val = atr.iloc[-1]
                        current_atr = float(current_atr_val) if not pd.isna(current_atr_val) else 0.0
                    except (IndexError, ValueError, TypeError):
                        current_atr = 0.0
                    
                    try:
                        current_price = float(df['close'].iloc[-1]) if len(df) > 0 else 0.0
                    except (IndexError, ValueError, TypeError):
                        current_price = 0.0
                    
                    # Calculate volatility with safety checks
                    if current_price > 0 and current_atr > 0:
                        volatility_pct = (current_atr / current_price) * 100
                        if pd.isna(volatility_pct) or np.isinf(volatility_pct):
                            volatility_pct = 0.0
                    else:
                        volatility_pct = 0.0
                
            except Exception as e:
                # Fallback
                avg_daily_vol = 0
                volatility_pct = 0

            results.append({
                'symbol': symbol,
                'volume': avg_daily_vol,
                'volatility': volatility_pct
            })

        # Convert to DataFrame for easy percentile ranking
        if not results:
            return {"core": [], "momentum": [], "speculative": []}
            
        metrics_df = pd.DataFrame(results)
        
        for _, row in metrics_df.iterrows():
            sym = row['symbol']
            vol = row['volume']
            vola = row['volatility']
            
            # Handle NaN/Inf values in comparisons
            try:
                vol_float = float(vol) if not pd.isna(vol) else 0.0
                vola_float = float(vola) if not pd.isna(vola) else 0.0
            except (ValueError, TypeError):
                tier_3.append(sym)
                continue
            
            if pd.isna(vol_float) or np.isinf(vol_float) or pd.isna(vola_float) or np.isinf(vola_float):
                tier_3.append(sym)
                continue
            
            # Classification Thresholds
            if vol_float > 100_000_000: # $100M Daily Volume
                tier_1.append(sym)
            elif vol_float > 10_000_000 and vola_float > 1.5: # $10M + >1.5% ATR
                tier_2.append(sym)
            else:
                tier_3.append(sym)
                
        logger.info(f"Calibration Complete. Core: {len(tier_1)}, Momentum: {len(tier_2)}, Spec: {len(tier_3)}")
        
        return {
            "core": tier_1,
            "momentum": tier_2,
            "speculative": tier_3,
            "all": symbols,
            "metrics": metrics_df
        }

    async def sync_universe(self):
        """Iterate through ALL active USDT pairs and fetch history (Parallelized)."""
        logger.info("Starting Universe Sync (BETA MODE)...")
        
        # 1. Update Registry (Keep this so we know what exists)
        await self.update_symbol_registry()
        
        # 1b. PRUNE ANCIENT DATA (Phase 13: Space)
        await asyncio.to_thread(self.prune_old_data, 90)
        
        # Get symbols from simplified config or legacy format
        symbols = get_trading_symbols(settings)
        
        logger.info(f"Syncing data for {len(symbols)} Priority Symbols (BETA LIMIT)...")
        
        # 2. Parallel Fetch with Semaphore
        # Limit concurrency to avoid hitting Binance rate limits (1200 weight/min)
        # Each fetch does 2 calls (1m, 1h). 
        # Let's be safe with 5 concurrent workers.
        sem = asyncio.Semaphore(5)
        
        async def _sync_symbol(symbol: str):
            async with sem:
                try:
                    logger.info(f"Syncing {symbol}...")
                    # 1m Data - Reduced to 7 days for Beta speed
                    await self.fetch_and_store(symbol, Client.KLINE_INTERVAL_1MINUTE, lookback_days=7)
                    
                    # 1h Data - Reduced to 90 days for Beta speed
                    await self.fetch_and_store(symbol, Client.KLINE_INTERVAL_1HOUR, lookback_days=90)
                    
                    # Small sleep to be nice
                    await asyncio.sleep(0.1)
                except Exception as e:
                    logger.error(f"Failed to sync {symbol}: {e}")

        # 2. Sequential/Staggered Fetch to avoid IO burst
        count = 0
        for symbol in symbols:
            await _sync_symbol(symbol)
            count += 1
            # STAGGER: Small gap between symbols to avoid IO/CPU burst
            if count < len(symbols):
                await asyncio.sleep(1.0)
            
        logger.info(f"[SUCCESS] Universe Sync Complete ({count} priority symbols processed).")

    def get_data(self, symbol: str, interval: str, start: Optional[datetime] = None, end: Optional[datetime] = None, limit: int = 0) -> List[Dict]:
        """Query DB for OHLCV data. Supports optional limit for 'latest' data."""
        
        # BLOCKLIST: Ignore known metadata keys to prevent DB spam and API noise
        if symbol.upper() in ["GLOBAL", "CRYPTO", "FOREX", "STOCKS", "COMMODITIES", "UNKNOWN", "SECTOR", "TOTAL"]:
            return []

        db = self.LocalSession()
        try:
            query = db.query(OHLCV).filter(OHLCV.symbol == symbol, OHLCV.interval == interval)
            
            if start:
                query = query.filter(OHLCV.timestamp >= start)
            if end:
                query = query.filter(OHLCV.timestamp <= end)
                
            # Debug logging (only logs at DEBUG level to reduce noise)
            logger.debug(f"Querying {symbol} {interval} from {start} to {end} (Limit: {limit})")
            
            if limit > 0:
                # If limiting, get the NEWEST first, then reverse
                query = query.order_by(OHLCV.timestamp.desc()).limit(limit)
                results = query.all()
                results.reverse() # Restore Chronological Order
            else:
                # Standard range query
                results = query.order_by(OHLCV.timestamp.asc()).all()
            
            count = len(results)
            
            # ─────────────────────────────────────────────────────────────────
            # SELF-HEALING FALLBACK (Fix for new symbols like GBPJPY)
            # ─────────────────────────────────────────────────────────────────
            if count == 0:
                logger.debug(f"[DataManager] Missing DB data for {symbol} {interval}. Triggering SELF-HEALING (API Fetch).")
                try:
                    # 1. Fetch from API immediately
                    # Use limit=100 as default to get enough context for indicators
                    fetch_limit = limit if limit > 0 else 100
                    live_data = self.fetch_live_data(symbol, interval, limit=fetch_limit)
                    
                    if live_data and len(live_data) > 0:
                        logger.debug(f"[DataManager] Self-Healing SUCCESS: Fetched {len(live_data)} candles for {symbol}")
                        
                        # 2. Convert API format (ms int) to DB format (ISO string)
                        from datetime import timezone
                        healed_results = []
                        for d in live_data:
                            try:
                                ts_ms = d['timestamp']
                                # Basic validation
                                if not ts_ms: continue
                                
                                healed_results.append({
                                    'symbol': symbol,
                                    'interval': interval,
                                    'timestamp': ts_ms, # Keep input timestamp
                                    'open': float(d['open']),
                                    'high': float(d['high']),
                                    'low': float(d['low']),
                                    'close': float(d['close']),
                                    'volume': float(d['volume']) 
                                })
                            except Exception:
                                continue
                                
                        # Return API results directly (DB insert happens in background via fetch_and_store usually, 
                        # but here we just return what we found for immediate use)
                        return healed_results
                        
                except Exception as e:
                    logger.error(f"[DataManager] Self-Healing FAILED for {symbol}: {e}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error querying data for {symbol}: {e}")
            return []
        finally:
            db.close()

    def get_latest_ohlcv_df(self, symbol: str, interval: str, limit: int = 1000) -> pd.DataFrame:
        """
        Helper: Fetch data and return as pandas DataFrame (for Analysis/Dreamer).
        """
        data = self.get_data(symbol, interval, limit=limit)
        if not data:
            return pd.DataFrame()
        # Convert SQLAlchemy objects to dicts if necessary
        dict_data = []
        for row in data:
            if hasattr(row, '__table__'):
                dict_data.append({c.name: getattr(row, c.name) for c in row.__table__.columns})
            elif isinstance(row, dict):
                dict_data.append(row)
            else:
                dict_data.append(vars(row))
                
        df = pd.DataFrame(dict_data)
        
        # Ensure correct types
        cols = ['open', 'high', 'low', 'close', 'volume']
        for c in cols:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors='coerce')
        
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
        return df

    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """
        Fetch the latest price for a symbol.
        Supports both Crypto (Binance) and TradFi (Yahoo).
        """
        try:
            # 1. Normalize
            target_symbol = self.sn.normalize(symbol)
            is_tradfi_indicator = any(x in target_symbol for x in [".", "-", "^", "="]) or target_symbol in self.sn.aliases
            
            # 2. TradFi Path
            if is_tradfi_indicator:
                # Try Yahoo
                try:
                    stats = self.yahoo.get_ticker_stats(target_symbol)
                    if stats and 'price' in stats:
                        return float(stats['price'])
                except Exception as e:
                    logger.debug(f"Yahoo price fetch failed for {target_symbol}: {e}")

            # 3. Crypto Path (Binance)
            # Try Direct API (Freshest)
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        except Exception as e:
            # Fallback: Try to get latest close from DB
            try:
                db = self.LocalSession()
                last_candle = db.query(OHLCV).filter(
                    OHLCV.symbol == symbol
                ).order_by(OHLCV.timestamp.desc()).first()
                db.close()
                
                if last_candle:
                    return last_candle.close
            except Exception:
                pass
                
            # logger.warning(f"Could not fetch price for {symbol}: {e}")
            return None

    def get_ticker_stats(self, symbol: str) -> Optional[Dict]:
        """
        Fetch detailed 24h ticker stats with Robust Failover and Caching.
        """
        # 0. CHECK CACHE
        symbol_upper = symbol.upper()
        now = time.time()
        if symbol_upper in self._stats_cache:
            cached = self._stats_cache[symbol_upper]
            if now - cached['ts'] < self._cache_ttl:
                return cached['data']

        # 1. Alias Resolution using Central Normalizer
        target_symbol = self.sn.normalize(symbol)
        
        is_commodity = symbol.upper().startswith(("XAU", "XAG"))
        is_tradfi_indicator = any(x in target_symbol for x in [".", "-", "^", "="])
        is_yahoo_target = is_commodity or is_tradfi_indicator or target_symbol in self.sn.aliases
        
        if is_yahoo_target:
            stats = self.yahoo.get_ticker_stats(target_symbol)
            if stats:
                stats['source'] = 'GLOBAL_MARKETS'
                stats['timestamp'] = time.time()
                # CACHE BEFORE RETURN
                self._stats_cache[symbol_upper] = {'data': stats, 'ts': time.time()}
                return stats
            
            # If it's definitely TradFi and Yahoo failed, do NOT fall through to Binance
            if is_tradfi_indicator:
                logger.warning(f"[DataManager] TradFi symbol {target_symbol} failed on Yahoo. Skipping Binance.")
                return None
        
        # 3. CRYPTO PATH: Try Binance First (Default for Crypto-looking)
        try:
            # Only hit Binance if it doesn't look like a TradFi ticker
            if not is_tradfi_indicator:
                ticker = self.client.get_ticker(symbol=target_symbol)
                stats = {
                    'price': float(ticker['lastPrice']),
                    'change_pct': float(ticker['priceChangePercent']),
                    'high': float(ticker['highPrice']),
                    'low': float(ticker['lowPrice']),
                'volume': float(ticker['volume']),
                'quote_volume': float(ticker['quoteVolume']),
                'trades': int(ticker['count']),
                'source': 'BINANCE_FUTURES',
                'timestamp': time.time()
            }
            
            # WATCHTOWER VERIFICATION: Check if we have a cached consensus price
            # This doesn't make new API calls - just checks the cache
            try:
                from services.watchtower import get_watchtower
                tower = get_watchtower()
                consensus = tower.get_cached_price(symbol)
                if consensus:
                    stats['consensus_price'] = consensus
                    # Calculate fracture (deviation from consensus)
                    fracture = abs(stats['price'] - consensus) / consensus * 100
                    stats['fracture_pct'] = round(fracture, 4)
            except Exception:
                pass  # Watchtower unavailable, continue with Binance data
                
            # CACHE BEFORE RETURN
            self._stats_cache[symbol_upper] = {'data': stats, 'ts': time.time()}
            return stats
            
        except Exception as e:
            # 4. Fallback to Yahoo if Binance Fails
            logger.warning(f"Binance fetch failed for {symbol}, trying Yahoo fallback: {e}")
            stats = self.yahoo.get_ticker_stats(target_symbol)
            if stats:
                stats['source'] = 'GLOBAL_MARKETS'
                stats['timestamp'] = time.time()
            
            # UPDATE CACHE BEFORE RETURN
            if stats:
                self._stats_cache[symbol_upper] = {'data': stats, 'ts': time.time()}
            return stats


    def fetch_live_data(self, symbol: str, interval: str, limit: int = 200, start: datetime = None) -> List[Dict]:
        """
        Fetch OHLCV data from API (Binance or Yahoo Fallback).
        Handles APIError(code=-1121) by switching to yfinance automatically.
        """
        # 0. BLOCKLIST GUARD
        if symbol.upper() in ["GLOBAL", "CRYPTO", "FOREX", "STOCKS", "COMMODITIES", "UNKNOWN", "SECTOR", "TOTAL"]:
            return []

        # 1. CHECK CACHE: Is this a known TradFi symbol?
        if symbol in self.TRADFI_CACHE:
            return self._fetch_yfinance_fallback(symbol, interval, limit)

        # 2. PREEMPTIVE CHECK: Illegal Binance Characters (Error -1100)
        # Symbols with =, ^, or - (unless standard pair) are definitely not on Binance Spot/Futures
        # e.g. "HG=F", "^GSPC", "DX-Y.NYB"
        if any(char in symbol for char in ['=', '^']) or ('.' in symbol):
             self.TRADFI_CACHE.add(symbol)
             return self._fetch_yfinance_fallback(symbol, interval, limit)

        from services.symbol_normalizer import get_symbol_normalizer
        normalizer = get_symbol_normalizer()
        binance_symbol = normalizer.to_binance(symbol)
        
        if not binance_symbol:
            if any(c.islower() for c in symbol):
                logger.warning(f"Symbol {symbol} contains lowercase chars (e.g. kPEPE). Skipping Binance fetch.")
                return []
            self.TRADFI_CACHE.add(symbol)
            return self._fetch_yfinance_fallback(symbol, interval, limit)

        # 2. TRY BINANCE
        try:
            klines = self.client.get_klines(symbol=binance_symbol, interval=interval, limit=limit)
            
            data = []
            for k in klines:
                data.append({
                    'timestamp': k[0],
                    'open': float(k[1]),
                    'high': float(k[2]),
                    'low': float(k[3]),
                    'close': float(k[4]),
                    'volume': float(k[5])
                })
            return data

        except BinanceAPIException as e:
            # Code -1121: Invalid Symbol (likely TradFi stock)
            if e.code == -1121:
                logger.warning(f"Symbol {symbol} not found on Binance. Switching to Yahoo Finance (TradFi).")
                self.TRADFI_CACHE.add(symbol) # Cache this knowledge
                return self._fetch_yfinance_fallback(symbol, interval, limit)
            else:
                # Genuine API error
                logger.error(f"Binance API Error for {symbol}: {e}")
                # Don't raise, just return empty so we don't crash loop
                return []
                
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return []

    def get_market_mood(self, symbol: str = "BTCUSDT") -> Dict[str, float]:
        """
        Returns volatility (0-1), trend_strength (0-1), recent_change (-1 to 1) for Pidgin Poet.
        Uses last 24h of 1H data for the proxy symbol.
        """
        try:
            # 1. Fetch last 24h of 1H data
            end = datetime.utcnow()
            start = end - timedelta(hours=24)
            data = self.get_data(symbol, "1h", start=start, end=end)
            
            if not data or len(data) < 10:
                # Fallback to random conservative values if no data
                return {"volatility": 0.5, "trend_strength": 0.5, "recent_change": 0.0}
                
            df = pd.DataFrame(data)
            
            # 2. Calculate Volatility (Normalized Range Average)
            # High volatility = 1.0, Low = 0.0
            # Typical range for BTC is 1-5%. 
            df['range'] = (df['high'] - df['low']) / df['close']
            vol_raw = df['range'].mean()
            # Scale: 0.5% (0.005) -> 0.1, 5% (0.05) -> 1.0
            volatility = min(1.0, vol_raw * 20)
            
            # 3. Trend Strength (Directional Magnitude)
            start_price = float(df.iloc[0]['open'])
            end_price = float(df.iloc[-1]['close'])
            if start_price == 0: start_price = 1.0
            
            pct_change = (end_price - start_price) / start_price
            trend_strength = min(1.0, abs(pct_change) * 10) # 10% move = 1.0 strength
            
            # 4. Recent Change (Last Hour)
            last_close = float(df.iloc[-1]['close'])
            prev_close = float(df.iloc[-2]['close']) if len(df) > 1 else last_close
            recent_change_pct = ((last_close - prev_close) / prev_close) * 100
            
            return {
                "volatility": volatility,
                "trend_strength": trend_strength,
                "recent_change": recent_change_pct
            }
        except Exception as e:
            logger.error(f"Failed to get market mood: {e}")
            return {"volatility": 0.5, "trend_strength": 0.5, "recent_change": 0.0}


    def prune_old_data(self, retention_days: int = 90):
        """
        Garbage Collection for the Database (Phase 13).
        Prevents infinite bloat by deleting data older than retention limit.
        """
        cutoff = datetime.utcnow() - timedelta(days=retention_days)
        logger.info(f"PRUNING: Deleting market data older than {cutoff.isoformat()}...")
        
        db = self.LocalSession()
        try:
            # SQLAlchemy efficiently handles bulk deletes
            # We use the explicit Table object or mapped class
            deleted = db.query(OHLCV).filter(OHLCV.timestamp < cutoff).delete()
            
            with self.db_lock:
                db.commit()
                # VACUUM to reclaim disk space (SQLite specific)
                # Warning: VACUUM is heavy. Maybe runs only on startup?
                # We'll skip VACUUM for now to avoid locking the DB for seconds.
                
            logger.info(f"PRUNING: Removed {deleted} ancient records.")
        except Exception as e:
            logger.error(f"PRUNING FAILED: {e}")
            db.rollback()
        finally:
            db.close()
            
    def set_user_intel_style(self, user_id: int, style: str):
        """Sets the active intel style for a user."""
        try:
            with self.SessionLocal() as session:
                settings = session.query(UserBotSettings).filter_by(user_id=user_id).first()
                if not settings:
                    settings = UserBotSettings(user_id=user_id, active_style=style)
                    session.add(settings)
                else:
                    settings.active_style = style
                session.commit()
                logger.info(f"[DataManager] User {user_id} set intel style to {style}")
        except Exception as e:
            logger.error(f"[DataManager] Error setting intel style for {user_id}: {e}")

    def get_user_intel_style(self, user_id: int) -> str:
        """Gets the active intel style for a user."""
        try:
            with self.SessionLocal() as session:
                settings = session.query(UserBotSettings).filter_by(user_id=user_id).first()
                return settings.active_style if settings else 'ALL'
        except Exception as e:
            logger.error(f"[DataManager] Error getting intel style for {user_id}: {e}")
            return 'ALL'

    def set_user_simple_mode(self, user_id: int, val: int):
        """Sets the UI mode (0=Complex, 1=Simple, 2=All) for a user."""
        try:
            with self.SessionLocal() as session:
                settings = session.query(UserBotSettings).filter_by(user_id=user_id).first()
                if not settings:
                    settings = UserBotSettings(user_id=user_id, simple_mode=val)
                    session.add(settings)
                else:
                    settings.simple_mode = val
                session.commit()
                logger.info(f"[DataManager] User {user_id} simple_mode set to {val}")
        except Exception as e:
            logger.error(f"[DataManager] Error setting simple_mode for {user_id}: {e}")

    def get_user_simple_mode(self, user_id: int) -> int:
        """Gets the UI mode (0=Complex, 1=Simple, 2=All) for a user."""
        try:
            with self.SessionLocal() as session:
                settings = session.query(UserBotSettings).filter_by(user_id=user_id).first()
                # Default is SIMPLE (1)
                if not settings: return 1
                return int(settings.simple_mode)
        except Exception as e:
            # logger.error(f"[DataManager] Error getting simple_mode for {user_id}: {e}")
            return 1



    async def get_all_ticker_prices(self) -> Dict[str, float]:
        """
        Fetch all ticker prices from Binance in a single call.
        Returns a mapping of symbol -> price.
        """
        try:
            # Sync call for all tickers
            tickers = await asyncio.to_thread(self.client.get_all_tickers)
            return {t['symbol']: float(t['price']) for t in tickers}
        except Exception as e:
            logger.error(f"Failed to fetch all tickers: {e}")
            return {}

    # ─────────────────────────────────────────────────────────────────────────
    # SESSION STATE (For Evolving Fractal)
    # ─────────────────────────────────────────────────────────────────────────

    def get_session_state(self, user_id: int) -> Dict:
        """Get the current session state for a user (for fractal evolution)."""
        import json
        from services.data.schema import UserSessionState
        
        try:
            with self.SessionLocal() as session:
                state = session.query(UserSessionState).filter_by(user_id=user_id).first()
                if state:
                    return {
                        'user_id': state.user_id,
                        'tabs_visited': json.loads(state.tabs_visited or '[]'),
                        'buttons_pressed': state.buttons_pressed or 0,
                        'last_symbol': state.last_symbol or 'BTCUSDT',
                        'fractal_seed': state.fractal_seed or 0.0,
                        'updated_at': state.updated_at
                    }
                # Return defaults for new user
                return {
                    'user_id': user_id,
                    'tabs_visited': [],
                    'buttons_pressed': 0,
                    'last_symbol': 'BTCUSDT',
                    'fractal_seed': 0.0,
                    'updated_at': None
                }
        except Exception as e:
            logger.error(f"[DataManager] Error getting session state for {user_id}: {e}")
            return {'user_id': user_id, 'tabs_visited': [], 'buttons_pressed': 0, 
                    'last_symbol': 'BTCUSDT', 'fractal_seed': 0.0, 'updated_at': None}

    def update_session_state(self, user_id: int, tab: str = None, symbol: str = None):
        """
        Update user session state when they interact with the bot.
        Called on button presses, tab visits, symbol views.
        """
        import json
        from services.data.schema import UserSessionState
        
        try:
            with self.SessionLocal() as session:
                state = session.query(UserSessionState).filter_by(user_id=user_id).first()
                
                if not state:
                    # Create new state
                    state = UserSessionState(
                        user_id=user_id,
                        tabs_visited='[]',
                        buttons_pressed=0,
                        last_symbol='BTCUSDT',
                        fractal_seed=0.0
                    )
                    session.add(state)
                
                # Update counters
                state.buttons_pressed = (state.buttons_pressed or 0) + 1
                
                # Update tabs visited (unique list, max 20)
                tabs = json.loads(state.tabs_visited or '[]')
                if tab and tab not in tabs:
                    tabs.append(tab)
                    if len(tabs) > 20:
                        tabs = tabs[-20:]  # Keep last 20
                    state.tabs_visited = json.dumps(tabs)
                
                # Update last symbol
                if symbol:
                    state.last_symbol = symbol
                
                # Evolve fractal seed (simple hash-based evolution)
                state.fractal_seed = (state.fractal_seed + 0.01) % 1.0
                
                session.commit()
                logger.debug(f"[Session] Updated state for {user_id}: buttons={state.buttons_pressed}")
                
        except Exception as e:
            logger.error(f"[DataManager] Error updating session state: {e}")

    def get_fractal_params(self, user_id: int) -> Dict:
        """
        Generate fractal parameters based on user's session state.
        Returns params for ASCIIArt.generate_mandelbrot().
        """
        state = self.get_session_state(user_id)
        
        # Base position (Mandelbrot cardioid)
        base_x, base_y = -0.745, 0.1
        
        # Drift based on tabs visited (more exploration = wider orbit)
        breadth = len(state.get('tabs_visited', []))
        breadth_factor = min(breadth / 10.0, 1.0)
        
        # Zoom based on interaction count (more engaged = deeper zoom)
        presses = state.get('buttons_pressed', 0)
        zoom = 8.0 + min(presses * 0.3, 40.0)  # Cap at 48x zoom
        
        # Iterations based on engagement
        iterations = 30 + min(presses * 2, 70)  # Cap at 100 iterations
        
        # Seed-based position drift
        seed = state.get('fractal_seed', 0.0)
        import math
        drift_x = base_x + (math.cos(seed * 2 * math.pi) * 0.02 * breadth_factor)
        drift_y = base_y + (math.sin(seed * 2 * math.pi) * 0.02 * breadth_factor)
        
        return {
            'center_x': drift_x,
            'center_y': drift_y,
            'zoom': zoom,
            'iterations': int(iterations),
            'width': 32,
            'height': 12,
            'last_symbol': state.get('last_symbol', 'BTCUSDT'),
            'breadth': breadth,
            'engagement': presses
        }

    def update_user_activity(self, user_id: int):
        """
        [CENSUS TAKER] 
        Records user presence. 
        1. Ensures they exist in UserBotSettings (increments Total).
        2. Updates timestamp in UserSessionState (increments Active).
        """
        from services.data.schema import UserBotSettings, UserSessionState
        session = self.SessionLocal()
        try:
            # 1. Ensure UserBotSettings (Registration)
            settings = session.query(UserBotSettings).filter_by(user_id=user_id).first()
            if not settings:
                settings = UserBotSettings(user_id=user_id)
                session.add(settings)
                logger.info(f"[CENSUS] NEW PILOT REGISTERED: {user_id}")
            
            # 2. Update Session State (Activity Pulse)
            state = session.query(UserSessionState).filter_by(user_id=user_id).first()
            if not state:
                state = UserSessionState(user_id=user_id)
                session.add(state)
            
            state.updated_at = datetime.utcnow()
            session.commit()
        except Exception as e:
            logger.error(f"[DataManager] Census Error for {user_id}: {e}")
            session.rollback()
        finally:
            session.close()

    def get_user_stats(self) -> Dict[str, int]:
        """Returns total registered users and active users (last 24h)."""
        from services.data.schema import UserBotSettings, UserSessionState
        session = self.SessionLocal()
        try:
            total_users = session.query(UserBotSettings).count()
            
            # Active Users: Interactions within the last 24 hours
            cutoff = datetime.utcnow() - timedelta(hours=24)
            active_users = session.query(UserSessionState).filter(UserSessionState.updated_at >= cutoff).count()
            
            return {
                "total": total_users,
                "active": active_users
            }
        except Exception as e:
            logger.error(f"[DataManager] Failed to fetch user stats: {e}")
            return {"total": 0, "active": 0}
        finally:
            session.close()

# Global Instance (Lazy Loading)
data_manager = None

def get_data_manager():
    global data_manager
    if data_manager is None:
        data_manager = DataManager()
    return data_manager

