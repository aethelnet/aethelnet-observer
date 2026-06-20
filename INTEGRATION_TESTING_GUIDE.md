# Fund Allocation Integration Testing Guide

**Date:** January 2025  
**Status:** Ready for Testing

---

## Overview

This guide provides step-by-step instructions for testing the fund allocation feature integration between frontend and backend.

## Prerequisites

- Backend is running on `http://127.0.0.1:8000`
- Frontend is running on `http://127.0.0.1:1420`
- Backend has implemented all allocation features (see `BACKEND_READY_FOR_TESTING.md`)
- Budget allocation data is available from `/api/auto-discovery/status`

---

## Test Scenarios

### Test 1: Order Placement with Allocation (Trading Pool)

**Steps:**
1. Navigate to Opportunities view
2. Find an opportunity with valid entry window
3. Click "Place Limit Order" button
4. In the Order Preview Modal:
   - Verify "Fund Allocation" section is visible
   - Verify all 4 partitions are displayed (Trading Pool, Whitelist, Auto-Discovery, Reserve)
   - Verify total available funds is shown
   - Click on "Trading Pool" partition (should highlight)
   - Click "50%" preset button
   - Verify allocation amount is set to 50% of available trading pool funds
   - Verify preview shows original vs new position value
5. Click "Confirm Order"
6. Verify success toast shows: "Order placed for {symbol} ($X.XX from trading pool)"
7. Verify order status updates to "Pending"

**Expected Backend Response:**
```json
{
  "success": true,
  "order_id": "order_12345",
  "status": "pending",
  "allocation": {
    "source": "trading_pool",
    "amount": 100.50,
    "remaining_in_pool": 899.50
  },
  "budget_allocation": {
    "reserve": 500.00,
    "whitelist": 250.00,
    "auto_discovery": 250.00,
    "trading_pool": 500.00
  }
}
```

**Verification:**
- [ ] Order placed successfully
- [ ] Success message includes allocation info
- [ ] Order status is "Pending" (not "none")
- [ ] Response includes allocation object
- [ ] Response includes budget_allocation object

---

### Test 2: Insufficient Funds Error

**Steps:**
1. Navigate to Opportunities view
2. Find an opportunity
3. Click "Place Limit Order"
4. In Order Preview Modal:
   - Select "Trading Pool" (or any pool with limited funds)
   - Enter an amount greater than available funds (e.g., if available is $50, enter $100)
   - Frontend should show validation error
5. If frontend validation passes, click "Confirm Order"
6. Verify error toast shows backend error message: "Insufficient funds in trading_pool. Available: $X.XX, Requested: $Y.YY"

**Expected Backend Response:**
```json
{
  "error": true,
  "detail": "Insufficient funds in trading_pool. Available: $50.00, Requested: $100.50"
}
```

**Verification:**
- [ ] Frontend shows validation error before sending
- [ ] Backend returns 400 error if validation bypassed
- [ ] Error message is clear and includes available/requested amounts
- [ ] Order is NOT placed

---

### Test 3: Reserve Pool Allocation

**Steps:**
1. Navigate to Opportunities view
2. Find an opportunity
3. Click "Place Limit Order"
4. In Order Preview Modal:
   - Select "Reserve" partition (should show warning)
   - Verify warning message appears: "Reserve pool allocation requires confirmation"
   - Set allocation amount (e.g., 25%)
   - Verify reserve partition is highlighted differently
5. Click "Confirm Order"
6. Verify order is placed (frontend sends `confirm_reserve: true` automatically)

**Expected Backend Behavior:**
- Backend should accept reserve allocation if `confirm_reserve: true` is sent
- If `confirm_reserve` is missing or false, backend should return error

**Verification:**
- [ ] Reserve partition shows warning in UI
- [ ] Order with reserve allocation succeeds
- [ ] `confirm_reserve: true` is sent in request

---

### Test 4: Order Without Allocation (Backward Compatibility)

**Steps:**
1. Navigate to Opportunities view
2. Find an opportunity
3. Click "Place Limit Order"
4. In Order Preview Modal:
   - Do NOT set any allocation amount
   - Leave allocation at 0 or don't interact with allocation controls
5. Click "Confirm Order"
6. Verify order is placed using original position value

**Expected Backend Behavior:**
- Backend should accept order without allocation object
- Order should use original `position_value` from opportunity
- Response should not include allocation fields

**Verification:**
- [ ] Order placed successfully
- [ ] Original position value is used
- [ ] No allocation errors

---

### Test 5: Invalid Allocation Source

**Steps:**
1. This test requires manual API testing or frontend modification
2. Send order with invalid allocation source (e.g., `"source": "invalid_pool"`)
3. Verify backend returns 400 error with valid sources listed

**Expected Backend Response:**
```json
{
  "error": true,
  "detail": "Invalid allocation source: invalid_pool. Valid sources: trading_pool, whitelist, auto_discovery, reserve"
}
```

**Verification:**
- [ ] Backend validates source
- [ ] Error message lists valid sources
- [ ] Order is NOT placed

---

### Test 6: Order Status After Placement

**Steps:**
1. Place an order with allocation
2. After successful placement, check order status
3. Navigate to opportunity list
4. Verify order status badge shows "Pending" (not "none")
5. Verify button changed from "Place Limit Order" to status badge

**Verification:**
- [ ] Order status is "Pending" immediately after placement
- [ ] Status persists after page refresh
- [ ] UI reflects correct status

---

### Test 7: Budget Allocation Display

**Steps:**
1. Navigate to Opportunities view
2. Click "Place Limit Order" on any opportunity
3. In Order Preview Modal:
   - Verify "Fund Allocation" section loads
   - Verify total available funds is displayed
   - Verify all 4 partitions show correct amounts
   - Verify partition bars show correct percentages
   - Verify partition colors are distinct:
     - Trading Pool: Blue (#60a5fa)
     - Whitelist: Green (#4ade80)
     - Auto-Discovery: Yellow (#fbbf24)
     - Reserve: Purple (#a78bfa)

**Verification:**
- [ ] Budget data loads correctly
- [ ] All partitions display
- [ ] Visual bars are proportional
- [ ] Colors are distinct

---

### Test 8: Preset Allocation Buttons

**Steps:**
1. Open Order Preview Modal
2. Select a partition (e.g., Trading Pool)
3. Click "25%" preset button
4. Verify amount is set to 25% of available funds
5. Click "50%" preset button
6. Verify amount updates to 50%
7. Click "75%" preset button
8. Verify amount updates to 75%
9. Click "100%" preset button
10. Verify amount is set to full available amount

**Verification:**
- [ ] All preset buttons work
- [ ] Amounts are calculated correctly
- [ ] Input field updates
- [ ] Preview updates

---

### Test 9: Custom Allocation Amount

**Steps:**
1. Open Order Preview Modal
2. Select a partition
3. Enter custom amount in input field (e.g., $75.50)
4. Verify preview shows updated position value
5. Try entering amount greater than available
6. Verify frontend validation prevents/limits it
7. Try entering negative amount
8. Verify frontend validation prevents it

**Verification:**
- [ ] Custom input works
- [ ] Validation prevents over-allocation
- [ ] Validation prevents negative amounts
- [ ] Preview updates in real-time

---

### Test 10: Multiple Orders from Same Pool

**Steps:**
1. Place first order with allocation from Trading Pool ($100)
2. Place second order with allocation from Trading Pool ($50)
3. Verify both orders succeed
4. Check budget allocation after both orders
5. Verify remaining funds are calculated correctly

**Verification:**
- [ ] Multiple orders from same pool succeed
- [ ] Budget allocation updates correctly
- [ ] Remaining funds are accurate

---

## Error Handling Tests

### Test 11: Network Error During Allocation Fetch

**Steps:**
1. Stop backend server
2. Open Order Preview Modal
3. Verify modal still opens
4. Verify allocation section shows loading or error state
5. Verify user can still place order without allocation

**Verification:**
- [ ] Modal doesn't crash
- [ ] Graceful error handling
- [ ] Order can still be placed without allocation

---

### Test 12: Backend Returns Allocation Error

**Steps:**
1. Place order with allocation that exceeds available funds
2. Verify error toast shows backend error message
3. Verify error message is user-friendly
4. Verify modal doesn't close on error
5. Verify user can adjust allocation and retry

**Verification:**
- [ ] Error messages are clear
- [ ] User can retry after error
- [ ] Modal state is preserved

---

## UI/UX Tests

### Test 13: Partition Manager Visual Feedback

**Steps:**
1. Open Order Preview Modal
2. Hover over different partitions
3. Verify hover effect (border color change, background highlight)
4. Click on a partition
5. Verify selected state (highlighted border, shadow)
6. Click on Reserve partition
7. Verify reserve-specific styling (yellow border)

**Verification:**
- [ ] Hover effects work
- [ ] Selected state is clear
- [ ] Reserve partition is visually distinct

---

### Test 14: Responsive Design

**Steps:**
1. Open Order Preview Modal
2. Resize browser window
3. Verify partition manager grid adapts
4. Verify all controls remain accessible
5. Verify no horizontal scrolling

**Verification:**
- [ ] Layout is responsive
- [ ] Controls remain usable
- [ ] No layout breaks

---

## Integration Checklist

### Frontend Verification
- [ ] Budget allocation loads from API
- [ ] Partition manager displays correctly
- [ ] Allocation controls work (dropdown, input, presets)
- [ ] Validation prevents invalid allocations
- [ ] Reserve pool shows warning
- [ ] Allocation data is sent in order request
- [ ] Success message includes allocation info
- [ ] Error messages are user-friendly
- [ ] Order status updates correctly

### Backend Verification
- [ ] Allocation object is accepted in request
- [ ] Budget validation works (sufficient funds check)
- [ ] Invalid source returns clear error
- [ ] Reserve requires confirmation
- [ ] Response includes allocation info
- [ ] Response includes budget_allocation
- [ ] Order status is "pending" after placement

### End-to-End Verification
- [ ] Order with allocation places successfully
- [ ] Order status reflects "pending" immediately
- [ ] Budget allocation updates in response
- [ ] Error handling works for all scenarios
- [ ] Backward compatibility (orders without allocation)

---

## Known Issues / Limitations

1. **Dynamic Budget Calculation**
   - Budget is calculated dynamically, not persisted
   - Multiple simultaneous orders may show same available funds
   - Frontend should refresh budget after each order

2. **Fund Return**
   - Allocation info is stored for fund return
   - Actual fund return requires wallet system integration
   - Currently logs fund return requirement

3. **Real-time Updates**
   - Budget allocation in response is snapshot at order time
   - Does not reflect real-time changes from other orders
   - Frontend should periodically refresh budget data

---

## Debugging Tips

### Check Browser Console
- Look for `[DEBUG]` messages from order placement
- Check for API errors
- Verify allocation data in logs

### Check Network Tab
- Verify POST request includes allocation object
- Check response includes allocation info
- Verify error responses for failed allocations

### Check Backend Logs
- Look for allocation validation messages
- Check fund return logs on order cancel
- Verify order registration

---

## Success Criteria

✅ All test scenarios pass  
✅ Error handling works correctly  
✅ UI is responsive and user-friendly  
✅ Backend validates all allocation data  
✅ Order status updates correctly  
✅ Budget allocation displays accurately  
✅ Backward compatibility maintained

---

## Next Steps After Testing

1. **If All Tests Pass:**
   - Remove debug instrumentation
   - Document any edge cases found
   - Consider performance optimizations

2. **If Issues Found:**
   - Document issues with steps to reproduce
   - Fix frontend issues
   - Coordinate with backend team for backend issues

3. **Enhancements:**
   - Add performance metrics display (if backend provides)
   - Implement real-time budget updates
   - Add fund return UI feedback


