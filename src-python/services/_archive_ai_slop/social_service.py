"""
SocialService: The 'Graffiti Wall' of the Bot.
Handles user comments (Yarns) and Reactions.
Now supports PostgreSQL for Cloud Persistence.
"""
import sqlite3
import logging
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Optional
from datetime import datetime
import time 
from config import get_settings

logger = logging.getLogger("SocialService")

class SocialService:
    DB_PATH = "social.db"
    
    def __init__(self):
        self.settings = get_settings()
        self.is_postgres = bool(getattr(self.settings, "DATABASE_URL", None))
        self._init_db()
        self._yarn_cache = {} # symbol -> {admin: dict, users: list, ts: float}
        self._cache_ttl = 10.0 # 10 seconds cache for yarns
        
    def _get_conn(self):
        if self.is_postgres:
            return psycopg2.connect(self.settings.DATABASE_URL, cursor_factory=RealDictCursor)
        else:
            conn = sqlite3.connect(self.DB_PATH, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            return conn

    def _init_db(self):
        try:
            conn = self._get_conn()
            c = conn.cursor()
            
            if self.is_postgres:
                # PostgreSQL Schema
                c.execute("""
                    CREATE TABLE IF NOT EXISTS comments (
                        id SERIAL PRIMARY KEY,
                        symbol TEXT NOT NULL,
                        user_id BIGINT,
                        username TEXT,
                        text TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                c.execute("""
                    CREATE TABLE IF NOT EXISTS sentiments (
                        user_id BIGINT,
                        symbol TEXT,
                        reaction TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (user_id, symbol)
                    );
                """)
            else:
                # SQLite Schema
                c.execute('''
                    CREATE TABLE IF NOT EXISTS comments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        user_id INTEGER,
                        username TEXT,
                        text TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                c.execute('''
                    CREATE TABLE IF NOT EXISTS sentiments (
                        user_id INTEGER,
                        symbol TEXT,
                        reaction TEXT, -- 'BULL', 'BEAR', 'MOON', 'DOOM'
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (user_id, symbol)
                    )
                ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"SocialDB Init Error: {e}")

    def post_yarn(self, symbol: str, user_id: int, username: str, text: str):
        """Post a comment (Yarn)"""
        try:
            conn = self._get_conn()
            c = conn.cursor()
            symbol = symbol.upper().replace("/", "")
            
            query = "INSERT INTO comments (symbol, user_id, username, text) VALUES (%s, %s, %s, %s)" if self.is_postgres else \
                    "INSERT INTO comments (symbol, user_id, username, text) VALUES (?, ?, ?, ?)"
            
            c.execute(query, (symbol, user_id, username, text))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Post Yarn Error: {e}")
            return False

    def get_yarns(self, symbol: str = None, limit: int = 5) -> tuple[Optional[Dict], List[Dict]]:
        """
        Get latest yarns (with short-lived cache).
        Returns: (admin_yarn, user_yarns)
        """
        # 1. Check Cache
        cache_key = symbol or "GLOBAL"
        if cache_key in self._yarn_cache:
            entry = self._yarn_cache[cache_key]
            if time.time() - entry["ts"] < self._cache_ttl:
                return entry["admin"], entry["users"]

        return self._fetch_yarns_from_db(symbol, limit)

    def _fetch_yarns_from_db(self, symbol: str = None, limit: int = 5) -> tuple[Optional[Dict], List[Dict]]:
        """Raw DB fetch logic."""
        try:
            conn = self._get_conn()
            c = conn.cursor()
            
            placeholder = "%s" if self.is_postgres else "?"
            
            # Get Admin ID
            admin_id_str = getattr(self.settings, "TELEGRAM_CHAT_ID", "0")
            try:
                admin_id = int(admin_id_str)
            except:
                admin_id = 0

            admin_yarn = None
            user_yarns = []

            if symbol:
                symbol = symbol.upper().replace("/", "")
                
                # 1. Get Latest Admin Yarn
                q_admin = f"SELECT * FROM comments WHERE symbol = {placeholder} AND user_id = {placeholder} ORDER BY id DESC LIMIT 1"
                c.execute(q_admin, (symbol, admin_id))
                row = c.fetchone()
                if row:
                    # Convert to dict
                    admin_yarn = dict(row) if self.is_postgres else dict(row)

                # 2. Get User Yarns (exclude admin)
                q_users = f"SELECT * FROM comments WHERE symbol = {placeholder} AND user_id != {placeholder} ORDER BY id DESC LIMIT {placeholder}"
                c.execute(q_users, (symbol, admin_id, limit))
                rows = c.fetchall()
                # Reverse for chronological order
                user_yarns = [dict(r) for r in rows][::-1]

            else:
                # Global Feed
                
                # 1. Get Latest Admin Yarn Global
                q_admin = f"SELECT * FROM comments WHERE user_id = {placeholder} ORDER BY id DESC LIMIT 1"
                c.execute(q_admin, (admin_id,))
                row = c.fetchone()
                if row:
                     admin_yarn = dict(row)

                # 2. Get User Yarns Global
                q_users = f"SELECT * FROM comments WHERE user_id != {placeholder} ORDER BY id DESC LIMIT {placeholder}"
                c.execute(q_users, (admin_id, limit))
                rows = c.fetchall()
                user_yarns = [dict(r) for r in rows][::-1]
                
            conn.close()
            
            # Update Cache (Short-lived 10s)
            self._yarn_cache[symbol or "GLOBAL"] = {
                "admin": admin_yarn,
                "users": user_yarns,
                "ts": time.time()
            }
            
            return admin_yarn, user_yarns

        except Exception as e:
            logger.error(f"Get Yarns Error: {e}")
            return None, []

    def get_top_yarns_global(self, limit: int = 3, exclude_symbol: str = None) -> List[Dict]:
        """Get top yarns across all symbols"""
        try:
            conn = self._get_conn()
            c = conn.cursor()
            placeholder = "%s" if self.is_postgres else "?"
            
            if exclude_symbol:
                exclude_symbol = exclude_symbol.upper().replace("/", "")
                query = f"""
                    SELECT * FROM comments 
                    WHERE symbol != {placeholder} 
                    ORDER BY id DESC 
                    LIMIT {placeholder}
                """
                c.execute(query, (exclude_symbol, limit))
            else:
                query = f"SELECT * FROM comments ORDER BY id DESC LIMIT {placeholder}"
                c.execute(query, (limit,))
            
            rows = c.fetchall()
            conn.close()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Get Top Yarns Global Error: {e}")
            return []

    def set_sentiment(self, user_id: int, symbol: str, reaction: str):
        """Set user sentiment for a symbol"""
        try:
            conn = self._get_conn()
            c = conn.cursor()
            symbol = symbol.upper().replace("/", "")
            
            if self.is_postgres:
                # PostgreSQL Upsert
                query = """
                    INSERT INTO sentiments (user_id, symbol, reaction, updated_at) 
                    VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT(user_id, symbol) 
                    DO UPDATE SET reaction=EXCLUDED.reaction, updated_at=CURRENT_TIMESTAMP
                """
            else:
                # SQLite Upsert
                query = """
                    INSERT INTO sentiments (user_id, symbol, reaction, updated_at) 
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(user_id, symbol) DO UPDATE SET reaction=excluded.reaction, updated_at=CURRENT_TIMESTAMP
                """

            c.execute(query, (user_id, symbol, reaction))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Set Sentiment Error: {e}")
            return False

    def get_sentiment_counts(self, symbol: str) -> Dict[str, int]:
        """Get reaction counts"""
        try:
            conn = self._get_conn()
            c = conn.cursor()
            symbol = symbol.upper().replace("/", "")
            
            placeholder = "%s" if self.is_postgres else "?"
            query = f"SELECT reaction, COUNT(*) as count FROM sentiments WHERE symbol = {placeholder} GROUP BY reaction"
            
            c.execute(query, (symbol,))
            rows = c.fetchall()
            conn.close()
            
            # Handle different return formats
            if self.is_postgres:
                 # RealDictCursor returns [{'reaction': 'UPVOTE', 'count': 5}, ...]
                 return {row['reaction']: row['count'] for row in rows}
            else:
                 # sqlite3.Row returns tuple-like access by column name or index
                 # But previous implementation relied on index r[0], r[1]
                 return {r[0]: r[1] for r in rows}
                 
        except Exception as e:
            logger.error(f"Sentiment Count Error: {e}")
            return {}

    def get_karma(self, symbol: str) -> int:
        """Get net sentiment score (Upvotes - Downvotes)"""
        try:
            counts = self.get_sentiment_counts(symbol)
            return counts.get('UPVOTE', 0) - counts.get('DOWNVOTE', 0)
        except:
            return 0

# Singleton
_social_instance = None
def get_social_service():
    global _social_instance
    if _social_instance is None:
        _social_instance = SocialService()
    return _social_instance
