# Frontend Opportunity API Guide

**Date:** January 2025  
**Status:** Updated with ID-based endpoint support

---

## Overview

This guide documents the frontend's interaction with the opportunity API endpoints, including the new ID-based order placement endpoint and opportunity caching.

---

## Order Placement Endpoints

### 1. ID-Based Endpoint (Primary)

**Endpoint:** `POST /api/opportunities/{id}/place-order`

**Purpose:** Place order using cached opportunity ID (more efficient)

**Request:**
- **URL Parameter:** `{id}` - Opportunity ID (e.g., `opp_BTCEUR_0_1234567890`)
- **Query Parameters:**
  - `auto_execute` (optional, boolean): Auto-execute when conditions met
- **Request Body:**
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
  Or empty body `{}` if no allocation:
  ```json
  {}
  ```

**Response:**
```json
{
  "order_id": "order_12345",
  "entry_order_id": "entry_12345",
  "status": "Pending",
  "message": "Order placed successfully",
  "allocation": {
    "source": "trading_pool",
    "amount": 100.50
  },
  "budget_allocation": {
    "reserve": 4.24,
    "whitelist": 3.96,
    "auto_discovery": 5.93,
    "trading_pool": 9.89
  }
}
```

**Error Responses:**
- `404 Not Found`: Opportunity not found in backend cache
- `400 Bad Request`: Invalid allocation or validation error
- `500 Internal Server Error`: Server error

**Fallback Behavior:**
- If ID-based endpoint fails (404, 500, or network error), frontend automatically falls back to full data endpoint
- Fallback is transparent to the user

---

### 2. Full Data Endpoint (Fallback)

**Endpoint:** `POST /api/opportunities/place-order`

**Purpose:** Place order with full opportunity data (fallback when ID-based fails)

**Request:**
- **Query Parameters:**
  - `auto_execute` (optional, boolean): Auto-execute when conditions met
- **Request Body:** Full opportunity object
  ```json
  {
    "id": "opp_BTCEUR_0_1234567890",
    "symbol": "BTCEUR",
    "opportunity_type": "SELL",
    "current_price": 75194.41,
    "target_price": 71810.66,
    "stop_loss": 76698.3,
    "quantity": 0.0001,
    "position_value": 7.5,
    "confidence": 0.9,
    "risk_reward_ratio": 2.25,
    "allocation": {
      "source": "trading_pool",
      "amount": 100.50,
      "position_value": 100.50
    },
    // ... other opportunity fields
  }
  ```

**Response:** Same as ID-based endpoint

---

## Frontend Implementation

### API Function: `placeOpportunityOrder()`

**Location:** `src/shared/api.js`

**Behavior:**
1. Checks if opportunity has an ID
2. If ID exists:
   - Tries ID-based endpoint first
   - Sends only allocation data (if provided) or empty body
   - If successful, returns result
   - If fails (404, 500, network), falls back to full data endpoint
3. If no ID or fallback needed:
   - Uses full data endpoint
   - Sends complete opportunity object

**Code Flow:**
```javascript
placeOpportunityOrder(opportunity, autoExecute)
  ↓
Has opportunity.id?
  ↓ YES
Try: POST /api/opportunities/{id}/place-order
  ↓
Success? → Return result
  ↓ NO (404/500/network)
Fallback to: POST /api/opportunities/place-order (full data)
  ↓
Return result
```

---

## Opportunity Caching

### Cache Implementation

**Location:** `src/views/OpportunitiesView.vue`

**Cache Structure:**
- **Type:** `Map<string, any>` (keyed by opportunity ID)
- **Storage:** In-memory, component-scoped
- **Lifetime:** Until component unmounts or opportunity expires

**Cache Operations:**

1. **Cache Opportunity:**
   ```javascript
   cacheOpportunity(opportunity)
   // Stores: { ...opportunity, cachedAt: timestamp }
   ```

2. **Get Cached Opportunity:**
   ```javascript
   const cached = getCachedOpportunity(opportunityId)
   ```

3. **Clear Expired Opportunities:**
   ```javascript
   clearExpiredOpportunities()
   // Removes opportunities where expires_at < now
   ```

### When Opportunities Are Cached

- **On Fetch:** When `fetchSymbolData()` successfully fetches opportunities
- **Automatic:** All opportunities from API response are cached
- **Cleanup:** Expired opportunities are removed automatically

### Cache Benefits

1. **ID-Based Orders:** Enables efficient order placement using cached IDs
2. **Reduced Payload:** ID-based endpoint sends only allocation data
3. **Performance:** Faster order placement (smaller request body)
4. **Reliability:** Fallback ensures orders always work

---

## Error Handling

### ID-Based Endpoint Errors

**404 Not Found:**
- Opportunity not in backend cache
- Frontend automatically falls back to full data endpoint
- User sees no error (transparent fallback)

**500 Server Error:**
- Backend error
- Frontend automatically falls back to full data endpoint
- User sees no error (transparent fallback)

**Network Errors:**
- Connection failures
- Frontend automatically falls back to full data endpoint
- User sees no error (transparent fallback)

### Full Data Endpoint Errors

**400 Bad Request:**
- Invalid opportunity data
- Invalid allocation
- Insufficient funds
- User sees error message

**500 Server Error:**
- Backend error
- User sees error message with retry option

---

## Usage Examples

### Example 1: Place Order with ID and Allocation

```javascript
const opportunity = {
  id: 'opp_BTCEUR_0_1234567890',
  symbol: 'BTCEUR',
  // ... other fields
  allocation: {
    source: 'trading_pool',
    amount: 100.50,
    position_value: 100.50
  }
}

const result = await placeOpportunityOrder(opportunity, false)
// Tries: POST /api/opportunities/opp_BTCEUR_0_1234567890/place-order
// Body: { "allocation": { ... } }
```

### Example 2: Place Order with ID, No Allocation

```javascript
const opportunity = {
  id: 'opp_BTCEUR_0_1234567890',
  symbol: 'BTCEUR',
  // ... other fields
  // No allocation
}

const result = await placeOpportunityOrder(opportunity, false)
// Tries: POST /api/opportunities/opp_BTCEUR_0_1234567890/place-order
// Body: {}
```

### Example 3: Place Order Without ID (Fallback)

```javascript
const opportunity = {
  symbol: 'BTCEUR',
  // ... other fields
  // No ID
}

const result = await placeOpportunityOrder(opportunity, false)
// Uses: POST /api/opportunities/place-order
// Body: { full opportunity object }
```

---

## Testing

### Test ID-Based Endpoint

```bash
# Test with valid ID and allocation
curl -X POST "http://127.0.0.1:8000/api/opportunities/opp_BTCEUR_0_1234567890/place-order" \
  -H "Content-Type: application/json" \
  -d '{
    "allocation": {
      "source": "trading_pool",
      "amount": 100.50,
      "position_value": 100.50
    }
  }'

# Test with valid ID, no allocation
curl -X POST "http://127.0.0.1:8000/api/opportunities/opp_BTCEUR_0_1234567890/place-order" \
  -H "Content-Type: application/json" \
  -d '{}'

# Test with invalid ID (should return 404)
curl -X POST "http://127.0.0.1:8000/api/opportunities/invalid_id/place-order" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Test Fallback

1. Place order with valid ID → Should use ID-based endpoint
2. Place order with invalid ID → Should fallback to full data endpoint
3. Place order without ID → Should use full data endpoint directly

---

## Backend Requirements

### ID-Based Endpoint

The backend must:
1. Accept opportunity ID in URL path
2. Look up opportunity from cache by ID
3. Accept allocation data in request body (or empty body)
4. Return 404 if opportunity not found in cache
5. Validate allocation data if provided
6. Place order using cached opportunity data

### Full Data Endpoint

The backend must:
1. Accept full opportunity object in request body
2. Validate all opportunity fields
3. Place order using provided data
4. Work as fallback when ID-based endpoint fails

---

## Related Documentation

- `FRONTEND_BACKEND_COORDINATION.md` - General API coordination
- `BACKEND_WHITELIST_VERIFICATION.md` - Whitelist logic
- `INTEGRATION_TESTING_GUIDE.md` - Testing guide
- `MEDIUM_PRIORITY_TASKS_STATUS.md` - Implementation status


