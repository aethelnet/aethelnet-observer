# Whitelist Persistence Fix

**Date:** January 2025  
**Status:** ✅ **IMPLEMENTED**

---

## Problem

Whitelist promotion didn't persist to config, so promoted symbols weren't available to `get_trading_symbols()` for automatic trading.

**Root Cause:**
- Promotion endpoint added symbols to `auto_engine.whitelist_symbols` (in-memory only)
- `get_trading_symbols()` reads from `settings.SYMBOLS_WHITELIST` or `BASE_CURRENCIES + QUOTE_CURRENCIES` (from .env/config)
- Promoted symbols were never written to config, so trading service couldn't see them

---

## Solution

Implemented a runtime whitelist system that persists promoted symbols to `promoted_symbols.json` and integrates with `get_trading_symbols()`.

---

## Changes Made

### 1. Runtime Whitelist Functions (`backend/config/settings.py`)

✅ **Already implemented** - Functions to manage a runtime whitelist file:

- `get_runtime_whitelist()` - Reads promoted symbols from `promoted_symbols.json`
- `add_to_runtime_whitelist(symbol)` - Adds symbol to runtime whitelist file
- `remove_from_runtime_whitelist(symbol)` - Removes symbol from runtime whitelist file
- `_get_runtime_whitelist_path()` - Returns path to `promoted_symbols.json` in project root

### 2. Updated `get_trading_symbols()` (`backend/config/settings.py`)

✅ **Already implemented** - Now includes promoted symbols from runtime whitelist:

```python
def get_trading_symbols(settings: Settings) -> List[str]:
    # ... get base symbols from config ...
    
    # Get promoted symbols from runtime whitelist
    promoted_symbols = get_runtime_whitelist()
    
    # Combine base symbols with promoted symbols
    # (preserves order, removes duplicates)
    result = list(base_symbols)
    for symbol in sorted(promoted_symbols):
        if symbol not in seen:
            result.append(symbol)
    
    return result
```

**Result**: Promoted symbols are now available to the trading service! ✅

### 3. Updated Promotion Endpoint (`backend/routers/data.py`)

✅ **Updated** - `POST /api/auto-discovery/promote/{symbol}` now:
- Adds symbol to runtime whitelist (persists to `promoted_symbols.json`)
- Adds symbol to in-memory whitelist (for discovery exclusion)
- Removes symbol from discovered symbols
- Returns confirmation that symbol is persisted

**Changes:**
```python
# Add to runtime whitelist (persists to promoted_symbols.json)
from backend.config.settings import add_to_runtime_whitelist
persisted = add_to_runtime_whitelist(symbol_upper)

# Add to in-memory whitelist (for discovery exclusion)
auto_engine.whitelist_symbols.add(symbol_upper)
```

### 4. Updated Remove Endpoint (`backend/routers/data.py`)

✅ **Updated** - `POST /api/auto-discovery/remove/{symbol}` now:
- Removes from discovered symbols
- Removes from in-memory whitelist
- **Removes from runtime whitelist** (persists removal)

**Changes:**
```python
# Remove from runtime whitelist (persists removal)
from backend.config.settings import remove_from_runtime_whitelist
runtime_removed = remove_from_runtime_whitelist(symbol_upper)
```

### 5. Auto-Discovery Engine (`backend/services/auto_discovery_engine.py`)

✅ **Already correct** - Initializes whitelist from `get_trading_symbols()` (includes promoted symbols):

```python
# Initialize whitelist symbols
from backend.config.settings import get_trading_symbols
self.whitelist_symbols = set(get_trading_symbols(self.settings))
```

This ensures the engine stays in sync with runtime whitelist on startup.

---

## File Structure

```
project_root/
  ├── .env                          # Base config (BASE_CURRENCIES, etc.)
  ├── promoted_symbols.json         # Runtime whitelist (promoted symbols)
  └── backend/
      ├── config/
      │   └── settings.py           # get_trading_symbols() reads both
      └── routers/
          └── data.py               # Promotion/remove endpoints
```

---

## How It Works

### Promotion Flow

1. User clicks "Promote" on discovered symbol
2. `POST /api/auto-discovery/promote/{symbol}` called
3. Symbol added to `promoted_symbols.json` ✅
4. Symbol added to in-memory whitelist (excluded from discovery)
5. Symbol removed from discovered symbols
6. **Symbol now available to `get_trading_symbols()`** ✅

### Trading Service Flow

1. `trading_service.py` calls `get_trading_symbols(settings)`
2. `get_trading_symbols()` reads:
   - Base symbols from config (BASE_CURRENCIES + QUOTE_CURRENCIES or SYMBOLS_WHITELIST)
   - Promoted symbols from `promoted_symbols.json`
3. Returns combined list (base + promoted, deduplicated)
4. Trading service can now trade promoted symbols! ✅

---

## Runtime Whitelist File Format

```json
{
  "symbols": [
    "BTCUSDC",
    "ETHUSDC"
  ],
  "updated_at": null
}
```

**Location:** `promoted_symbols.json` in project root

---

## Testing

### Test Promotion Persistence

```bash
# 1. Promote a symbol
curl -X POST http://localhost:8000/api/auto-discovery/promote/BTCUSDC

# 2. Check runtime whitelist file
cat promoted_symbols.json

# 3. Verify it's in get_trading_symbols()
# (Check via trading config endpoint if available, or check logs)
```

### Test End-to-End

1. **Discover symbol**: Wait for auto-discovery to find a symbol
2. **Promote symbol**: Click "Promote" or use API
3. **Verify in config**: Check `get_trading_symbols()` includes it
4. **Trading service**: Should now be able to trade it automatically

### Test Removal

```bash
# Remove a promoted symbol
curl -X POST http://localhost:8000/api/auto-discovery/remove/BTCUSDC

# Verify it's removed from promoted_symbols.json
cat promoted_symbols.json
```

---

## Benefits

1. ✅ **Persistent**: Promoted symbols survive backend restarts
2. ✅ **Non-intrusive**: Doesn't modify `.env` file
3. ✅ **Works with any config format**: BASE_CURRENCIES/QUOTE_CURRENCIES or SYMBOLS_WHITELIST
4. ✅ **Deduplicated**: `get_trading_symbols()` handles duplicates
5. ✅ **Reversible**: Can remove symbols via remove endpoint

---

## Migration Notes

- Existing promoted symbols (in-memory only) won't be in runtime whitelist
- Users need to re-promote symbols after this update
- Or manually add to `promoted_symbols.json`:
  ```json
  {
    "symbols": ["SYMBOL1", "SYMBOL2"]
  }
  ```

---

## Status

✅ **FIXED**: Whitelist promotion now persists to config and is available to trading service!

**Summary:**
- ✅ Runtime whitelist functions implemented
- ✅ `get_trading_symbols()` includes promoted symbols
- ✅ Promotion endpoint persists to `promoted_symbols.json`
- ✅ Remove endpoint removes from `promoted_symbols.json`
- ✅ Auto-discovery engine syncs on startup

**Result:** Promoted symbols are now available for automatic trading! 🎉


