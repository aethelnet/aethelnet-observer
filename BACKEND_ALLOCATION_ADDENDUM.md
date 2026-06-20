# Backend Order Placement - Fund Allocation Addendum

**Add to:** Backend Order Placement & Status Fix Guide  
**Date:** January 2025

---

## Fund Allocation Support in Order Placement

### Overview
Frontend will send allocation data with order placement requests, allowing users to specify which budget pool (trading_pool, whitelist, auto_discovery, reserve) to allocate funds from.

### Required Changes to Order Placement Endpoint

**File:** `backend/api/predictions.py` - `place_opportunity_order_by_data()`

#### 1. Accept Allocation Data in Request

**Request Body Format:**
```json
{
  "id": "opp_abc123",
  "symbol": "BTCEUR",
  // ... other opportunity fields ...
  "allocation": {
    "source": "trading_pool",
    "amount": 100.50,
    "position_value": 100.50
  }
}
```

**Allocation Object:**
- `source` (string, required if allocation provided): One of `"trading_pool"`, `"whitelist"`, `"auto_discovery"`, `"reserve"`
- `amount` (number, required if allocation provided): Dollar amount to allocate
- `position_value` (number, required if allocation provided): New position value

**Note:** `allocation` is optional - if not provided, use original `position_value` from opportunity.

#### 2. Validate Allocation Data

**Validation Rules:**
```python
if 'allocation' in opportunity_data:
    allocation = opportunity_data['allocation']
    source = allocation.get('source')
    amount = allocation.get('amount')
    position_value = allocation.get('position_value')
    
    # Validate source
    valid_sources = ['trading_pool', 'whitelist', 'auto_discovery', 'reserve']
    if source not in valid_sources:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid allocation source: {source}. Valid sources: {', '.join(valid_sources)}"
        )
    
    # Validate amount
    if not amount or amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Allocation amount must be positive"
        )
    
    # Get current budget allocation
    auto_engine = get_auto_discovery_engine()
    budget = auto_engine.budget_allocation
    
    # Map source to budget field
    source_map = {
        'trading_pool': 'trading_pool',
        'whitelist': 'whitelist',
        'auto_discovery': 'auto_discovery',
        'reserve': 'reserve'
    }
    available = getattr(budget, source_map[source], 0)
    
    # Validate sufficient funds
    if amount > available:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient funds in {source}. Available: ${available:.2f}, Requested: ${amount:.2f}",
            extra={
                "available_funds": available,
                "requested_amount": amount,
                "pool": source
            }
        )
    
    # Reserve pool protection (optional)
    if source == 'reserve' and not allocation.get('confirm_reserve', False):
        raise HTTPException(
            status_code=400,
            detail="Reserve pool allocation requires explicit confirmation. Set 'confirm_reserve': true"
        )
```

#### 3. Deduct Funds from Budget Pool

**After Order Placement Success, Before Returning Response:**
```python
# After order is successfully placed and registered
if 'allocation' in opportunity_data:
    allocation = opportunity_data['allocation']
    source = allocation['source']
    amount = allocation['amount']
    
    # Deduct from budget
    source_map = {
        'trading_pool': 'trading_pool',
        'whitelist': 'whitelist',
        'auto_discovery': 'auto_discovery',
        'reserve': 'reserve'
    }
    budget_field = source_map[source]
    current_value = getattr(auto_engine.budget_allocation, budget_field, 0)
    setattr(auto_engine.budget_allocation, budget_field, current_value - amount)
    
    # Store allocation info for potential refund on cancel/expire
    # (Add to order tracker or separate allocation tracker)
    order_tracker.store_allocation_info(
        order_id=order_id,
        opportunity_id=opportunity_id,
        allocation_source=source,
        allocation_amount=amount
    )
```

#### 4. Update Response to Include Allocation Info

**Enhanced Success Response:**
```python
response = {
    "success": True,
    "order_id": order_id if order_id else None,
    "status": "Pending",
    "opportunity_id": opportunity_id,
    "symbol": opportunity_data.get('symbol'),
    # ... other fields ...
}

# Add allocation info if provided
if 'allocation' in opportunity_data:
    allocation = opportunity_data['allocation']
    source = allocation['source']
    budget = auto_engine.budget_allocation
    source_map = {
        'trading_pool': 'trading_pool',
        'whitelist': 'whitelist',
        'auto_discovery': 'auto_discovery',
        'reserve': 'reserve'
    }
    remaining = getattr(budget, source_map[source], 0)
    
    response["allocation"] = {
        "source": source,
        "amount": allocation['amount'],
        "remaining_in_pool": remaining
    }
    
    # Optional: Include updated budget allocation
    response["budget_allocation"] = {
        "reserve": budget.reserve,
        "whitelist": budget.whitelist,
        "auto_discovery": budget.auto_discovery,
        "trading_pool": budget.trading_pool
    }

return response
```

### Fund Return on Order Cancel/Expire

**File:** `backend/services/order_tracker.py`

**When order is cancelled or expires:**
```python
def cancel_order(self, order_id: str, reason: str = "cancelled"):
    # ... existing cancel logic ...
    
    # Return funds to original pool if allocation exists
    allocation_info = self.get_allocation_info(order_id)
    if allocation_info:
        auto_engine = get_auto_discovery_engine()
        budget = auto_engine.budget_allocation
        source = allocation_info['allocation_source']
        amount = allocation_info['allocation_amount']
        
        source_map = {
            'trading_pool': 'trading_pool',
            'whitelist': 'whitelist',
            'auto_discovery': 'auto_discovery',
            'reserve': 'reserve'
        }
        budget_field = source_map[source]
        current_value = getattr(budget, budget_field, 0)
        setattr(budget, budget_field, current_value + amount)
        
        # Remove allocation info
        self.remove_allocation_info(order_id)
```

### Allocation Storage

**Add to Order Tracker:**
```python
class OrderTracker:
    def __init__(self):
        # ... existing init ...
        self.order_allocations: Dict[str, Dict] = {}  # order_id -> allocation info
    
    def store_allocation_info(self, order_id: str, opportunity_id: str, 
                             allocation_source: str, allocation_amount: float):
        self.order_allocations[order_id] = {
            'opportunity_id': opportunity_id,
            'allocation_source': allocation_source,
            'allocation_amount': allocation_amount,
            'timestamp': time.time()
        }
    
    def get_allocation_info(self, order_id: str) -> Optional[Dict]:
        return self.order_allocations.get(order_id)
    
    def remove_allocation_info(self, order_id: str):
        self.order_allocations.pop(order_id, None)
```

### Testing Checklist

**Allocation Validation:**
- [ ] Order with valid allocation succeeds
- [ ] Order with allocation exceeding available funds returns 400 error
- [ ] Order with invalid pool name returns 400 error
- [ ] Order with negative amount returns 400 error
- [ ] Order with zero amount returns 400 error
- [ ] Order without allocation uses original position_value

**Fund Deduction:**
- [ ] Funds are deducted from correct pool on order placement
- [ ] Budget allocation is updated immediately
- [ ] Response includes remaining funds in pool
- [ ] Response includes updated budget allocation (optional)

**Reserve Pool:**
- [ ] Reserve allocation without confirmation returns 400 error
- [ ] Reserve allocation with confirmation succeeds
- [ ] Reserve pool is properly protected

**Fund Return:**
- [ ] Cancelled orders return funds to original pool
- [ ] Expired orders return funds to original pool
- [ ] Budget allocation updates when funds are returned
- [ ] Allocation info is cleaned up after refund

### Integration with Existing Fixes

This allocation feature should be integrated with the existing order placement fixes:

1. **Order ID Fix:** Ensure allocation validation happens before order placement, so if allocation fails, no order is created
2. **Status Persistence:** Allocation deduction should happen after order is successfully registered
3. **Error Handling:** Allocation errors should follow the same error response format as other order placement errors

### Notes

- Allocation is **optional** - existing orders without allocation should continue to work
- Reserve pool protection is recommended but can be implemented later
- Fund return on cancel/expire is important for user experience
- Consider adding allocation info to order status endpoint for tracking


