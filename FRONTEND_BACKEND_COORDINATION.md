# Frontend-Backend Coordination Document

**Last Updated:** January 2025  
**Purpose:** Document frontend behavior and expectations for backend API responses

---

## Symbol Opportunities View - Promote/Remove Button Behavior

### Promote Button (`/api/auto-discovery/promote/{symbol}`)

**Frontend Behavior:**
1. Before API call: Frontend checks if symbol is already whitelisted using `isWhitelisted(symbol)`
2. If already whitelisted: Shows error toast "Symbol {symbol} is already whitelisted" and skips API call
3. API call: Sends POST to `/api/auto-discovery/promote/{symbol}`
4. Success handling:
   - Shows success toast: "Symbol {symbol} promoted to whitelist"
   - Refreshes whitelist status via `fetchWhitelistStatus()`
   - Refreshes symbol data via `fetchSymbolData()`
5. Error handling:
   - If error detail contains "already" or "whitelist": Shows "Symbol {symbol} is already whitelisted"
   - Otherwise: Shows error detail from API response
   - Refreshes whitelist status to sync state

**Expected API Response:**
- **Success:** `{ success: true }` or any non-error response
- **Error (already whitelisted):** `{ error: true, detail: "..." }` where detail mentions "already" or "whitelist"
- **Error (other):** `{ error: true, detail: "error message" }`

**Recommendation for Backend:**
- Return clear error message when symbol is already whitelisted (e.g., "Symbol {symbol} is already whitelisted")
- Consider returning `{ success: true }` even if already whitelisted (idempotent operation)

---

### Remove Button (`/api/auto-discovery/remove/{symbol}`)

**Frontend Behavior:**
1. Before API call: Frontend checks if symbol is whitelisted using `isWhitelisted(symbol)`
2. API call: Sends POST to `/api/auto-discovery/remove/{symbol}`
3. Success handling:
   - Shows success toast: "Symbol {symbol} removed"
   - Refreshes whitelist status via `fetchWhitelistStatus()`
   - Refreshes symbol data via `fetchSymbolData()`
4. Error handling:
   - If error detail contains "not found in discovered symbols" or "not found":
     - If symbol is whitelisted: Shows "Cannot remove whitelisted symbol {symbol} from this view. Please use the Auto-Discovery view to manage whitelisted symbols."
     - If symbol is not whitelisted: Shows "Symbol {symbol} is not found. It may have already been removed." and refreshes data
   - Otherwise: Shows error detail from API response

**Current Issue:**
- The `/api/auto-discovery/remove/{symbol}` endpoint appears to only work for discovered symbols
- Whitelisted-only symbols cannot be removed via this endpoint
- Frontend shows a helpful message directing users to Auto-Discovery view for whitelisted symbols

**Expected API Response:**
- **Success:** `{ success: true }` or any non-error response
- **Error (not found):** `{ error: true, detail: "Symbol {symbol} not found in discovered symbols" }`
- **Error (other):** `{ error: true, detail: "error message" }`

**Recommendation for Backend:**
- Consider making `/api/auto-discovery/remove/{symbol}` work for both discovered and whitelisted symbols
- OR provide a separate endpoint `/api/auto-discovery/remove-from-whitelist/{symbol}` for whitelisted symbols
- Return clear error messages distinguishing between "not found" and other errors

---

## Order Placement - API Response Format

### Current Frontend Implementation

**Frontend expects:**
```javascript
{
  success: true,           // OR
  order_id: "valid_id",    // Must not be "None" or null
  status: "Pending"        // Optional, defaults to "Pending"
}
```

**Frontend logic:**
```javascript
if ((result?.success || (result?.order_id && result.order_id !== "None" && result.order_id !== null)) && previewOpportunity.value.id) {
  orderStatuses.value.set(previewOpportunity.value.id, result?.status || 'Pending')
}
```

**Expected API Response Format:**
- **Success:** 
  ```json
  {
    "success": true,
    "order_id": "order_12345",
    "status": "Pending"
  }
  ```
  OR
  ```json
  {
    "order_id": "order_12345",
    "status": "Pending"
  }
  ```

- **Error:**
  ```json
  {
    "error": true,
    "detail": "Error message here"
  }
  ```

**Important Notes:**
- Frontend checks for `success: true` OR a valid `order_id` (not "None" or null)
- If `order_id` is the string "None" or null, frontend will NOT update order status
- Frontend uses `result?.status` if available, otherwise defaults to "Pending"
- Frontend stores order status in `orderStatuses` map keyed by opportunity ID

---

## Symbol Opportunities Data Structure

### Expected API Response from `/api/opportunities/symbols`

**Format:** Array of symbol objects

```json
[
  {
    "symbol": "BTCEUR",
    "price": 75139.09,
    "volume": 190,
    "z_score": -10.00,
    "signal": -10.00,
    "change_24h": 1.41,
    "opportunities": [
      {
        "id": "opp_123",
        "opportunity_type": "SELL",
        "direction": "SELL",
        "confidence": 0.95,
        "potential_profit_percent": 4.50,
        "target_price": 71757.83,
        "stop_loss": 76641.87,
        "countdown_seconds": 897,
        "expires_at": "2025-01-XX...",
        "entry_price_range": {
          "min": 74951.24,
          "max": 75326.94,
          "trigger": 75139.09
        },
        "entry_time_window": {
          "start": "2025-01-XX...",
          "end": "2025-01-XX..."
        },
        "execution": {
          "quantity": 0.00000264,
          "position_value": 198.50
        },
        "order_status": "none"  // or "Pending", "Filled", etc.
      }
    ]
  }
]
```

**Frontend Processing:**
- Frontend maps flat structure to nested structure for UI components
- Generates IDs for opportunities if not present: `opp_{symbol}_{idx}_{timestamp}`
- Maps `entry_price_min/max` to `entry_price_range` object
- Maps `entry_window_start/end` to `entry_time_window` object
- Maps `quantity` to `execution` object
- Uses `countdown_seconds` from backend if available, otherwise calculates from `expires_at`

---

## Auto-Discovery Status - Whitelist Detection

### Frontend Whitelist Status Check

**API:** `/api/auto-discovery/status`

**Frontend extracts whitelisted symbols from:**
```json
{
  "stats": {
    "symbols": {
      "BTCEUR": {
        "status": "whitelisted",  // or "whitelist"
        ...
      }
    }
  }
}
```

**Frontend logic:**
- Checks `data.status?.toLowerCase() === 'whitelisted' || data.status?.toLowerCase() === 'whitelist'`
- Stores whitelisted symbols in `whitelistedSymbols` Set
- Uses this to determine if promote/remove buttons should show different behavior

**Recommendation:**
- Backend should consistently use "whitelisted" (not "whitelist") for status field
- OR document which status values are valid

---

## Layout and Responsive Design Changes

### Recent Changes (January 2025)

**MainContent Component:**
- Changed from fixed `height: 100vh` to `flex: 1` with flexbox layout
- Added `overflow: hidden` to prevent double scrollbars

**OpportunitiesView:**
- Removed `max-width: 1400px` constraint - now uses full width
- Changed to flexbox layout: `display: flex; flex-direction: column; height: 100%`
- `.symbols-list` uses `flex: 1` with `overflow-y: auto` for scrolling
- Added responsive padding using `clamp(16px, 2vw, 24px)`

**Impact on Backend:**
- No API changes required
- Frontend now better utilizes available screen space
- Data fetching and display logic unchanged

---

## Error Handling Patterns

### Toast Notifications

Frontend uses custom events for toast notifications:
```javascript
window.dispatchEvent(new CustomEvent('toast:show', {
  detail: { type: 'success' | 'error', message: string, duration: 3000 }
}))
```

### API Error Response Format

Frontend expects:
```json
{
  "error": true,
  "status": 400,  // HTTP status code (optional)
  "detail": "Human-readable error message"
}
```

**Best Practices:**
- Always include `error: true` for error responses
- Include `detail` with user-friendly error message
- Include `status` for HTTP status codes when available
- Use consistent error message format across endpoints

---

## Testing Recommendations

### For Backend Developers

1. **Test Promote Endpoint:**
   - Test promoting already-whitelisted symbol (should return clear error)
   - Test promoting discovered symbol (should succeed)
   - Verify response format matches expected structure

2. **Test Remove Endpoint:**
   - Test removing discovered symbol (should succeed)
   - Test removing whitelisted symbol (currently fails - consider fixing)
   - Test removing non-existent symbol (should return clear "not found" error)

3. **Test Order Placement:**
   - Verify `order_id` is never the string "None" or null on success
   - Include `status` field in response
   - Test error responses include `error: true` and `detail`

4. **Test Symbol Opportunities:**
   - Verify all required fields are present
   - Test with and without `countdown_seconds` (frontend calculates if missing)
   - Verify `order_status` field is included for opportunities with orders

---

## Questions for Backend Team

1. **Remove Whitelisted Symbols:**
   - Should `/api/auto-discovery/remove/{symbol}` work for whitelisted symbols?
   - Or should there be a separate endpoint for removing from whitelist?

2. **Promote Already-Whitelisted:**
   - Should promoting an already-whitelisted symbol be idempotent (return success)?
   - Or should it return an error?

3. **Order Status Values:**
   - What are the valid `order_status` values?
   - Should frontend handle "none" differently than other statuses?

4. **Symbol Status Values:**
   - What are the valid `status` values for symbols in auto-discovery?
   - Should we standardize on "whitelisted" vs "whitelist"?

---

## Fund Allocation / Wallet Partition Manager

### Overview

The frontend will display a fund allocation partition manager in the Order Preview Modal, allowing users to:
- View available funds across different budget pools (trading_pool, whitelist, auto_discovery, reserve)
- See performance metrics for each partition
- Allocate funds from specific pools to trades
- Adjust position value based on allocation

### Budget Allocation Data

**API Endpoint:** `/api/auto-discovery/status`

**Frontend extracts budget allocation from:**
```json
{
  "budget_allocation": {
    "reserve": 4.24,
    "whitelist": 3.96,
    "auto_discovery": 5.93,
    "trading_pool": 9.89
  }
}
```

**Frontend Behavior:**
- Fetches budget allocation when Order Preview Modal opens
- Displays total available funds: sum of all pools
- Shows visual partition bars for each pool with percentage of total
- Allows user to select allocation source and amount

**Expected API Response:**
- Budget allocation should always be present in `/api/auto-discovery/status` response
- Values should be in USD (or base currency)
- Values should be non-negative numbers
- If a pool is empty, return `0.0` (not `null` or missing)

### Performance Metrics (Optional Enhancement)

**Frontend would like to display:**
- P&L per partition
- Win rate per partition
- Number of trades per partition

**Current Status:**
- Performance metrics are optional
- Frontend will gracefully handle missing metrics
- If available, should be included in `/api/auto-discovery/status` response

**Suggested Response Format (if implemented):**
```json
{
  "budget_allocation": {
    "reserve": 4.24,
    "whitelist": 3.96,
    "auto_discovery": 5.93,
    "trading_pool": 9.89
  },
  "partition_performance": {
    "trading_pool": {
      "pnl": 12.50,
      "win_rate": 0.65,
      "total_trades": 25
    },
    "whitelist": {
      "pnl": 8.30,
      "win_rate": 0.72,
      "total_trades": 18
    },
    "auto_discovery": {
      "pnl": -2.10,
      "win_rate": 0.45,
      "total_trades": 12
    },
    "reserve": {
      "pnl": 0.0,
      "win_rate": 0.0,
      "total_trades": 0
    }
  }
}
```

### Order Placement with Allocation

**API Endpoint:** `POST /api/opportunities/place-order`

**Frontend will send allocation data in request body:**
```json
{
  "id": "opp_abc123",
  "symbol": "BTCEUR",
  "opportunity_type": "SELL",
  // ... other opportunity fields ...
  "allocation": {
    "source": "trading_pool",
    "amount": 100.50,
    "position_value": 100.50
  }
}
```

**Allocation Object Fields:**
- `source` (string, required): One of `"trading_pool"`, `"whitelist"`, `"auto_discovery"`, or `"reserve"`
- `amount` (number, required): Dollar amount to allocate from selected pool
- `position_value` (number, required): New position value after allocation (may differ from original)

**Backend Requirements:**

1. **Validation:**
   - Validate `allocation.source` is one of the valid pool names
   - Validate `allocation.amount` doesn't exceed available funds in selected pool
   - Validate `allocation.amount` is positive and non-zero
   - If validation fails, return error with clear message

2. **Fund Deduction:**
   - Deduct `allocation.amount` from the selected pool's budget
   - Update budget allocation immediately after order placement
   - Ensure atomic operation (deduct funds only if order placement succeeds)

3. **Response:**
   - Include updated budget allocation in response (optional but helpful)
   - Confirm which pool was used in response

**Success Response Format:**
```json
{
  "success": true,
  "order_id": "order_12345",
  "status": "Pending",
  "opportunity_id": "opp_abc123",
  "symbol": "BTCEUR",
  "allocation": {
    "source": "trading_pool",
    "amount": 100.50,
    "remaining_in_pool": 8.89
  },
  "budget_allocation": {
    "reserve": 4.24,
    "whitelist": 3.96,
    "auto_discovery": 5.93,
    "trading_pool": 8.89
  }
}
```

**Error Response Format (Insufficient Funds):**
```json
{
  "error": true,
  "detail": "Insufficient funds in trading_pool. Available: $9.89, Requested: $100.50",
  "status": 400,
  "available_funds": 9.89,
  "requested_amount": 100.50,
  "pool": "trading_pool"
}
```

**Error Response Format (Invalid Pool):**
```json
{
  "error": true,
  "detail": "Invalid allocation source: invalid_pool. Valid sources: trading_pool, whitelist, auto_discovery, reserve",
  "status": 400
}
```

### Allocation Behavior

**Frontend Behavior:**
- Allocation is **optional** - if not provided, use original `position_value` from opportunity
- User can select allocation source from dropdown
- User can set custom amount or use preset percentages (25%, 50%, 75%, 100%)
- Frontend validates amount doesn't exceed available funds before sending
- Reserve pool should be marked as "protected" (frontend will show warning)

**Backend Behavior:**
- If `allocation` object is missing, use original `position_value` from opportunity
- If `allocation` is provided, validate and use it
- Reserve pool should require additional confirmation (backend can enforce this)
- Update budget allocation atomically with order placement

### Reserve Pool Protection

**Frontend Behavior:**
- Reserve pool will be visually distinguished (different color/styling)
- Frontend will show warning when allocating from reserve
- User must explicitly confirm reserve allocation

**Backend Recommendation:**
- Consider requiring additional parameter for reserve allocation (e.g., `confirm_reserve: true`)
- OR return error if reserve allocation attempted without confirmation
- OR implement separate endpoint for reserve allocations

**Suggested Request Format (with reserve confirmation):**
```json
{
  "allocation": {
    "source": "reserve",
    "amount": 50.00,
    "position_value": 50.00,
    "confirm_reserve": true
  }
}
```

### Budget Allocation Updates

**After Order Placement:**
- Backend should update budget allocation immediately
- Updated allocation should be reflected in next `/api/auto-discovery/status` call
- Consider including updated allocation in order placement response

**After Order Fills/Cancels:**
- When order fills: funds remain deducted (used for position)
- When order cancels: funds should be returned to original pool
- When order expires: funds should be returned to original pool

**Backend Requirements:**
- Track which pool each order's funds came from
- Implement fund return mechanism for cancelled/expired orders
- Update budget allocation when funds are returned

### Testing Checklist

**Budget Allocation Display:**
- [ ] `/api/auto-discovery/status` returns `budget_allocation` object
- [ ] All four pools (reserve, whitelist, auto_discovery, trading_pool) are present
- [ ] Values are non-negative numbers
- [ ] Empty pools return `0.0` (not null)

**Order Placement with Allocation:**
- [ ] Order with valid allocation succeeds
- [ ] Funds are deducted from correct pool
- [ ] Order with allocation exceeding available funds returns error
- [ ] Order with invalid pool name returns error
- [ ] Order without allocation uses original position_value
- [ ] Response includes updated budget allocation

**Fund Validation:**
- [ ] Cannot allocate more than available in pool
- [ ] Cannot allocate negative amounts
- [ ] Cannot allocate zero amounts
- [ ] Invalid pool names are rejected

**Reserve Pool:**
- [ ] Reserve allocation requires confirmation (if implemented)
- [ ] Reserve allocation without confirmation fails (if implemented)
- [ ] Reserve pool is clearly marked as protected

**Fund Return:**
- [ ] Cancelled orders return funds to original pool
- [ ] Expired orders return funds to original pool
- [ ] Budget allocation updates when funds are returned

---

## Contact

For questions or clarifications about frontend behavior, please refer to:
- `src/views/OpportunitiesView.vue` - Main opportunities view implementation
- `src/components/OrderPreviewModal.vue` - Order preview and allocation UI
- `src/shared/api.js` - API client implementation
- This document for coordination between frontend and backend

