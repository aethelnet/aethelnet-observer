# Developer Guide - Frontend-Backend Connections

> [!WARNING]
> **Outdated Architecture Notice:**
> This document describes the previous **Vanilla JavaScript (ES6 Modules) Unified Dashboard** setup. 
> The project has since been migrated to a modern **Vue 3 + TypeScript + Vite Single Page Application** located under the `/src` directory.
> - The entry point is now [main.ts](file:///home/nikahrlyn/auratic-systems-prime/frontend/src/main.ts) and [App.vue](file:///home/nikahrlyn/auratic-systems-prime/frontend/src/App.vue).
> - Views are Vue components located in [src/views/](file:///home/nikahrlyn/auratic-systems-prime/frontend/src/views/).
> - State management is handled via Pinia in [src/stores/systemStatus.js](file:///home/nikahrlyn/auratic-systems-prime/frontend/src/stores/systemStatus.js).
> - Development is run using `npm run dev` (Vite, port 1420) rather than a static python server.
> 
> While the endpoints and API connection patterns described below remain similar, the code snippets and structure below reflect the older vanilla JS files. For the modern Vue 3 documentation, please refer to the [[Frontend Architecture]] guide in the wiki.

**Technical guide for developers** - How the frontend connects to the backend, with code examples and verification methods.

---

## Table of Contents

1. [Development Environment Setup](#1-development-environment-setup)
2. [Backend Connection Architecture](#2-backend-connection-architecture)
3. [API Polling Implementation](#3-api-polling-implementation)
4. [WebSocket Implementation](#4-websocket-implementation)
5. [API Endpoint Mapping](#5-api-endpoint-mapping)
6. [View-by-View Connection Patterns](#6-view-by-view-connection-patterns)
7. [Verification Tools](#7-verification-tools)
8. [Debugging Connection Issues](#8-debugging-connection-issues)
9. [Code Patterns Reference](#9-code-patterns-reference)
10. [Complete Code Examples](#10-complete-code-examples)
11. [Testing Connection Functionality](#11-testing-connection-functionality)
12. [Best Practices](#12-best-practices)

---

## 1. Development Environment Setup

### Prerequisites

**Required:**
- **Backend running** on `http://localhost:8000`
  - Verify: `curl http://localhost:8000/api/dashboard/metrics`
  - Should return JSON, not connection error
- **Modern browser** with DevTools (Chrome, Firefox, Edge, Safari)
  - JavaScript enabled (ES6 modules support required)
  - DevTools accessible (F12)
- **Python 3 or PHP** for serving the unified app
  - Python 3: `python3 -m http.server 1420`
  - PHP: `php -S localhost:1420`

**Optional:**
- `jq` for pretty-printing JSON in terminal
- `curl` for API testing (usually pre-installed)

### Project Structure

```
Frontend/
├── index.html              # Main application shell (port 1420)
├── app.js                  # Hash-based router for unified app
├── views/                  # View modules (ES6 modules)
│   ├── dashboard.js       # Dashboard view module
│   ├── chartview.js       # Trading chart view (refactored class-based)
│   ├── opportunities.js   # Trade opportunities view
│   ├── scanner.js         # Market scanner view
│   ├── analytics.js       # Performance analytics view
│   ├── prophecy.js        # PROPHECY alert center view
│   ├── risk.js            # Risk management view
│   ├── execution.js       # Trade execution view
│   └── creative.js         # Creative 3D view
├── components/             # Shared components
│   └── ControlSlider.js   # Reusable slider component
├── shared.css             # Shared styles
├── styles.css             # Application styles
├── navigation.js          # Navigation helper
├── help-system.js        # Help system
├── ws-client.js           # WebSocket client
└── launch-all.sh          # Launch unified app
```

### How to Serve the Application

**Unified Application (Recommended)**
```bash
./launch-all.sh
# Starts single app on port 1420
# All views accessible via hash routing
# Example: http://localhost:1420#chartview
```

**Manual Server Start**
```bash
# From Frontend directory
python3 -m http.server 1420
# Or with PHP:
php -S localhost:1420
```

**Access Views:**
- Main app: `http://localhost:1420`
- Dashboard: `http://localhost:1420#dashboard` (default)
- ChartView: `http://localhost:1420#chartview`
- With params: `http://localhost:1420#chartview?symbol=BTCUSDT`

### Browser Developer Tools Setup

**Opening DevTools:**
- **F12** or **Ctrl+Shift+I** (Windows/Linux)
- **Cmd+Option+I** (Mac)
- Right-click → "Inspect"

**Key Tabs for Connection Debugging:**

1. **Network Tab:**
   - Filter by "Fetch/XHR" for API calls
   - Filter by "WS" for WebSocket
   - Click request to see:
     - Headers (request/response)
     - Payload (POST data)
     - Response (JSON data)
     - Timing (request duration)

2. **Console Tab:**
   - See `console.log()` output
   - See `console.error()` for failures
   - Execute JavaScript commands
   - Check connection status logs

3. **Application Tab:**
   - **WebSocket:** See active connections
   - **Storage:** Check localStorage/sessionStorage

### Backend Connection Verification

**Quick Test:**
```bash
# Test backend is running and responding
curl http://localhost:8000/api/dashboard/metrics

# Expected: JSON response with metrics
# If fails: Backend not running or wrong port
```

**Check All Endpoints:**
```bash
# Use the provided script
./check_endpoints.sh

# Or manually test each:
curl http://localhost:8000/api/dashboard/metrics
curl http://localhost:8000/api/dashboard/market-data
curl http://localhost:8000/api/dashboard/positions
curl http://localhost:8000/api/trades
curl http://localhost:8000/api/signals
curl http://localhost:8000/api/physics
curl http://localhost:8000/api/failsafe/status
```

---

## 2. Backend Connection Architecture

### Connection Methods

**API Polling (Primary)**
- Frontend requests data every 5-10 seconds
- Always works, reliable
- Used by all views

**WebSocket (Optional)**
- Persistent connection for real-time updates
- Falls back to polling if unavailable
- Currently used in Dashboard view (#dashboard)

### API Base Configuration

**Location in Code:**
```javascript
// Found in every view's <script> section
const API_BASE = 'http://localhost:8000/api';
```

**Verification:**
```bash
# Check all views use same base
grep -r "API_BASE" *.html */index.html
# Should all show: http://localhost:8000/api
```

---

## 3. API Polling Implementation

### Standard Fetch Pattern

**Code Example (from `index.html`):**
```javascript
const API_BASE = 'http://localhost:8000/api';

async function fetchPandL() {
    try {
        const response = await fetch(`${API_BASE}/dashboard/metrics`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const data = await response.json();
        // Update UI with data
        document.getElementById('main-pnl-badge').textContent = 
            `Main P&L: ${formatCurrency(data.main_pnl)}`;
    } catch (error) {
        console.error('[ERROR] Failed to fetch P&L metrics:', error);
    }
}
```

**Key Components:**
1. `fetch()` - Makes HTTP request
2. `response.ok` - Checks HTTP status (200-299)
3. `response.json()` - Parses JSON response
4. `try/catch` - Error handling

### Polling Intervals

**Code Pattern:**
```javascript
// Start polling on page load
function init() {
    fetchPandL(); // Initial fetch
    setInterval(fetchPandL, 5000); // Poll every 5 seconds
}
```

**Intervals by View:**
- **Dashboard (#dashboard):** 5s (P&L), 10s (trading status)
- **Analytics (#analytics):** 5s (metrics), 10s (trades)
- **Risk (#risk):** 5s
- **Execution (#execution):** 5s
- **ChartView (#chartview):** Variable (on-demand + periodic)

**Verification:**
- **Network tab:** See requests every 5-10 seconds
- **Console:** Check for polling logs
- **Timing:** Verify interval frequency

### Error Handling Pattern

**Code:**
```javascript
async function fetchData() {
    try {
        const response = await fetch(`${API_BASE}/endpoint`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('Fetch failed:', error);
        // Graceful degradation - show "--" or cached data
        return null;
    }
}
```

**What Happens on Error:**
1. `catch` block executes
2. Error logged to console
3. UI shows fallback (e.g., "--" or last known value)
4. Polling continues (will retry next interval)

---

## 4. WebSocket Implementation

### Connection Setup

**Code Pattern (from `index.html`):**
```javascript
const WS_URL = 'ws://localhost:8000/ws';
let ws = null;
let wsConnected = false;

function connectWebSocket() {
    try {
        ws = new WebSocket(WS_URL);
        
        ws.onopen = () => {
            console.log('[WebSocket] Connected');
            wsConnected = true;
            updateStatus('Connected');
            // Optionally reduce polling frequency when WS is active
        };
        
        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log('[WebSocket] Message received:', data);
                handleUpdate(data); // Process real-time update
            } catch (error) {
                console.error('[WebSocket] Failed to parse message:', error);
            }
        };
        
        ws.onerror = (error) => {
            console.error('[WebSocket] Error:', error);
            wsConnected = false;
            // Falls back to polling automatically
            // Polling continues regardless of WebSocket status
        };
        
        ws.onclose = (event) => {
            console.log('[WebSocket] Closed', {
                code: event.code,
                reason: event.reason,
                wasClean: event.wasClean
            });
            wsConnected = false;
            // Attempt reconnection after delay (exponential backoff)
            const delay = Math.min(5000 * Math.pow(2, reconnectAttempts), 30000);
            setTimeout(connectWebSocket, delay);
        };
    } catch (error) {
        console.error('[WebSocket] Failed to connect:', error);
        wsConnected = false;
        // Continue with polling only
    }
}

// Initialize on page load
window.addEventListener('load', () => {
    connectWebSocket();
});
```

### Message Handling

**Code Pattern:**
```javascript
ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    
    // Handle different message types
    switch (message.type) {
        case 'metrics':
            updateMetrics(message.data);
            break;
        case 'trade':
            addTradeToFeed(message.data);
            break;
        case 'position':
            updatePosition(message.data);
            break;
        default:
            console.log('[WebSocket] Unknown message type:', message.type);
    }
};
```

### Reconnection Logic

**Exponential Backoff Pattern:**
```javascript
let reconnectAttempts = 0;
const MAX_RECONNECT_DELAY = 30000; // 30 seconds max

ws.onclose = () => {
    reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), MAX_RECONNECT_DELAY);
    
    console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${reconnectAttempts})`);
    
    setTimeout(() => {
        connectWebSocket();
    }, delay);
};

ws.onopen = () => {
    reconnectAttempts = 0; // Reset on successful connection
};
```

### Fallback to Polling

**Code Pattern:**
```javascript
// Polling continues regardless of WebSocket status
let pollInterval = setInterval(fetchData, 5000);

// WebSocket enhances but doesn't replace polling
ws.onmessage = (event) => {
    // Real-time update (instant)
    handleUpdate(JSON.parse(event.data));
};

// If WebSocket fails, polling still works
ws.onerror = () => {
    console.log('[WebSocket] Using polling fallback');
    // Polling interval already running
};
```

### Verification

**Network Tab:**
1. Open Network tab (F12)
2. Filter by "WS" (WebSocket)
3. See connection status:
   - **101 Switching Protocols** = Connected
   - **Failed** = Connection failed
4. Click connection → "Messages" tab:
   - See frames sent/received
   - Check message content
   - Verify JSON format

**Console:**
- Look for `[WebSocket] Connected` logs
- Check for error messages
- Verify `wsConnected` flag changes
- Monitor reconnection attempts

**Backend Logs:**
- Check backend for WebSocket connection logs
- Verify messages are being sent
- Check for connection errors

**Visual:**
- Status indicator should show "Connected" when WS active
- Updates should appear instantly (vs. 5s polling delay)

---

## 5. API Endpoint Mapping

### Metrics Endpoint: `/api/dashboard/metrics`

**Code (from `index.html`):**
```javascript
async function fetchPandL() {
    try {
        const response = await fetch(`${API_BASE}/dashboard/metrics`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const data = await response.json();
        // Update UI with data
        document.getElementById('main-pnl-badge').textContent = 
            `Main P&L: ${formatCurrency(data.main_pnl)}`;
        document.getElementById('shadow-pnl-badge').textContent = 
            `Shadow P&L: ${formatCurrency(data.shadow_pnl)}`;
    } catch (error) {
        console.error('[ERROR] Failed to fetch P&L metrics:', error);
    }
}
```

**Data Flow:**
1. **Backend:** Calculates metrics from trades/positions
2. **API:** Returns JSON response
3. **Frontend:** `fetch()` makes HTTP GET request
4. **Frontend:** `response.json()` parses JSON
5. **Frontend:** Updates DOM elements with data

**Response Structure:**
```json
{
  "total_pnl": -27.38,
  "shadow_pnl": 0.76,
  "win_rate": 0.372,  // Decimal 0-1 (multiply by 100 for %)
  "total_trades": 43,
  "winning_trades": 16,
  "open_positions": 1,
  "daily_pnl": 0.0,
  "max_drawdown": -50.0,
  "drawdown_percentage": 5.2,
  "peak_equity": 1000.0,
  "current_equity": 950.0,
  "validation": {
    "trades_met": true,
    "win_rate_met": false,
    "drawdown_met": true,
    "live_ready": false
  }
}
```

**Verification:**
```bash
# Test endpoint
curl http://localhost:8000/api/dashboard/metrics

# Pretty print with jq
curl http://localhost:8000/api/dashboard/metrics | jq

# Check specific field
curl http://localhost:8000/api/dashboard/metrics | jq '.total_pnl'
```

**Network Tab:**
- **Request:**
  - Method: `GET`
  - URL: `http://localhost:8000/api/dashboard/metrics`
  - Headers: Standard browser headers
- **Response:**
  - Status: `200 OK` (success)
  - Content-Type: `application/json`
  - Body: JSON with metrics
- **Timing:**
  - Duration: Usually <100ms if backend is local
  - If slow: Check backend performance

**Console Logs:**
```javascript
// Add logging to see data flow
console.log('[FETCH] Requesting metrics...');
const response = await fetch(`${API_BASE}/dashboard/metrics`);
console.log('[FETCH] Response status:', response.status);
const data = await response.json();
console.log('[FETCH] Data received:', data);
```

**Backend Logs:**
- Check backend console for request logs
- Should see: `GET /api/dashboard/metrics`
- Verify response is generated

### Market Data Endpoint: `/api/dashboard/market-data`

**Code (from `chartview/index.html`):**
```javascript
async function fetchMarketData() {
    const response = await fetch(`${API_BASE}/dashboard/market-data`);
    const data = await response.json();
    // Array of market objects: [{symbol, price, signal_strength, ...}, ...]
    return data;
}
```

**Response Structure:**
```json
[
  {
    "symbol": "BTCUSDT",
    "price": 87813.67,
    "signal_strength": "STRONG BUY",
    "signal": 0.6546,
    "volume": 1234567.89,
    "change_24h": 2.5
  }
]
```

**Verification:**
```bash
curl http://localhost:8000/api/dashboard/market-data | jq
```

### Positions Endpoint: `/api/dashboard/positions`

**Code (from `chartview/index.html`):**
```javascript
async function fetchPositions() {
    const response = await fetch(`${API_BASE}/dashboard/positions`);
    const positions = await response.json();
    // Array of open positions
    return positions;
}
```

**Response:**
```json
[
  {
    "symbol": "BTCUSDT",
    "side": "LONG",
    "entry_price": 87000.0,
    "current_price": 87813.67,
    "unrealized_pnl": 40.68,
    "hold_time_seconds": 900
  }
]
```

### Historical Trades: `/api/trades`

**Code (from `chartview/index.html`):**
```javascript
async function fetchHistoricalTrades(symbol) {
    const response = await fetch(`${API_BASE}/trades`);
    const trades = await response.json();
    // Filter by symbol
    return trades.filter(t => t.symbol === symbol);
}
```

**Response:**
```json
[
  {
    "symbol": "BTCUSDT",
    "entry_price": 87000.0,
    "exit_price": 87500.0,
    "pnl": 25.0,
    "hold_time_seconds": 1800
  }
]
```

### Signals Endpoint: `/api/dashboard/signals`

**Code:**
```javascript
async function fetchSignalHistory(symbol) {
    const response = await fetch(`${API_BASE}/dashboard/signals${symbol ? `?symbol=${symbol}` : ''}`);
    const signals = await response.json();
    return signals.filter(s => s.symbol === symbol);
}
```

**Response Structure:**
```json
[
  {
    "id": 123,
    "symbol": "BTCUSDT",
    "timestamp": "2025-01-01T12:00:00Z",
    "price": 87813.67,
    "signal": "PROPHECY_BUY",
    "direction": "BUY",
    "confidence": 0.92,
    "regime": "high_volatility",
    "is_prophecy": true,
    "prophecy_type": "MAJOR_MOVE",
    "predicted_move_percent": 3.2,
    "resonance": 0.92,
    "intensity": 2.0
  }
]
```

**Key Points:**
- Returns array of signals
- PROPHECY events have `is_prophecy: true`
- Includes `predicted_move_percent`, `resonance`, `intensity` for PROPHECY events
- Filter by symbol using query parameter
- Used by ChartView (1423) and PROPHECY Alert Center (1428)

### Physics Endpoint: `/api/physics`

**Code:**
```javascript
async function fetchPhysicsState(symbol) {
    const response = await fetch(`${API_BASE}/physics`);
    const physics = await response.json();
    // Returns array, find symbol-specific or use first
    return physics.find(p => p.symbol === symbol) || physics[0] || {};
}
```

**Response:**
```json
[
  {
    "symbol": "BTCUSDT",
    "momentum": 0.5,
    "strain": 0.3,
    "force": 0.7,
    "squeeze": 0.2,
    "flow": 0.6,
    "entropy": 0.4,
    "jerk": 0.1,
    "sympathy": 0.8
  }
]
```

### Failsafe Endpoints: `/api/failsafe/*`

**Emergency Stop (POST):**
```javascript
fetch(`${API_BASE}/failsafe/panic`, { method: 'POST' })
    .then(res => res.json())
    .then(data => console.log('Emergency stop:', data));
```

**Trading Toggle:**
```javascript
// Get current status
fetch(`${API_BASE}/failsafe/status`)
    .then(res => res.json())
    .then(data => {
        const isPanic = data.panic_active;
        const endpoint = isPanic ? '/failsafe/resume' : '/failsafe/panic';
        return fetch(`${API_BASE}${endpoint}`, { method: 'POST' });
    });
```

**Verification:**
```bash
# Check status
curl http://localhost:8000/api/failsafe/status

# Trigger panic (use with caution!)
curl -X POST http://localhost:8000/api/failsafe/panic
```

---

## 6. View-by-View Connection Patterns

### Dashboard View (#dashboard)

**API Connections:**
```javascript
// Metrics polling (every 5s)
setInterval(fetchPandL, 5000);

// Trading status (every 10s)
setInterval(updateTradingStatus, 10000);

// Functions:
async function fetchPandL() {
    const response = await fetch(`${API_BASE}/dashboard/metrics`);
    const data = await response.json();
    // Update UI
}

function updateTradingStatus() {
    fetch(`${API_BASE}/failsafe/status`)
        .then(res => res.json())
        .then(data => {
            const status = data.panic_active ? 'PAUSED' : 'ACTIVE';
            document.getElementById('trading-status').textContent = status;
        });
}
```

**WebSocket (if implemented):**
- Connection: `ws://localhost:8000/ws`
- Real-time metric updates
- Falls back to polling if fails

**Verification:**
- Network tab: See `/dashboard/metrics` every 5s
- Network tab: See `/failsafe/status` every 10s
- Console: Check for connection logs

### ChartView (#chartview)

**Multiple API Endpoints:**
```javascript
// Backend connection check
async function checkBackend() {
    const response = await fetch(`${API_BASE}/dashboard/metrics`);
    // Update status badge
}

// Market data (periodic)
async function fetchMarketData() {
    const response = await fetch(`${API_BASE}/dashboard/market-data`);
}

// Positions (for markers)
async function fetchPositions() {
    const response = await fetch(`${API_BASE}/dashboard/positions`);
}

// Historical trades (on-demand when layer enabled)
async function fetchHistoricalTrades(symbol) {
    const response = await fetch(`${API_BASE}/trades`);
}

// Signals (on-demand when layer enabled)
async function fetchSignalHistory(symbol) {
    const response = await fetch(`${API_BASE}/signals`);
}

// Physics factors (periodic)
async function fetchPhysicsState(symbol) {
    const response = await fetch(`${API_BASE}/physics`);
}
```

**External API (Binance):**
```javascript
// Direct Binance API for candlesticks
async function fetchCandlestickData(symbol, interval = '1m') {
    const url = `https://api.binance.com/api/v3/klines?symbol=${symbol}&interval=${interval}&limit=500`;
    const response = await fetch(url);
    const klines = await response.json();
    // Convert to TradingView format
    return convertBinanceToTradingView(klines);
}
```

**Caching Strategy:**
```javascript
let tradesCache = null;
let signalsCache = null;
let physicsCache = null;

// Cache with timestamp
if (tradesCache && tradesCache.symbol === symbol) {
    return tradesCache.data; // Use cache
}
// Otherwise fetch and cache
```

**Verification:**
- Network tab: Multiple endpoints called
- Network tab: Binance API calls visible
- Console: Cache hits/misses logged

### Analytics View (#analytics)

**API Connections:**
```javascript
const UPDATE_INTERVAL = 5000;

async function fetchMetrics() {
    const response = await fetch(`${API_BASE}/dashboard/metrics`);
    const data = await response.json();
    // Update charts with Chart.js
    updateCharts(data);
}

async function fetchTrades() {
    const response = await fetch(`${API_BASE}/dashboard/recent-trades`);
    const trades = await response.json();
    // Update trade history
}

// Polling
setInterval(fetchMetrics, UPDATE_INTERVAL);
setInterval(fetchTrades, UPDATE_INTERVAL * 2);
```

**Data Flow:**
1. Fetch from API
2. Parse JSON
3. Transform for Chart.js
4. Update chart data

**Verification:**
- Network tab: See requests every 5s and 10s
- Console: Data logged
- Visual: Charts update

### Risk View (#risk)

**API Connections:**
```javascript
async function fetchMetrics() {
    const response = await fetch(`${API_BASE}/dashboard/metrics`);
    // Extract risk metrics: max_drawdown, drawdown_percentage
}

async function fetchPositions() {
    const response = await fetch(`${API_BASE}/dashboard/positions`);
    // Calculate position risk
}

async function fetchMarketData() {
    const response = await fetch(`${API_BASE}/dashboard/market-data`);
    // Market risk assessment
}
```

### Port 1426 - Execution

**API Connections:**
```javascript
const UPDATE_INTERVAL = 5000;

async function fetchTrades() {
    const response = await fetch(`${API_BASE}/dashboard/recent-trades`);
    const trades = await response.json();
    // Update live feed
    updateTradeFeed(trades);
}

setInterval(fetchTrades, UPDATE_INTERVAL);
```

**Real-time Updates:**
- Polls every 5 seconds
- Shows new trades as they execute
- Filters by symbol when selected

### Port 1427 - Trade Opportunities

**API Connections:**
```javascript
const API_BASE = 'http://localhost:8000/api';
const UPDATE_INTERVAL = 15000; // 15 seconds

async function fetchOpportunities(filters = {}) {
    const queryParams = new URLSearchParams();
    if (filters.symbol) queryParams.append('symbol', filters.symbol);
    if (filters.min_confidence) queryParams.append('min_confidence', filters.min_confidence);
    if (filters.urgency) queryParams.append('urgency', filters.urgency);
    
    const response = await fetch(`${API_BASE}/opportunities?${queryParams}`);
    const opportunities = await response.json();
    return opportunities;
}

setInterval(() => fetchOpportunities(), UPDATE_INTERVAL);
```

**Key Features:**
- Fetches from `/api/opportunities`
- Supports query parameters: `symbol`, `min_confidence`, `urgency`
- Auto-refreshes every 15 seconds
- Filters and sorts client-side
- Falls back to mock data if API unavailable

### Port 1428 - PROPHECY Alert Center

**API Connections:**
```javascript
const API_BASE = 'http://localhost:8000/api';
const UPDATE_INTERVAL = 5000; // 5 seconds

async function fetchProphecies(filters = {}) {
    const url = `${API_BASE}/dashboard/signals${filters.symbol ? `?symbol=${filters.symbol}` : ''}`;
    const response = await fetch(url);
    const signals = await response.json();
    
    // Filter for PROPHECY events only
    const prophecies = signals.filter(s => s.is_prophecy === true);
    return prophecies;
}

setInterval(() => fetchProphecies(), UPDATE_INTERVAL);
```

**Key Features:**
- Fetches from `/api/dashboard/signals`
- Filters for `is_prophecy: true` events
- Auto-refreshes every 5 seconds
- Countdown timers update every second
- Falls back to mock data if API unavailable
- Links to ChartView with `?showProphecy=true` parameter

**Data Structure:**
```javascript
{
  symbol: "BTCUSDT",
  is_prophecy: true,
  prophecy_type: "MAJOR_MOVE",
  predicted_move_percent: 3.2,
  resonance: 0.92,
  intensity: 2.0,
  direction: "BUY",
  price: 87813.67,
  timestamp: "2025-01-01T12:00:00Z"
}
```

### Ports 1421, 1422 - Creative Views

**API Connections:**
```javascript
async function fetchMarketData() {
    const response = await fetch(`${API_BASE}/dashboard/market-data`);
    const data = await response.json();
    // Create 3D nodes from market data
    createNodes(data);
    // Calculate correlations
    createConnections(data);
}
```

---

## 7. Verification Tools

### Browser Developer Tools

**Network Tab:**
1. Open DevTools (F12)
2. Click "Network" tab
3. Filter by "Fetch/XHR" for API calls
4. Filter by "WS" for WebSocket
5. Click any request to see:
   - **Headers:** Request/response headers
   - **Payload:** Request body (if POST)
   - **Response:** JSON response data
   - **Timing:** Request duration

**Console Tab:**
- See `console.log()` output
- See `console.error()` for failures
- Check connection status logs
- Verify data received

**Application Tab:**
- **WebSocket:** See active WebSocket connections
- **Storage:** Check localStorage/sessionStorage

### Command Line Verification

**Test Endpoints:**
```bash
# Metrics
curl http://localhost:8000/api/dashboard/metrics | jq

# Market data
curl http://localhost:8000/api/dashboard/market-data | jq

# Positions
curl http://localhost:8000/api/dashboard/positions | jq

# Trades
curl http://localhost:8000/api/trades | jq

# Signals
curl http://localhost:8000/api/signals | jq

# Physics
curl http://localhost:8000/api/physics | jq

# Failsafe status
curl http://localhost:8000/api/failsafe/status | jq
```

**Check Backend is Running:**
```bash
# Simple connectivity test
curl -I http://localhost:8000/api/dashboard/metrics
# Should return: HTTP/1.1 200 OK
```

**Monitor Requests:**
```bash
# Watch backend logs (if available)
tail -f /path/to/backend/logs
```

### Code-Level Verification

**Add Logging:**
```javascript
async function fetchData() {
    console.log('[FETCH] Starting request to', endpoint);
    const startTime = Date.now();
    
    try {
        const response = await fetch(`${API_BASE}/endpoint`);
        const duration = Date.now() - startTime;
        console.log('[FETCH] Success', {
            status: response.status,
            duration: `${duration}ms`
        });
        
        const data = await response.json();
        console.log('[FETCH] Data received', data);
        return data;
    } catch (error) {
        console.error('[FETCH] Failed', error);
        throw error;
    }
}
```

**Check Connection State:**
```javascript
// Add to any view
async function verifyConnection() {
    try {
        const response = await fetch(`${API_BASE}/dashboard/metrics`);
        console.log('Connection status:', response.ok ? 'OK' : 'FAILED');
        console.log('HTTP status:', response.status);
        return response.ok;
    } catch (error) {
        console.error('Connection failed:', error);
        return false;
    }
}

// Call periodically
setInterval(verifyConnection, 10000);
```

---

## 8. Debugging Connection Issues

### API Not Responding

**Symptoms:**
- Status shows "Disconnected"
- Metrics show "--"
- Console shows fetch errors

**Debug Steps:**
1. **Check Backend:**
   ```bash
   curl http://localhost:8000/api/dashboard/metrics
   ```

2. **Check Network Tab:**
   - Look for failed requests (red)
   - Check status code (404, 500, etc.)
   - Check error message

3. **Check Console:**
   - Look for `[ERROR]` messages
   - Check CORS errors
   - Verify API_BASE is correct

4. **Common Causes:**
   - Backend not running
   - Wrong port (should be 8000)
   - CORS configuration issue
   - Firewall blocking

**Solutions:**
- Start backend: `cd backend && python3 main.py`
- Verify port: Check backend logs
- Check CORS: Backend must allow `localhost:1420-1428`

### WebSocket Not Connecting

**Symptoms:**
- WebSocket status shows disconnected
- Console shows connection errors
- Falls back to polling

**Debug Steps:**
1. **Network Tab:**
   - Filter by "WS"
   - Check connection status
   - See error frames

2. **Console:**
   - Look for `WebSocket error` messages
   - Check `onerror` handler logs

3. **Backend:**
   - Verify WebSocket endpoint exists
   - Check backend logs

**Solutions:**
- WebSocket is optional - polling works fine
- If needed, verify backend WebSocket endpoint
- Check backend WebSocket logs

### CORS Errors

**Symptoms:**
- Console shows: `Access to fetch at '...' from origin '...' has been blocked by CORS policy`
- Network tab shows failed preflight requests

**What is CORS:**
- Browser security feature
- Backend must explicitly allow frontend origins

**Solution:**
- Backend must include CORS headers:
  ```
  Access-Control-Allow-Origin: http://localhost:1420
  Access-Control-Allow-Methods: GET, POST
  Access-Control-Allow-Headers: Content-Type
  ```

### Data Not Updating

**Symptoms:**
- UI shows stale data
- No new requests in Network tab

**Debug Steps:**
1. **Check Polling:**
   ```javascript
   // Verify interval is set
   console.log('Poll interval:', pollInterval);
   ```

2. **Network Tab:**
   - Verify requests are happening
   - Check request frequency
   - Verify responses contain new data

3. **Console:**
   - Check for errors preventing updates
   - Verify data parsing

**Solutions:**
- Ensure `setInterval()` is called
- Check for JavaScript errors
- Verify backend is generating new data

### Wrong Data Format

**Symptoms:**
- UI shows incorrect values
- Console shows parsing errors
- Data structure mismatch

**Debug Steps:**
1. **Network Tab:**
   - Click request → "Response" tab
   - Inspect actual JSON structure

2. **Console:**
   ```javascript
   // Log raw response
   const response = await fetch(`${API_BASE}/endpoint`);
   const text = await response.text();
   console.log('Raw response:', text);
   const data = JSON.parse(text);
   console.log('Parsed data:', data);
   ```

3. **Compare:**
   - Check API_MAPPING.md for expected structure
   - Compare with actual response

**Solutions:**
- Update code to match actual API response
- Or update backend to match expected format
- Check field names (e.g., `total_pnl` vs `main_pnl`)

---

## 9. Code Patterns Reference

### Standard API Fetch Pattern

```javascript
const API_BASE = 'http://localhost:8000/api';

async function fetchData() {
    try {
        const response = await fetch(`${API_BASE}/endpoint`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Fetch failed:', error);
        return null; // or throw, depending on use case
    }
}
```

### Polling Pattern

```javascript
let pollInterval = null;

function startPolling() {
    // Initial fetch
    fetchData();
    
    // Set up interval
    pollInterval = setInterval(() => {
        fetchData();
    }, 5000); // 5 seconds
}

function stopPolling() {
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }
}

// Cleanup on page unload
window.addEventListener('beforeunload', stopPolling);
```

### Connection Status Pattern

```javascript
async function checkConnection() {
    try {
        const response = await fetch(`${API_BASE}/dashboard/metrics`);
        const statusEl = document.getElementById('status');
        
        if (response.ok) {
            statusEl.textContent = 'Connected';
            statusEl.className = 'status-badge connected';
            return true;
        } else {
            statusEl.textContent = 'Disconnected';
            statusEl.className = 'status-badge disconnected';
            return false;
        }
    } catch (error) {
        document.getElementById('status').textContent = 'Disconnected';
        document.getElementById('status').className = 'status-badge disconnected';
        return false;
    }
}

// Check on load and periodically
checkConnection();
setInterval(checkConnection, 10000);
```

### Caching Pattern

```javascript
let dataCache = null;
const CACHE_TTL = 5000; // 5 seconds

async function fetchDataWithCache(symbol) {
    // Check cache
    if (dataCache && 
        dataCache.symbol === symbol && 
        Date.now() - dataCache.timestamp < CACHE_TTL) {
        console.log('Using cached data');
        return dataCache.data;
    }
    
    // Fetch new data
    const response = await fetch(`${API_BASE}/endpoint`);
    const data = await response.json();
    
    // Cache it
    dataCache = {
        symbol: symbol,
        data: data,
        timestamp: Date.now()
    };
    
    return data;
}
```

### Error Handling with Retry

```javascript
async function fetchWithRetry(url, maxRetries = 3) {
    for (let i = 0; i < maxRetries; i++) {
        try {
            const response = await fetch(url);
            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            if (i === maxRetries - 1) throw error;
            await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
        }
    }
}
```

### POST Request Pattern

```javascript
async function postData(endpoint, data) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('POST failed:', error);
        throw error;
    }
}

// Usage
postData('/failsafe/panic', {})
    .then(data => console.log('Success:', data))
    .catch(err => console.error('Error:', err));
```

---

## 10. Complete Code Examples

### Complete API Fetching with Polling

**Full Implementation:**
```javascript
const API_BASE = 'http://localhost:8000/api';
let pollInterval = null;
let apiConnected = false;

async function fetchMetrics() {
    try {
        console.log('[FETCH] Requesting metrics...');
        const startTime = Date.now();
        
        const response = await fetch(`${API_BASE}/dashboard/metrics`);
        const duration = Date.now() - startTime;
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        console.log(`[FETCH] Success (${duration}ms):`, data);
        
        // Update connection status
        apiConnected = true;
        updateStatus('Connected');
        
        // Update UI
        updateMetricsDisplay(data);
        
        return data;
    } catch (error) {
        console.error('[FETCH] Failed:', error);
        apiConnected = false;
        updateStatus('Disconnected');
        return null;
    }
}

function startPolling() {
    // Initial fetch
    fetchMetrics();
    
    // Set up interval
    pollInterval = setInterval(fetchMetrics, 5000);
    console.log('[POLL] Started polling every 5 seconds');
}

function stopPolling() {
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
        console.log('[POLL] Stopped polling');
    }
}

// Initialize
window.addEventListener('load', () => {
    startPolling();
});

// Cleanup
window.addEventListener('beforeunload', () => {
    stopPolling();
});
```

**Verification:**
- Network tab: See requests every 5 seconds
- Console: See `[FETCH]` and `[POLL]` logs
- UI: Metrics update every 5 seconds

### Complete WebSocket with Fallback

**Full Implementation:**
```javascript
const API_BASE = 'http://localhost:8000/api';
const WS_URL = 'ws://localhost:8000/ws';

let ws = null;
let wsConnected = false;
let pollInterval = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_DELAY = 30000;

function connectWebSocket() {
    try {
        console.log('[WS] Attempting connection...');
        ws = new WebSocket(WS_URL);
        
        ws.onopen = () => {
            console.log('[WS] Connected');
            wsConnected = true;
            reconnectAttempts = 0;
            updateStatus('Connected (WebSocket)');
        };
        
        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log('[WS] Message:', data);
                handleRealtimeUpdate(data);
            } catch (error) {
                console.error('[WS] Parse error:', error);
            }
        };
        
        ws.onerror = (error) => {
            console.error('[WS] Error:', error);
            wsConnected = false;
            updateStatus('Connected (Polling)');
        };
        
        ws.onclose = (event) => {
            console.log('[WS] Closed', {
                code: event.code,
                reason: event.reason,
                wasClean: event.wasClean
            });
            wsConnected = false;
            updateStatus('Connected (Polling)');
            
            // Reconnect with exponential backoff
            if (event.code !== 1000) { // Not a normal closure
                reconnectAttempts++;
                const delay = Math.min(
                    1000 * Math.pow(2, reconnectAttempts),
                    MAX_RECONNECT_DELAY
                );
                console.log(`[WS] Reconnecting in ${delay}ms`);
                setTimeout(connectWebSocket, delay);
            }
        };
    } catch (error) {
        console.error('[WS] Connection failed:', error);
        wsConnected = false;
    }
}

// Start polling (always works)
function startPolling() {
    fetchMetrics();
    pollInterval = setInterval(fetchMetrics, 5000);
}

// Initialize both
window.addEventListener('load', () => {
    startPolling(); // Always start polling
    connectWebSocket(); // Try WebSocket (optional)
});
```

**Verification:**
- Network tab: See WebSocket connection (filter by "WS")
- Console: See `[WS]` connection logs
- Status: Shows "Connected (WebSocket)" when active

### Complete Connection Manager

**Combined API + WebSocket with Automatic Fallback:**
```javascript
class ConnectionManager {
    constructor(apiBase, wsUrl) {
        this.apiBase = apiBase;
        this.wsUrl = wsUrl;
        this.ws = null;
        this.pollInterval = null;
        this.wsConnected = false;
        this.apiConnected = false;
        this.reconnectAttempts = 0;
    }
    
    // API Polling (always active)
    startPolling(interval = 5000) {
        this.fetchData();
        this.pollInterval = setInterval(() => this.fetchData(), interval);
    }
    
    async fetchData() {
        try {
            const response = await fetch(`${this.apiBase}/dashboard/metrics`);
            if (response.ok) {
                this.apiConnected = true;
                const data = await response.json();
                this.onDataUpdate(data);
            }
        } catch (error) {
            this.apiConnected = false;
            console.error('[API] Fetch failed:', error);
        }
    }
    
    // WebSocket (optional enhancement)
    connectWebSocket() {
        try {
            this.ws = new WebSocket(this.wsUrl);
            
            this.ws.onopen = () => {
                this.wsConnected = true;
                this.reconnectAttempts = 0;
                console.log('[WS] Connected');
            };
            
            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.onRealtimeUpdate(data);
            };
            
            this.ws.onerror = () => {
                this.wsConnected = false;
                // Polling continues
            };
            
            this.ws.onclose = () => {
                this.wsConnected = false;
                this.attemptReconnect();
            };
        } catch (error) {
            console.error('[WS] Connection failed:', error);
        }
    }
    
    attemptReconnect() {
        const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts++), 30000);
        setTimeout(() => this.connectWebSocket(), delay);
    }
    
    // Callbacks (override in usage)
    onDataUpdate(data) {
        console.log('[ConnectionManager] Data update:', data);
    }
    
    onRealtimeUpdate(data) {
        console.log('[ConnectionManager] Realtime update:', data);
    }
    
    // Cleanup
    disconnect() {
        if (this.pollInterval) clearInterval(this.pollInterval);
        if (this.ws) this.ws.close();
    }
}

// Usage
const connection = new ConnectionManager(
    'http://localhost:8000/api',
    'ws://localhost:8000/ws'
);

connection.onDataUpdate = (data) => {
    updateMetrics(data);
};

connection.onRealtimeUpdate = (data) => {
    updateMetrics(data);
};

connection.startPolling(5000);
connection.connectWebSocket();
```

---

## 11. Testing Connection Functionality

### Manual Testing Workflow

**Step 1: Verify Backend**
```bash
curl http://localhost:8000/api/dashboard/metrics
# Should return JSON
```

**Step 2: Open View**
```bash
./serve.sh
# Open http://localhost:1420
```

**Step 3: Open DevTools**
- Press F12
- Go to Network tab
- Filter by "Fetch/XHR"

**Step 4: Verify Requests**
- See requests every 5 seconds
- Click request → Check Response tab
- Verify JSON structure

**Step 5: Check Console**
- Look for connection logs
- Verify no errors
- Check data received

**Step 6: Verify UI Updates**
- Metrics should update
- Status should show "Connected"
- Data should appear in UI

### Automated Testing Script

**Create `test-connections.sh`:**
```bash
#!/bin/bash

API_BASE="http://localhost:8000/api"

echo "Testing backend connections..."

endpoints=(
    "/dashboard/metrics"
    "/dashboard/market-data"
    "/dashboard/positions"
    "/dashboard/recent-trades"
    "/trades"
    "/signals"
    "/physics"
    "/failsafe/status"
)

for endpoint in "${endpoints[@]}"; do
    echo -n "Testing $endpoint... "
    response=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE$endpoint")
    if [ "$response" = "200" ]; then
        echo "✅ OK"
    else
        echo "❌ Failed ($response)"
    fi
done
```

**Run:**
```bash
chmod +x test-connections.sh
./test-connections.sh
```

### Integration Testing

**Test Full Data Flow:**
1. Backend generates data
2. Frontend fetches data
3. Data displays in UI
4. Updates occur on schedule

**Verification Points:**
- Backend logs show requests
- Network tab shows responses
- Console shows data received
- UI shows updated values

---

## 12. Best Practices

### Connection Code Patterns

**Error Handling:**
```javascript
// Always wrap fetch in try-catch
try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
} catch (error) {
    console.error('Fetch failed:', error);
    // Graceful degradation
    return null;
}
```

**Retry Logic:**
```javascript
async function fetchWithRetry(url, maxRetries = 3) {
    for (let i = 0; i < maxRetries; i++) {
        try {
            const response = await fetch(url);
            if (response.ok) return await response.json();
        } catch (error) {
            if (i === maxRetries - 1) throw error;
            await new Promise(r => setTimeout(r, 1000 * (i + 1)));
        }
    }
}
```

**Cleanup:**
```javascript
// Always cleanup intervals
window.addEventListener('beforeunload', () => {
    if (pollInterval) clearInterval(pollInterval);
    if (ws) ws.close();
});
```

**Status Management:**
```javascript
// Centralized status updates
function updateConnectionStatus(apiOk, wsOk) {
    const statusEl = document.getElementById('status');
    if (apiOk) {
        statusEl.textContent = wsOk ? 'Connected (WebSocket)' : 'Connected (Polling)';
        statusEl.className = 'status-badge connected';
    } else {
        statusEl.textContent = 'Disconnected';
        statusEl.className = 'status-badge disconnected';
    }
}
```

### Performance Optimization

**Polling Frequency:**
- **5 seconds:** Good balance for most metrics
- **10 seconds:** For less critical data
- **1 second:** Too frequent, wastes resources
- **30+ seconds:** Too slow for real-time feel

**Caching Strategies:**
```javascript
// Cache with TTL
let cache = { data: null, timestamp: 0, ttl: 5000 };

async function fetchWithCache() {
    if (cache.data && Date.now() - cache.timestamp < cache.ttl) {
        return cache.data; // Use cache
    }
    
    const data = await fetch(url).then(r => r.json());
    cache = { data, timestamp: Date.now(), ttl: 5000 };
    return data;
}
```

**Request Optimization:**
- Batch multiple data needs into single request (if backend supports)
- Use caching to avoid redundant requests
- Debounce rapid updates

### Reliability Patterns

**Fallback Mechanisms:**
- Always have polling as fallback
- WebSocket enhances but doesn't replace polling
- Graceful degradation on errors

**Error Recovery:**
- Automatic retry with backoff
- Clear error messages to user
- Continue functioning with stale data if needed

**Connection Monitoring:**
- Periodic connection checks
- Visual status indicators
- Logging for debugging

---

## Quick Reference

### All API Endpoints

| Endpoint | Method | Used By | Purpose |
|----------|--------|---------|---------|
| `/api/dashboard/metrics` | GET | All views | Performance metrics |
| `/api/dashboard/market-data` | GET | 1420, 1423, 1425, 1421, 1422 | Market prices, signals |
| `/api/dashboard/positions` | GET | 1423, 1425 | Open positions |
| `/api/dashboard/recent-trades` | GET | 1424, 1426 | Recent trade history |
| `/api/trades` | GET | 1423 | Historical trades |
| `/api/dashboard/signals` | GET | 1423, 1428 | Trading signals with PROPHECY metadata |
| `/api/physics` | GET | 1423 | Physics factors |
| `/api/predictions` | GET | 1423 | ML predictions |
| `/api/opportunities` | GET | 1427 | Trade opportunities |
| `/api/failsafe/status` | GET | 1420 | Trading status |
| `/api/failsafe/panic` | POST | 1420 | Emergency stop |
| `/api/failsafe/resume` | POST | 1420 | Resume trading |

### Verification Checklist

**Before Development:**
- [ ] Backend running on port 8000
- [ ] Test endpoint: `curl http://localhost:8000/api/dashboard/metrics`
- [ ] Browser DevTools open (F12)

**During Development:**
- [ ] Network tab shows API calls
- [ ] Console shows no errors
- [ ] Data appears in UI
- [ ] Status shows "Connected"

**After Changes:**
- [ ] Refresh page
- [ ] Check Network tab for new requests
- [ ] Verify data updates
- [ ] Test error scenarios

---

## Related Documentation

- **Usage Guide:** `USAGE_GUIDE.md` - User-facing guide
- **API Mapping:** `API_MAPPING.md` - Endpoint documentation
- **Verification Report:** `VERIFICATION_REPORT.md` - System status

---

*Last updated: December 31, 2024*

