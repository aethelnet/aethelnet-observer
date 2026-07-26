"""
Database Interface - Vendor-Agnostic Abstraction Layer

This module provides an abstract interface for database operations,
allowing easy switching between Supabase, SQLite, or self-hosted Postgres.

Usage:
    from services.db import get_db
    db = get_db()  # Returns provider based on DB_PROVIDER env var
    
    # CRUD operations
    result = await db.insert("table", {"col": "value"})
    rows = await db.select("table", filters={"id": "123"})
    await db.update("table", {"col": "new"}, filters={"id": "123"})
    await db.delete("table", filters={"id": "123"})
"""

import os
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass


@dataclass
class QueryResult:
    """Standardized query result across all providers."""
    data: List[Dict[str, Any]]
    count: int
    error: Optional[str] = None
    
    @property
    def success(self) -> bool:
        return self.error is None
    
    @property
    def first(self) -> Optional[Dict[str, Any]]:
        return self.data[0] if self.data else None


class DatabaseInterface(ABC):
    """
    Abstract base class for database providers.
    
    All database access should go through this interface,
    never directly to Supabase SDK or sqlite3.
    """
    
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to database."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close database connection."""
        pass
    
    @abstractmethod
    async def execute(self, query: str, params: Optional[Dict] = None) -> QueryResult:
        """Execute raw SQL query (use sparingly)."""
        pass
    
    # ==========================================
    # CRUD Operations
    # ==========================================
    
    @abstractmethod
    async def insert(
        self, 
        table: str, 
        data: Union[Dict, List[Dict]],
        returning: Optional[List[str]] = None
    ) -> QueryResult:
        """Insert one or more rows."""
        pass
    
    @abstractmethod
    async def select(
        self,
        table: str,
        columns: Optional[List[str]] = None,
        filters: Optional[Dict] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> QueryResult:
        """Select rows with optional filtering, ordering, pagination."""
        pass
    
    @abstractmethod
    async def update(
        self,
        table: str,
        data: Dict,
        filters: Dict
    ) -> QueryResult:
        """Update rows matching filters."""
        pass
    
    @abstractmethod
    async def delete(
        self,
        table: str,
        filters: Dict
    ) -> QueryResult:
        """Delete rows matching filters."""
        pass
    
    @abstractmethod
    async def upsert(
        self,
        table: str,
        data: Union[Dict, List[Dict]],
        conflict_columns: List[str]
    ) -> QueryResult:
        """Insert or update on conflict."""
        pass
    
    # ==========================================
    # Time-Series Operations (for trade data)
    # ==========================================
    
    @abstractmethod
    async def insert_timeseries(
        self,
        table: str,
        timestamp_col: str,
        data: Union[Dict, List[Dict]]
    ) -> QueryResult:
        """Insert time-series data (optimized for TimescaleDB)."""
        pass
    
    @abstractmethod
    async def query_timeseries(
        self,
        table: str,
        timestamp_col: str,
        start_time: str,
        end_time: str,
        columns: Optional[List[str]] = None,
        resample: Optional[str] = None  # e.g., "1h", "1d"
    ) -> QueryResult:
        """Query time-series data with optional resampling."""
        pass
    
    # ==========================================
    # Full-Text Search
    # ==========================================
    
    @abstractmethod
    async def search(
        self,
        table: str,
        query: str,
        search_columns: List[str],
        limit: int = 50
    ) -> QueryResult:
        """Full-text search across columns."""
        pass
    
    # ==========================================
    # Schema Operations
    # ==========================================
    
    @abstractmethod
    async def table_exists(self, table: str) -> bool:
        """Check if table exists."""
        pass
    
    @abstractmethod
    async def create_table(self, table: str, schema: Dict[str, str]) -> bool:
        """Create table with schema. Key=column, Value=type."""
        pass


# ==========================================
# Provider Registry
# ==========================================

_db_instance: Optional[DatabaseInterface] = None


def get_db() -> DatabaseInterface:
    """
    Get database instance based on DB_PROVIDER env var.
    
    Supported providers:
    - supabase (default): Supabase Postgres
    - sqlite: Local SQLite
    - postgres: Self-hosted Postgres
    """
    global _db_instance
    
    if _db_instance is not None:
        return _db_instance
    
    provider = os.getenv("DB_PROVIDER", "supabase").lower()
    
    if provider == "supabase":
        from services.db.supabase_provider import SupabaseDB
        _db_instance = SupabaseDB()
    elif provider == "sqlite":
        from services.db.sqlite_provider import SQLiteDB
        _db_instance = SQLiteDB()
    elif provider == "postgres":
        from services.db.postgres_provider import PostgresDB
        _db_instance = PostgresDB()
    else:
        raise ValueError(f"Unknown DB_PROVIDER: {provider}")
    
    return _db_instance


async def reset_db() -> None:
    """Reset database instance (useful for testing)."""
    global _db_instance
    if _db_instance:
        await _db_instance.disconnect()
    _db_instance = None
