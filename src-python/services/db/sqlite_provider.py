"""
SQLite Database Provider

Local-first, embedded database for development and offline use.
Implements the DatabaseInterface for easy switching between providers.
"""

import os
import sqlite3
import json
from typing import Dict, List, Optional, Any, Union
from contextlib import contextmanager

from services.db.interface import DatabaseInterface, QueryResult


class SQLiteDB(DatabaseInterface):
    """
    SQLite implementation of DatabaseInterface.
    
    Great for:
    - Local development
    - Offline-first applications
    - Testing without cloud dependencies
    - Lightweight deployments
    """
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.getenv(
            "SQLITE_DB_PATH",
            os.path.join(os.path.dirname(__file__), "..", "..", "data", "auratic.db")
        )
        self._connection: Optional[sqlite3.Connection] = None
        
    @contextmanager
    def _conn(self):
        """Get database connection with row factory."""
        if self._connection is None:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            self._connection = sqlite3.connect(self.db_path)
            self._connection.row_factory = sqlite3.Row
        yield self._connection
    
    async def connect(self) -> bool:
        """Establish connection."""
        try:
            with self._conn() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception as e:
            return False
    
    async def disconnect(self) -> None:
        """Close connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    async def execute(self, query: str, params: Optional[Dict] = None) -> QueryResult:
        """Execute raw SQL."""
        try:
            with self._conn() as conn:
                cursor = conn.execute(query, params or {})
                rows = cursor.fetchall()
                conn.commit()
                return QueryResult(
                    data=[dict(row) for row in rows],
                    count=len(rows)
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
        if isinstance(data, dict):
            data = [data]
        
        if not data:
            return QueryResult(data=[], count=0)
        
        try:
            with self._conn() as conn:
                results = []
                for row in data:
                    cols = ", ".join(row.keys())
                    placeholders = ", ".join(["?" for _ in row])
                    query = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"
                    cursor = conn.execute(query, list(row.values()))
                    
                    if returning:
                        new_id = cursor.lastrowid
                        select_cols = ", ".join(returning)
                        cursor = conn.execute(
                            f"SELECT {select_cols} FROM {table} WHERE rowid = ?",
                            [new_id]
                        )
                        result_row = cursor.fetchone()
                        if result_row:
                            results.append(dict(result_row))
                
                conn.commit()
                return QueryResult(data=results, count=len(data))
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
        """Select with filtering, ordering, pagination."""
        try:
            cols = ", ".join(columns) if columns else "*"
            query = f"SELECT {cols} FROM {table}"
            params = []
            
            if filters:
                conditions = []
                for key, value in filters.items():
                    conditions.append(f"{key} = ?")
                    params.append(value)
                query += " WHERE " + " AND ".join(conditions)
            
            if order_by:
                query += f" ORDER BY {order_by}"
            if limit:
                query += f" LIMIT {limit}"
            if offset:
                query += f" OFFSET {offset}"
            
            with self._conn() as conn:
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                return QueryResult(
                    data=[dict(row) for row in rows],
                    count=len(rows)
                )
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
            set_clauses = ", ".join([f"{k} = ?" for k in data.keys()])
            where_clauses = " AND ".join([f"{k} = ?" for k in filters.keys()])
            
            query = f"UPDATE {table} SET {set_clauses} WHERE {where_clauses}"
            params = list(data.values()) + list(filters.values())
            
            with self._conn() as conn:
                cursor = conn.execute(query, params)
                conn.commit()
                return QueryResult(data=[], count=cursor.rowcount)
        except Exception as e:
            return QueryResult(data=[], count=0, error=str(e))
    
    async def delete(self, table: str, filters: Dict) -> QueryResult:
        """Delete rows matching filters."""
        try:
            where_clauses = " AND ".join([f"{k} = ?" for k in filters.keys()])
            query = f"DELETE FROM {table} WHERE {where_clauses}"
            
            with self._conn() as conn:
                cursor = conn.execute(query, list(filters.values()))
                conn.commit()
                return QueryResult(data=[], count=cursor.rowcount)
        except Exception as e:
            return QueryResult(data=[], count=0, error=str(e))
    
    async def upsert(
        self,
        table: str,
        data: Union[Dict, List[Dict]],
        conflict_columns: List[str]
    ) -> QueryResult:
        """Insert or update on conflict."""
        if isinstance(data, dict):
            data = [data]
        
        try:
            with self._conn() as conn:
                for row in data:
                    cols = ", ".join(row.keys())
                    placeholders = ", ".join(["?" for _ in row])
                    conflict_cols = ", ".join(conflict_columns)
                    
                    update_clause = ", ".join([
                        f"{k} = excluded.{k}" 
                        for k in row.keys() 
                        if k not in conflict_columns
                    ])
                    
                    query = f"""
                        INSERT INTO {table} ({cols}) VALUES ({placeholders})
                        ON CONFLICT({conflict_cols}) DO UPDATE SET {update_clause}
                    """
                    conn.execute(query, list(row.values()))
                
                conn.commit()
                return QueryResult(data=[], count=len(data))
        except Exception as e:
            return QueryResult(data=[], count=0, error=str(e))
    
    # ==========================================
    # Time-Series Operations
    # ==========================================
    
    async def insert_timeseries(
        self,
        table: str,
        timestamp_col: str,
        data: Union[Dict, List[Dict]]
    ) -> QueryResult:
        """Insert time-series data (standard insert for SQLite)."""
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
        """Query time-series data."""
        try:
            cols = ", ".join(columns) if columns else "*"
            query = f"""
                SELECT {cols} FROM {table}
                WHERE {timestamp_col} >= ? AND {timestamp_col} <= ?
                ORDER BY {timestamp_col}
            """
            
            with self._conn() as conn:
                cursor = conn.execute(query, [start_time, end_time])
                rows = cursor.fetchall()
                return QueryResult(
                    data=[dict(row) for row in rows],
                    count=len(rows)
                )
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
        """Full-text search using LIKE (basic, no FTS5 required)."""
        try:
            conditions = " OR ".join([f"{col} LIKE ?" for col in search_columns])
            pattern = f"%{query}%"
            params = [pattern] * len(search_columns)
            
            sql = f"SELECT * FROM {table} WHERE {conditions} LIMIT {limit}"
            
            with self._conn() as conn:
                cursor = conn.execute(sql, params)
                rows = cursor.fetchall()
                return QueryResult(
                    data=[dict(row) for row in rows],
                    count=len(rows)
                )
        except Exception as e:
            return QueryResult(data=[], count=0, error=str(e))
    
    # ==========================================
    # Schema Operations
    # ==========================================
    
    async def table_exists(self, table: str) -> bool:
        """Check if table exists."""
        try:
            with self._conn() as conn:
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    [table]
                )
                return cursor.fetchone() is not None
        except:
            return False
    
    async def create_table(self, table: str, schema: Dict[str, str]) -> bool:
        """Create table with schema."""
        try:
            cols = ", ".join([f"{k} {v}" for k, v in schema.items()])
            query = f"CREATE TABLE IF NOT EXISTS {table} ({cols})"
            
            with self._conn() as conn:
                conn.execute(query)
                conn.commit()
            return True
        except:
            return False
