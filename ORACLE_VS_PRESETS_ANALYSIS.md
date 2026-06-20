# Oracle vs Presets: Why Coffee/Espresso When We Have Oracle?

**Question**: Why do we have Coffee/Espresso presets when we have an alpha mode autopilot Oracle system?

**Date**: 2026-01-01

---

## Current Architecture

### What You Have

1. **Oracle System** (`backend/services/oracle.py`)
   - Synthesizes signals from multiple sources:
     - Logic (Physics/Z-Score): 40% weight
     - Soul (ML): 30% weight
     - Hindsight (Pattern Matching): 20% weight
     - Sentiment: 10% weight
   - Output: "Truth Score" (-1.0 to +1.0)
   - **Status**: ✅ Exists but **NOT used for trading decisions**

2. **Auto-Discovery Engine with Oracle Mode** (`backend/services/auto_discovery_engine.py`)
   - Scans all symbols × all strategies
   - Ranks opportunities globally
   - Uses Oracle for opportunity discovery
   - **Status**: ✅ Active for **symbol discovery**, not trading execution

3. **Coffee/Espresso Presets** (`backend/config/settings.py`)
   - Simple parameter sets:
     - `MIN_HOLD_TIME`: 90 seconds (Coffee) / 10 seconds (Espresso)
     - `SIGNAL_PERSISTENCE`: 2 confirmations (Coffee) / 1 (Espresso)
     - `SIGNAL_THRESHOLD`: 0.65 (both)
   - **Status**: ✅ **Currently the master strategy** - actually executes trades

---

## The Problem

**The presets are a legacy policy layer that filters signals, but the Oracle system is more sophisticated and should be making the decisions.**

### Current Flow (Preset-Based)
```
BrainEngine → Z-Score Signal
    ↓
Preset Filter (threshold, persistence, hold time)
    ↓
Trading Service → Execute Trade
```

### What It Should Be (Oracle-Based)
```
BrainEngine → Z-Score
ML Models → Probability
Pattern Matcher → Predicted Return
    ↓
Oracle → Truth Score (synthesized)
    ↓
Trading Service → Execute Trade
```

---

## Why Presets Exist (Historical Context)

From `docs/STRATEGY_ARCHITECTURE.md`:

> **The preset system (Coffee/Espresso) is the master strategy that actually executes trades.**
> 
> - `settings.py` defines preset values (Coffee: 45s hold, 2 persistence, 0.65 threshold)
> - `trading_service.py` reads these settings directly
> - All trading decisions flow through the preset policy layer

**The presets are a simplified "policy layer" that:**
- Filters signals by strength (threshold)
- Requires confirmation (persistence)
- Controls trade duration (hold time)
- Manages risk (position size, stop loss)

**But this is redundant if the Oracle is synthesizing all these inputs already!**

---

## The Oracle System

The Oracle (`backend/services/oracle.py`) is designed to be **"The Ultimate Synthesizer"**:

```python
def calculate_truth_score(self, state: Dict[str, Any]) -> float:
    """
    Input: State Dictionary containing inputs from all sub-systems.
    Output: Float -1.0 (Strong SELL) to +1.0 (Strong BUY).
    """
    # Combines:
    # - Logic (Physics/Z-Score): 40%
    # - Soul (ML): 30%
    # - Hindsight (Patterns): 20%
    # - Sentiment: 10%
    return score
```

**This is exactly what should be making trading decisions!**

---

## Why Oracle Isn't Being Used

Looking at `trading_service.py`, the trading loop:
1. Gets signals from BrainEngine (z-scores)
2. Applies preset filters (threshold, persistence, hold time)
3. Executes trades

**The Oracle is never called in the trading loop!**

The Oracle is only used by:
- Auto-Discovery Engine (for opportunity scanning)
- Not for actual trade execution

---

## Solution: Make Oracle the Master

### Option 1: Replace Presets with Oracle (Recommended)

**Change the trading service to:**
1. Get Oracle truth score instead of raw z-score
2. Use Oracle score as the primary signal
3. Keep presets only for risk management (position size, stop loss)

**Benefits:**
- Oracle synthesizes multiple signals (better decisions)
- Presets become risk parameters only (not signal filters)
- More sophisticated decision-making

### Option 2: Make Oracle Adaptive

**Let Oracle decide the "preset" dynamically:**
- Oracle analyzes market conditions
- Oracle selects optimal hold time, threshold, persistence
- No fixed presets needed

**Benefits:**
- Fully autonomous
- Adapts to market conditions
- No manual preset tuning

### Option 3: Hybrid (Oracle + Presets as Safety)

**Use Oracle for signals, presets as safety limits:**
- Oracle provides truth score
- Presets provide maximum risk limits
- Best of both worlds

---

## Current State Analysis

### What's Actually Running

1. **Trading Loop** (`trading_service.py`):
   - ✅ Uses presets (Coffee/Espresso parameters)
   - ❌ Does NOT use Oracle

2. **Auto-Discovery** (`auto_discovery_engine.py`):
   - ✅ Uses Oracle for opportunity scanning
   - ✅ Finds best symbol-strategy combinations
   - ❌ But doesn't control main trading loop

3. **Oracle** (`oracle.py`):
   - ✅ Exists and works
   - ❌ Not integrated into trading decisions

---

## Recommendation

**Yes, the Oracle should be in charge!** The presets are a legacy simplification that should be replaced or made optional.

### Implementation Plan

1. **Phase 1**: Integrate Oracle into trading service
   - Replace z-score threshold with Oracle truth score
   - Keep presets for risk management only

2. **Phase 2**: Make Oracle adaptive
   - Let Oracle determine optimal parameters dynamically
   - Remove fixed presets

3. **Phase 3**: Full Oracle autonomy
   - Oracle controls all trading decisions
   - Presets become fallback safety limits only

---

## Code Changes Needed

### File: `backend/services/trading_service.py`

**Current**:
```python
# Uses preset threshold
if abs(signal) > SIGNAL_THRESHOLD:  # 0.65
    if check_signal_persistence(symbol, signal):  # 2 confirmations
        # Execute trade
```

**Should Be**:
```python
# Use Oracle truth score
from backend.services.oracle import get_oracle

oracle = get_oracle()
state = {
    'logic_signal': z_score,
    'ml_probability': ml_prediction,
    'pattern_return': pattern_prediction,
    'sentiment_score': sentiment
}
truth_score = oracle.calculate_truth_score(state)

# Use Oracle score instead of preset threshold
if abs(truth_score) > 0.5:  # Oracle's recommendation
    # Execute trade
```

---

## Answer to Your Question

**"Why Coffee or Espresso at all?"**

**Short Answer**: They're not necessary if the Oracle is working. They're a legacy policy layer that should be replaced by Oracle-based decision-making.

**The Oracle system is more sophisticated and should be making the decisions, not simple preset filters.**

---

## Status

- ✅ Oracle system exists and works
- ✅ Auto-Discovery uses Oracle for opportunity scanning
- ❌ Trading service does NOT use Oracle (uses presets instead)
- ⚠️ Presets are currently the "master strategy" but shouldn't be

**Action Required**: Integrate Oracle into the trading service to replace preset-based signal filtering.





