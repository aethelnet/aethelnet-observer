# Fund Return Guide

**Date:** January 2025  
**Status:** Documentation

---

## Overview

When orders are cancelled or fail, funds that were allocated from budget pools should be returned to their original source. This guide explains the fund return behavior and implementation.

---

## When Funds Are Returned

### Automatic Fund Return

Funds are automatically returned when:

1. **Order Cancellation:**
   - User cancels a pending order
   - Order is cancelled due to expiry
   - Order is cancelled due to invalid conditions

2. **Order Failure:**
   - Order placement fails after funds were deducted
   - Order execution fails
   - System error during order processing

### Fund Return Process

1. **Allocation Tracking:**
   - When order is placed with allocation, allocation info is stored
   - Allocation includes: `source`, `amount`, `position_value`
   - Allocation is linked to order ID

2. **Fund Return:**
   - On order cancellation/failure, backend looks up allocation info
   - Funds are returned to original pool (`source`)
   - Budget allocation is updated

3. **User Notification:**
   - User may see updated budget allocation in response
   - No explicit "funds returned" message (automatic process)

---

## Allocation Object Structure

### Request Format

When placing an order with allocation:

```json
{
  "allocation": {
    "source": "trading_pool",
    "amount": 100.50,
    "position_value": 100.50,
    "confirm_reserve": false
  }
}
```

### Fields

- **`source`** (string, required): Budget pool name
  - Valid values: `"trading_pool"`, `"whitelist"`, `"auto_discovery"`, `"reserve"`
- **`amount`** (number, required): Dollar amount allocated
- **`position_value`** (number, required): New position value after allocation
- **`confirm_reserve`** (boolean, optional): Confirmation for reserve pool allocation

---

## Backend Implementation

### Fund Return Logic

**Location:** Backend order management system

**Process:**
1. Store allocation info when order is placed
2. On cancellation/failure:
   - Look up allocation by order ID
   - Return `amount` to `source` pool
   - Update budget allocation
   - Log fund return operation

### Budget Allocation Update

After fund return, budget allocation is updated:

```json
{
  "budget_allocation": {
    "reserve": 4.24,
    "whitelist": 3.96,
    "auto_discovery": 5.93,
    "trading_pool": 9.89  // Increased by returned amount
  }
}
```

---

## Frontend Behavior

### Order Placement

Frontend sends allocation data with order:

```javascript
const orderData = {
  id: opportunity.id,
  symbol: opportunity.symbol,
  // ... other fields
  allocation: {
    source: 'trading_pool',
    amount: 100.50,
    position_value: 100.50
  }
}

const result = await placeOpportunityOrder(orderData)
```

### Order Cancellation

Frontend doesn't explicitly request fund return - backend handles it automatically:

```javascript
// Cancel order
await cancelOrder(orderId)
// Backend automatically returns funds to original pool
```

### Budget Updates

Frontend may receive updated budget allocation in responses:

```javascript
// Order placement response
{
  order_id: "...",
  budget_allocation: {
    trading_pool: 9.89  // Updated after allocation
  }
}

// Order cancellation (if response includes budget)
{
  status: "cancelled",
  budget_allocation: {
    trading_pool: 10.89  // Updated after fund return
  }
}
```

---

## User Experience

### What Users See

1. **Order Placement:**
   - User sees order placed successfully
   - Budget allocation may be updated in response
   - No explicit "funds deducted" message

2. **Order Cancellation:**
   - User sees order cancelled
   - Funds are automatically returned
   - No explicit "funds returned" message (automatic)

3. **Budget Display:**
   - Budget allocation shows available funds
   - Funds reflect current state (after returns)
   - No separate "returned funds" indicator

---

## Edge Cases

### Partial Fund Return

**Scenario:** Order partially filled, then cancelled

**Behavior:**
- Only unfilled portion is returned
- Filled portion remains in position
- Allocation reflects partial return

### Multiple Allocations

**Scenario:** Order uses funds from multiple pools

**Behavior:**
- Each allocation is tracked separately
- Funds returned to respective pools
- Budget allocation updated for all pools

### Missing Allocation Info

**Scenario:** Order cancelled but allocation info missing

**Behavior:**
- Backend logs error
- Funds may not be returned (requires investigation)
- User should refresh budget allocation

---

## Testing

### Test Fund Return

1. **Place Order with Allocation:**
   ```bash
   curl -X POST "http://127.0.0.1:8000/api/opportunities/place-order" \
     -H "Content-Type: application/json" \
     -d '{
       "id": "opp_test",
       "allocation": {
         "source": "trading_pool",
         "amount": 50.00
       }
     }'
   ```

2. **Check Budget Allocation:**
   ```bash
   curl http://127.0.0.1:8000/api/auto-discovery/status | jq '.budget_allocation'
   ```

3. **Cancel Order:**
   ```bash
   curl -X POST "http://127.0.0.1:8000/api/orders/{order_id}/cancel"
   ```

4. **Verify Funds Returned:**
   ```bash
   curl http://127.0.0.1:8000/api/auto-discovery/status | jq '.budget_allocation'
   # trading_pool should be increased by 50.00
   ```

---

## Implementation Status

### Backend

- ✅ Allocation tracking implemented
- ✅ Fund return on cancellation implemented
- ✅ Budget allocation updates implemented
- ⚠️ Fund return logging (may need enhancement)

### Frontend

- ✅ Sends allocation data with orders
- ✅ Receives budget allocation in responses
- ✅ Displays budget allocation to users
- ℹ️ Fund return is automatic (no frontend action needed)

---

## Related Documentation

- `INTEGRATION_TESTING_GUIDE.md` - Testing guide (mentions fund return)
- `FRONTEND_BACKEND_COORDINATION.md` - API coordination
- `FRONTEND_OPPORTUNITY_API_GUIDE.md` - Opportunity API guide

---

## Notes

- Fund return is automatic - users don't need to request it
- Allocation info must be stored for fund return to work
- Budget allocation updates reflect current state (includes returns)
- Frontend doesn't need special handling for fund return


