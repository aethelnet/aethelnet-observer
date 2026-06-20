# Frontend Implementation Status - Actionable Trading Opportunities

**Date:** 2026-01-01  
**Status:** ✅ **COMPLETE** - Ready for backend integration

---

## Overview

The frontend has been fully prepared for the actionable trading opportunities feature. All UI components, API integrations, and order management systems are in place and ready to work with the backend implementation.

---

## Implementation Summary

### 1. API Client Functions (`src/shared/api.js`)

✅ **placeOpportunityOrder(opportunity, autoExecute)**
- Endpoint: `POST /api/opportunities/place-order`
- Sends full opportunity object in request body
- Supports `auto_execute` query parameter
- Returns order placement response with order IDs

✅ **getOpportunityOrderStatus(opportunityId)**
- Endpoint: `GET /api/opportunities/{opportunity_id}/order-status`
- Fetches current order status for an opportunity
- Returns status object with order state

### 2. Order Preview Modal (`src/components/OrderPreviewModal.vue`)

✅ **Complete Order Preview Component**
- Displays opportunity summary (symbol, type, confidence)
- Shows entry conditions:
  - Time window (start - end with countdown)
  - Price range (min - max with trigger price)
  - Current price comparison
- Displays trade details:
  - Quantity and position value
  - Target price and expected profit
  - Stop loss and max loss
  - Risk/reward ratio
- Shows order configuration (order type, time in force)
- Confirm/Cancel buttons with loading states
- Responsive design with light/dark mode support

### 3. Enhanced Opportunities View (`src/views/OpportunitiesView.vue`)

✅ **Entry Window Display**
- Shows entry time window when available
- Displays entry price range (min - max)
- Shows trigger price with tolerance
- Validates entry window before allowing order placement

✅ **Order Placement UI**
- "Place Limit Order" button on each opportunity
- Button disabled if entry window expired
- Opens Order Preview Modal on click
- Shows order status badge when order is placed

✅ **Order Status Tracking**
- Visual status badges: "Pending", "Active", "Completed", "Cancelled"
- Color-coded status indicators
- Automatic status updates every 5 seconds
- Status persistence across data refreshes

✅ **Enhanced Opportunity Display**
- Entry conditions section (time window, price range)
- Stop loss display
- Quantity display (when available)
- Improved countdown label: "Valid for: Xm Ys"
- Visual highlighting for opportunities with active orders

### 4. Data Handling

✅ **Opportunity ID Management**
- Generates IDs for opportunities without them (backward compatible)
- Uses IDs as keys for order status tracking
- Preserves IDs across data refreshes

✅ **Entry Window Validation**
- Checks if entry window is still valid
- Disables "Place Order" button if window expired
- Calculates remaining time in entry window

✅ **Order Status Management**
- Tracks order statuses by opportunity ID
- Fetches statuses for all opportunities with orders
- Updates statuses automatically every 5 seconds

---

## Expected Backend Data Structure

The frontend expects opportunities with the following structure:

```typescript
interface Opportunity {
  id: string  // Required for order tracking
  symbol: string
  opportunity_type: 'BUY' | 'SELL'
  confidence: number  // 0-1
  target_price: number
  stop_loss: number
  potential_profit_percent: number
  expected_move_percent: number
  
  // Entry conditions (new)
  entry_price_range?: {
    min: number
    max: number
    trigger: number
    tolerance?: number
  }
  
  entry_time_window?: {
    start: string  // ISO datetime
    end: string    // ISO datetime
    expires_at: string
  }
  
  // Execution details (new)
  execution?: {
    order_type: 'LIMIT' | 'MARKET'
    quantity: number
    position_value: number
    time_in_force?: string
  }
  
  // Risk metrics (new)
  risk_metrics?: {
    max_loss: number
    max_loss_percent: number
    risk_reward_ratio: number
    expected_profit?: number
  }
  
  // Existing fields
  expires_at: string
  created_at: string
  time_horizon_minutes?: number
}
```

---

## API Endpoints Used

### Order Placement
- **Endpoint:** `POST /api/opportunities/place-order`
- **Method:** POST
- **Body:** Full opportunity object (JSON)
- **Query Params:** `auto_execute` (optional boolean)
- **Response:** 
  ```json
  {
    "order_id": "string",
    "entry_order_id": "string",
    "status": "Pending",
    "message": "Order placed successfully"
  }
  ```

### Order Status
- **Endpoint:** `GET /api/opportunities/{opportunity_id}/order-status`
- **Method:** GET
- **Response:**
  ```json
  {
    "status": "Pending" | "Active" | "Completed" | "Cancelled",
    "order_id": "string",
    "entry_order_id": "string",
    "take_profit_order_id": "string",
    "stop_loss_order_id": "string"
  }
  ```

---

## UI Flow

1. **User sees opportunity** → Entry window and price range displayed
2. **User clicks "Place Limit Order"** → Order Preview Modal opens
3. **User reviews details** → All trade information visible
4. **User clicks "Confirm Order"** → Order sent to backend
5. **Order placed** → Button changes to status badge
6. **Status updates** → Automatically refreshes every 5 seconds

---

## Features Ready

✅ Entry window display (time + price range)  
✅ Order preview modal with full details  
✅ Order placement with full opportunity object  
✅ Order status tracking and display  
✅ Automatic status updates  
✅ Entry window validation  
✅ Visual status indicators  
✅ Error handling and toast notifications  
✅ Backward compatibility (works with opportunities without entry windows)  

---

## Testing Checklist

- [x] Order Preview Modal displays correctly
- [x] Entry windows show time and price ranges
- [x] "Place Order" button disabled when window expired
- [x] Order placement sends full opportunity object
- [x] Order status badges display correctly
- [x] Status updates automatically
- [x] Error handling works
- [x] Toast notifications appear
- [x] Backward compatible with old opportunity format

---

## Notes

- The frontend is fully backward compatible. If opportunities don't have entry windows, they still display normally (just without the "Place Order" button or entry conditions).
- Order status tracking only works for opportunities with IDs. The frontend generates IDs for opportunities that don't have them, but these won't persist across backend refreshes.
- The frontend expects the backend to provide all opportunity data in the `/api/opportunities/symbols` endpoint response.

---

## Status: ✅ READY FOR INTEGRATION

The frontend is complete and ready to work with the backend implementation. All components are in place, tested, and waiting for the backend to start providing enhanced opportunity data with entry windows and execution details.



