# Trade Opportunities View

**Port:** 1427  
**Purpose:** Display upcoming trade opportunities identified by ML prediction engine

---

## Overview

The Trade Opportunities view shows actionable trading opportunities with:
- **Predicted price movements** with confidence levels
- **Time horizons** for when moves are expected
- **Risk/reward ratios** for each opportunity
- **Urgency indicators** (HIGH/MEDIUM/LOW)
- **Live countdown timers** showing time until opportunity expires

---

## Features

### Summary Cards
- **Total Opportunities:** Count of all available opportunities
- **High Confidence:** Opportunities with >75% confidence
- **Avg Expected Move:** Average predicted price movement
- **High Urgency:** Count of time-sensitive opportunities

### Filtering & Sorting
- **Sort by:** Confidence, Urgency, Expected Move, or Time Horizon
- **Filter by Type:** BUY only, SELL only, or All
- **Min Confidence:** Threshold slider (0-100%)
- **Symbol Filter:** Filter by specific trading pair

### Opportunity Cards
Each card displays:
- Symbol and opportunity type (BUY/SELL)
- Predicted move percentage (large, prominent)
- Time horizon and countdown timer
- Confidence meter (visual bar)
- Current price, target price, stop loss
- Risk/reward ratio
- Action buttons (View Chart, Dismiss)

### Actions
- **View Chart:** Opens chartview with symbol and predictions enabled
- **Dismiss:** Removes opportunity from view

---

## API Integration

### Endpoint: `/api/opportunities`

**Expected Response:**
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
    "expires_at": "2024-12-31T12:10:00Z"
  }
]
```

**Fallback:** If endpoint not available, generates mock opportunities based on current market data and signals.

---

## Auto-Refresh

- **Opportunities:** Updates every 15 seconds
- **Countdown Timers:** Update every second
- **Backend Status:** Checked every 5 seconds

---

## Usage

1. **Start Server:**
   ```bash
   ./serve.sh
   ```

2. **Open Browser:**
   ```
   http://localhost:1427
   ```

3. **Navigate:**
   - Click "View Chart" on any opportunity to see predictions
   - Use filters to find specific opportunities
   - Sort by confidence to see best opportunities first

---

## Integration

- **From Dashboard:** Click "Opportunities" in navigation
- **To Chartview:** Click "View Chart" button on any opportunity
- **Cross-View:** Chartview opens with symbol and predictions enabled

---

**Status:** ✅ **READY** - Full opportunities view with filtering, sorting, and live updates.



