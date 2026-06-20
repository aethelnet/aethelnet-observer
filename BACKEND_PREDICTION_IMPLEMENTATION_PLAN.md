# Backend Prediction & Opportunities Implementation Plan

**Date:** January 1, 2025  
**Purpose:** Guide for backend agent to implement real prediction and opportunities endpoints  
**Status:** Ready for Implementation

---

## Overview

This plan provides step-by-step instructions for implementing the `/api/predictions` and `/api/opportunities` endpoints to replace frontend mock data with real ML prediction engine outputs.

---

## Current State

### Frontend Expectations

The frontend currently uses mock data when these endpoints are unavailable:
- **Predictions:** `/api/predictions?symbol={symbol}`
- **Opportunities:** `/api/opportunities`

Both views work with mock data, but will automatically switch to real data once endpoints are implemented.

### Backend Context

Based on existing codebase:
- ML prediction engine exists and generates signals
- Physics factors are calculated (momentum, strain, force, etc.)
- Signal history is persisted
- Market data is available via `/api/dashboard/market-data`

---

## Implementation Plan

### Phase 1: Predictions Endpoint (`/api/predictions`)

#### 1.1 Endpoint Specification

**Route:** `GET /api/predictions`

**Query Parameters:**
- `symbol` (optional): Filter by symbol (e.g., `?symbol=BTCUSDT`)
  - If omitted, return predictions for all active symbols

**Response Format:**
```json
{
  "symbol": "BTCUSDT",
  "current_price": 87813.67,
  "predictions": [
    {
      "time_horizon_minutes": 5,
      "predicted_price": 88000.0,
      "confidence": 0.75,
      "direction": "UP",
      "expected_move_percent": 2.1,
      "timestamp": "2024-12-31T12:05:00Z"
    },
    {
      "time_horizon_minutes": 15,
      "predicted_price": 88500.0,
      "confidence": 0.65,
      "direction": "UP",
      "expected_move_percent": 3.8,
      "timestamp": "2024-12-31T12:15:00Z"
    },
    {
      "time_horizon_minutes": 30,
      "predicted_price": 89000.0,
      "confidence": 0.55,
      "direction": "UP",
      "expected_move_percent": 5.2,
      "timestamp": "2024-12-31T12:30:00Z"
    }
  ],
  "last_update": "2024-12-31T12:00:00Z"
}
```

**Field Descriptions:**
- `symbol`: Trading pair symbol (e.g., "BTCUSDT")
- `current_price`: Current market price
- `predictions`: Array of prediction objects
  - `time_horizon_minutes`: Prediction time horizon (5, 15, 30, 60, etc.)
  - `predicted_price`: Expected price at that time
  - `confidence`: Confidence level (0.0 to 1.0, where 1.0 = 100%)
  - `direction`: "UP", "DOWN", or "NEUTRAL"
  - `expected_move_percent`: Expected percentage change (positive for UP, negative for DOWN)
  - `timestamp`: ISO timestamp for when this prediction is valid
- `last_update`: When predictions were last calculated

#### 1.2 Implementation Steps

**Step 1: Create Prediction Model/Function**

```python
def generate_predictions(symbol: str, current_price: float, 
                         signal_data: dict, physics_factors: dict,
                         time_horizons: list = [5, 15, 30]) -> list:
    """
    Generate price predictions for multiple time horizons.
    
    Args:
        symbol: Trading pair symbol
        current_price: Current market price
        signal_data: Current signal data (signal, signal_strength, etc.)
        physics_factors: Physics factors (momentum, strain, force, etc.)
        time_horizons: List of time horizons in minutes
    
    Returns:
        List of prediction dictionaries
    """
    predictions = []
    
    # Extract signal information
    signal = signal_data.get('signal', 0)  # Z-score
    signal_strength = signal_data.get('signal_strength', 'NEUTRAL')
    
    # Determine base direction
    direction = 'NEUTRAL'
    if 'BUY' in signal_strength:
        direction = 'UP'
    elif 'SELL' in signal_strength:
        direction = 'DOWN'
    
    # Calculate base move percentage from signal strength
    # Stronger signals = larger expected moves
    base_move = abs(signal) * 0.5  # Adjust multiplier based on your model
    
    # Use physics factors to refine predictions
    momentum = physics_factors.get('momentum', 0)
    force = physics_factors.get('force', 0)
    
    # Adjust base move based on physics
    adjusted_move = base_move * (1 + momentum * 0.3 + force * 0.2)
    
    # Generate predictions for each time horizon
    for horizon in time_horizons:
        # Confidence decreases with longer time horizons
        confidence = max(0.3, 0.9 - (horizon / 60) * 0.3)
        
        # Move percentage scales with time (longer = larger moves)
        move_scale = horizon / 15.0  # Normalize to 15 minutes
        move_percent = adjusted_move * move_scale
        
        # Clamp move percentage (e.g., max 10% for 30 minutes)
        max_move = min(10.0, horizon * 0.3)
        move_percent = min(move_percent, max_move)
        
        # Calculate predicted price
        if direction == 'UP':
            predicted_price = current_price * (1 + move_percent / 100)
        elif direction == 'DOWN':
            predicted_price = current_price * (1 - move_percent / 100)
        else:
            predicted_price = current_price  # Neutral = no change
        
        # Adjust confidence based on signal strength
        if 'STRONG' in signal_strength:
            confidence = min(0.95, confidence + 0.15)
        elif signal_strength in ['BUY', 'SELL']:
            confidence = min(0.85, confidence + 0.10)
        
        prediction = {
            "time_horizon_minutes": horizon,
            "predicted_price": round(predicted_price, 2),
            "confidence": round(confidence, 2),
            "direction": direction,
            "expected_move_percent": round(move_percent if direction == 'UP' else -move_percent, 2),
            "timestamp": (datetime.now() + timedelta(minutes=horizon)).isoformat()
        }
        predictions.append(prediction)
    
    return predictions
```

**Step 2: Create API Endpoint**

```python
@app.get("/api/predictions")
async def get_predictions(symbol: Optional[str] = None):
    """
    Get ML prediction engine forecasts for future price movements.
    
    Query params:
        symbol: Optional symbol filter (e.g., BTCUSDT)
    """
    try:
        # Get market data
        market_data = await get_market_data()
        
        # Filter by symbol if provided
        if symbol:
            market_data = [d for d in market_data if d['symbol'] == symbol.upper()]
        
        results = []
        
        for data in market_data:
            symbol_name = data['symbol']
            current_price = data['price']
            
            # Get signal data
            signal_data = {
                'signal': data.get('signal', 0),
                'signal_strength': data.get('signal_strength', 'NEUTRAL')
            }
            
            # Get physics factors for this symbol
            physics_factors = await get_physics_factors(symbol_name)
            
            # Generate predictions
            predictions = generate_predictions(
                symbol=symbol_name,
                current_price=current_price,
                signal_data=signal_data,
                physics_factors=physics_factors,
                time_horizons=[5, 15, 30]  # Can be configurable
            )
            
            result = {
                "symbol": symbol_name,
                "current_price": current_price,
                "predictions": predictions,
                "last_update": datetime.now().isoformat()
            }
            
            results.append(result)
        
        # If symbol filter provided, return single object; otherwise return array
        if symbol and len(results) == 1:
            return results[0]
        elif symbol and len(results) == 0:
            return {
                "symbol": symbol.upper(),
                "current_price": 0,
                "predictions": [],
                "last_update": datetime.now().isoformat()
            }
        else:
            return results
            
    except Exception as e:
        logger.error(f"Error generating predictions: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate predictions")
```

**Step 3: Helper Functions**

```python
async def get_physics_factors(symbol: str) -> dict:
    """
    Get physics factors for a symbol.
    Uses existing /api/physics endpoint logic.
    """
    # Use your existing physics calculation logic
    # Return dict with: momentum, strain, force, squeeze, flow, entropy, jerk, sympathy
    pass

async def get_market_data() -> list:
    """
    Get current market data.
    Uses existing /api/dashboard/market-data logic.
    """
    # Use your existing market data fetching logic
    pass
```

**Step 4: Caching (Optional but Recommended)**

```python
from functools import lru_cache
from datetime import datetime, timedelta

# Cache predictions for 30 seconds to avoid excessive calculations
prediction_cache = {}

def get_cached_predictions(symbol: str):
    """Get cached predictions if still valid."""
    if symbol in prediction_cache:
        cached_data, timestamp = prediction_cache[symbol]
        if datetime.now() - timestamp < timedelta(seconds=30):
            return cached_data
    return None

def cache_predictions(symbol: str, predictions: dict):
    """Cache predictions with timestamp."""
    prediction_cache[symbol] = (predictions, datetime.now())
```

---

### Phase 2: Opportunities Endpoint (`/api/opportunities`)

#### 2.1 Endpoint Specification

**Route:** `GET /api/opportunities`

**Query Parameters:**
- `symbol` (optional): Filter by symbol
- `min_confidence` (optional): Minimum confidence threshold (0-1)
- `urgency` (optional): Filter by urgency ("HIGH", "MEDIUM", "LOW")

**Response Format:**
```json
[
  {
    "symbol": "BTCUSDT",
    "opportunity_type": "BUY",
    "predicted_move_percent": 3.5,
    "time_horizon_minutes": 10,
    "confidence": 0.82,
    "current_price": 87813.67,
    "target_price": 90887.65,
    "stop_loss": 85000.0,
    "risk_reward_ratio": 2.5,
    "urgency": "HIGH",
    "expires_at": "2024-12-31T12:10:00Z",
    "created_at": "2024-12-31T12:00:00Z"
  }
]
```

**Field Descriptions:**
- `symbol`: Trading pair symbol
- `opportunity_type`: "BUY" or "SELL"
- `predicted_move_percent`: Expected price movement percentage
- `time_horizon_minutes`: When the move is expected
- `confidence`: ML confidence (0.0 to 1.0)
- `current_price`: Current market price
- `target_price`: Expected price at target
- `stop_loss`: Recommended stop loss price
- `risk_reward_ratio`: Calculated risk/reward ratio
- `urgency`: "HIGH", "MEDIUM", or "LOW" based on time and confidence
- `expires_at`: When opportunity expires (time_horizon from now)
- `created_at`: When opportunity was identified

#### 2.2 Implementation Steps

**Step 1: Create Opportunity Detection Function**

```python
def identify_opportunities(symbol: str, predictions: list, 
                       current_price: float, signal_data: dict) -> list:
    """
    Identify trade opportunities from predictions.
    
    Args:
        symbol: Trading pair symbol
        predictions: List of predictions from generate_predictions()
        current_price: Current market price
        signal_data: Current signal data
    
    Returns:
        List of opportunity dictionaries
    """
    opportunities = []
    
    # Only consider predictions with sufficient confidence
    min_confidence_threshold = 0.6
    
    for pred in predictions:
        if pred['confidence'] < min_confidence_threshold:
            continue
        
        # Only create opportunities for UP or DOWN predictions
        if pred['direction'] == 'NEUTRAL':
            continue
        
        # Calculate target price (predicted price)
        target_price = pred['predicted_price']
        
        # Calculate stop loss (2% below entry for BUY, 2% above for SELL)
        stop_loss_pct = 0.02
        if pred['direction'] == 'UP':
            stop_loss = current_price * (1 - stop_loss_pct)
        else:
            stop_loss = current_price * (1 + stop_loss_pct)
        
        # Calculate risk/reward ratio
        potential_profit = abs(target_price - current_price)
        potential_loss = abs(current_price - stop_loss)
        risk_reward = potential_profit / potential_loss if potential_loss > 0 else 0
        
        # Only create opportunity if risk/reward is favorable (>= 1.5)
        if risk_reward < 1.5:
            continue
        
        # Determine urgency
        # HIGH: High confidence + short time horizon
        # MEDIUM: Medium confidence or medium time horizon
        # LOW: Lower confidence or longer time horizon
        if pred['confidence'] >= 0.75 and pred['time_horizon_minutes'] <= 15:
            urgency = 'HIGH'
        elif pred['confidence'] >= 0.65 or pred['time_horizon_minutes'] <= 30:
            urgency = 'MEDIUM'
        else:
            urgency = 'LOW'
        
        opportunity = {
            "symbol": symbol,
            "opportunity_type": "BUY" if pred['direction'] == 'UP' else "SELL",
            "predicted_move_percent": pred['expected_move_percent'],
            "time_horizon_minutes": pred['time_horizon_minutes'],
            "confidence": pred['confidence'],
            "current_price": current_price,
            "target_price": round(target_price, 2),
            "stop_loss": round(stop_loss, 2),
            "risk_reward_ratio": round(risk_reward, 2),
            "urgency": urgency,
            "expires_at": pred['timestamp'],
            "created_at": datetime.now().isoformat()
        }
        
        opportunities.append(opportunity)
    
    return opportunities
```

**Step 2: Create API Endpoint**

```python
@app.get("/api/opportunities")
async def get_opportunities(
    symbol: Optional[str] = None,
    min_confidence: Optional[float] = None,
    urgency: Optional[str] = None
):
    """
    Get upcoming trade opportunities identified by ML prediction engine.
    
    Query params:
        symbol: Optional symbol filter
        min_confidence: Minimum confidence threshold (0-1)
        urgency: Filter by urgency (HIGH, MEDIUM, LOW)
    """
    try:
        # Get market data
        market_data = await get_market_data()
        
        # Filter by symbol if provided
        if symbol:
            market_data = [d for d in market_data if d['symbol'] == symbol.upper()]
        
        all_opportunities = []
        
        for data in market_data:
            symbol_name = data['symbol']
            current_price = data['price']
            
            # Get signal data
            signal_data = {
                'signal': data.get('signal', 0),
                'signal_strength': data.get('signal_strength', 'NEUTRAL')
            }
            
            # Get physics factors
            physics_factors = await get_physics_factors(symbol_name)
            
            # Generate predictions
            predictions = generate_predictions(
                symbol=symbol_name,
                current_price=current_price,
                signal_data=signal_data,
                physics_factors=physics_factors,
                time_horizons=[5, 10, 15, 30]  # Multiple horizons for opportunities
            )
            
            # Identify opportunities from predictions
            opportunities = identify_opportunities(
                symbol=symbol_name,
                predictions=predictions,
                current_price=current_price,
                signal_data=signal_data
            )
            
            all_opportunities.extend(opportunities)
        
        # Apply filters
        if min_confidence is not None:
            all_opportunities = [
                o for o in all_opportunities 
                if o['confidence'] >= min_confidence
            ]
        
        if urgency:
            all_opportunities = [
                o for o in all_opportunities 
                if o['urgency'].upper() == urgency.upper()
            ]
        
        # Sort by confidence (highest first)
        all_opportunities.sort(key=lambda x: x['confidence'], reverse=True)
        
        return all_opportunities
        
    except Exception as e:
        logger.error(f"Error generating opportunities: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate opportunities")
```

---

## Integration with Existing Code

### Using Existing Components

**1. Market Data:**
```python
# Reuse existing market data endpoint logic
# From: /api/dashboard/market-data
```

**2. Physics Factors:**
```python
# Reuse existing physics calculation
# From: /api/physics endpoint
```

**3. Signal Data:**
```python
# Reuse existing signal calculation
# From: /api/signals or /api/dashboard/market-data
```

### Database Integration (Optional)

If you want to persist predictions/opportunities:

```python
# Add prediction storage
async def store_predictions(symbol: str, predictions: dict):
    """Store predictions in database for historical tracking."""
    # Use your existing database connection
    pass

# Add opportunity storage
async def store_opportunity(opportunity: dict):
    """Store opportunity in database."""
    # Use your existing database connection
    pass
```

---

## Testing

### Test Cases

**1. Predictions Endpoint:**
```bash
# Test with symbol
curl http://localhost:8000/api/predictions?symbol=BTCUSDT

# Test without symbol (all symbols)
curl http://localhost:8000/api/predictions
```

**2. Opportunities Endpoint:**
```bash
# Test all opportunities
curl http://localhost:8000/api/opportunities

# Test with filters
curl http://localhost:8000/api/opportunities?min_confidence=0.7&urgency=HIGH
curl http://localhost:8000/api/opportunities?symbol=BTCUSDT
```

### Expected Behavior

1. **Predictions:**
   - Returns predictions for requested symbol(s)
   - Predictions have valid timestamps in future
   - Confidence values between 0.0 and 1.0
   - Directions are UP, DOWN, or NEUTRAL

2. **Opportunities:**
   - Returns only opportunities with confidence >= 0.6
   - Risk/reward ratio >= 1.5
   - Urgency correctly assigned
   - Expires_at is in the future

---

## Configuration

### Tunable Parameters

Add these to your config or make them adjustable:

```python
# Prediction parameters
PREDICTION_TIME_HORIZONS = [5, 15, 30]  # minutes
PREDICTION_BASE_MOVE_MULTIPLIER = 0.5
PREDICTION_MAX_MOVE_PCT = 10.0  # Maximum expected move percentage

# Opportunity parameters
OPPORTUNITY_MIN_CONFIDENCE = 0.6
OPPORTUNITY_MIN_RISK_REWARD = 1.5
OPPORTUNITY_STOP_LOSS_PCT = 0.02  # 2% stop loss
```

---

## Performance Considerations

1. **Caching:**
   - Cache predictions for 30 seconds
   - Cache opportunities for 15 seconds
   - Invalidate cache when new market data arrives

2. **Calculation Frequency:**
   - Predictions: Calculate every 30 seconds
   - Opportunities: Calculate every 15 seconds
   - Can be adjusted based on system load

3. **Database Queries:**
   - Batch fetch market data and physics factors
   - Use async database operations
   - Consider connection pooling

---

## Error Handling

```python
try:
    # Generate predictions/opportunities
    result = generate_predictions(...)
except ValueError as e:
    logger.error(f"Invalid input: {e}")
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

---

## Migration Path

1. **Phase 1:** Implement basic endpoints with simple logic
2. **Phase 2:** Add caching for performance
3. **Phase 3:** Integrate with existing ML models (if separate)
4. **Phase 4:** Add database persistence for historical tracking
5. **Phase 5:** Add advanced features (multiple models, confidence calibration)

---

## Success Criteria

✅ Endpoints return valid JSON  
✅ Predictions have future timestamps  
✅ Opportunities have valid risk/reward ratios  
✅ Frontend automatically uses real data (no more mocks)  
✅ Performance is acceptable (< 500ms response time)  
✅ Error handling works correctly  

---

## Notes

- **Start Simple:** Begin with basic prediction logic, refine based on results
- **Use Existing Data:** Leverage signals, physics factors, and market data you already have
- **Iterate:** Adjust multipliers and thresholds based on real-world performance
- **Monitor:** Track prediction accuracy over time to improve confidence calculations

---

**Status:** Ready for Backend Implementation

This plan provides everything needed to implement the endpoints. The frontend will automatically switch from mock to real data once these endpoints are available.



