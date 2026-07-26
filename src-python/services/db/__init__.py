"""
Database Module - Vendor-Agnostic Database Access

Switch between Supabase, SQLite, or self-hosted Postgres
via a single environment variable: DB_PROVIDER

Usage:
    from services.db import get_db
    
    db = get_db()
    result = await db.select("users", filters={"id": "123"})
"""

from services.db.interface import (
    DatabaseInterface,
    QueryResult,
    get_db,
    reset_db
)

__all__ = [
    "DatabaseInterface",
    "QueryResult", 
    "get_db",
    "reset_db"
]
