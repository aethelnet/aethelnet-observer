# API Call Verification Guide - Fund Allocation

**Purpose:** Verify that allocation data is being sent correctly to the backend API

---

## How to Verify API Calls

### Method 1: Browser DevTools Network Tab

1. Open Browser DevTools (F12)
2. Go to **Network** tab
3. Filter by "place-order" or "opportunities"
4. Place an order with allocation
5. Click on the `POST /api/opportunities/place-order` request
6. Check **Payload** or **Request** tab to see the request body

**Expected Request Body:**
```json
{
  "id": "opp_05be5a3e",
  "symbol": "BTCEUR",
  "opportunity_type": "SELL",
  // ... other opportunity fields ...
  "allocation": {
    "source": "trading_pool",
    "amount": 4.9457694265,
    "position_value": 4.9457694265,
    "confirm_reserve": false
  }
}
```

**Verify:**
- [ ] `allocation` object is present
- [ ] `allocation.source` is one of: `trading_pool`, `whitelist`, `auto_discovery`, `reserve`
- [ ] `allocation.amount` is a positive number
- [ ] `allocation.position_value` matches the new position value
- [ ] `allocation.confirm_reserve` is `true` if source is `reserve`, otherwise `false`

### Method 2: Debug Logs

Check the debug logs for these entries:

**1. Order Data Prepared:**
```
Location: OpportunitiesView.vue:553
Message: "Order data prepared with allocation"
Data should show:
- hasAllocation: true
- allocation: { source, amount, position_value, confirm_reserve }
```

**2. Full Order Data Being Sent:**
```
Location: OpportunitiesView.vue:565
Message: "Full order data being sent to API"
Data should show:
- hasAllocation: true
- allocationObject: { source, amount, position_value, confirm_reserve }
- fullOrderDataPreview: (first 1000 chars of JSON)
```

**3. Request Body Before API Call:**
```
Location: api.js:207
Message: "Before apiFetch call - full request body"
Data should show:
- hasAllocation: true
- allocationObject: { source, amount, position_value, confirm_reserve }
- requestBodyPreview: (first 1500 chars of JSON)
```

**4. API Response:**
```
Location: api.js:225
Message: "apiFetch returned - full response"
Data should show:
- hasAllocation: true (if backend processed allocation)
- allocationObject: { source, amount, remaining_in_pool }
- hasBudgetAllocation: true (if backend returns it)
- budgetAllocation: { reserve, whitelist, auto_discovery, trading_pool }
```

### Method 3: Console Logs

Check browser console for:
```
[DEBUG] OrderPreviewModal confirm event emitted {
  allocationSource: 'trading_pool',
  allocatedAmount: 4.9457694265,
  originalPositionValue: 0.2,
  newPositionValue: 4.9457694265,
  confirmReserve: false
}
```

---

## Expected API Request Format

### Request URL
```
POST http://127.0.0.1:8000/api/opportunities/place-order
```

### Request Headers
```
Content-Type: application/json
```

### Request Body Structure
```json
{
  "id": "opp_05be5a3e",
  "symbol": "BTCEUR",
  "opportunity_type": "SELL",
  "confidence": 0.95,
  "target_price": 71746.63,
  "stop_loss": 76629.91,
  "execution": {
    "order_type": "LIMIT",
    "quantity": 0.00000264,
    "position_value": 0.2
  },
  "allocation": {
    "source": "trading_pool",
    "amount": 4.9457694265,
    "position_value": 4.9457694265,
    "confirm_reserve": false
  }
}
```

**Key Points:**
- `allocation` is a top-level property in the opportunity object
- `allocation.source` uses snake_case: `trading_pool` (not `tradingPool`)
- `allocation.amount` is the dollar amount to allocate
- `allocation.position_value` is the new position value (may differ from original)
- `allocation.confirm_reserve` is `true` only if source is `reserve`

---

## Expected API Response Format

### Success Response (with Allocation)
```json
{
  "success": true,
  "order_id": "order_12345",
  "status": "pending",
  "opportunity_id": "opp_05be5a3e",
  "symbol": "BTCEUR",
  "allocation": {
    "source": "trading_pool",
    "amount": 4.9457694265,
    "remaining_in_pool": 4.9542305735
  },
  "budget_allocation": {
    "reserve": 4.24,
    "whitelist": 3.96,
    "auto_discovery": 5.93,
    "trading_pool": 4.95
  }
}
```

**Verify in Response:**
- [ ] `allocation` object is present
- [ ] `allocation.source` matches what was sent
- [ ] `allocation.amount` matches what was sent
- [ ] `allocation.remaining_in_pool` is calculated correctly
- [ ] `budget_allocation` object is present (optional)
- [ ] `budget_allocation.trading_pool` reflects the deduction

---

## Common Issues to Check

### Issue 1: Allocation Not Sent
**Symptoms:**
- Request body doesn't include `allocation` object
- Backend doesn't process allocation

**Check:**
- Verify `allocationData` is passed to `confirmPlaceOrder()`
- Verify `orderData.allocation` is not `undefined`
- Check logs for "Order data prepared with allocation"

### Issue 2: Wrong Field Names
**Symptoms:**
- Backend returns "Invalid allocation source"
- Backend doesn't recognize allocation fields

**Check:**
- Verify `source` (not `allocationSource`)
- Verify `amount` (not `allocatedAmount`)
- Verify `position_value` (not `newPositionValue`)
- Verify `confirm_reserve` (not `confirmReserve`)

### Issue 3: Allocation Amount Mismatch
**Symptoms:**
- Backend processes allocation but amount is wrong
- Position value doesn't match

**Check:**
- Verify `allocation.amount` matches user input
- Verify `allocation.position_value` matches preview
- Check for rounding errors

### Issue 4: Reserve Confirmation Missing
**Symptoms:**
- Backend returns error for reserve allocation
- "Reserve pool allocation requires explicit confirmation"

**Check:**
- Verify `confirm_reserve: true` when source is `reserve`
- Check logs for `confirmReserve` value

---

## Quick Verification Commands

### Check Logs for Allocation Data
```bash
# View recent allocation logs
tail -1000 .cursor/debug.log | jq -r 'select(.message | contains("allocation") or contains("Allocation")) | "\(.timestamp) | \(.location) | \(.message)"' | tail -20

# View full request body
tail -2000 .cursor/debug.log | jq -r 'select(.message | contains("full request body")) | .data.requestBodyPreview' | tail -5

# View API response
tail -2000 .cursor/debug.log | jq -r 'select(.message | contains("apiFetch returned")) | .data.fullResult' | tail -5
```

---

## Verification Checklist

After placing an order with allocation:

- [ ] Browser console shows allocation data in confirm event
- [ ] Network tab shows `allocation` object in request payload
- [ ] Request body includes correct `allocation` structure
- [ ] Backend response includes `allocation` object
- [ ] Backend response includes `budget_allocation` (optional)
- [ ] Success message shows allocation info
- [ ] Order status updates to "pending"
- [ ] No errors in console or network tab

---

## Next Steps

1. **Place an order with allocation** and check:
   - Browser Network tab for request payload
   - Debug logs for allocation data
   - Backend response for allocation confirmation

2. **If allocation is not in request:**
   - Check `allocationData` is being passed correctly
   - Verify `orderData.allocation` is not undefined
   - Check for JavaScript errors

3. **If backend doesn't process allocation:**
   - Verify request format matches backend expectations
   - Check backend logs for allocation validation
   - Verify backend endpoint is updated


