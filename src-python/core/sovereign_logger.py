import logging
import sqlite3
import os
import json
from datetime import datetime

# AURATIC SYSTEMS - SOVEREIGN SQLITE LOGGER
# Pipes standard Python logs into the Market Manifold for Superset Visualization

class SQLiteHandler(logging.Handler):
    def __init__(self, db_path):
        super().__init__()
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Ensures the debug_logs table exists."""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        try:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS debug_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    level TEXT,
                    module TEXT,
                    message TEXT,
                    exception TEXT,
                    process_id INTEGER,
                    thread_id INTEGER
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def emit(self, record):
        """Inserts a log record into the database."""
        try:
            msg = self.format(record)
            level = record.levelname
            module = record.name
            process_id = record.process
            thread_id = record.thread
            
            exception = ""
            if record.exc_info:
                exception = logging.Formatter().formatException(record.exc_info)

            conn = sqlite3.connect(self.db_path, timeout=30.0)
            try:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO debug_logs (level, module, message, exception, process_id, thread_id) VALUES (?, ?, ?, ?, ?, ?)",
                    (level, module, msg, exception, process_id, thread_id)
                )
                conn.commit()
            finally:
                conn.close()
        except Exception:
            self.handleError(record)

def add_sovereign_handler(logger_name="AuraticBackend", db_path="market_data.db"):
    """Attaches the SQLiteHandler to the specified logger."""
    logger = logging.getLogger(logger_name)
    handler = SQLiteHandler(db_path)
    # Use a simpler format for DB storage as fields are separated
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return handler
