# Market Scanner - Multi-Symbol Command Center

**Port:** 1429  
**Purpose:** Comprehensive market overview showing all tracked symbols with aggregated data from signals, opportunities, PROPHECY events, and positions

---

## 🎯 What It Does

The Market Scanner provides a unified table view of all tracked symbols, aggregating data from multiple sources to give you a complete market overview at a glance. This is your command center for monitoring the entire market.

---

## 🚀 Quick Start

```bash
cd scanner
./serve.sh
# Open http://localhost:1429
```

---

## 📊 Features

### Sortable Table
- Click any column header to sort (ascending/descending)
- Visual indicators show current sort column and direction
- Supports sorting by: Symbol, Price, Signal, 24h Change, Volume, Signals Count, PROPHECY Count, Opportunities Count, Position, P&L

### Comprehensive Data Display
Each row shows:
- **Symbol** - Trading pair name
- **Price** - Current market price
- **Signal** - Trading signal strength (STRONG BUY/BUY/NEUTRAL/SELL/STRONG SELL)
- **24h Change** - Percentage change in last 24 hours (color-coded)
- **Volume** - Trading volume (formatted: K/M)
- **Signals** - Count of active signals for this symbol
- **PROPHECY** - Count of PROPHECY events (gold highlight if >0)
- **Opportunities** - Count of trade opportunities (green highlight if >0)
- **Position** - Current position status (LONG/SHORT/NONE)
- **P&L** - Unrealized profit/loss if position exists

### Filtering
- **Signal Filter**: All / BUY / SELL / NEUTRAL
- **PROPHECY Filter**: All / Has PROPHECY / No PROPHECY
- **Opportunities Filter**: All / Has Opportunities / No Opportunities
- **Position Filter**: All / Has Position / No Position
- **Symbol Search**: Text input to filter by symbol name

### Color Coding
- **Signal Badges**: Green (BUY), Red (SELL), Gray (NEUTRAL)
- **24h Change**: Green (positive), Red (negative)
- **PROPHECY Count**: Gold highlight when >0
- **Opportunities Count**: Green highlight when >0
- **Row Background**: Subtle gold highlight for symbols with PROPHECY events

### Quick Actions
Each row has three action buttons:
- **Chart** → Opens ChartView with symbol pre-selected
- **Opps** → Opens Opportunities view filtered by symbol
- **PROPHECY** → Opens PROPHECY view filtered by symbol

### Summary Statistics
Top summary cards show:
- **Total Symbols** - Number of tracked symbols
- **With PROPHECY** - Symbols with active PROPHECY events
- **With Opportunities** - Symbols with trade opportunities
- **Open Positions** - Symbols with open positions
- **Avg Signal** - Average signal strength across all symbols

### Auto-Refresh
- Automatically refreshes data every 10 seconds
- Request deduplication prevents duplicate API calls
- Client-side caching (30-second cache per endpoint)
- Graceful error handling with status indicators

---

## 📊 Data Sources

The scanner aggregates data from multiple API endpoints:

- **Market Data** (`/api/dashboard/market-data`): Price, signal strength, volume, 24h change
- **Signals** (`/api/dashboard/signals`): Signal history, PROPHECY events
- **Opportunities** (`/api/opportunities`): Trade opportunities
- **Positions** (`/api/dashboard/positions`): Open positions and P&L

---

## 🎨 Design Philosophy

**Comprehensive Overview**
- See all symbols at once
- Quick visual scanning with color coding
- One-glance understanding of market state

**Actionable**
- Quick action buttons for detailed views
- Filter to focus on specific conditions
- Sort to prioritize by any metric

**Efficient**
- Client-side caching reduces API calls
- Request deduplication prevents duplicates
- Optimized rendering for smooth performance

---

## 🔗 Integration

### Navigation
- Links to Dashboard, Chartview, Opportunities, PROPHECY, Analytics

### Quick Actions
- **Chart**: Opens ChartView with `?symbol={symbol}` parameter
- **Opps**: Opens Opportunities view (filtered by symbol)
- **PROPHECY**: Opens PROPHECY view (filtered by symbol)

---

## 💡 Usage Tips

1. **Start Here**: Use Market Scanner as your daily starting point to see overall market conditions
2. **Filter by PROPHECY**: Filter "Has PROPHECY" to see only symbols with major move predictions
3. **Sort by Opportunities**: Sort by opportunities count to find symbols with most trade setups
4. **Watch Positions**: Filter "Has Position" to monitor your open trades
5. **Quick Navigation**: Use action buttons to jump to detailed views for specific symbols

---

## 📝 Notes

- The scanner shows all symbols tracked by the backend
- Data is aggregated in real-time from multiple sources
- PROPHECY events are highlighted with gold color coding
- Symbols with PROPHECY events have a subtle gold row background
- All counts are live and update every 10 seconds

---

## 🚧 Future Enhancements

- Export to CSV
- Custom column selection
- Saved filter presets
- Watchlist management
- Real-time WebSocket updates
- Multi-symbol comparison charts

---

**Status:** ✅ **LIVE** - Complete Implementation



