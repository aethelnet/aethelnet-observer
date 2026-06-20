# Database Connection Error Fix

**Error**: `sqlite3.OperationalError: unable to open database file`

**Location**: `/var/home/nhrlyn/Projects/Backup/auratic-systems-prime/backend/services/database.py:63`

---

## Root Cause

The `get_database()` function uses a relative path `"market_data.db"` by default, which fails if:
1. The backend is run from a different working directory
2. The directory doesn't have write permissions
3. The path resolution fails

**Current Code** (`database.py:847`):
```python
def get_database(db_path: str = "market_data.db") -> Database:
    """Get the global database instance (singleton)."""
    global _database_instance
    if _database_instance is None:
        with _database_lock:
            if _database_instance is None:
                _database_instance = Database(db_path)  # Uses relative path!
                logger.info("Database singleton initialized")
    return _database_instance
```

**Settings has DB_PATH** (`config/settings.py:22`):
```python
DB_PATH: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "market_data.db")
```

But `get_database()` doesn't use it!

---

## Solution

### Option 1: Use Settings DB_PATH (Recommended)

**File**: `/var/home/nhrlyn/Projects/Backup/auratic-systems-prime/backend/services/database.py`

**Change** (line 847):
```python
def get_database(db_path: Optional[str] = None) -> Database:
    """Get the global database instance (singleton)."""
    global _database_instance
    if _database_instance is None:
        with _database_lock:
            if _database_instance is None:
                # Use DB_PATH from settings if not provided
                if db_path is None:
                    from backend.config import get_settings
                    settings = get_settings()
                    db_path = settings.DB_PATH
                _database_instance = Database(db_path)
                logger.info(f"Database singleton initialized at {db_path}")
    return _database_instance
```

### Option 2: Update main.py to Pass DB_PATH

**File**: `/var/home/nhrlyn/Projects/Backup/auratic-systems-prime/backend/main.py`

**Change** (around line 289):
```python
from backend.config import get_settings
settings = get_settings()
db = get_database(settings.DB_PATH)
```

### Option 3: Make Database Use Absolute Path

**File**: `/var/home/nhrlyn/Projects/Backup/auratic-systems-prime/backend/services/database.py`

**Change** (line 35-36):
```python
def __init__(self, db_path: str = "market_data.db"):
    # Convert to absolute path if relative
    if not os.path.isabs(db_path):
        # If relative, resolve from project root
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        db_path = os.path.join(project_root, db_path)
    self.db_path = db_path
```

---

## Verification

After applying the fix:

1. **Check database path**:
```python
from backend.services.database import get_database
db = get_database()
print(f"Database path: {db.db_path}")
print(f"Path exists: {os.path.exists(db.db_path)}")
print(f"Path is absolute: {os.path.isabs(db.db_path)}")
```

2. **Test connection**:
```python
from backend.services.database import get_database
db = get_database()
# Should not raise error
conn = db._connect()
print("Connection successful!")
```

3. **Check permissions**:
```bash
ls -la /var/home/nhrlyn/Projects/Backup/auratic-systems-prime/market_data.db
# Should show: -rw-r--r-- (read/write for owner)
```

---

## Current Database Files

Found multiple database files:
- `/var/home/nhrlyn/Projects/Backup/auratic-systems-prime/market_data.db` (8.3 GB) ✅
- `/var/home/nhrlyn/Projects/Backup/auratic-systems-prime/backend/market_data.db` (19 MB)

The main database is at the project root, so the fix should use that path.

---

## Recommended Implementation

**Use Option 1** - It's the cleanest and ensures consistency:

1. Update `get_database()` to use `settings.DB_PATH` by default
2. This ensures the database always uses the correct absolute path
3. No need to change call sites throughout the codebase

**Code Change**:
```python
def get_database(db_path: Optional[str] = None) -> Database:
    """Get the global database instance (singleton)."""
    global _database_instance
    if _database_instance is None:
        with _database_lock:
            if _database_instance is None:
                # Use DB_PATH from settings if not provided
                if db_path is None:
                    try:
                        from backend.config import get_settings
                        settings = get_settings()
                        db_path = settings.DB_PATH
                    except Exception as e:
                        logger.warning(f"Could not load DB_PATH from settings: {e}, using default")
                        db_path = "market_data.db"
                _database_instance = Database(db_path)
                logger.info(f"Database singleton initialized at {db_path}")
    return _database_instance
```

---

## Status

- ✅ Database file exists at project root
- ✅ File has correct permissions
- ❌ Code uses relative path instead of absolute
- ❌ Settings.DB_PATH is defined but not used

**Fix Required**: Update `get_database()` to use `settings.DB_PATH`





