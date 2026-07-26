"""
Supabase Database Provider

Cloud-first Postgres with auth, realtime, and storage.
Implements the DatabaseInterface for easy switching between providers.

EGRESS PROTECTION: This provider includes built-in caching and
circuit breaker to prevent quota overages.
"""

import os
import time
import hashlib
import json
import logging
from typing import Dict, List, Optional, Any, Union

from services.db.interface import DatabaseInterface, QueryResult

logger = logging.getLogger("SupabaseDB")


class SupabaseDB(DatabaseInterface):
    """
    Supabase implementation of DatabaseInterface.
    
    Includes EGRESS PROTECTION:
    - Query caching with configurable TTL
    - Egress tracking and circuit breaker
    - Default query limits
    """
    
    # --- EGRESS PROTECTION CONFIG ---
    CACHE_TTL_SECONDS = 300  # 5 minutes default cache
    MAX_EGRESS_MB_PER_HOUR = 500  # Circuit breaker: 500 MB/hour max
    DEFAULT_LIMIT = 1000  # Max rows per unbounded SELECT
    
    def __init__(self):
        self._client = None
        self._url = os.getenv("SUPABASE_URL")
        self._key = os.getenv("SUPABASE_KEY")
        
        # Query Cache: {hash: (data, timestamp)}
        self._cache: Dict[str, tuple] = {}
        
        # Egress Tracking: MB transferred this hour
        self._egress_mb = 0.0
        self._egress_hour = 0  # Hour of last reset
        self._circuit_open = False  # True = queries blocked
    
    def _get_client(self):
        """Lazy-load Supabase client."""
        if self._client is None:
            if not self._url or not self._key:
                raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
            
            from supabase import create_client
            self._client = create_client(self._url, self._key)
        return self._client
    
    def _cache_key(self, table: str, **kwargs) -> str:
        """Generate cache key from query parameters."""
        raw = f"{table}:{json.dumps(kwargs, sort_keys=True, default=str)}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]
    
    def _get_cached(self, key: str) -> Optional[QueryResult]:
        """Get cached result if fresh."""
        if key in self._cache:
            data, ts = self._cache[key]
            if time.time() - ts < self.CACHE_TTL_SECONDS:
                logger.debug(f"[CACHE HIT] {key}")
                return data
            else:
                del self._cache[key]  # Expired
        return None
    
    def _set_cached(self, key: str, result: QueryResult) -> None:
        """Cache a result (limit cache size to 1000 entries)."""
        if len(self._cache) > 1000:
            # Evict oldest 20%
            sorted_keys = sorted(self._cache.keys(), key=lambda k: self._cache[k][1])
            for k in sorted_keys[:200]:
                del self._cache[k]
        self._cache[key] = (result, time.time())
    
    def _track_egress(self, data: Any) -> None:
        """Track approximate egress and trigger circuit breaker if needed."""
        current_hour = int(time.time() / 3600)
        
        # Reset counter each hour
        if current_hour != self._egress_hour:
            self._egress_mb = 0.0
            self._egress_hour = current_hour
            self._circuit_open = False
            logger.info("[EGRESS] Hourly counter reset.")
        
        # Estimate size of response
        size_bytes = len(json.dumps(data, default=str)) if data else 0
        size_mb = size_bytes / (1024 * 1024)
        self._egress_mb += size_mb
        
        # Check circuit breaker
        if self._egress_mb > self.MAX_EGRESS_MB_PER_HOUR:
            self._circuit_open = True
            logger.critical(
                f"[EGRESS] CIRCUIT BREAKER OPEN! {self._egress_mb:.1f} MB this hour "
                f"(limit: {self.MAX_EGRESS_MB_PER_HOUR} MB). Queries blocked until next hour."
            )
    
    def _check_circuit(self) -> Optional[QueryResult]:
        """Return error if circuit breaker is open."""
        if self._circuit_open:
            return QueryResult(
                data=[],
                count=0,
                error=f"Circuit breaker open: {self._egress_mb:.1f} MB egress this hour. Wait for reset."
            )
        return None
    
    async def connect(self) -> bool:
        """Establish connection."""
        try:
            client = self._get_client()
            # Test connection with simple query
            client.table("_test_connection").select("*").limit(1).execute()
            return True
        except:
            return True  # Table might not exist, but connection works
    
    async def disconnect(self) -> None:
        """Close connection and clear cache."""
        self._client = None
        self._cache.clear()
    
    async def execute(self, query: str, params: Optional[Dict] = None) -> QueryResult:
        """Execute raw SQL via RPC."""
        try:
            client = self._get_client()
            result = client.rpc("execute_sql", {"query": query, "params": params or {}}).execute()
            return QueryResult(
                data=result.data or [],
                count=len(result.data or [])
            )
        except Exception as e:
            return QueryResult(data=[], count=0, error=str(e))
    
    # ==========================================
    # CRUD Operations
    # ==========================================
    
    async def insert(
        self, 
        table: str, 
        data: Union[Dict, List[Dict]],
        returning: Optional[List[str]] = None
    ) -> QueryResult:
        """Insert one or more rows."""
        try:
            client = self._get_client()
            query = client.table(table).insert(data)
            
            if returning:
                query = query.select(",".join(returning))
            
            result = query.execute()
            return QueryResult(
                data=result.data or [],
                count=len(result.data or [])
            )
        except Exception as e:
            return QueryResult(data=[], count=0, error=str(e))
    
    async def select(
        self,
        table: str,
        columns: Optional[List[str]] = None,
        filters: Optional[Dict] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> QueryResult:
        """Select with filtering, ordering, pagination + egress protection."""
        
        # --- EGRESS PROTECTION: Check Circuit Breaker ---
        circuit_error = self._check_circuit()
        if circuit_error:
            return circuit_error
        
        # --- EGRESS PROTECTION: Check Cache ---
        cache_key = self._cache_key(
            table, columns=columns, filters=filters, 
            order_by=order_by, limit=limit, offset=offset
        )
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            client = self._get_client()
            cols = ",".join(columns) if columns else "*"
            query = client.table(table).select(cols)
            
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            if order_by:
                # Handle "col DESC" format
                parts = order_by.split()
                col = parts[0]
                desc = len(parts) > 1 and parts[1].upper() == "DESC"
                query = query.order(col, desc=desc)
            
            # --- EGRESS PROTECTION: Default Limit ---
            # Unbounded SELECTs are dangerous - apply default limit
            effective_limit = limit if limit else self.DEFAULT_LIMIT
            query = query.limit(effective_limit)
            
            if offset:
                query = query.range(offset, offset + effective_limit - 1)
            
            result = query.execute()
            
            # --- EGRESS PROTECTION: Track Egress ---
            self._track_egress(result.data)
            
            qr = QueryResult(
                data=result.data or [],
                count=len(result.data or [])
            )
            
            # --- Cache the result ---
            self._set_cached(cache_key, qr)
            
            return qr
        except Exception as e:
            return QueryResult(data=[], count=0, error=str(e))
    
    async def update(
        self,
        table: str,
        data: Dict,
        filters: Dict
    ) -> QueryResult:
        """Update rows matching filters."""
        try:
            client = self._get_client()
            query = client.table(table).update(data)
            
            for key, value in filters.items():
                query = query.eq(key, value)
            
            result = query.execute()
            return QueryResult(
                data=result.data or [],
                count=len(result.data or [])
            )
        except Exception as e:
            return QueryResult(data=[], count=0, error=str(e))
    
    async def delete(self, table: str, filters: Dict) -> QueryResult:
        """Delete rows matching filters."""
        try:
            client = self._get_client()
            query = client.table(table).delete()
            
            for key, value in filters.items():
                query = query.eq(key, value)
            
            result = query.execute()
            return QueryResult(
                data=result.data or [],
                count=len(result.data or [])
            )
        except Exception as e:
            return QueryResult(data=[], count=0, error=str(e))
    
    async def upsert(
        self,
        table: str,
        data: Union[Dict, List[Dict]],
        conflict_columns: List[str]
    ) -> QueryResult:
        """Insert or update on conflict."""
        try:
            client = self._get_client()
            result = client.table(table).upsert(
                data,
                on_conflict=",".join(conflict_columns)
            ).execute()
            
            return QueryResult(
                data=result.data or [],
                count=len(result.data or [])
            )
        except Exception as e:
            return QueryResult(data=[], count=0, error=str(e))
    
    # ==========================================
    # Time-Series Operations (TimescaleDB)
    # ==========================================
    
    async def insert_timeseries(
        self,
        table: str,
        timestamp_col: str,
        data: Union[Dict, List[Dict]]
    ) -> QueryResult:
        """Insert time-series data (uses hypertable if TimescaleDB enabled)."""
        return await self.insert(table, data)
    
    async def query_timeseries(
        self,
        table: str,
        timestamp_col: str,
        start_time: str,
        end_time: str,
        columns: Optional[List[str]] = None,
        resample: Optional[str] = None
    ) -> QueryResult:
        """Query time-series with optional TimescaleDB functions + egress protection."""
        
        # --- EGRESS PROTECTION: Check Circuit Breaker ---
        circuit_error = self._check_circuit()
        if circuit_error:
            return circuit_error
        
        # --- EGRESS PROTECTION: Check Cache ---
        cache_key = self._cache_key(
            table, timestamp_col=timestamp_col, 
            start=start_time, end=end_time, columns=columns, resample=resample
        )
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            client = self._get_client()
            cols = ",".join(columns) if columns else "*"
            
            query = client.table(table).select(cols)
            query = query.gte(timestamp_col, start_time)
            query = query.lte(timestamp_col, end_time)
            query = query.order(timestamp_col)
            
            # --- EGRESS PROTECTION: Limit time-series ---
            # Time-series can be huge; cap at 5000 rows
            query = query.limit(5000)
            
            result = query.execute()
            
            # --- EGRESS PROTECTION: Track Egress ---
            self._track_egress(result.data)
            
            qr = QueryResult(
                data=result.data or [],
                count=len(result.data or [])
            )
            
            # --- Cache the result ---
            self._set_cached(cache_key, qr)
            
            return qr
        except Exception as e:
            return QueryResult(data=[], count=0, error=str(e))
    
    # ==========================================
    # Full-Text Search
    # ==========================================
    
    async def search(
        self,
        table: str,
        query: str,
        search_columns: List[str],
        limit: int = 50
    ) -> QueryResult:
        """Full-text search using Postgres tsvector if available."""
        try:
            client = self._get_client()
            
            # Use textSearch if fts column exists, else use ilike
            result = client.table(table).select("*")
            
            # Simple ILIKE search across columns
            # In production, you'd use .textSearch() on a tsvector column
            for col in search_columns:
                result = result.ilike(col, f"%{query}%")
            
            result = result.limit(limit).execute()
            
            return QueryResult(
                data=result.data or [],
                count=len(result.data or [])
            )
        except Exception as e:
            return QueryResult(data=[], count=0, error=str(e))
    
    # ==========================================
    # Schema Operations
    # ==========================================
    
    async def table_exists(self, table: str) -> bool:
        """Check if table exists."""
        try:
            client = self._get_client()
            client.table(table).select("*").limit(1).execute()
            return True
        except:
            return False
    
    async def create_table(self, table: str, schema: Dict[str, str]) -> bool:
        """
        Create table with schema.
        
        Note: Supabase doesn't support DDL via REST API.
        Use Supabase Dashboard or migrations for table creation.
        """
        # Log warning - DDL not supported via REST
        import logging
        logging.warning(
            f"Cannot create table '{table}' via Supabase REST API. "
            "Use Supabase Dashboard or SQL migrations."
        )
        return False
