"""
Macro Events Database Schema and Backfill
Creates the macro_events table and populates historical data.
"""
import sqlite3
import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger("MacroEventsDB")


def get_db_path() -> str:
    """Get the database path."""
    # Try environment variable first
    db_path = os.getenv("DATA_DIR", "")
    if db_path:
        return os.path.join(db_path, "market_data.db")
    
    # Fallback to project root
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, "market_data.db")


def init_macro_events_table(db_path: Optional[str] = None):
    """
    Create the macro_events table if it doesn't exist.
    Also extends market_episodes with macro columns.
    """
    if db_path is None:
        db_path = get_db_path()
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create macro_events table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS macro_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            country TEXT,
            timestamp INTEGER NOT NULL,
            date_str TEXT,
            time_str TEXT,
            impact TEXT,
            sector TEXT,
            forecast_ff REAL,
            forecast_inv REAL,
            actual REAL,
            previous REAL,
            consensus_forecast REAL,
            forecast_divergence REAL,
            surprise REAL,
            source_count INTEGER DEFAULT 1,
            created_at INTEGER DEFAULT (strftime('%s', 'now')),
            UNIQUE(title, timestamp, country)
        )
    """)
    
    # Create index for fast lookups
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_macro_events_timestamp 
        ON macro_events(timestamp)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_macro_events_country 
        ON macro_events(country)
    """)
    
    # Extend market_episodes if table exists
    try:
        cursor.execute("SELECT macro_event_id FROM market_episodes LIMIT 1")
    except sqlite3.OperationalError:
        # Column doesn't exist, try to add it
        try:
            cursor.execute("ALTER TABLE market_episodes ADD COLUMN macro_event_id INTEGER")
            logger.info("Added macro_event_id to market_episodes")
        except:
            pass
            
    try:
        cursor.execute("SELECT macro_surprise FROM market_episodes LIMIT 1")
    except sqlite3.OperationalError:
        try:
            cursor.execute("ALTER TABLE market_episodes ADD COLUMN macro_surprise REAL")
            logger.info("Added macro_surprise to market_episodes")
        except:
            pass
            
    try:
        cursor.execute("SELECT forecast_divergence FROM market_episodes LIMIT 1")
    except sqlite3.OperationalError:
        try:
            cursor.execute("ALTER TABLE market_episodes ADD COLUMN forecast_divergence REAL")
            logger.info("Added forecast_divergence to market_episodes")
        except:
            pass
    
    conn.commit()
    conn.close()
    
    logger.info(f"[MACRO] Database initialized: {db_path}")


def insert_event(event: dict, db_path: Optional[str] = None):
    """Insert a single event into macro_events."""
    if db_path is None:
        db_path = get_db_path()
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO macro_events 
            (title, country, timestamp, date_str, time_str, impact, sector,
             forecast_ff, forecast_inv, actual, previous, consensus_forecast,
             forecast_divergence, surprise, source_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event.get('title', ''),
            event.get('country', ''),
            event.get('timestamp', 0),
            event.get('date', ''),
            event.get('time', ''),
            event.get('impact', 'Low'),
            event.get('sector', 'MACRO'),
            event.get('forecast_ff'),
            event.get('forecast_inv'),
            _parse_float(event.get('actual')),
            _parse_float(event.get('previous')),
            event.get('consensus_forecast'),
            event.get('forecast_divergence', 0.0),
            event.get('surprise'),
            event.get('source_count', 1)
        ))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # Duplicate
    finally:
        conn.close()


def _parse_float(value) -> Optional[float]:
    """Parse value to float."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        value = value.strip().upper()
        if value in ['', 'N/A', '-']:
            return None
        # Handle suffixes
        multiplier = 1.0
        if value.endswith('%'):
            value = value[:-1]
        elif value.endswith('K'):
            value = value[:-1]
            multiplier = 1000
        elif value.endswith('M'):
            value = value[:-1]
            multiplier = 1_000_000
        try:
            return float(value.replace(',', '')) * multiplier
        except ValueError:
            return None
    return None


def link_episodes_to_events(db_path: Optional[str] = None, window_seconds: int = 3600):
    """
    Link market_episodes to nearby macro_events.
    Each episode gets the closest macro event within the time window.
    """
    if db_path is None:
        db_path = get_db_path()
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all episodes without macro_event_id
    cursor.execute("""
        SELECT id, timestamp FROM market_episodes 
        WHERE macro_event_id IS NULL
        ORDER BY timestamp
    """)
    episodes = cursor.fetchall()
    
    updated = 0
    for ep_id, ep_ts in episodes:
        # Find closest high-impact event
        cursor.execute("""
            SELECT id, surprise, forecast_divergence 
            FROM macro_events 
            WHERE ABS(timestamp - ?) < ?
              AND impact IN ('High', 'Medium')
            ORDER BY ABS(timestamp - ?)
            LIMIT 1
        """, (ep_ts, window_seconds, ep_ts))
        
        result = cursor.fetchone()
        if result:
            event_id, surprise, divergence = result
            cursor.execute("""
                UPDATE market_episodes 
                SET macro_event_id = ?, macro_surprise = ?, forecast_divergence = ?
                WHERE id = ?
            """, (event_id, surprise, divergence, ep_id))
            updated += 1
    
    conn.commit()
    conn.close()
    
    logger.info(f"[MACRO] Linked {updated} episodes to events")
    return updated


async def backfill_from_hydra(db_path: Optional[str] = None):
    """
    Fetch events from Hydra and populate macro_events table.
    """
    from services.event_hydra import get_event_hydra
    
    if db_path is None:
        db_path = get_db_path()
    
    # Ensure table exists
    init_macro_events_table(db_path)
    
    hydra = get_event_hydra()
    events = await hydra.fetch_all()
    
    logger.info(f"[MACRO] Backfilling {len(events)} events from Hydra")
    
    for event in events:
        insert_event(event, db_path)
    
    # Link episodes
    link_episodes_to_events(db_path)
    
    return len(events)


def get_event_for_timestamp(timestamp: int, db_path: Optional[str] = None) -> Optional[dict]:
    """
    Get the closest macro event for a given timestamp.
    Returns event dict or None.
    """
    if db_path is None:
        db_path = get_db_path()
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, title, country, timestamp, impact, surprise, 
               consensus_forecast, forecast_divergence
        FROM macro_events 
        WHERE ABS(timestamp - ?) < 3600
        ORDER BY ABS(timestamp - ?)
        LIMIT 1
    """, (timestamp, timestamp))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            'id': result[0],
            'title': result[1],
            'country': result[2],
            'timestamp': result[3],
            'impact': result[4],
            'surprise': result[5],
            'consensus_forecast': result[6],
            'forecast_divergence': result[7]
        }
    return None


# CLI
if __name__ == "__main__":
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) > 1 and sys.argv[1] == "init":
        init_macro_events_table()
        print("Database initialized.")
    elif len(sys.argv) > 1 and sys.argv[1] == "backfill":
        count = asyncio.run(backfill_from_hydra())
        print(f"Backfilled {count} events.")
    elif len(sys.argv) > 1 and sys.argv[1] == "link":
        count = link_episodes_to_events()
        print(f"Linked {count} episodes.")
    else:
        print("Usage: python macro_events_db.py [init|backfill|link]")
