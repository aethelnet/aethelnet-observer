# Risk Management Dashboard - Port 1425

**Comprehensive risk monitoring and portfolio analysis**

---

## 🚀 Quick Start

```bash
cd risk
./serve.sh
# Open http://localhost:1425
```

---

## 🎯 Purpose

This dashboard provides **real-time risk monitoring** for your trading portfolio:

- **Portfolio Heat Map** - Visual exposure per symbol
- **Position Sizing** - Distribution of position sizes
- **Risk Metrics** - Total exposure, concentration, VaR estimates
- **Correlation Analysis** - Which positions move together
- **Risk Alerts** - Automatic warnings for threshold breaches

---

## 📊 Features

### **Risk Metrics Cards:**
- **Total Exposure** - Total value of all open positions
- **Max Position Size** - Largest single position value
- **Position Count** - Number of open positions
- **Portfolio Concentration** - Top 3 positions as % of equity
- **Estimated VaR (24h)** - Value at Risk estimate (95% confidence)
- **Unrealized P&L** - Total unrealized profit/loss

### **Visualizations:**
1. **Position Sizing Distribution** - Doughnut chart showing position sizes
2. **Exposure by Side** - Bar chart of LONG vs SHORT exposure
3. **Portfolio Heat Map** - Grid showing exposure per symbol (color-coded)
4. **Correlation Matrix** - Table showing correlation between positions

### **Risk Alerts:**
- 🔴 **High Exposure** - Portfolio exposure exceeds threshold (80% of equity)
- ⚠️ **Large Position** - Single position exceeds threshold (30% of equity)
- ⚠️ **High Concentration** - Top 3 positions exceed threshold (50% of equity)
- ℹ️ **No Positions** - Portfolio is flat

---

## 🔧 Technical Stack

- **Chart.js** - Position sizing and side exposure charts
- **Vanilla JavaScript** - Risk calculations and visualizations
- **REST API** - Fetches from:
  - `/api/dashboard/positions` - Open positions
  - `/api/dashboard/market-data` - Market data for correlations
  - `/api/dashboard/metrics` - Equity and metrics

---

## 📝 Risk Calculations

### **Position Value:**
```
Position Value = Quantity × Current Price
```

### **Total Exposure:**
```
Total Exposure = Sum of all Position Values
```

### **Portfolio Concentration:**
```
Concentration = (Top 3 Position Values / Equity) × 100
```

### **VaR Estimate:**
```
VaR = Total Exposure × 2% × 2.33 (95% confidence)
```
*Assumes 2% daily volatility per position*

### **Correlation:**
Based on 24h price change similarity between symbols.

---

## ⚙️ Risk Thresholds

Configurable in code (defaults):
- **Max Position:** 30% of equity
- **Max Concentration:** 50% of equity (top 3)
- **Max Exposure:** 80% of equity
- **Correlation Warning:** 70% correlation

---

## 🎨 Design Philosophy

- **Red Theme** - Risk-focused color scheme
- **Real-time Updates** - Live data every 5 seconds
- **Visual Alerts** - Clear warnings for risk breaches
- **Comprehensive** - Multiple views of risk exposure

---

## 🔮 Future Enhancements

- Historical risk metrics
- Custom risk thresholds (UI configurable)
- Risk score calculation
- Position-level risk breakdown
- Export risk report

---

**Status:** ✅ **READY** - Risk management dashboard!







