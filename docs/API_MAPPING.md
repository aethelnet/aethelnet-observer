# Backend API Mapping for HTML Dashboard

**Date:** December 29, 2024  
**Purpose:** Document exact API endpoints and data structures

---

## 📊 **Backend API Endpoints**

### **1. Metrics: `/api/dashboard/metrics`**

**Response Structure:**
```json
{
  "total_pnl": -27.38,           // Main P&L (not "main_pnl")
  "shadow_pnl": 0.76,            // Shadow engine P&L
  "win_rate": 0.372,             // Decimal 0-1 (NOT percentage!)
  "total_trades": 43,
  "winning_trades": 16,
  "open_positions": 1,
  "daily_pnl": 0.0,
  "max_drawdown": -50.0,        // Absolute dollars
  "drawdown_percentage": 5.2,    // Percentage
  "peak_equity": 1000.0,
  "current_equity": 950.0,
  "validation": {
    "trades_met": true,
    "win_rate_met": false,
    "drawdown_met": true,
    "live_ready": false
  },
  "dec_30_ready": false,
  "last_update": "2024-12-29T22:15:00Z"
}
```

**Key Points:**
- ✅ Use `total_pnl` (not `main_pnl`)
- ✅ `win_rate` is decimal 0-1 (multiply by 100 for percentage)
- ✅ `shadow_pnl` is available
- ✅ `validation` object shows readiness status

---

### **2. Market Data: `/api/dashboard/market-data`**

**Response Structure:**
```json
[
  {
    "symbol": "BTCUSDT",
    "price": 87813.67,
    "signal": 0.6546,                    // Number (Z-score)
    "signal_strength": "STRONG BUY",     // String
    "volume": 1234567.89,
    "change_24h": 2.5,                   // Percentage (not "change_percent_24h")
    "last_update": "2024-12-29T22:15:00Z"
  }
]
```

**Key Points:**
- ✅ Use `signal_strength` (string) for display
- ✅ Use `change_24h` (not `change_percent_24h`)
- ✅ `signal` is numeric (Z-score)
- ✅ Returns array of market data objects

---

### **3. Positions: `/api/dashboard/positions`**

**Response Structure:**
```json
[
  {
    "symbol": "BTCUSDT",
    "side": "LONG",
    "entry_price": 87000.0,
    "current_price": 87813.67,
    "quantity": 0.05,
    "unrealized_pnl": 40.68,
    "entry_time": "2024-12-29T22:00:00Z",
    "hold_time_seconds": 900
  }
]
```

**Key Points:**
- ✅ Returns array (empty if no positions)
- ✅ `unrealized_pnl` is calculated
- ✅ `hold_time_seconds` is in seconds

---

### **4. Recent Trades: `/api/dashboard/recent-trades`**

**Response Structure:**
```json
[
  {
    "symbol": "BTCUSDT",
    "side": "LONG",
    "entry_price": 87000.0,
    "exit_price": 87500.0,
    "quantity": 0.05,
    "pnl": 25.0,
    "hold_time_seconds": 1800,
    "timestamp": "2024-12-29T22:15:00Z"
  }
]
```

**Key Points:**
- ✅ Returns array of closed trades
- ✅ `pnl` is realized P&L
- ✅ Most recent trades are last in array

---

## 🔧 **HTML Dashboard Mapping**

### **Current Implementation:**

**Metrics Widget:**
- ✅ Uses `/api/dashboard/metrics`
- ✅ Maps `total_pnl` → Main P&L
- ✅ Maps `shadow_pnl` → Shadow P&L
- ✅ Converts `win_rate` (0-1) → percentage
- ✅ Displays `total_trades`, `open_positions`

**Market Data Widget:**
- ✅ Uses `/api/dashboard/market-data`
- ✅ Maps `signal_strength` → Signal badge
- ✅ Maps `change_24h` → 24h Change
- ✅ Displays `price`, `symbol`

---

## ✅ **Verification Checklist**

- [x] API base URL: `http://localhost:8000/api`
- [x] Metrics endpoint: `/api/dashboard/metrics`
- [x] Market data endpoint: `/api/dashboard/market-data`
- [x] Win rate conversion: decimal → percentage
- [x] Field name mapping: `total_pnl` (not `main_pnl`)
- [x] Signal display: `signal_strength` (string)

---

### **5. Predictions: `/api/predictions`**

**Purpose:** Get ML prediction engine forecasts for future price movements

**Query Parameters:**
- `symbol` (optional): Filter by symbol (e.g., `?symbol=BTCUSDT`)

**Response Structure:**
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

**Key Points:**
- ✅ Returns predictions for multiple time horizons
- ✅ `confidence` is decimal 0-1 (multiply by 100 for percentage)
- ✅ `direction` is "UP", "DOWN", or "NEUTRAL"
- ✅ `expected_move_percent` is the predicted percentage change
- ✅ If endpoint not available, frontend will use mock/placeholder data

**Fallback/Mock Data:**
If backend doesn't expose this endpoint yet, frontend will generate mock predictions based on current signals and physics factors.

---

### **6. Trade Opportunities: `/api/opportunities`**

**Purpose:** Get upcoming trade opportunities identified by ML prediction engine

**Query Parameters:**
- `symbol` (optional): Filter by symbol
- `min_confidence` (optional): Minimum confidence threshold (0-1)
- `urgency` (optional): Filter by urgency level ("HIGH", "MEDIUM", "LOW")

**Response Structure:**
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
  },
  {
    "symbol": "ETHUSDT",
    "opportunity_type": "SELL",
    "predicted_move_percent": -2.3,
    "time_horizon_minutes": 15,
    "confidence": 0.68,
    "current_price": 2450.50,
    "target_price": 2394.00,
    "stop_loss": 2500.00,
    "risk_reward_ratio": 1.8,
    "urgency": "MEDIUM",
    "expires_at": "2024-12-31T12:15:00Z",
    "created_at": "2024-12-31T12:00:00Z"
  }
]
```

**Key Points:**
- ✅ Returns array of opportunities (empty if none available)
- ✅ `confidence` is decimal 0-1
- ✅ `opportunity_type` is "BUY" or "SELL"
- ✅ `urgency` indicates time sensitivity ("HIGH", "MEDIUM", "LOW")
- ✅ `expires_at` is when the opportunity is no longer valid
- ✅ If endpoint not available, frontend will use mock/placeholder data

**Fallback/Mock Data:**
If backend doesn't expose this endpoint yet, frontend will generate mock opportunities based on current signals and market data.

---

## 🔧 **HTML Dashboard Mapping**

### **Current Implementation:**

**Metrics Widget:**
- ✅ Uses `/api/dashboard/metrics`
- ✅ Maps `total_pnl` → Main P&L
- ✅ Maps `shadow_pnl` → Shadow P&L
- ✅ Converts `win_rate` (0-1) → percentage
- ✅ Displays `total_trades`, `open_positions`

**Market Data Widget:**
- ✅ Uses `/api/dashboard/market-data`
- ✅ Maps `signal_strength` → Signal badge
- ✅ Maps `change_24h` → 24h Change
- ✅ Displays `price`, `symbol`

**Predictions (NEW):**
- ✅ Uses `/api/predictions?symbol={symbol}`
- ✅ Displays future price predictions on chart
- ✅ Shows confidence intervals and time horizons
- ✅ Falls back to mock data if endpoint unavailable

**Opportunities (NEW):**
- ✅ Uses `/api/opportunities`
- ✅ Displays upcoming trade opportunities
- ✅ Filters and sorts by confidence, urgency, expected move
- ✅ Falls back to mock data if endpoint unavailable

---

## ✅ **Verification Checklist**

- [x] API base URL: `http://localhost:8000/api`
- [x] Metrics endpoint: `/api/dashboard/metrics`
- [x] Market data endpoint: `/api/dashboard/market-data`
- [x] Win rate conversion: decimal → percentage
- [x] Field name mapping: `total_pnl` (not `main_pnl`)
- [x] Signal display: `signal_strength` (string)
- [x] Predictions endpoint: `/api/predictions` (with fallback)
- [x] Opportunities endpoint: `/api/opportunities` (with fallback)

---

**Status:** ✅ **MAPPED** - HTML dashboard matches backend API structure. New prediction and opportunities endpoints documented with fallback support.

