# ChartView Design - Minimal TradingView Integration

**Date:** December 29, 2024  
**Purpose:** Document what we're building and why

---

## 🎯 **What We're Building**

### **Minimal TradingView Chart**
- ✅ **Candlesticks** - Price action visualization
- ✅ **Volume bars** - Trading volume overlay
- ✅ **Symbol selector** - Dropdown with 6 active symbols
- ✅ **Timeframe selector** - 1m, 5m, 15m, 1h, 4h, 1d
- ✅ **Info panel** - Current price, 24h change, volume, signal strength

### **What We're NOT Building**
- ❌ TradingView indicators (RSI, MACD, etc.)
- ❌ Drawing tools (lines, shapes, etc.)
- ❌ Complex features
- ❌ Redundancy with TradingView's full platform

---

## 📊 **Data Sources**

### **1. Candlestick Data**
- **Source:** Binance Public API (`/api/v3/klines`)
- **Why:** Backend only provides current price, not OHLCV history
- **Format:** Fetched directly from Binance, converted to TradingView format

### **2. Market Data (Info Panel)**
- **Source:** Backend API (`/api/dashboard/market-data`)
- **Provides:** Current price, signal strength, 24h change, volume
- **Purpose:** Real-time updates for info panel

---

## 🔧 **Active Symbols**

The chartview shows the 6 symbols the backend is actively trading:

```
BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT, DOGEUSDT
```

**Symbol selector:** Dropdown populated with these 6 symbols (hardcoded for now, can be made dynamic later).

---

## 🚀 **How It Works**

1. **Page loads** → TradingView library loads
2. **Chart initializes** → Creates candlestick + volume series
3. **Fetches data** → Gets 500 candles from Binance API
4. **Displays chart** → Shows candlesticks + volume
5. **Auto-refresh** → Updates every 60 seconds

**User interactions:**
- **Change symbol** → Fetches new candlestick data for that symbol
- **Change timeframe** → Fetches data for new interval (1m, 5m, etc.)

---

## 💡 **Why This Approach**

### **Minimal & Focused**
- Only shows what we need: price action + volume
- No feature bloat
- Fast and simple

### **Direct Data Source**
- Fetches from Binance (reliable, public API)
- No backend dependency for historical data
- Real-time updates from backend for current price/signals

### **TradingView Lightweight Charts**
- Professional-grade candlestick rendering
- Lightweight (no full TradingView platform)
- Free and open-source

---

## 🔄 **Future Enhancements (Optional)**

If needed later:
- Overlay signal strength markers on chart
- Show entry/exit points for positions
- Add simple moving average line
- Dynamic symbol list from backend API

**But for now:** Keep it simple - just candlesticks + volume.

---

## 📝 **Files**

- `index.html` - Main chartview page
- `serve.sh` - Development server script
- `README.md` - Quick start guide

---

**Status:** ✅ **READY** - Minimal TradingView integration, focused on essentials.

