# Comprehensive Usage Guide - Auratic Trading Frontend

> [!WARNING]
> **Outdated Architecture Notice:**
> This document describes the previous **Vanilla JavaScript (ES6 Modules) Unified Dashboard** setup. 
> The project has since been migrated to a modern **Vue 3 + TypeScript + Vite Single Page Application** running entirely on **port 1420**.
> - There are no longer separate servers running on ports 1421-1429.
> - Access the views via hash routing on port 1420 (e.g. `http://localhost:1420/#chart`, `http://localhost:1420/#opportunities`).
> - The new views and controls are managed inside Vue files under `/src/views`.
> 
> While the user workflows and parameter controls described in this guide remain fully relevant, any references to individual ports or vanilla `.html` file paths should be adapted to the unified Vue 3 hash routes.

**Welcome!** This guide will help you get comfortable with the entire frontend interface, from initial setup to advanced trading workflows.

---

## Table of Contents

1. [Getting Started](#1-getting-started)
2. [System Overview](#2-system-overview)
3. [Complete Button and Control Reference](#3-complete-button-and-control-reference)
4. [View-by-View Guide](#4-view-by-view-guide)
5. [Glossary of Trading Terms](#5-glossary-of-trading-terms)
6. [Simple Trading Advice](#6-simple-trading-advice)
7. [Common Workflows](#7-common-workflows)
8. [Advanced Features](#8-advanced-features)
9. [Getting Comfortable](#9-getting-comfortable)
10. [Troubleshooting](#10-troubleshooting)
11. [Best Practices](#11-best-practices)

---

## 1. Getting Started

### Prerequisites

Before launching the frontend, ensure you have:

- **Backend running** on `http://localhost:8000`
  - The frontend requires the backend API to function
  - Check backend status before starting frontend views
- **Modern web browser** (Chrome, Firefox, Edge, or Safari)
  - JavaScript must be enabled
  - WebSocket support recommended (but not required)
- **Python 3 or PHP** (for serving the views)
  - Most systems have Python 3 pre-installed
  - PHP is an alternative option

### Launching the Unified Application

The easiest way to start the frontend:

```bash
# From the Frontend directory
./launch-all.sh
```

This will:
- Start the unified application on port 1420
- Display a summary with all available views
- Show the main URL and navigation options

**To stop the server:**
```bash
./launch-all.sh --stop
```

### Understanding the Unified App Structure

**Single Application with Hash Routing:**
All views are now unified into a single application running on port 1420. Navigation between views uses hash-based routing (like `#dashboard`, `#chartview`), which means:
- No page reloads when switching views
- Faster navigation
- Better state management
- All views share the same session

**The 9 Available Views:**
All views are accessible from the main application via hash routing:

| Route | View | Purpose | When to Use |
|-------|------|---------|-------------|
| `#dashboard` | MVP Dashboard | Main entry point, overview | Start here daily, quick status check |
| `#chartview` | Trading Chart View | Professional charting with Control Deck | Analyze price action, review trades |
| `#opportunities` | Trade Opportunities | ML prediction opportunities | Review upcoming trade opportunities |
| `#scanner` | Market Scanner | Multi-symbol command center | Comprehensive market overview across all symbols |
| `#analytics` | Performance Analytics | Metrics and analytics | Deep dive into performance data |
| `#prophecy` | PROPHECY Alert Center | Major move predictions | Monitor high-confidence predictions before they happen |
| `#risk` | Risk Management | Risk monitoring | Check safety, monitor drawdown |
| `#execution` | Trade Execution | Live trade feed | Watch trades as they happen |
| `#creative` | Creative View | 3D market connections | Explore market relationships visually |

**How to Access:**
- Main application: `http://localhost:1420`
- Navigate using header links (no page reload)
- Or use direct URLs: `http://localhost:1420#chartview`
- URL parameters supported: `http://localhost:1420#chartview?symbol=BTCUSDT`

### First-Time Setup Checklist

- [ ] Backend is running on port 8000
- [ ] Launch the unified app with `./launch-all.sh`
- [ ] Open the application (http://localhost:1420)
- [ ] Verify backend connection (should show "Connected" status)
- [ ] Check that metrics are loading on the dashboard
- [ ] Test navigation by clicking header links to switch views
- [ ] Familiarize yourself with hash routing (notice URL changes to `#viewname`)

### Backend Connection Requirements

**What is a Backend?**
Think of the backend as the "brain" of the trading system. It's a separate program running on your computer that:
- Connects to cryptocurrency exchanges (like Binance)
- Analyzes market data using complex algorithms
- Makes trading decisions based on mathematical models
- Executes trades automatically
- Tracks performance and calculates metrics

The frontend (what you're looking at) is the "dashboard" - it displays information from the backend in a visual, easy-to-understand way.

**How They Connect:**
The frontend connects to the backend via:

- **API Base:** `http://localhost:8000/api`
  - **What it is:** An API (Application Programming Interface) is like a menu at a restaurant - the frontend "orders" data from the backend
  - **How it works:** The frontend asks the backend "What's my current P&L?" every 5-10 seconds, and the backend responds with the data
  - **Used for:** Fetching metrics, trades, positions, market data
  - **Why polling:** Like checking your mailbox regularly - the frontend checks for updates periodically
  - **Reliability:** This method always works, even if other connections fail

- **WebSocket:** `ws://localhost:8000/ws` (optional)
  - **What it is:** A persistent connection that allows instant updates
  - **How it works:** Like a phone call that stays open - the backend can "call" the frontend immediately when something changes
  - **Advantage:** Updates appear instantly instead of waiting for the next "mailbox check"
  - **Fallback:** If WebSocket fails, the frontend automatically uses the polling method instead
  - **Not required:** The system works perfectly without it - it's just a nice enhancement

**Think of it like this:**
- **API Polling:** Like checking your email every few minutes - reliable, always works
- **WebSocket:** Like getting instant text messages - faster, but not essential

**Note:** The frontend works perfectly with API polling alone. WebSocket failures don't affect functionality - you'll just see updates every 5-10 seconds instead of instantly.

### What to Expect on First Launch

1. **Status indicators** may show "Disconnected" initially
   - Wait a few seconds for the first API call
   - Should change to "Connected" (green) when backend responds
2. **Metrics may show "--" or "0"**
   - This is normal if the backend hasn't executed trades yet
   - Data will populate as the system runs
3. **Charts may be empty**
   - Historical data loads on first view
   - Give it a moment to fetch and display

---

## 2. System Overview

### Architecture Overview

The frontend is built with:
- **Simple HTML + Vanilla JavaScript** - No build step required
- **Chart.js** - For simple visualizations (Analytics, Risk, Execution)
- **TradingView Lightweight Charts** - For professional candlestick charts (ChartView)
- **Three.js** - For 3D visualizations (Creative views)

### How Views Connect to Backend

All views use the same backend API:
- Fetch data via REST API (`/api/dashboard/*`)
- Optional WebSocket for real-time updates
- Graceful degradation if backend is unavailable

### Data Flow

**API Polling (Primary Method):**
- Views poll backend every 5-10 seconds
- Updates metrics, charts, and displays
- Works reliably even if WebSocket fails

**WebSocket (Optional Enhancement):**
- Provides instant updates when available
- Reduces API polling frequency
- Falls back to polling if connection fails

### Navigation Between Views

**From MVP Dashboard (1420):**
- Click navigation links at the top
- Links to: Analytics, Chartview, Creative, Execution

**Direct Access:**
- Open any view directly in browser
- Each view is independent
- No need to start from MVP Dashboard

### Common UI Patterns

All views share:
- **Dark theme** - Easy on the eyes for long monitoring sessions
- **Status indicators** - Show backend connection status
- **Help system** - Press F1 or click ? button
- **Tooltips** - Hover over controls for instant help
- **Real-time updates** - Data refreshes automatically

### Help System

**Access help in any view:**
- **Press F1** or **?** key
- **Click the ? button** (usually bottom-right)
- **Hover over controls** for tooltips

**Help includes:**
- Control explanations
- Keyboard shortcuts
- View-specific guidance
- Troubleshooting tips

---

## 3. Complete Button and Control Reference

### MVP Dashboard (Port 1420)

#### Emergency Stop Button 🛑
- **Location:** Control Panel section
- **Function:** Immediately halts all trading activity
- **When to use:** Emergency situations only (unexpected behavior, system errors, market anomalies)
- **Effect:** 
  - Stops all open positions
  - Prevents new trades
  - Requires manual confirmation dialog
- **Safety:** Can be resumed later via Trading Toggle
- **Warning:** Use only when absolutely necessary

#### Trading Toggle Button ⏸️
- **Location:** Control Panel section
- **Function:** Enable or disable the trading system
- **When to use:** To pause trading without emergency stop (planned maintenance, parameter adjustments)
- **Effect:**
  - Stops new trades when disabled
  - Continues monitoring market data
  - Shows current status (ACTIVE/PAUSED)
- **Status Indicator:** Displays current state next to button

#### Navigation Links
- **Analytics:** Opens Performance Analytics Hub (port 1424)
- **Chartview:** Opens Trading Chart View (port 1423)
- **Opportunities:** Opens Trade Opportunities (port 1427)
- **PROPHECY:** Opens PROPHECY Alert Center (port 1428)
- **Creative:** Opens 3D Market Connections (port 1421)
- **Execution:** Opens Trade Execution Monitor (port 1426)

#### Help Button (?)
- **Location:** Bottom-right corner
- **Function:** Opens comprehensive help modal
- **Keyboard shortcut:** F1 or ?

### Trading Chart View (Port 1423)

#### Control Deck Toggle (HIDE/SHOW)
- **Location:** Top-left of Control Deck panel
- **Function:** Minimize or restore the Control Deck panel
- **Use case:** Save screen space when not adjusting parameters
- **Effect:** Hides/shows entire Control Deck panel

#### Symbol Selector
- **Location:** Toolbar at top
- **Function:** Choose which trading pair to display
- **Options:** BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT, DOGEUSDT
- **Effect:** Updates chart, markers, and data for selected symbol

#### Timeframe Buttons
- **Location:** Toolbar at top
- **Options:** 1M, 5M, 15M, 1H, 4H, 1D

**What is a Timeframe?**
A timeframe determines how much time each candlestick represents. Think of it like zooming in or out on a map:
- **Zoomed in (1m, 5m):** See every detail, like street level on a map
- **Zoomed out (4h, 1d):** See the big picture, like viewing a whole city

**Why Different Timeframes Matter:**
Different timeframes show different information:
- **Short timeframes** show detailed price movements but can be "noisy" (lots of small fluctuations)
- **Long timeframes** show overall trends but hide short-term details

**What each means:**
  - **1M (1 minute):** Each candle = 1 minute of price action
    - **Use for:** Very short-term analysis, seeing every price tick
    - **Shows:** Detailed price movements, good for day trading
    - **Trade-off:** Very detailed but can be overwhelming with too much information
  
  - **5M (5 minutes):** Each candle = 5 minutes
    - **Use for:** Intraday trading, short-term patterns
    - **Shows:** Good balance of detail and clarity
    - **Trade-off:** Less noise than 1m, still shows short-term moves
  
  - **15M (15 minutes):** Each candle = 15 minutes
    - **Use for:** Balanced view, not too detailed, not too broad
    - **Shows:** Short to medium-term trends
    - **Trade-off:** Good starting point for most analysis
  
  - **1H (1 hour):** Each candle = 1 hour
    - **Use for:** Daily trading perspective, swing trading
    - **Shows:** Medium-term trends, clearer patterns
    - **Trade-off:** Less detail but clearer direction
  
  - **4H (4 hours):** Each candle = 4 hours
    - **Use for:** Swing trading, position holding
    - **Shows:** Longer-term trends, major moves
    - **Trade-off:** Shows bigger picture, misses short-term details
  
  - **1D (1 day):** Each candle = 1 day
    - **Use for:** Long-term trend analysis, position trading
    - **Shows:** Overall market direction over weeks/months
    - **Trade-off:** Very clear trends but no short-term detail

**How to Choose:**
- **Beginners:** Start with 1H or 4H - easier to see patterns
- **Active monitoring:** Use 15M or 1H for balanced view
- **Quick analysis:** Use 5M or 15M for recent activity
- **Long-term review:** Use 4H or 1D for overall trends

**Effect:** Changes candlestick granularity and historical data range. Switching timeframes is like changing the zoom level - you see the same market but at different levels of detail.

#### Layer Toggles (8 buttons)

**📊 HIST (Historical Data)**
- **What it shows:** Historical candlestick data from Binance (the cryptocurrency exchange)
- **Why it matters:** You need to see past price action to understand current prices in context
- **What you'll see:** 
  - Candlesticks showing price movements over time
  - Entry/exit markers showing where the system bought and sold
  - Price levels that acted as support or resistance
- **Think of it as:** A history book of price movements - you can see what happened before to understand what might happen next
- **When to use:** Always keep this enabled - it's the foundation of the chart

**⚡ LIVE (Live Updates)**
- **What it shows:** Real-time price updates as they happen
- **Why it matters:** Prices change constantly - this shows the most current price
- **How it works:** 
  - When enabled, the latest candlestick updates every 5 seconds
  - You see the price moving in real-time
  - The most recent candle "grows" as new price data comes in
- **Think of it as:** A live news feed - you see updates as they happen, not after the fact
- **When to use:** Enable when you want to see current market activity

**📈 VOL (Volume Bars)**
- **What it shows:** Trading volume (how much cryptocurrency was traded) for each time period
- **Why it matters:** Volume tells you how "serious" a price move is
  - **High volume + price up:** Many people buying = strong upward move
  - **High volume + price down:** Many people selling = strong downward move
  - **Low volume:** Few people trading = move might not last
- **What you'll see:** Bars below the price chart, taller bars = more volume
- **Think of it as:** A crowd meter - more people = more significant move
- **When to use:** Enable to confirm if price movements are meaningful or just noise

**🎮 SIM (Simulation Lines)**
- **What it shows:** Predicted or simulated price movements based on the system's mathematical models
- **Why it matters:** Shows what the system "thinks" might happen based on its analysis
- **How it works:** 
  - Uses physics factors (momentum, force, etc.) to predict price ranges
  - Shows upper and lower bounds of where price might go
  - Based on current parameters and market conditions
- **Think of it as:** A weather forecast for prices - not guaranteed, but based on current conditions
- **When to use:** Enable to see system predictions and understand how it's thinking

**👻 GHOST (Ghost Series)**
- **What it shows:** Alternative price series for comparison (like a moving average)
- **Why it matters:** Helps you see price trends more clearly by smoothing out noise
- **How it works:** 
  - Calculates an average of recent prices
  - Shows as a semi-transparent line over the candlesticks
  - Makes it easier to see the overall direction
- **Think of it as:** A blur filter on a photo - reduces detail but shows the main shape
- **When to use:** Enable when you want to see the trend without being distracted by small fluctuations

**💧 LIQUID (Liquidity Markers)**
- **What it shows:** Areas where there's a lot of trading activity (support and resistance levels)
- **Why it matters:** These levels often act as "price magnets" - prices tend to bounce off them
  - **Support:** Price level where buying happens (price bounces up)
  - **Resistance:** Price level where selling happens (price bounces down)
- **What you'll see:** Horizontal lines showing important price levels
- **Think of it as:** Floor and ceiling for prices - hard to break through
- **When to use:** Enable to see where prices might reverse or get stuck

**💰 TRADES (Trade Markers)**
- **What it shows:** Historical trade entry and exit points from your trading system
- **Why it matters:** See where the system actually bought and sold to understand its performance
- **What you'll see:** 
  - **Green markers/lines:** Entry points (where system bought)
  - **Red markers/lines:** Exit points (where system sold)
  - Shows P&L for each trade
- **Think of it as:** A replay of your trading history - see exactly what happened
- **When to use:** Enable to analyze past trades and learn from wins/losses

**📡 SIGNALS (Signal Markers)**
- **What it shows:** Trading signals from the system - buy/sell recommendations
- **Why it matters:** Shows when the system detects trading opportunities
- **What you'll see:** 
  - Markers showing buy/sell signals
  - Confidence levels (how sure the system is)
  - Regime information (bull/bear/sideways market)
- **Think of it as:** Traffic signals for trading - green (buy), red (sell), yellow (caution)
- **When to use:** Enable to see what the system is "thinking" and when it sees opportunities

**👁️ PROPHECY (PROPHECY Markers)**
- **What it shows:** Major Move Detected events from THOTH oracle - high-confidence predictions of significant price movements
- **Why it matters:** Early warning before major price movements happen (>1.5% or resonance >0.9)
- **What you'll see:** 
  - Gold detection price line (where PROPHECY was detected)
  - Target price line (where price is predicted to go - green for BUY, red for SELL)
  - Resonance value (confidence level, 0-1 scale)
  - Predicted move percentage
  - Intensity indicator (MAX INTENSITY for intensity >= 2.0)
- **Think of it as:** The oracle's eye - seeing major moves before they happen
- **When to use:** Enable to see high-confidence major move predictions on chart
- **Note:** Also available in dedicated PROPHECY Alert Center (port 1428)

#### Master Control Sliders

**Aggregation Sensitivity**
- **Range:** 0.1 - 5.0
- **Recommended:** 1.0 - 2.0
- **What it does:** Controls how sensitive the system is to price movements
- **Higher values:** More sensitive, reacts to smaller movements
- **Lower values:** Less sensitive, requires larger movements
- **Use case:** Adjust based on market volatility

**Signal Fidelity**
- **Range:** 0.0 - 1.0
- **Recommended:** 0.3 - 0.7
- **What it does:** Smoothing factor for price signals
- **0.0:** Raw data, no smoothing (more noise, faster response)
- **1.0:** Maximum smoothing (less noise, delayed signals)
- **Higher values:** Reduces noise but may delay signals

**Smoothing Level**
- **Range:** 0.0 - 1.0
- **Recommended:** 0.4 - 0.6
- **What it does:** Additional smoothing for chart display
- **Effect:** Makes charts easier to read but may hide short-term movements

#### Physics Parameter Sliders

**Friction**
- **Range:** 0.0 - 1.0
- **Recommended:** 0.2 - 0.5
- **What it does:** Simulates market friction/resistance
- **Higher values:** Slower price movements in simulations
- **Lower values:** Faster, more responsive movements

**Elasticity**
- **Range:** 0.0 - 2.0
- **Recommended:** 0.8 - 1.2
- **What it does:** Controls price bounce-back behavior
- **Higher values:** More elastic (bouncy) behavior
- **Lower values:** Less elastic, more damped

**Drift (Bias)**
- **Range:** -1.0 to 1.0
- **Recommended:** -0.2 to 0.2
- **What it does:** Bias term for price direction in simulations
- **Positive:** Upward bias
- **Negative:** Downward bias
- **0:** No bias (neutral)

**Volatility (Noise)**
- **Range:** 0.0 - 2.0
- **Recommended:** 0.1 - 0.5
- **What it does:** Adds random noise to simulations
- **Higher values:** More volatility in simulations
- **0:** No noise (deterministic)

#### Section Expand/Collapse Buttons
- **Location:** Control Deck section headers
- **Function:** Expand or collapse sections (Price Graph, Master Control, Physics, Simulation, Physics Factors, Performance)
- **Use case:** Organize Control Deck to focus on specific parameter groups

#### Help Button (?)
- **Location:** Control Deck header
- **Function:** Opens Control Deck-specific help
- **Keyboard shortcut:** F1 or ?

### Creative Views (Ports 1421, 1422)

#### Port 1421 - Creative View Controls

**Reset View Button**
- Returns 3D camera to default position and angle
- Use when you've rotated or zoomed too far
- Resets to initial view

**Toggle Connections Button**
- Show/hide connection lines between market nodes
- Connections represent correlations between markets
- Useful for focusing on specific relationships

**Toggle Labels Button**
- Show/hide correlation values on connection lines
- Labels show the strength of relationships
- Helps identify strong vs. weak correlations

**Reset Filter Button**
- Resets correlation filter to 30% threshold
- Shows only connections above this threshold
- Reduces visual clutter

**Mouse Controls:**
- **Drag:** Rotate the 3D view
- **Scroll:** Zoom in/out
- **Click node:** Highlight connections for that market

#### Port 1422 - Creative View v2 Controls

**📊 Chart Button**
- Toggle price history chart overlay
- Shows detailed price movements for selected market
- Click a node first to select a market

**🔄 Reset Button**
- Return 3D camera to default position
- Resets view to initial state

**🏷️ Labels Button**
- Show/hide market name labels on nodes
- Useful for identifying specific markets
- Note: Currently removed (feature deferred)

**🐛 Debug Button**
- Show/hide debug information panel
- Technical details about the visualization
- Useful for troubleshooting

**Close Chart Button**
- Closes the price chart overlay
- Returns to 3D view only

**Close Debug Button**
- Closes the debug panel

**Mouse Controls:**
- **Click node:** Select a market to see its price chart
- **Drag:** Rotate the 3D view
- **Scroll:** Zoom in/out
- **Click market in list:** Select and focus on that market

### Analytics, Risk, Execution (Ports 1424-1426)

#### Port 1424 - Performance Analytics
- **Help Button (?):** Opens help modal with analytics guidance
- **Interactive Charts:** Click and hover for details
- **Auto-updates:** Refreshes every 5 seconds

#### Port 1425 - Risk Management
- **Help Button (?):** Opens help modal with risk guidance
- **Risk Alerts:** Color-coded (Critical/Warning/Info)
- **Interactive Charts:** Hover for detailed metrics

#### Port 1426 - Trade Execution Monitor
- **Help Button (?):** Opens help modal
- **Symbol Selection:** Click symbol items to filter trades
- **Live Feed:** Auto-updates in real-time
- **Trade Items:** Clickable for details

---

## 4. View-by-View Guide

### Port 1420: MVP Dashboard

**Purpose:** Main entry point and overview dashboard

**Use Case:** 
- Daily monitoring starting point
- Quick status check
- Emergency controls access
- Navigation hub

**Key Features:**
- Performance metrics (P&L, win rate, trades)
- Market data table
- Recent trades log
- Emergency stop and trading toggle
- P&L over time chart

**Getting Started:**
1. Open http://localhost:1420
2. Check backend status (should be "Connected")
3. Review performance metrics
4. Check recent trades
5. Use navigation links to explore other views

**Common Workflows:**
- **Morning check:** Open MVP Dashboard, review overnight performance
- **Quick status:** Check P&L and win rate at a glance
- **Emergency:** Use Emergency Stop if needed
- **Navigation:** Jump to other views via links

**What to Watch For:**
- Backend connection status (should be green "Connected")
- P&L trends (positive = good, negative = review)
- Win rate (aim for >45% in validation phase)
- Recent trade activity (should see trades if system is active)

**Tips:**
- This is your "home base" - start here daily
- Bookmark this URL for quick access
- Use Emergency Stop only in true emergencies
- Trading Toggle is safer for planned pauses

### Port 1423: Trading Chart View

**Purpose:** Professional charting with full Control Deck

**Use Case:**
- Analyzing price action
- Reviewing trade entry/exit points
- Understanding system signals
- Adjusting system parameters

**Key Features:**
- Professional candlestick charts (TradingView Lightweight Charts)
- 8 layer toggles (HIST, LIVE, VOL, SIM, GHOST, LIQUID, TRADES, SIGNALS)
- Symbol selector (6 trading pairs)
- Timeframe selector (1m to 1d)
- Control Deck with sliders for parameters
- Real-time price updates
- Historical trade markers
- Signal markers with confidence

**Getting Started:**
1. Open http://localhost:1423
2. Select a symbol from dropdown
3. Choose a timeframe (start with 1H or 4H)
4. Enable HIST and VOL layers
5. Explore Control Deck sliders

**Common Workflows:**
- **Trade analysis:** Enable TRADES layer, review entry/exit points
- **Signal review:** Enable SIGNALS layer, see system recommendations
- **Parameter tuning:** Adjust sliders in Control Deck, observe effects
- **Multi-timeframe:** Switch timeframes to see different perspectives

**All Controls Explained:**
- See "Complete Button and Control Reference" section above

**What to Watch For:**
- Price trends (upward = bullish, downward = bearish)
- Volume spikes (indicate significant moves)
- Trade markers (green entries, red exits)
- Signal markers (buy/sell recommendations)
- Support/resistance levels (LIQUID layer)

**Tips:**
- Start with HIST + VOL + TRADES layers enabled
- Use 1H or 4H timeframe for balanced view
- Control Deck can be hidden to maximize chart space
- Experiment with sliders to understand their effects
- Use SIGNALS layer to see system predictions

### Port 1424: Performance Analytics Hub

**Purpose:** Comprehensive performance metrics and analytics

**Use Case:**
- Deep dive into performance
- Understanding win rates and P&L trends
- Analyzing trade statistics
- Equity curve analysis

**Key Features:**
- Total P&L, win rate, trade count
- Average P&L per trade
- Best/worst trade statistics
- Equity curve chart
- P&L timeline chart
- Win rate trend
- Drawdown visualization

**Getting Started:**
1. Open http://localhost:1424
2. Review top metrics (P&L, win rate, trades)
3. Examine equity curve (should trend upward if profitable)
4. Check P&L timeline for patterns
5. Review drawdown periods

**Common Workflows:**
- **Performance review:** Check all metrics, identify trends
- **Equity analysis:** Review equity curve for consistency
- **Drawdown analysis:** Identify periods of losses
- **Trade statistics:** Review best/worst trades

**What to Watch For:**
- **Positive P&L:** System is profitable
- **Win rate >45%:** Good for validation phase
- **Upward equity curve:** Consistent performance
- **Large drawdowns:** May indicate issues
- **Best vs. worst trades:** Understand trade distribution

**Tips:**
- Check this view daily for performance trends
- Equity curve should generally trend upward
- Large drawdowns may require investigation
- Compare win rate to target (45%+ in validation)

### Port 1425: Risk Management Dashboard

**Purpose:** Monitor risk metrics and alerts

**Use Case:**
- Risk assessment
- Position monitoring
- Alert management
- Safety checks

**Key Features:**
- Risk alerts (Critical/Warning/Info)
- Max drawdown tracking
- Position size monitoring
- Exposure metrics
- Risk heat maps
- Correlation matrices

**Getting Started:**
1. Open http://localhost:1425
2. Check risk alerts (should be green/info if healthy)
3. Review max drawdown (should be within limits)
4. Check position sizes
5. Monitor exposure levels

**Common Workflows:**
- **Daily risk check:** Review all risk metrics
- **Alert response:** Address critical/warning alerts
- **Drawdown monitoring:** Watch for excessive drawdowns
- **Position review:** Ensure position sizes are appropriate

**What to Watch For:**
- **Critical alerts:** Immediate action required
- **Warning alerts:** Monitor closely
- **Max drawdown:** Should stay below 8% in validation
- **Position sizes:** Should respect MAX_POSITION_SIZE
- **Exposure:** Total exposure should be reasonable

**Tips:**
- Check this view regularly (at least daily)
- Address critical alerts immediately
- Max drawdown >8% may trigger validation failure
- Position sizes should be conservative in validation phase

### Port 1426: Trade Execution Monitor

**Purpose:** Real-time trade execution feed

**Use Case:**
- Live trade monitoring
- Execution quality assessment
- Trade timeline analysis
- Symbol-specific trade review

**Key Features:**
- Live trade feed (updates in real-time)
- Execution metrics (slippage, hold time)
- Trade timeline visualization
- Symbol filtering
- Trade details (entry/exit, P&L, direction)

**Getting Started:**
1. Open http://localhost:1426
2. Watch live trade feed
3. Review execution metrics
4. Click symbols to filter trades
5. Examine trade timeline

**Common Workflows:**
- **Live monitoring:** Watch trades as they execute
- **Execution review:** Check slippage and hold times
- **Symbol analysis:** Filter by symbol to see performance
- **Timeline review:** See trading activity patterns

**What to Watch For:**
- **Trade frequency:** Should see trades if system is active
- **Slippage:** Should be low (<0.5% ideal)
- **Hold time:** Should match system parameters (~45 seconds)
- **P&L distribution:** Mix of wins and losses expected
- **Execution quality:** Fast execution, minimal slippage

**Tips:**
- Keep this view open during active trading
- Monitor slippage - high slippage may indicate issues
- Hold time should be consistent with system settings
- Review trade timeline for patterns

### Port 1427: Trade Opportunities

**Purpose:** ML prediction engine trade opportunities

**Use Case:**
- Review upcoming trade opportunities
- Filter and sort opportunities by confidence
- Monitor opportunity countdown timers
- Navigate to chart for detailed analysis

**Key Features:**
- Opportunity cards with predicted moves
- Confidence meters and urgency indicators
- Live countdown timers
- Filtering by symbol, type, confidence
- Sorting by confidence, urgency, move, time
- "View Chart" button for detailed analysis

**Getting Started:**
1. Open http://localhost:1427
2. Review summary cards (total, high confidence, avg move)
3. Browse opportunity cards
4. Use filters to focus on specific opportunities
5. Click "View Chart" to see detailed price action

**Common Workflows:**
- **Opportunity review:** Browse all active opportunities
- **High confidence focus:** Filter by min confidence >75%
- **Urgent opportunities:** Sort by time remaining
- **Symbol analysis:** Filter by specific symbol

**What to Watch For:**
- **High confidence opportunities:** >75% confidence
- **Urgent opportunities:** <10 minutes remaining
- **Large predicted moves:** >2% expected movement
- **Opportunity count:** More opportunities = more market activity

**Tips:**
- Check this view regularly for new opportunities
- Focus on high-confidence opportunities first
- Use countdown timers to prioritize urgent ones
- Combine with ChartView for detailed analysis

### Port 1428: PROPHECY Alert Center

**Purpose:** Real-time PROPHECY event feed - Major Move predictions from THOTH oracle

**Use Case:**
- Monitor high-confidence major move predictions
- Get early warning before significant price movements
- Track PROPHECY accuracy and resonance
- Quick access to actionable predictions

**Key Features:**
- Active PROPHECY events feed (auto-refreshes every 5 seconds)
- Large predicted move % display
- Live countdown timers (updates every second)
- Resonance meter (visual confidence indicator)
- Intensity badges (MAX INTENSITY for high-confidence)
- Summary stats (total events, high resonance, avg move, expiring soon)
- Filtering and sorting (resonance, move, time, intensity)
- One-click "View Chart" integration

**Getting Started:**
1. Open http://localhost:1428
2. Review summary cards for active PROPHECY events
3. Browse PROPHECY cards - larger cards = higher resonance
4. Watch countdown timers for time-sensitive predictions
5. Click "View Chart" to see PROPHECY markers on chart

**Common Workflows:**
- **Daily monitoring:** Check for new PROPHECY events
- **High resonance focus:** Filter by min resonance >0.9
- **Urgent predictions:** Watch countdown timers (<10 minutes)
- **Chart analysis:** Click "View Chart" to see PROPHECY on price chart

**What to Watch For:**
- **High resonance events:** >0.9 resonance = very high confidence
- **MAX INTENSITY badge:** Intensity >= 2.0 = strongest predictions
- **Large predicted moves:** >2% = significant price movement expected
- **Expiring soon:** <10 minutes = time-sensitive, act quickly
- **Gold/red urgency:** Visual indicators for high-confidence or imminent moves

**Understanding PROPHECY:**
- **What it is:** High-confidence predictions of major price movements (>1.5% or resonance >0.9)
- **Who generates it:** THOTH oracle (ML prediction engine)
- **When it triggers:** When system detects high-confidence major moves
- **Why it matters:** Early warning before price movements happen
- **Tagline:** "The system that doesn't care about news - it generates news"

**Tips:**
- This is your "news feed" - predictions before they happen
- Higher resonance = higher confidence in prediction
- MAX INTENSITY events are the most confident predictions
- Use countdown timers to prioritize time-sensitive predictions
- Combine with ChartView to see PROPHECY markers on price chart
- Filter by symbol to focus on specific trading pairs

### Port 1421: Creative View (3D Market Connections)

**Purpose:** Visualize market correlations in 3D

**Use Case:**
- Understanding market relationships
- Visual correlation analysis
- Market network exploration

**Key Features:**
- 3D visualization of market nodes
- Connection lines showing correlations
- Interactive 3D navigation
- Correlation filtering
- Node highlighting

**Getting Started:**
1. Open http://localhost:1421
2. Observe 3D market network
3. Drag to rotate view
4. Scroll to zoom
5. Click nodes to see connections
6. Toggle connections/labels

**Common Workflows:**
- **Correlation exploration:** Toggle connections to see relationships
- **Market analysis:** Click nodes to highlight connections
- **Filter adjustment:** Use correlation filter to focus on strong relationships

**What to Watch For:**
- **Strong connections:** Thick lines = high correlation
- **Market clusters:** Groups of connected markets
- **Isolated nodes:** Markets with few connections

**Tips:**
- Use Reset View if you get lost in 3D space
- Toggle connections to reduce visual clutter
- Click nodes to focus on specific markets
- Correlation filter helps identify strong relationships

### Port 1422: Creative View v2 (3D Network + Chart)

**Purpose:** Enhanced 3D visualization with price chart overlay

**Use Case:**
- Combined 3D and chart analysis
- Market network with price context
- Interactive market exploration

**Key Features:**
- 3D market network
- Price chart overlay (toggleable)
- Debug panel
- Node selection
- Market list sidebar

**Getting Started:**
1. Open http://localhost:1422
2. Explore 3D network
3. Click a node to select market
4. Toggle chart to see price history
5. Use debug panel for technical details

**Common Workflows:**
- **Market selection:** Click node, view price chart
- **Network exploration:** Navigate 3D space, find relationships
- **Price analysis:** Combine 3D view with chart data

**What to Watch For:**
- **Node colors:** Green = buy signal, Red = sell signal
- **Node sizes:** Larger = higher volume
- **Price charts:** Show historical price action for selected market

**Tips:**
- Click nodes in 3D view or sidebar list
- Toggle chart to see price context
- Use debug panel for technical insights
- Reset view if navigation gets confusing

---

## 5. Glossary of Trading Terms

### Basic Trading Terms

**P&L (Profit & Loss)**
- **What it is:** The total profit or loss from all trades combined
- **How to read it:**
  - **Positive number (e.g., +$50):** You've made money overall
  - **Negative number (e.g., -$30):** You've lost money overall
  - **Zero:** Break-even (neither profit nor loss)
- **Why it matters:** This is the bottom line - are you making or losing money?
- **Think of it as:** Your bank account balance for trading - positive = good, negative = bad
- **Example:** If you started with $1000 and now have $1050, your P&L is +$50 (5% profit)

**Win Rate**
- **What it is:** The percentage of trades that ended up profitable
- **How it's calculated:** (Number of Winning Trades / Total Number of Trades) × 100
- **How to read it:**
  - **50%:** Half your trades win, half lose (break-even if wins = losses)
  - **60%:** 6 out of 10 trades win (good!)
  - **40%:** 4 out of 10 trades win (concerning if losses are bigger than wins)
- **Why it matters:** Shows how often the system is "right" - but remember, a 40% win rate can still be profitable if wins are bigger than losses
- **Target:** >45% in validation phase means the system wins more often than it loses
- **Example:** If you made 100 trades and 55 were profitable, your win rate is 55%

**Drawdown**
- **What it is:** How much your account value has dropped from its highest point
- **How to understand it:**
  - Imagine your account goes: $1000 → $1100 → $950
  - Highest point: $1100
  - Lowest point after that: $950
  - Drawdown: $1100 - $950 = $150 (or 13.6% of the peak)
- **Why it matters:** Shows the "worst case" - how much you could lose from a peak
- **Think of it as:** Like a roller coaster - you went up to $1100, then down to $950. The drawdown measures how far down you went.
- **Key point:** Even profitable systems have drawdowns - it's normal. The goal is to keep them small (<8% in validation)
- **Example:** 
  - Start: $1000
  - Peak: $1100 (you're up $100!)
  - Current: $900 (you're down $100 from start, but down $200 from peak)
  - Drawdown from peak: $200 (18.2%) - this is what matters for risk

**Equity Curve**
- A chart showing account value over time
- Upward trend = profitable system
- Downward trend = losing system
- Should generally trend upward for good systems

**Position Size**
- The amount of capital allocated to a single trade
- Expressed as percentage of account (e.g., 0.5% = 0.5% of account)
- Smaller sizes = lower risk, larger sizes = higher risk

**Entry/Exit**
- **Entry:** The price at which a position is opened
- **Exit:** The price at which a position is closed
- Entry price - Exit price = P&L for the trade

**Long/Short**
- **Long:** Buying an asset expecting price to rise (profit when price goes up)
- **Short:** Selling an asset expecting price to fall (profit when price goes down)
- This system primarily uses LONG positions

**Slippage**
- The difference between expected price and actual execution price
- Caused by market movement during order execution
- Lower slippage = better execution quality
- Target: <0.5% for good execution

### Technical Terms

**Candlestick**
- **What it is:** A visual representation of price action over a specific time period (1 minute, 1 hour, 1 day, etc.)
- **What it shows:** Four key prices in one visual:
  - **Open (O):** Price at the start of the period
  - **High (H):** Highest price during the period
  - **Low (L):** Lowest price during the period
  - **Close (C):** Price at the end of the period
- **How to read it:**
  - **Green/White candlestick:** Close price was higher than open price (price went up)
  - **Red/Black candlestick:** Close price was lower than open price (price went down)
  - **Body (thick part):** Shows the range between open and close
  - **Wicks (thin lines):** Show how far price went above (top wick) or below (bottom wick) the body
- **Why it matters:** One candlestick tells you a complete story of price movement in that time period
- **Think of it as:** A mini price chart compressed into one symbol
- **Example:** 
  - A green candlestick with a long body and small wicks = strong upward move
  - A red candlestick with long wicks and small body = price tried to move but got rejected

**Timeframe**
- The time period each candlestick represents
- Examples: 1 minute, 5 minutes, 1 hour, 1 day
- Shorter timeframes = more detail, more noise
- Longer timeframes = less detail, clearer trends

**Volume**
- The amount of an asset traded in a time period
- Higher volume = more market activity
- Volume spikes often accompany significant price moves
- Used to confirm price movements

**Support/Resistance**
- **Support:** Price level where buying pressure is strong (price tends to bounce up)
- **Resistance:** Price level where selling pressure is strong (price tends to bounce down)
- These levels can act as barriers to price movement

**Signal Strength**
- A measure of how strong a trading signal is
- Examples: "STRONG BUY", "BUY", "NEUTRAL", "SELL", "STRONG SELL"
- Stronger signals = higher confidence in the prediction

**Confidence Level**
- A percentage (0-100%) indicating how confident the system is in a signal
- Higher confidence = more reliable signal
- Lower confidence = more uncertain signal

**Regime**
- The overall market condition
- **Bull:** Upward trending market (prices generally rising)
- **Bear:** Downward trending market (prices generally falling)
- **Sideways:** Range-bound market (prices moving sideways)
- System adapts behavior based on detected regime

### System-Specific Terms

**Physics Factors**
- **What they are:** Eight mathematical measurements the system uses to understand market behavior, inspired by physics concepts
- **Why "Physics"?** Markets behave in ways similar to physical systems - they have momentum, forces, and energy. These factors measure those properties.

**The Eight Factors Explained:**

1. **Momentum**
   - **What it measures:** How fast price is changing (speed and direction)
   - **Think of it as:** Like a ball rolling - is it speeding up or slowing down?
   - **High momentum:** Price moving strongly in one direction
   - **Low momentum:** Price moving slowly or changing direction

2. **Strain**
   - **What it measures:** Market stress or pressure building up
   - **Think of it as:** Like a spring being compressed - pressure building before a release
   - **High strain:** Market under stress, might be ready for a big move
   - **Low strain:** Market is calm, stable

3. **Force**
   - **What it measures:** The driving forces pushing price in a direction
   - **Think of it as:** Like wind pushing a sailboat - what's driving the price?
   - **High force:** Strong buying or selling pressure
   - **Low force:** Weak or balanced forces

4. **Squeeze**
   - **What it measures:** How compressed price movements are (trading in a tight range)
   - **Think of it as:** Like a spring being squeezed - energy building up
   - **High squeeze:** Price stuck in narrow range, might explode soon
   - **Low squeeze:** Price moving freely

5. **Flow**
   - **What it measures:** How easily money is moving in/out (liquidity)
   - **Think of it as:** Like water flow - is money flowing smoothly or blocked?
   - **High flow:** Lots of trading, easy to buy/sell
   - **Low flow:** Less trading, harder to execute

6. **Entropy**
   - **What it measures:** Market randomness or disorder (how chaotic)
   - **Think of it as:** Like a room - organized (low entropy) or messy (high entropy)?
   - **High entropy:** Very random, unpredictable movements
   - **Low entropy:** More organized, predictable patterns

7. **Jerk**
   - **What it measures:** How quickly momentum is changing (acceleration of acceleration)
   - **Think of it as:** Like a car - not just speeding up, but how quickly it's speeding up
   - **High jerk:** Rapid changes in momentum (volatile)
   - **Low jerk:** Smooth, gradual changes

8. **Sympathy**
   - **What it measures:** How correlated this market is with other markets
   - **Think of it as:** Like friends - do they move together or independently?
   - **High sympathy:** Moves with other markets (like Bitcoin and Ethereum)
   - **Low sympathy:** Moves independently

**Why They Matter:**
- These factors help the system understand market conditions
- Different combinations indicate different market states
- The system uses them to make trading decisions
- You can see them in the Control Deck's Physics Factors section

**Shadow Position**
- A simulated position used for testing strategies
- Not a real trade, but tracks what would have happened
- Used to validate strategies before live trading
- Shown as "Shadow P&L" in dashboard

**Validation Phase**
- A testing period before full deployment
- System must meet criteria:
  - Minimum trades (e.g., 75 trades)
  - Minimum win rate (e.g., 45%)
  - Maximum drawdown (e.g., 8%)
  - Target hours (e.g., 3 hours)
- Only after validation does system move to full trading

**Hold Time**
- How long a position is held before closing
- Current system: ~45 seconds average
- Shorter hold times = more trades, less risk per trade
- Longer hold times = fewer trades, more risk per trade

**Correlation**
- A measure of how two markets move together
- Range: 0% (no relationship) to 100% (move together)
- High correlation = markets move similarly
- Used in Creative views to show market relationships

**Market Connections**
- Visual representation of correlations between markets
- Shown as lines in 3D Creative views
- Thicker lines = stronger correlation
- Helps identify market relationships

### Risk Terms

**Max Drawdown**
- The largest peak-to-trough decline in equity
- Measured from highest equity point to lowest point
- Example: Equity goes $1000 → $1100 → $950, max drawdown = $150 (13.6%)
- Target: Stay below 8% in validation phase

**Risk Metrics**
- Various measurements of trading risk:
  - Position size limits
  - Exposure levels
  - Drawdown tracking
  - Correlation risk

**Position Limits**
- Maximum position size allowed
- Set by MAX_POSITION_SIZE parameter
- Prevents overexposure to single trades
- Example: 0.5% = no single trade uses more than 0.5% of account

**Emergency Stop**
- A safety feature that immediately halts all trading
- Stops all open positions
- Prevents new trades
- Use only in emergencies

**Panic Switch**
- An automatic safety mechanism
- Triggers when system detects issues (high disk usage, system load, etc.)
- Automatically pauses trading
- Protects system from dangerous conditions

---

## 6. Simple Trading Advice

### Understanding the Dashboard

**What Good Performance Looks Like:**
- **Positive P&L:** System is making money
- **Win rate >45%:** More wins than losses (in validation phase)
- **Upward equity curve:** Consistent growth over time
- **Reasonable drawdown:** Stays below 8% in validation
- **Steady trade flow:** Regular trading activity

**When to Be Concerned:**
- **Negative P&L:** System is losing money (review after sufficient trades)
- **Win rate <40%:** Too many losing trades
- **Large drawdowns:** Exceeding 8% in validation
- **No trades:** System may not be finding opportunities
- **Erratic equity curve:** Large swings, inconsistent performance

**Key Metrics to Monitor:**
1. **Total P&L:** Overall profitability
2. **Win Rate:** Trade success percentage
3. **Max Drawdown:** Risk level
4. **Trade Count:** System activity
5. **Average P&L:** Quality of trades

### Risk Management Basics

**Why Position Sizing Matters:**
- **What is Position Sizing?** It's how much of your account you risk on each trade
- **The Math:**
  - If you have $1000 and use 1% position size = $10 per trade
  - If you have $1000 and use 0.5% position size = $5 per trade
  - If you have $1000 and use 10% position size = $100 per trade (risky!)

- **Why Smaller is Safer:**
  - **Smaller positions = lower risk per trade**
    - If a trade loses, you only lose a small percentage
    - Example: 0.5% position loses = you lose 0.5% of account
    - Example: 10% position loses = you lose 10% of account (20x worse!)
  
  - **Protects account from large losses**
    - Even if you have 10 losing trades in a row at 0.5%, you've only lost 5% total
    - But 10 losing trades at 10% = 100% loss (account wiped out!)
  
  - **Allows system to recover from losing streaks**
    - Losing streaks are normal - even good systems lose sometimes
    - Small positions mean you can survive many losses and still recover
    - Large positions mean one bad streak can wipe you out
  
  - **Current system uses conservative sizing (0.5% or less)**
    - This is very safe - you'd need 200 losing trades to lose everything
    - Allows the system to learn and improve without catastrophic risk
    - Perfect for validation phase when you're testing the system

- **Real-World Example:**
  - **Bad:** Use 20% per trade, lose 5 trades = 100% account loss (game over)
  - **Good:** Use 0.5% per trade, lose 5 trades = 2.5% account loss (still have 97.5%, can recover)

**Understanding Drawdown:**
- Drawdown is normal - even profitable systems have losing periods
- Key is keeping drawdown manageable (<8% in validation)
- Large drawdowns may indicate system issues
- Recovery time matters - quick recovery is better

**When to Use Emergency Stop:**
- System behaving unexpectedly
- Market conditions have changed dramatically
- Technical issues detected
- Risk metrics exceed safe limits
- **Not for:** Normal losses, temporary drawdowns, planned pauses

**Setting Appropriate Limits:**
- Position size: Start conservative (0.5% or less)
- Max drawdown: 8% in validation, adjust based on risk tolerance
- Win rate target: 45%+ in validation phase
- Trade frequency: Let system determine based on opportunities

### Interpreting Signals

**What Signal Strength Means:**
- **STRONG BUY/SELL:** High confidence, strong signal
- **BUY/SELL:** Moderate confidence, decent signal
- **NEUTRAL:** No clear signal, wait for better opportunity
- Stronger signals are more reliable but less frequent

**Confidence Levels Explained:**
- **80-100%:** Very high confidence, strong signal
- **60-79%:** Good confidence, reliable signal
- **40-59%:** Moderate confidence, use with caution
- **<40%:** Low confidence, may be unreliable
- Higher confidence = more likely to be correct

**When Signals Are Reliable vs. Uncertain:**
- **Reliable:** High confidence (>60%), strong signal, confirmed by volume
- **Uncertain:** Low confidence (<50%), weak signal, low volume
- **Regime matters:** Signals more reliable in trending markets
- **Multiple confirmations:** Better when multiple factors agree

**Regime Detection (Bull/Bear/Sideways):**
- **Bull market:** Prices generally rising, uptrends
- **Bear market:** Prices generally falling, downtrends
- **Sideways:** Prices moving in range, no clear trend
- System adapts strategy based on detected regime
- Different regimes require different approaches

### Chart Analysis Basics

**Reading Candlesticks:**
Understanding candlesticks is like learning to read a language - once you understand the basics, you can see what the market is "saying."

- **Green/White Candlesticks:**
  - **Meaning:** Price closed higher than it opened (bullish/upward)
  - **What happened:** Buyers were stronger than sellers during this period
  - **Think of it as:** A "win" for buyers - they pushed price up
  - **Example:** Opened at $100, closed at $105 = green candle showing $5 gain

- **Red/Black Candlesticks:**
  - **Meaning:** Price closed lower than it opened (bearish/downward)
  - **What happened:** Sellers were stronger than buyers during this period
  - **Think of it as:** A "win" for sellers - they pushed price down
  - **Example:** Opened at $100, closed at $95 = red candle showing $5 loss

- **Body Size (the thick part):**
  - **Large body:** Strong move - buyers or sellers were very determined
  - **Small body:** Weak move - indecision, neither side won decisively
  - **Think of it as:** The size of the "battle" - big body = big fight, small body = small skirmish
  - **Example:** Large green body = strong buying pressure, small red body = weak selling

- **Wicks (the thin lines above/below):**
  - **Top wick:** Shows how high price went before being pushed back down
  - **Bottom wick:** Shows how low price went before being pushed back up
  - **Long wicks:** Price tried to move far but got rejected
  - **Short wicks:** Price stayed close to open/close (strong control)
  - **Think of it as:** The "attempts" - long wick = tried hard but failed, short wick = stayed in control
  - **Example:** Long top wick on red candle = sellers tried to push price up but failed

- **Common Patterns:**
  - **Multiple green candles in a row:** Uptrend - buyers in control
  - **Multiple red candles in a row:** Downtrend - sellers in control
  - **Small bodies with long wicks:** Indecision - both sides fighting
  - **Large green candle after red candles:** Possible reversal - buyers taking control
  - **Large red candle after green candles:** Possible reversal - sellers taking control

**Putting It Together:**
- A large green candle with small wicks = strong buying, price went up and stayed up
- A small red candle with long wicks = weak selling, price tried to go down but bounced back
- Multiple large green candles = strong uptrend
- Mix of small candles = sideways/choppy market

**Understanding Volume:**
- **High volume:** Strong conviction, significant move
- **Low volume:** Weak conviction, may reverse
- **Volume spikes:** Often accompany important price moves
- **Volume confirmation:** Price moves with volume are more reliable

**Support and Resistance Levels:**
- **What they are:** Price levels where the market has historically reacted strongly
- **Support:**
  - **Definition:** A price level where buying pressure is strong enough to prevent prices from falling further
  - **How it works:** When price reaches support, buyers step in and push price back up
  - **Think of it as:** A floor - price bounces up when it hits the floor
  - **Visual:** Price touches this level multiple times and bounces up each time
  - **Example:** Bitcoin keeps bouncing off $40,000 - that's a support level
  
- **Resistance:**
  - **Definition:** A price level where selling pressure is strong enough to prevent prices from rising further
  - **How it works:** When price reaches resistance, sellers step in and push price back down
  - **Think of it as:** A ceiling - price bounces down when it hits the ceiling
  - **Visual:** Price touches this level multiple times and bounces down each time
  - **Example:** Bitcoin keeps getting rejected at $45,000 - that's a resistance level

- **Why they matter:**
  - Prices often reverse at these levels
  - They help predict where price might go
  - Breaking through them often signals a significant move
  
- **Breakthrough:**
  - When price breaks above resistance or below support, it often continues in that direction
  - Like breaking through a wall - once broken, price often moves strongly
  - Example: If Bitcoin breaks above $45,000 resistance, it might surge to $50,000

- **Multiple touches:**
  - The more times price touches a support/resistance level, the stronger it becomes
  - Like a door that's been slammed many times - it gets weaker
  - Strong levels: Price bounces many times before breaking
  - Weak levels: Price breaks through quickly

**Timeframe Selection for Different Goals:**
- **Short-term (1m, 5m):** Day trading, quick decisions
- **Medium-term (15m, 1h):** Swing trading, balanced view
- **Long-term (4h, 1d):** Position trading, trend analysis
- **Multiple timeframes:** Use together for confirmation

### Performance Analysis

**What Win Rate Is Acceptable:**
- **Validation phase:** 45%+ is target
- **Long-term:** 50%+ is good, 55%+ is excellent
- **Context matters:** Win rate alone doesn't tell full story
- **Risk-reward:** Lower win rate OK if average win > average loss

**Understanding P&L Trends:**
- **Upward trend:** System is profitable, keep monitoring
- **Downward trend:** System losing, investigate after sufficient trades
- **Sideways:** Break-even, may need adjustment
- **Volatility:** Large swings may indicate issues

**Equity Curve Interpretation:**
- **Smooth upward:** Ideal, consistent profits
- **Steep upward:** Very profitable but may be risky
- **Downward:** Losing system, needs review
- **Erratic:** Inconsistent, may need parameter adjustment

**When to Adjust Parameters:**
- **After validation:** System has proven itself
- **Market changes:** Regime shifts may require adjustment
- **Persistent issues:** Drawdown, low win rate after many trades
- **Not too often:** Let system run, avoid over-optimization

### Common Mistakes to Avoid

**Overreacting to Short-Term Losses:**
- Losing trades are normal, even for profitable systems
- Don't stop system after a few losses
- Need sufficient sample size (75+ trades) to judge
- Focus on long-term trends, not individual trades

**Ignoring Risk Metrics:**
- Risk dashboard exists for a reason - use it
- Drawdown warnings are important
- Position size limits protect you
- Regular risk checks prevent disasters

**Changing Parameters Too Frequently:**
- Let system run and gather data
- Frequent changes prevent learning what works
- Wait for validation period to complete
- Make changes based on data, not emotions

**Not Understanding the System Before Using It:**
- Read documentation thoroughly
- Understand what each metric means
- Know when to use emergency stop
- Familiarize yourself with all views
- Start with small position sizes

---

## 7. Common Workflows

### Daily Monitoring Workflow

**Morning Routine (5 minutes):**
1. Open MVP Dashboard (port 1420)
2. Check backend connection status
3. Review overnight P&L
4. Check win rate and trade count
5. Review recent trades
6. Check Risk Dashboard (port 1425) for alerts
7. Quick glance at ChartView (port 1423) for price action

**What to Look For:**
- Positive P&L trend
- Win rate staying above 45%
- No critical risk alerts
- Normal trade frequency
- No unexpected behavior

### Analyzing Performance

**Using Analytics and ChartView Together:**
1. Open Analytics (port 1424) for metrics overview
2. Review equity curve for trends
3. Check P&L timeline for patterns
4. Switch to ChartView (port 1423)
5. Enable TRADES layer to see entry/exit points
6. Compare chart performance to analytics metrics
7. Identify winning vs. losing trade patterns

**Key Questions:**
- Are trades entering at good prices?
- Are exits timely?
- What patterns lead to wins vs. losses?
- Is system following signals correctly?

### Risk Assessment

**Using Risk Dashboard Effectively:**
1. Open Risk Dashboard (port 1425)
2. Check all risk alerts (should be green/info)
3. Review max drawdown (should be <8%)
4. Check position sizes (should respect limits)
5. Review exposure levels
6. Check correlation matrices if available
7. Address any warnings immediately

**Red Flags:**
- Critical alerts = immediate action
- Drawdown approaching 8% = monitor closely
- Position sizes too large = review settings
- Excessive exposure = reduce risk

### Trade Analysis

**Reviewing Execution and Chart Data:**
1. Open Execution Monitor (port 1426)
2. Review recent trades in live feed
3. Check slippage (should be <0.5%)
4. Review hold times (should match system ~45s)
5. Switch to ChartView (port 1423)
6. Enable TRADES and SIGNALS layers
7. Analyze entry/exit points relative to signals
8. Identify execution quality issues

**What to Analyze:**
- Entry timing vs. signals
- Exit timing vs. price action
- Slippage impact on P&L
- Hold time effectiveness

### Emergency Procedures

**Using Emergency Stop and Trading Toggle:**
1. **Emergency Stop (True Emergency):**
   - Click Emergency Stop button
   - Confirm in dialog
   - System halts immediately
   - Review what happened
   - Fix issues before resuming

2. **Trading Toggle (Planned Pause):**
   - Click Trading Toggle
   - System pauses new trades
   - Monitoring continues
   - Resume when ready

**When to Use Each:**
- **Emergency Stop:** System errors, unexpected behavior, critical issues
- **Trading Toggle:** Planned maintenance, parameter review, temporary pause

### Parameter Adjustment

**When and How to Adjust Settings:**
1. **Wait for Validation:** Let system complete validation period
2. **Gather Data:** Need sufficient trades (75+) to make decisions
3. **Identify Issues:** Use Analytics to find problems
4. **Make Small Changes:** Adjust one parameter at a time
5. **Test Changes:** Monitor results after adjustments
6. **Document Changes:** Note what changed and why

**Common Adjustments:**
- Position size (if too risky or too conservative)
- Sensitivity (if missing opportunities or too many false signals)
- Smoothing (if too noisy or too delayed)

---

## 8. Advanced Features

### Control Deck in ChartView

**Layer Toggles:**
- Combine multiple layers for comprehensive analysis
- Example: HIST + VOL + TRADES + SIGNALS = full picture
- Experiment with different combinations
- Each layer adds information

**Sliders:**
- Start with default values
- Make small adjustments
- Observe effects on chart
- Document what works
- Don't over-optimize

**Physics Factors:**
- Advanced system metrics
- Shown in Control Deck
- Help understand system state
- Not typically user-adjustable
- Monitor for system health

### 3D Visualizations

**Creative Views:**
- Use for market relationship analysis
- Identify correlated markets
- Visual exploration of market network
- Not essential for daily trading
- Useful for understanding market structure

**Navigation Tips:**
- Reset view if lost
- Click nodes to focus
- Toggle connections to reduce clutter
- Use filters to focus on strong relationships

### Real-Time Updates

**WebSocket vs. Polling:**
- WebSocket provides instant updates (when available)
- Polling updates every 5-10 seconds (always works)
- Both methods are functional
- WebSocket is enhancement, not requirement

**Monitoring:**
- Watch status indicators
- "Connected" = backend responding
- "Disconnected" = check backend
- Data still updates via polling if WebSocket fails

### Historical Data Analysis

**Using Historical Markers:**
- Enable HIST layer in ChartView
- See 24h high/low levels
- Support/resistance markers
- Past trade entry/exit points
- Helps understand price context

**Trade History:**
- Enable TRADES layer
- Review past trade performance
- Learn from wins and losses
- Identify patterns
- Improve understanding

### Physics Factors Interpretation

**Eight Factors:**
1. **Momentum:** Price change rate (higher = faster moves)
2. **Strain:** Market pressure (higher = more stress)
3. **Force:** Driving forces (higher = stronger moves)
4. **Squeeze:** Compression (higher = tighter range)
5. **Flow:** Liquidity (higher = better flow)
6. **Entropy:** Randomness (higher = more chaotic)
7. **Jerk:** Acceleration change (higher = more volatile)
8. **Sympathy:** Correlation (higher = more connected)

**What They Mean:**
- Shown in Control Deck Physics Factors section
- Help understand market state
- Not directly adjustable
- Monitor for system insights

### Performance Metrics Deep Dive

**Analytics Dashboard:**
- Total P&L: Overall profitability
- Win Rate: Success percentage
- Trade Count: Activity level
- Average P&L: Trade quality
- Best/Worst Trades: Extremes
- Equity Curve: Long-term trend
- Drawdown: Risk level

**Interpreting Together:**
- No single metric tells full story
- Combine metrics for complete picture
- Look for trends, not single values
- Compare to validation targets

---

## 9. Getting Comfortable

### Progressive Learning Path

**Week 1: Basics**
- Day 1: Launch all views, explore MVP Dashboard
- Day 2: Learn ChartView basics (symbols, timeframes)
- Day 3: Understand Analytics metrics
- Day 4: Review Risk Dashboard
- Day 5: Monitor Execution feed
- Day 6: Explore Creative views
- Day 7: Review all views, identify favorites

**Week 2: Intermediate**
- Learn Control Deck in ChartView
- Understand layer toggles
- Experiment with sliders
- Analyze trade patterns
- Review performance trends

**Week 3: Advanced**
- Combine multiple views for analysis
- Adjust parameters (if needed)
- Deep dive into physics factors
- Advanced chart analysis
- Develop personal workflow

### Recommended View Order

**For Beginners:**
1. MVP Dashboard (start here)
2. Analytics (understand performance)
3. Risk (learn risk management)
4. Execution (see live trades)
5. ChartView (advanced charting)
6. Creative views (optional, for exploration)

**For Daily Use:**
1. MVP Dashboard (quick check)
2. Risk Dashboard (safety check)
3. Analytics (performance review)
4. ChartView (detailed analysis if needed)

### Practice Exercises

**Exercise 1: Basic Navigation**
- Launch all views
- Navigate between views
- Use help system (F1)
- Hover over controls for tooltips

**Exercise 2: Chart Analysis**
- Open ChartView
- Change symbols
- Switch timeframes
- Enable different layers
- Observe changes

**Exercise 3: Performance Review**
- Open Analytics
- Review all metrics
- Examine equity curve
- Check P&L timeline
- Identify trends

**Exercise 4: Risk Check**
- Open Risk Dashboard
- Review all alerts
- Check drawdown
- Verify position sizes
- Address any warnings

**Exercise 5: Trade Analysis**
- Open Execution Monitor
- Review recent trades
- Filter by symbol
- Check execution quality
- Compare to ChartView

### Keyboard Shortcuts

- **F1 or ?:** Open help modal (any view)
- **ESC:** Close help modal
- **Tab:** Navigate between controls (accessibility)
- **Arrow keys:** Adjust sliders (when focused)

### Help System

**How to Access:**
- Press F1 or ? key
- Click ? button (usually bottom-right)
- Hover over controls for tooltips

**What's Available:**
- Control explanations
- View-specific guidance
- Keyboard shortcuts
- Troubleshooting tips
- Trading advice

### First Week Checklist

**Day 1: Setup**
- [ ] Launch all views
- [ ] Verify backend connection
- [ ] Explore MVP Dashboard
- [ ] Read this guide

**Day 2: Charts**
- [ ] Learn ChartView basics
- [ ] Change symbols and timeframes
- [ ] Enable basic layers
- [ ] Review trade markers

**Day 3: Analytics**
- [ ] Understand all metrics
- [ ] Review equity curve
- [ ] Check P&L trends
- [ ] Identify patterns

**Day 4: Risk**
- [ ] Review risk dashboard
- [ ] Understand alerts
- [ ] Check drawdown
- [ ] Verify position sizes

**Day 5: Execution**
- [ ] Monitor live feed
- [ ] Review execution quality
- [ ] Check slippage
- [ ] Analyze hold times

**Day 6: Advanced**
- [ ] Explore Control Deck
- [ ] Experiment with sliders
- [ ] Combine multiple views
- [ ] Develop workflow

**Day 7: Mastery**
- [ ] Comfortable with all views
- [ ] Understand all metrics
- [ ] Know when to use each view
- [ ] Confident in system operation

---

## 10. Troubleshooting

### Common Issues and Solutions

**Backend Not Connected:**
- **Symptom:** Status shows "Disconnected", metrics show "--"
- **Solution:**
  1. Check backend is running on port 8000
  2. Verify `http://localhost:8000/api` is accessible
  3. Check browser console for errors
  4. Restart backend if needed
  5. Refresh frontend page

**View Not Loading:**
- **Symptom:** Page blank or errors
- **Solution:**
  1. Check browser console (F12) for errors
  2. Verify serve script is running
  3. Check port is not in use
  4. Try refreshing page
  5. Restart serve script

**Data Not Updating:**
- **Symptom:** Metrics stuck, no new data
- **Solution:**
  1. Check backend connection
  2. Verify backend is processing trades
  3. Check browser console for API errors
  4. Refresh page
  5. Check WebSocket connection (optional)

**Performance Issues:**
- **Symptom:** Slow loading, laggy interface
- **Solution:**
  1. Close unnecessary browser tabs
  2. Check system resources
  3. Disable browser extensions
  4. Use lighter views if needed
  5. Restart browser

**Button Not Working:**
- **Symptom:** Clicking button does nothing
- **Solution:**
  1. Check browser console for errors
  2. Verify JavaScript is enabled
  3. Try refreshing page
  4. Check if help-system.js is loaded
  5. Try different browser

**Chart Not Displaying:**
- **Symptom:** Chart area blank
- **Solution:**
  1. Check browser console for errors
  2. Verify TradingView library loaded
  3. Check internet connection (CDN libraries)
  4. Try different symbol
  5. Refresh page

### Backend Connection Problems

**API Not Responding:**
- Check backend logs
- Verify backend is running
- Check firewall settings
- Verify port 8000 is accessible
- Test with: `curl http://localhost:8000/api/dashboard/metrics`

**WebSocket Not Connecting:**
- This is **expected** if backend WebSocket isn't available
- Frontend works with API polling alone
- WebSocket is optional enhancement
- Check console for connection attempts
- Not a critical issue

**CORS Errors:**
- Usually indicates backend configuration issue
- Check backend CORS settings
- Verify API base URL is correct
- Contact backend developer if needed

### View-Specific Issues

**ChartView:**
- Control Deck not showing: Check JavaScript console
- Layers not working: Verify layer toggle handlers
- Sliders not responding: Check ControlSlider.js loaded
- Chart blank: Verify TradingView library loaded

**Creative Views:**
- 3D not rendering: Check Three.js library loaded
- Controls not working: Check JavaScript console
- Performance slow: Reduce node count or simplify view

**Analytics/Risk/Execution:**
- Charts not showing: Check Chart.js library loaded
- Data not updating: Check backend connection
- Metrics wrong: Verify API endpoints

---

## 11. Best Practices

### Monitoring Strategy

**Daily Routine:**
1. Morning: Quick check of MVP Dashboard
2. Midday: Review Analytics and Risk
3. Evening: Full review of all metrics
4. As needed: Check Execution feed during active trading

**Weekly Review:**
1. Comprehensive performance analysis
2. Review equity curve trends
3. Check risk metrics
4. Analyze trade patterns
5. Adjust parameters if needed (after validation)

### When to Use Which View

**MVP Dashboard:**
- Daily starting point
- Quick status check
- Emergency controls
- Navigation hub

**ChartView:**
- Detailed price analysis
- Trade entry/exit review
- Signal analysis
- Parameter adjustment

**Analytics:**
- Performance deep dive
- Equity curve analysis
- Trade statistics
- Trend identification

**Risk Dashboard:**
- Safety checks
- Alert monitoring
- Drawdown tracking
- Position review

**Execution Monitor:**
- Live trade monitoring
- Execution quality
- Real-time activity
- Trade timeline

**Creative Views:**
- Market relationship exploration
- Correlation analysis
- Visual market understanding
- Optional, for learning

### How to Interpret Metrics

**Look for Trends, Not Single Values:**
- One bad trade doesn't mean system is broken
- One good day doesn't mean system is perfect
- Focus on overall trends over time
- Need sufficient sample size (75+ trades)

**Combine Multiple Metrics:**
- P&L + Win Rate + Drawdown = complete picture
- Don't rely on single metric
- Context matters
- Compare to validation targets

**Understand Normal Variation:**
- Some losses are expected
- Drawdowns are normal
- Win rate fluctuates
- Focus on long-term performance

### Safety Features

**Emergency Stop:**
- Use only in true emergencies
- Understand what it does
- Know how to resume
- Document why you used it

**Trading Toggle:**
- Safer for planned pauses
- Use for maintenance
- System continues monitoring
- Easy to resume

**Risk Alerts:**
- Pay attention to warnings
- Address critical alerts immediately
- Don't ignore risk metrics
- Regular risk checks prevent problems

### Regular Maintenance Tasks

**Daily:**
- Check backend connection
- Review P&L and win rate
- Check risk alerts
- Monitor trade activity

**Weekly:**
- Comprehensive performance review
- Analyze equity curve
- Review trade patterns
- Check system health

**Monthly:**
- Deep performance analysis
- Parameter review (if needed)
- System optimization (if validated)
- Documentation updates

### When to Intervene vs. Let System Run

**Let System Run:**
- Normal losses (expected)
- Temporary drawdowns (<8%)
- Win rate fluctuations
- Normal trade activity
- System following signals

**Intervene (Trading Toggle):**
- Planned maintenance
- Parameter review
- Market conditions changed
- Need to investigate issues
- Temporary pause needed

**Intervene (Emergency Stop):**
- System errors
- Unexpected behavior
- Critical risk alerts
- Technical issues
- Market anomalies

**Don't Intervene:**
- Normal variation
- Expected losses
- Temporary drawdowns
- Short-term fluctuations
- Before validation complete

---

## Conclusion

This guide covers everything you need to get comfortable with the Auratic Trading Frontend. Remember:

- **Start simple:** Begin with MVP Dashboard, learn gradually
- **Use help system:** F1 or ? for instant help
- **Monitor regularly:** Daily checks prevent issues
- **Understand metrics:** Know what each number means
- **Be patient:** Let system run, gather data before making changes
- **Stay safe:** Use risk dashboard, respect limits, know emergency procedures

**For additional help:**
- Press F1 in any view
- Hover over controls for tooltips
- Check browser console for detailed errors
- Review view-specific documentation

**Happy trading!** 🚀

---

*Last updated: December 31, 2024*

