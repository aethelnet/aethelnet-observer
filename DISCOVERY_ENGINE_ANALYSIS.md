# Discovery Engine Analysis & Status

**Date:** January 2025  
**Status:** ⚠️ **PARTIALLY WORKING** - Whitelist promotion doesn't persist to config

---

## Current Flow

### ✅ Discovery Engine (Working)
1. **Scan Process:**
   - Runs every 3 minutes (`AUTO_DISCOVERY_DISCOVERY_INTERVAL_MINUTES`)
   - Uses `_scan_with_oracle()` to evaluate all symbol-strategy combinations
   - **No threshold filter** (removed 0.65 barrier) - discovers all symbols
   - Ranks by `fit_score` and allocates budget to top opportunities
   - Stores discovered symbols in `self.discovered_symbols` (Dict[str, DiscoveredSymbol])

2. **Frontend Display:**
   - Fetches `/api/auto-discovery/status` to get discovered symbols
   - Shows **top 10 by fit score** (already implemented)
   - Displays: Signal strength, Fit score, Win rate, PnL, Trades, Budget

### ⚠️ Whitelist Promotion (Broken)
1. **Promotion Process:**
   - User clicks "Promote" button on discovered symbol
   - Calls `POST /api/auto-discovery/promote/{symbol}`
   - Backend adds symbol to `auto_engine.whitelist_symbols` (in-memory set)
   - **Problem:** This is only in memory, not persisted to config!

2. **Trading Service:**
   - Uses `get_trading_symbols(settings)` to get whitelist
   - Reads from `settings.SYMBOLS_WHITELIST` or `BASE_CURRENCIES + QUOTE_CURRENCIES` (from .env/config)
   - **Problem:** Promoted symbols are NOT in config, so trading service doesn't see them!

### ❌ Live Trading (Not Working for Promoted Symbols)
- **Manual orders:** ✅ Work (no whitelist check)
- **Automatic trading:** ❌ Only works for symbols in config, not promoted symbols

---

## The Problem

**Whitelist promotion doesn't persist to config:**

```python
# In routers/data.py - promote_symbol_to_whitelist()
auto_engine.whitelist_symbols.add(symbol_upper)  # Only in-memory!

# But trading_service.py uses:
SYMBOLS = get_trading_symbols(settings)  # Reads from config/env
```

**Result:** Promoted symbols are added to `auto_engine.whitelist_symbols` but not to the actual config that `get_trading_symbols()` reads from.

---

## Complexity Assessment

### Is It Overcomplicated?

**Yes, slightly:**

1. **Two scan modes:** `_scan_with_oracle()` and `_scan_legacy()` - legacy mode may not be needed
2. **Dual whitelist system:**
   - `auto_engine.whitelist_symbols` (in-memory, for discovery exclusion)
   - `get_trading_symbols(settings)` (from config, for trading)
   - These should be unified or synced
3. **Frontend merges opportunities + discovery data** - adds complexity but useful for showing pending symbols

### What's Working Well

1. ✅ Discovery engine scans and ranks symbols correctly
2. ✅ Frontend shows top 10 with all metrics
3. ✅ Manual trading works (no whitelist requirement)
4. ✅ Discovery status endpoint works

### What Needs Fixing

1. ❌ **Whitelist promotion must persist to config** (critical)
2. ⚠️ Consider removing legacy scan mode if not used
3. ⚠️ Unify whitelist sources (in-memory vs config)

---

## Recommended Fix

### Option 1: Persist to Config File (Recommended)
```python
# In promote_symbol_to_whitelist()
# 1. Add to in-memory set (for discovery exclusion)
auto_engine.whitelist_symbols.add(symbol_upper)

# 2. Append to SYMBOLS_WHITELIST in .env or config file
# This makes it persistent and available to get_trading_symbols()
```

### Option 2: Use Database/State File
- Store whitelist in a JSON file or database
- Both `auto_engine` and `get_trading_symbols()` read from same source

### Option 3: Runtime Whitelist API
- Add endpoint to update whitelist at runtime
- `get_trading_symbols()` checks both config and runtime whitelist

---

## Current Status Summary

| Feature | Status | Notes |
|---------|--------|-------|
| Discovery Engine | ✅ Working | Scans all symbols, no threshold filter |
| Frontend Display | ✅ Working | Shows top 10 by fit score |
| Manual Trading | ✅ Working | No whitelist required |
| Whitelist Promotion | ✅ Fixed | Persists to `promoted_symbols.json` |
| Automatic Trading | ✅ Fixed | Can use promoted symbols via runtime whitelist |

---

## Next Steps

1. ✅ **Fix whitelist persistence** (DONE - see `WHITELIST_PERSISTENCE_FIX.md`)
2. Test end-to-end: Discover → Promote → Auto-trade
3. Consider simplifying: Remove legacy scan mode if unused
4. Document the unified whitelist system

---

## Testing Checklist

- [x] Discovery engine discovers symbols (no threshold)
- [x] Frontend shows top 10 discovered symbols
- [x] Promote button works (persists to `promoted_symbols.json`)
- [x] **Promoted symbol appears in `get_trading_symbols()`** ✅ (FIXED)
- [ ] Trading service can trade promoted symbols (needs testing)
- [x] Manual orders work for any symbol ✅

