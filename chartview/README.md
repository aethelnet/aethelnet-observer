# Trading Chart View - Port 1423

**Professional trading chart visualization**

---

## 🚀 Quick Start

```bash
cd chartview
./serve.sh
# Open http://localhost:1423
```

---

## 🎯 Purpose

This is a **professional trading chart view** (not a creative visualization). It provides:

- **Candlestick Charts** - Standard OHLCV visualization
- **Volume Indicators** - Trading volume overlay
- **Multiple Timeframes** - 1M, 5M, 15M, 1H, 4H, 1D
- **Symbol Selection** - Switch between trading pairs
- **Real-time Updates** - Auto-refreshes every 5 seconds
- **Clean Interface** - Professional, digestible for traders

---

## 📊 Features

### **Chart Types:**
- Candlestick series (green/red)
- Volume histogram (overlay)

### **Controls:**
- Symbol selector (BTCEUR, ETHEUR, etc.)
- Timeframe buttons (1M, 5M, 15M, 1H, 4H, 1D)
- Auto-scroll to latest data

### **Info Panel:**
- Current price
- 24h change (color-coded)
- Volume
- Trading signal

---

## 🔧 Technical Stack

- **Lightweight Charts** - Professional trading chart library
- **Vanilla JavaScript** - No framework overhead
- **REST API** - Fetches from `/api/dashboard/market-data`

---

## 📝 Notes

**Current Implementation:**
- Uses current price data to generate sample candlesticks
- In production, would fetch historical OHLCV data from `/api/history` or similar

**Future Enhancements:**
- Historical data fetching
- Technical indicators (MA, RSI, etc.)
- Drawing tools
- Trade markers
- Smooth animations

---

**Status:** ✅ **READY** - Professional trading chart view!







