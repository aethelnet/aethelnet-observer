# Info Hub - Data Visualization & Insights

**Port:** 1430  
**Purpose:** Comprehensive data visualization center with contextual insights about trading system performance, opportunities, and market data.

---

## Overview

The Info Hub displays all trading data in visual formats (graphs, charts, indicators) with contextual explanations. This is NOT a tutorial, but a data-rich information center that helps users understand what's happening in the system.

---

## Features

### 1. Performance Dashboard Section
- **Equity Curve Chart** - Line chart showing account value over time
- **P&L Distribution** - Histogram of trade profits/losses
- **Win Rate Trend** - Visual representation of win rate
- **Contextual Note:** "Watch for consistent upward trend in equity curve. Drawdowns should be shallow and recover quickly."

### 2. Market Overview Section
- **Price Heatmap** - Grid showing all symbols with color-coded price changes
- **Signal Strength Distribution** - Bar chart of signal strengths across symbols
- **Volume Comparison** - Bar chart comparing volumes across symbols
- **Contextual Note:** "Strong signals (>2.0) with high volume are most reliable. Watch for divergences between price and volume."

### 3. Opportunities Analysis Section
- **Confidence Distribution** - Histogram of opportunity confidence levels
- **Risk/Reward Matrix** - Scatter plot: Risk vs Reward ratio
- **Opportunity Timeline** - Gantt-style chart showing when opportunities expire
- **Contextual Note:** "Higher confidence (>80%) with good risk/reward (>2.0) are best. Shorter time horizons are more reliable."

### 4. Timer & Window Visualization
- **Entry Window Timeline** - Visual timeline showing:
  - Current time
  - Entry windows for active opportunities
  - "Valid for" expiration times
  - Time horizons (when moves expected)
- **Countdown Indicators** - Real-time countdowns with color coding
- **Contextual Note:** "Entry Window = when to enter. Valid For = how long to decide. Time Horizon = when move completes. These are different!"

### 5. Position Analysis Section
- **Position P&L Chart** - Bar chart of unrealized P&L per position
- **Hold Time Distribution** - Histogram of how long positions are held
- **Contextual Note:** "Monitor unrealized P&L. Long hold times may indicate stuck positions."

### 6. Trade Execution Analysis
- **Trade Frequency** - Timeline showing trade frequency over time
- **Success Rate by Symbol** - Bar chart showing win rate per symbol
- **Contextual Note:** "Low slippage and fast fills indicate good execution. High trade frequency may indicate overtrading."

### 7. Auto-Discovery Insights
- **Discovery Statistics** - Total discovered, whitelisted, promotion rate
- **Contextual Note:** "Symbols that perform well should be promoted. Monitor discovery-to-whitelist conversion rate."

---

## Data Sources

All data is fetched in real-time from:
- `/api/dashboard/metrics` - Performance metrics
- `/api/dashboard/market-data` - Market prices and signals
- `/api/dashboard/positions` - Open positions
- `/api/dashboard/recent-trades` - Trade history
- `/api/opportunities/symbols` - Trade opportunities
- `/api/auto-discovery/status` - Auto-discovery stats

---

## Controls

- **Symbol Filter** - Filter all visualizations by specific symbol
- **Time Range** - Filter data by time period (1h, 24h, 7d, 30d)
- **Section Toggle** - Collapse/expand sections to focus on specific data
- **Auto-Refresh** - Updates every 5 seconds automatically

---

## Interactive Features

- **Hover Tooltips** - Detailed info on hover over charts and indicators
- **Color Coding:**
  - Green: Positive/good
  - Red: Negative/warning
  - Yellow: Caution
  - Blue: Neutral/info
- **Click to Expand** - Some charts can be expanded for detailed view

---

## Usage

### Launch
```bash
cd infohub
./serve.sh
```

Then open: `http://localhost:1430`

### Navigation
- Accessible from all other views via navigation links
- Direct URL: `http://localhost:1430/infohub/index.html`

---

## Contextual Explanations

Each section includes:
- **"What to Watch"** callout boxes - Key things to monitor
- **"Key Insight"** highlights - Important patterns to recognize
- **"Red Flags"** warnings - Things that indicate problems

These explanations help non-traders understand what the data means and what to pay attention to.

---

## Technical Details

- **Chart Library:** Chart.js for standard charts
- **D3.js:** Available for complex visualizations (if needed)
- **Update Frequency:** Every 5 seconds
- **Request Handling:** Uses AbortController for cancellation
- **Error Handling:** Graceful degradation if APIs unavailable

---

## Design Philosophy

The Info Hub is designed to be:
- **Data-Rich** - Shows comprehensive information
- **Contextual** - Explains what to watch for
- **Visual** - Uses charts and graphs for easy understanding
- **Real-Time** - Always shows current data
- **Accessible** - Clear explanations for non-traders

---

**Status:** ✅ Complete - All visualizations implemented with real-time data



