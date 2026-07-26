# Strategy State Persistence Analysis

## Current State: The Problem

### What Gets Lost on Restart

Strategies maintain **ephemeral state** that is **NOT persisted**:

1. **Trauma Cooldowns** (`trauma_cooldown_until`)
   - The Rat strategy uses this to avoid trading after bad trades
   - **Lost on restart** → Strategies immediately trade again (no memory of recent failures)

2. **Morale Multipliers** (`morale_multiplier`)
   - Buffs from the Board/Council that affect signal strength
   - **Lost on restart** → Strategies start at base strength (no accumulated confidence)

3. **Timing State** (`last_god_mode_ts`)
   - Prevents rapid-fire special mode activations
   - **Lost on restart** → Can trigger immediately on restart

4. **Adaptive Parameters**
   - Any learned thresholds, sensitivities, or calibration values
   - **Lost on restart** → Strategies reset to defaults

### What IS Persisted

The `LiveStrategyManager` saves:
- ✅ Active avatar selection
- ✅ Relic states (behelit, beans, goose, tarot)
- ✅ Execution mode (PAPER/LIVE)
- ✅ Auto-pilot state
- ✅ Trade history (JSON file)

**But NOT strategy internal state!**

---

## Current Coping Mechanisms

### 1. **Stateless Design** (Current Approach)
Strategies are designed to work without persistent state:
- They rely on `market_state` passed each tick
- No internal memory of past decisions
- Fresh start on every restart

**Pros:**
- Simple, no state management complexity
- Strategies are pure functions (easier to test)

**Cons:**
- Lose learned behavior
- Trauma/cooldown mechanics reset
- No adaptation over time
- Can't learn from past mistakes

### 2. **Manager-Level Persistence** (Partial)
The manager saves high-level state but not strategy internals:
```python
# manager_state.json saves:
{
    "active_avatar": "rat",
    "relics": {...},
    "execution_mode": "PAPER"
}
```

**Missing:**
- Strategy-specific state (trauma, morale, timing)
- Learned parameters
- Performance history per strategy

---

## Optimization Opportunities

### Option 1: Database-Backed Strategy State (RECOMMENDED)

**Use the new database tables we have!**

We can store strategy state in the `analyses` or create a new `strategy_state` table:

```python
# In database.py - add method:
def upsert_strategy_state(self, strategy_name: str, state: dict):
    """Save strategy internal state"""
    self.insert_analysis(
        symbol=None,
        ts=time.time(),
        analysis_type=f"strategy_state_{strategy_name}",
        payload=state
    )

def get_strategy_state(self, strategy_name: str) -> dict:
    """Load strategy state"""
    analyses = self.get_analyses(
        analysis_type=f"strategy_state_{strategy_name}",
        limit=1
    )
    return analyses[0]['payload'] if analyses else {}
```

**Benefits:**
- ✅ Uses existing database infrastructure
- ✅ Persistent across restarts
- ✅ Can track state history
- ✅ Easy to query/debug

**Implementation:**
- Add `save_state()` and `load_state()` to strategy base class
- Manager calls these on startup/shutdown
- Store in database instead of memory

---

### Option 2: Manager State Extension

Extend `manager_state.json` to include strategy states:

```python
# In manager.py save_manager_state():
state = {
    "active_avatar": self.active_avatar_key,
    "relics": self.relics,
    "strategy_states": {
        "rat": {
            "trauma_cooldown_until": self.avatars['rat'].trauma_cooldown_until,
            "morale_multiplier": getattr(self.avatars['rat'], 'morale_multiplier', 1.0),
            "last_god_mode_ts": self.avatars['rat'].last_god_mode_ts
        },
        # ... other strategies
    }
}
```

**Benefits:**
- ✅ Simple, uses existing persistence mechanism
- ✅ Fast (JSON file)
- ✅ Easy to inspect/debug

**Cons:**
- ❌ Only saves current state (no history)
- ❌ File-based (less robust than DB)
- ❌ Manual per-strategy implementation

---

### Option 3: Strategy Checkpoint System

Create a checkpoint system similar to the arena's checkpoint system:

```python
# Save strategy checkpoints
def save_strategy_checkpoint(self, strategy_name: str):
    import pickle
    strategy = self.avatars.get(strategy_name)
    if strategy:
        checkpoint = {
            'state': strategy.__dict__,
            'timestamp': time.time()
        }
        path = f"checkpoints/strategy_{strategy_name}_{int(time.time())}.pkl"
        with open(path, 'wb') as f:
            pickle.dump(checkpoint, f)

# Load on startup
def load_latest_checkpoint(self, strategy_name: str):
    # Find latest checkpoint and restore state
    ...
```

**Benefits:**
- ✅ Can save full strategy state (even complex objects)
- ✅ Version history (multiple checkpoints)
- ✅ Similar to existing arena checkpoint system

**Cons:**
- ❌ Pickle files (less portable than JSON/DB)
- ❌ More complex to manage
- ❌ Need cleanup logic for old checkpoints

---

## Recommended Solution: Hybrid Approach

### Phase 1: Quick Win (Manager State Extension)
Add strategy state to `manager_state.json` for immediate improvement:

```python
# In LiveStrategyManager.save_manager_state():
strategy_states = {}
for key, strategy in self.avatars.items():
    if hasattr(strategy, 'get_persistable_state'):
        strategy_states[key] = strategy.get_persistable_state()

state = {
    "active_avatar": self.active_avatar_key,
    "relics": self.relics,
    "strategy_states": strategy_states  # NEW
}
```

Add to each strategy:
```python
def get_persistable_state(self) -> dict:
    """Return state that should be persisted"""
    return {
        "trauma_cooldown_until": self.trauma_cooldown_until,
        "morale_multiplier": getattr(self, 'morale_multiplier', 1.0),
        "last_god_mode_ts": getattr(self, 'last_god_mode_ts', 0)
    }

def restore_state(self, state: dict):
    """Restore state from persisted data"""
    self.trauma_cooldown_until = state.get('trauma_cooldown_until', 0)
    self.morale_multiplier = state.get('morale_multiplier', 1.0)
    self.last_god_mode_ts = state.get('last_god_mode_ts', 0)
```

### Phase 2: Database Integration (Long-term)
Move to database for better tracking and history:

```python
# Use database.insert_analysis() for strategy state
# Allows querying state history, better for analytics
```

---

## Impact Analysis

### Current Behavior (Without Persistence)

**The Rat Strategy:**
- Trauma cooldown resets → Can trade immediately after restart (even if just had a bad trade)
- Morale multiplier resets → Loses Board confidence buffs
- No memory of recent performance

**Impact:**
- Strategies can make the same mistakes repeatedly
- No learning from past trades
- Trauma mechanics don't work across restarts

### With Persistence (Optimized)

**Benefits:**
- ✅ Strategies remember recent failures (trauma cooldowns persist)
- ✅ Maintains confidence levels (morale persists)
- ✅ Can learn and adapt over time
- ✅ More consistent behavior across restarts

**Performance Impact:**
- Minimal: Only save/load on startup/shutdown
- Database writes are async and batched
- JSON file writes are atomic and fast

---

## Implementation Checklist

### Quick Win (Manager State):
- [ ] Add `get_persistable_state()` to strategy base class
- [ ] Add `restore_state()` to strategy base class
- [ ] Update `save_manager_state()` to include strategy states
- [ ] Update `load_manager_state()` to restore strategy states
- [ ] Test with The Rat strategy (trauma, morale)

### Long-term (Database):
- [ ] Add `upsert_strategy_state()` to database.py
- [ ] Add `get_strategy_state()` to database.py
- [ ] Migrate from JSON to database
- [ ] Add state history tracking
- [ ] Add analytics queries for state evolution

---

## Testing Strategy

1. **Test Trauma Persistence:**
   - Trigger trauma in The Rat
   - Restart system
   - Verify trauma cooldown is still active

2. **Test Morale Persistence:**
   - Give strategy a morale buff
   - Restart system
   - Verify morale multiplier persists

3. **Test State Recovery:**
   - Run system for a while
   - Restart
   - Verify all strategies restore their state correctly

---

## Conclusion

**Current State:** Strategies are stateless and lose all internal state on restart.

**Optimization:** Add persistence for strategy state using either:
1. **Quick Win:** Extend `manager_state.json` (easiest, immediate benefit)
2. **Long-term:** Use database tables (better for analytics and history)

**Recommendation:** Start with Option 1 (manager state extension) for immediate improvement, then migrate to database for long-term tracking and analytics.




