# Performance Analytics Hub - Port 1424

**Comprehensive performance analytics and visualization dashboard**

---

## 🚀 Quick Start

```bash
cd analytics
./serve.sh
# Open http://localhost:1424
```

---

## 🎯 Purpose

This dashboard provides **deep performance analytics** for your trading system:

- **Real-time Metrics** - Live P&L, win rate, equity, drawdown
- **Equity Curve** - Visualize account growth over time
- **P&L Timeline** - Track profit/loss trends
- **Win Rate Trend** - Monitor performance consistency
- **Drawdown Visualization** - Identify risk periods
- **Trade Distribution** - Analyze P&L distribution patterns

---

## 📊 Features

### **Metrics Cards:**
- Total P&L (color-coded)
- Win Rate (%)
- Total Trades
- Current Equity
- Max Drawdown
- Daily P&L

### **Charts:**
1. **Equity Curve** - Line chart showing account equity over time
2. **P&L Timeline** - Bar chart of profit/loss at each update
3. **Win Rate Trend** - Line chart showing win rate percentage over time
4. **Drawdown Periods** - Area chart visualizing drawdown from peak equity
5. **Trade Distribution** - Histogram of P&L distribution across trade ranges

---

## 🔧 Technical Stack

- **Chart.js** - Professional charting library
- **Vanilla JavaScript** - No framework overhead
- **REST API** - Fetches from `/api/dashboard/metrics` and `/api/dashboard/recent-trades`

---

## 📝 How It Works

1. **Data Collection:**
   - Polls `/api/dashboard/metrics` every 5 seconds
   - Polls `/api/dashboard/recent-trades` every 10 seconds
   - Builds time-series history in memory (last 100 data points)

2. **Visualization:**
   - Charts update automatically as new data arrives
   - History accumulates over time (resets on page refresh)
   - All charts use Chart.js with dark theme

3. **Performance:**
   - Keeps only last 100 equity/P&L/winrate data points
   - Keeps last 500 trades for distribution analysis
   - Smooth animations with Chart.js update modes

---

## 🎨 Design Philosophy

- **Clean & Professional** - Dark theme, easy to read
- **Real-time Updates** - Live data every 5 seconds
- **Comprehensive** - Multiple views of the same data
- **Stable** - Simple, reliable, no complex features

---

## 🔮 Future Enhancements

- Historical data persistence (localStorage)
- Export charts as images
- Custom time ranges
- Comparison with shadow trading
- Performance alerts

---

**Status:** ✅ **READY** - Performance analytics dashboard!







