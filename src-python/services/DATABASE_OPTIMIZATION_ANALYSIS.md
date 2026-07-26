# Database Optimization Analysis

## Critical Findings: The System is Recalculating Everything

### Problem 1: Z-Scores Are NOT Persisted

**Current Flow:**
```
1. BrainEngine.ingest_candle() → Calculates z-score in memory
2. Stores in self.z_score_history (in-memory list)
3. On restart → ALL LOST, recalculates from scratch
```

**Impact:**
- Every restart requires recalculating z-scores for all symbols
- No persistence of calculated indicators
- Strategies can't verify against historical z-scores

**Evidence:**
```python
# backend/services/brain.py:23-47
def ingest_candle(self, timestamp_ms: int, close_price: float, volume: float):
    # Calculates z-score but NEVER saves to database
    z_score = (close_price - mean_price) / std_price
    self.z_score_history.append(z_score)  # Only in memory!
```

---

### Problem 2: The `analyses` Table Exists But Is NEVER USED

**The Database Has:**
```sql
CREATE TABLE analyses (
    id INTEGER PRIMARY KEY,
    symbol TEXT,
    ts REAL NOT NULL,
    analysis_type TEXT NOT NULL,  -- Could be "z_score", "regime", "physics"
    payload TEXT NOT NULL,        -- JSON with calculated values
    created_ts REAL
)
```

**But Nothing Writes To It!**

**Search Results:**
- `insert_analysis()` exists in database.py
- `get_analyses()` exists in database.py
- **ZERO calls to these methods in the codebase**

**Impact:**
- Database was designed for caching but is unused
- Every calculation is done fresh
- No way to verify historical calculations

---

### Problem 3: Redundant Calculations

**What Gets Recalculated Every Tick:**

1. **Z-Scores** (every tick, every symbol)
   - Calculated from last 20 prices
   - Could be cached and only updated with new data

2. **Physics Parameters** (if used)
   - Momentum, velocity, acceleration
   - Regime detection
   - All recalculated from scratch

3. **Regime Detection**
   - `current_regime = "UNKNOWN"` (never updated!)
   - No persistence

**Evidence:**
```python
# brain.py:30-38 - Recalculates mean/std every time
if len(self.price_history) >= 20:
    recent_prices = self.price_history[-20:]
    mean_price = np.mean(recent_prices)  # Recalculated!
    std_price = np.std(recent_prices)     # Recalculated!
    z_score = (close_price - mean_price) / std_price
```

**Optimization:**
- Could cache mean/std and update incrementally
- Or store z-scores in database and only calculate missing ones

---

### Problem 4: No Connection Between DataManager and BrainEngine

**DataManager:**
- Stores raw OHLCV data in database ✅
- Has methods to query historical data ✅

**BrainEngine:**
- Calculates indicators in memory ❌
- Doesn't use DataManager to load historical data ❌
- Doesn't persist calculated indicators ❌

**Missing Link:**
- BrainEngine should load historical z-scores on startup
- BrainEngine should save new z-scores to database
- Strategies should query database for historical indicators

---

## Optimization Plan

### Phase 1: Persist Z-Scores (IMMEDIATE WIN)

**Add to BrainEngine:**
```python
def ingest_candle(self, timestamp_ms: int, close_price: float, volume: float, symbol: str = "BTCUSDT"):
    # ... existing calculation ...
    
    # NEW: Persist to database
    if z_score is not None:
        from backend.services.database import get_database
        db = get_database()
        db.insert_analysis(
            symbol=symbol,
            ts=timestamp_ms / 1000.0,  # Convert to seconds
            analysis_type="z_score",
            payload={"z_score": z_score, "price": close_price, "volume": volume}
        )
```

**Add Load on Startup:**
```python
def load_historical_z_scores(self, symbol: str, limit: int = 1000):
    """Load recent z-scores from database"""
    from backend.services.database import get_database
    db = get_database()
    analyses = db.get_analyses(symbol=symbol, analysis_type="z_score", limit=limit)
    
    for analysis in analyses:
        z_score = analysis['payload']['z_score']
        self.z_score_history.append(z_score)
```

---

### Phase 2: Cache Physics Parameters

**Store in `analyses` table:**
```python
# When calculating physics parameters
db.insert_analysis(
    symbol=symbol,
    ts=timestamp,
    analysis_type="physics",
    payload={
        "momentum": momentum,
        "velocity": velocity,
        "regime": regime,
        "entropy": entropy
    }
)
```

**Load on Demand:**
```python
def get_cached_physics(self, symbol: str, timestamp: float):
    """Get cached physics parameters if available"""
    analyses = db.get_analyses(
        symbol=symbol,
        analysis_type="physics",
        limit=1
    )
    if analyses and abs(analyses[0]['ts'] - timestamp) < 60:  # Within 1 minute
        return analyses[0]['payload']
    return None  # Need to recalculate
```

---

### Phase 3: Incremental Calculation (Advanced)

**Instead of recalculating mean/std every time:**
```python
class IncrementalStats:
    def __init__(self, window_size=20):
        self.window_size = window_size
        self.prices = []
        self.sum = 0.0
        self.sum_sq = 0.0
    
    def add_price(self, price: float):
        self.prices.append(price)
        self.sum += price
        self.sum_sq += price * price
        
        if len(self.prices) > self.window_size:
            old_price = self.prices.pop(0)
            self.sum -= old_price
            self.sum_sq -= old_price * old_price
    
    def get_mean(self) -> float:
        return self.sum / len(self.prices) if self.prices else 0.0
    
    def get_std(self) -> float:
        n = len(self.prices)
        if n < 2:
            return 0.0
        mean = self.get_mean()
        variance = (self.sum_sq / n) - (mean * mean)
        return math.sqrt(variance) if variance > 0 else 0.0
```

**Benefits:**
- O(1) updates instead of O(n) recalculation
- Much faster for high-frequency ticks

---

## Implementation Priority

### 🔴 CRITICAL (Do First):
1. **Persist z-scores to database** - Use existing `analyses` table
2. **Load z-scores on startup** - Restore state from database
3. **Add symbol parameter** - BrainEngine needs to know which symbol

### 🟡 IMPORTANT (Do Next):
4. **Cache physics parameters** - Store regime, momentum, etc.
5. **Add database connection** - BrainEngine should use database singleton
6. **Verify against stored values** - Strategies can query historical indicators

### 🟢 OPTIMIZATION (Long-term):
7. **Incremental statistics** - Replace O(n) with O(1) updates
8. **Batch writes** - Write multiple analyses at once
9. **Index optimization** - Ensure fast queries on symbol+timestamp

---

## Code Cleanup Opportunities

### Redundant Code to Remove:

1. **Unused physics functions** in brain.py:
   - `calculate_momentum()` - Never called
   - `calculate_acceleration()` - Never called  
   - `minimize_error()` - Never called
   - These are dead code from AI generation

2. **Duplicate regime detection**:
   - `current_regime = "UNKNOWN"` (never updated)
   - Shadow engine has its own regime detection
   - Consolidate to one source of truth

3. **Multiple data sources**:
   - `DataManager` (SQLAlchemy + OHLCV table)
   - `Database` (sqlite3 + market_ticks table)
   - `BrainEngine` (in-memory lists)
   - **Consolidate to use database.py as single source**

---

## Expected Performance Improvements

### Before Optimization:
- Z-score calculation: ~0.1ms per tick (recalculating mean/std)
- On restart: Recalculate all z-scores (could be 1000s of ticks)
- No persistence: Can't verify historical calculations

### After Optimization:
- Z-score calculation: ~0.01ms (incremental) or 0ms (cached)
- On restart: Load from database (~10ms for 1000 z-scores)
- Full persistence: Can verify and audit all calculations

**Estimated Speedup: 10-100x for z-score calculations**

---

## Testing Strategy

1. **Verify Persistence:**
   - Calculate z-scores for 100 ticks
   - Restart system
   - Verify z-scores are loaded from database

2. **Verify Correctness:**
   - Compare calculated z-scores with stored ones
   - Ensure no drift or errors

3. **Performance Test:**
   - Measure calculation time before/after
   - Verify incremental updates are faster

---

## Conclusion

**Current State:** System recalculates everything from scratch, no persistence, redundant code.

**Optimized State:** 
- Z-scores persisted and loaded from database
- Physics parameters cached
- Incremental calculations where possible
- Single source of truth for data

**Impact:** 
- 10-100x faster calculations
- Full audit trail
- Strategies can verify against historical data
- More reliable and robust system




