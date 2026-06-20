# Backend Whitelist Logic Verification Guide

**Date:** January 2025  
**Status:** ✅ **IMPLEMENTED**  
**Purpose:** Verify that whitelist requirements are correctly applied only to automatic trading, not manual trading

---

## Overview

The whitelist system controls **automatic trading** only. **Manual trading** (user-initiated orders from opportunities) works for any symbol, regardless of whitelist status.

---

## Core Principle

**Whitelist = Automatic Trading Control**  
**Manual Trading = No Whitelist Requirement**

---

## Expected Behavior

### ✅ Manual Order Placement (Should Work)

**Endpoint:** `POST /api/opportunities/place-order`

**Behavior:**
- ✅ Accepts orders for **any symbol** that has an opportunity
- ✅ **Does NOT** check whitelist status when `auto_execute=false` (default)
- ✅ Works even if symbol is not whitelisted
- ✅ No discovery system requirement

**Implementation Location:**
- File: `backend/api/predictions.py`
- Function: `place_opportunity_order_by_data()`
- Lines: ~1004-1012

**Code:**
```python
# Check whitelist ONLY for automatic trading
if auto_execute:
    from backend.config.settings import get_trading_symbols
    whitelist_symbols = set(get_trading_symbols(settings))
    symbol_upper = symbol.upper()
    
    if symbol_upper not in whitelist_symbols:
        raise HTTPException(
            status_code=400,
            detail=f"Symbol {symbol} must be whitelisted for automatic trading. "
                   f"Please whitelist the symbol first or place the order manually (without auto_execute=true)."
        )
```

**Test Case:**
```bash
# Place order for non-whitelisted symbol
curl -X POST http://127.0.0.1:8000/api/opportunities/place-order \
  -H "Content-Type: application/json" \
  -d '{
    "id": "opp_test_manual",
    "symbol": "BTCEUR",
    "opportunity_type": "SELL",
    "current_price": 75194.41,
    "target_price": 71810.66,
    "stop_loss": 76698.3,
    "quantity": 0.0001,
    "position_value": 7.5,
    "confidence": 0.9,
    "risk_reward_ratio": 2.25
  }'
```

**Expected Result:**
- ✅ Order placed successfully
- ✅ Returns `order_id` and success response
- ✅ No error about whitelist or discovery

---

### ✅ Automatic Trading (Requires Whitelist)

**Endpoint:** `POST /api/opportunities/place-order?auto_execute=true`

**Behavior:**
- ✅ **ONLY** trades symbols that are whitelisted when `auto_execute=true`
- ✅ Checks whitelist status before executing
- ✅ Rejects automatic trades for non-whitelisted symbols with clear error message

**Test Case:**
```bash
# Try to auto-execute order for non-whitelisted symbol
curl -X POST "http://127.0.0.1:8000/api/opportunities/place-order?auto_execute=true" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "opp_test_auto",
    "symbol": "BTCEUR",
    "opportunity_type": "SELL",
    "current_price": 75194.41,
    "target_price": 71810.66,
    "stop_loss": 76698.3,
    "quantity": 0.0001,
    "position_value": 7.5
  }'
```

**Expected Result:**
- ✅ If symbol is whitelisted: Order placed successfully
- ✅ If symbol is NOT whitelisted: Error 400 with message:
  ```
  "Symbol BTCEUR must be whitelisted for automatic trading. Please whitelist the symbol first or place the order manually (without auto_execute=true)."
  ```

---

## Whitelist Management

### How Whitelist is Determined

**Source:** `backend/config/settings.py` - `get_trading_symbols()`

**Priority:**
1. `BASE_CURRENCIES` + `QUOTE_CURRENCIES` (auto-generated pairs)
2. `SYMBOLS_WHITELIST` (explicit comma-separated list)
3. Default fallback: `["BTCUSDC", "ETHUSDC", "SOLUSDC", "BNBUSDC", "ADAUSDC"]`

**Example:**
```python
# From .env or settings
BASE_CURRENCIES="BTC,ETH"
QUOTE_CURRENCIES="USDC,EUR"
# Results in: ["BTCUSDC", "BTCEUR", "ETHUSDC", "ETHEUR"]
```

### Promote to Whitelist

**Endpoint:** `POST /api/auto-discovery/promote/{symbol}`

**Behavior:**
- Requires symbol to be in discovery system first
- Promotes discovered symbol to whitelist
- Returns success or appropriate error

**Test Case:**
```bash
# Promote a discovered symbol
curl -X POST http://127.0.0.1:8000/api/auto-discovery/promote/BTCEUR

# Expected if symbol is discovered:
# ✅ Success: Symbol promoted to whitelist

# Expected if symbol is NOT discovered:
# ❌ 404: Symbol not found in discovered symbols
```

---

## Verification Checklist

### ✅ Manual Trading
- [x] Manual order placement works for non-whitelisted symbols
- [x] Manual order placement works for whitelisted symbols
- [x] No whitelist check in `/api/opportunities/place-order` when `auto_execute=false` (or not set)
- [x] Manual orders can be placed even if symbol is not in discovery system

### ✅ Automatic Trading
- [x] Auto-execution requires whitelist (`auto_execute=true`)
- [x] Automatic strategy execution checks whitelist (via trading service)
- [x] Auto-discovery trading only trades discovered symbols (separate from whitelist)
- [x] Clear error messages when automatic trading is blocked due to whitelist

### Whitelist Management
- [x] Promote endpoint requires symbol to be discovered first
- [x] Whitelist status is correctly tracked via `get_trading_symbols()`
- [x] Whitelist status is returned in discovery status endpoint

---

## Current Frontend Behavior

The frontend already implements this correctly:

1. **Manual Orders:**
   - No whitelist check before placing orders
   - "Place Limit Order" button works for all opportunities
   - Orders are sent directly to `/api/opportunities/place-order`

2. **Whitelist Display:**
   - Shows "Whitelisted" badge for whitelisted symbols
   - Used only for visual indication
   - Does not block manual order placement

3. **Promote to Whitelist:**
   - Only available for discovered symbols
   - Used to enable automatic trading for a symbol

---

## Backend Implementation Details

### Order Placement Endpoint

**File:** `backend/api/predictions.py` - `place_opportunity_order_by_data()`

**Logic:**
```python
# Check whitelist ONLY for automatic trading
if auto_execute:
    from backend.config.settings import get_trading_symbols
    whitelist_symbols = set(get_trading_symbols(settings))
    symbol_upper = symbol.upper()
    
    if symbol_upper not in whitelist_symbols:
        raise HTTPException(
            status_code=400,
            detail=f"Symbol {symbol} must be whitelisted for automatic trading. "
                   f"Please whitelist the symbol first or place the order manually (without auto_execute=true)."
        )

# Manual orders proceed without whitelist check
# ... rest of order placement logic ...
```

### Auto-Discovery Trading

**File:** `backend/services/auto_discovery_engine.py`

**Behavior:**
- Auto-discovery trades **discovered symbols** (separate from whitelist)
- Discovered symbols are tracked in `self.discovered_symbols`
- Whitelist symbols are excluded from discovery (`s.upper() not in self.whitelist_symbols`)
- Auto-discovery has its own budget pool

### Trading Service (Automatic Strategy Execution)

**File:** `backend/services/trading_service.py`

**Behavior:**
- Only trades symbols from `SYMBOLS` (whitelist)
- Uses `get_trading_symbols(settings)` to get whitelist
- Automatically enforces whitelist for all automatic trading

---

## Testing Commands

### Test 1: Manual Order (Should Work)
```bash
curl -X POST http://127.0.0.1:8000/api/opportunities/place-order \
  -H "Content-Type: application/json" \
  -d '{
    "id": "opp_manual_test",
    "symbol": "BTCEUR",
    "opportunity_type": "SELL",
    "current_price": 75194.41,
    "target_price": 71810.66,
    "stop_loss": 76698.3,
    "quantity": 0.0001,
    "position_value": 7.5,
    "entry_price_trigger": 75194.41,
    "entry_window_end": "2025-12-31T23:59:59Z"
  }'
```

**Expected:** ✅ Success (even if BTCEUR is not whitelisted)

### Test 2: Auto-Execute Order (Should Require Whitelist)
```bash
# First, ensure BTCEUR is NOT whitelisted
# Then try:
curl -X POST "http://127.0.0.1:8000/api/opportunities/place-order?auto_execute=true" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "opp_auto_test",
    "symbol": "BTCEUR",
    "opportunity_type": "SELL",
    "current_price": 75194.41,
    "target_price": 71810.66,
    "stop_loss": 76698.3,
    "quantity": 0.0001,
    "position_value": 7.5,
    "entry_price_trigger": 75194.41,
    "entry_window_end": "2025-12-31T23:59:59Z"
  }'
```

**Expected:** ❌ Error 400: "Symbol BTCEUR must be whitelisted for automatic trading..."

### Test 3: Check Whitelist Status
```bash
curl http://127.0.0.1:8000/api/auto-discovery/status | jq '.stats.symbols | to_entries | map(select(.value.status == "whitelisted" or .value.status == "whitelist"))'
```

---

## Summary

**Key Points:**
1. ✅ Manual orders = No whitelist check required (IMPLEMENTED)
2. ✅ Automatic trading = Whitelist check required (IMPLEMENTED)
3. ✅ Whitelist = Control mechanism for automatic trading only
4. ✅ Users can manually trade any opportunity, regardless of whitelist status

**Implementation Status:** ✅ **COMPLETE**

The backend now correctly distinguishes between manual and automatic trading:
- Manual orders (`auto_execute=false` or not set): No whitelist check
- Automatic orders (`auto_execute=true`): Whitelist check enforced

---

## Related Documentation

- Frontend-Backend Coordination: `FRONTEND_BACKEND_COORDINATION.md`
- API Integration: `FRONTEND_API_GUIDE.md`
- Auto-Discovery Guide: `FRONTEND_AUTO_DISCOVERY_GUIDE.md`
- Opportunity API: `FRONTEND_OPPORTUNITY_API_GUIDE.md`

