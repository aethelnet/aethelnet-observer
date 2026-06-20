# How to Use ChartView (Port 1423)

**Date:** December 29, 2024  
**Purpose:** Guide for using the chartview effectively

---

## 🎯 **What ChartView Shows**

### **1. Price Action (Candlesticks)**
- Historical price data from Binance
- Green candles = price went up
- Red candles = price went down
- Shows open, high, low, close for each period

### **2. Volume Bars**
- Trading volume for each period
- Green = price closed higher than it opened
- Red = price closed lower than it opened

### **3. Position Markers (NEW!)**
- **Green dashed line** = Entry price for open positions
- **Yellow dotted line** = Current price (if different from entry)
- Shows where your bot entered trades
- Updates automatically when positions change

### **4. Info Panel**
- **Price:** Current market price (from backend)
- **24h Change:** Percentage change in last 24 hours
- **Volume:** Trading volume
- **Signal:** Trading signal strength from bot

---

## 🎮 **How to Use It**

### **1. Select Symbol**
- Use dropdown at top-left
- Choose from 6 active symbols: BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT, DOGEUSDT
- Chart updates automatically

### **2. Change Timeframe**
- Click timeframe buttons: 1M, 5M, 15M, 1H, 4H, 1D
- Chart reloads with new interval
- 1M = 1 minute candles, 1H = 1 hour candles, etc.

### **3. Monitor Positions**
- **Green line** = Where bot entered (entry price)
- **Yellow line** = Current price (if position is open)
- Lines update automatically every 10 seconds
- If no lines = no open positions for that symbol

### **4. Watch Real-Time Updates**
- Chart updates every 60 seconds (full reload)
- Latest candle updates every 5 seconds (real-time price)
- Info panel updates every 5 seconds

---

## 💡 **Best Practices**

### **For Monitoring**
1. **Set timeframe to 1H or 4H** - Better for seeing overall trends
2. **Watch position markers** - See where bot entered vs current price
3. **Check info panel** - Monitor signal strength and 24h change

### **For Debugging**
1. **Use 1M or 5M** - See detailed price action
2. **Watch for signal changes** - Info panel shows signal strength
3. **Compare entry vs current** - Green vs yellow line distance = unrealized P&L

### **For Analysis**
1. **Switch between symbols** - See which ones have positions
2. **Check volume** - High volume = more activity
3. **Watch trends** - Green candles = uptrend, red = downtrend

---

## 🔍 **What to Look For**

### **Good Signs:**
- ✅ Position markers above current price (for long positions) = profit
- ✅ Green candles after entry = price moving in your favor
- ✅ Strong signal in info panel = bot sees opportunity

### **Warning Signs:**
- ⚠️ Position markers far below current price = loss
- ⚠️ Many red candles = downtrend
- ⚠️ Weak signal = bot not confident

---

## 🚀 **Features Implemented**

### **✅ Position Markers**
- Shows entry price (green dashed line)
- Shows current price (yellow dotted line)
- Updates automatically
- Only shows for current symbol

### **✅ Real-Time Price Updates**
- Latest candle updates every 5 seconds
- Info panel updates every 5 seconds
- Full chart reload every 60 seconds

### **✅ Error Handling**
- Shows errors in console
- Retries if chart not initialized
- Graceful fallbacks

---

## 📊 **Data Sources**

### **Candlestick Data**
- **Source:** Binance Public API
- **Update:** Every 60 seconds (full reload)
- **History:** Last 500 candles

### **Real-Time Price**
- **Source:** Backend API (`/api/dashboard/market-data`)
- **Update:** Every 5 seconds
- **Purpose:** Update latest candle + info panel

### **Position Data**
- **Source:** Backend API (`/api/positions`)
- **Update:** Every 10 seconds
- **Purpose:** Show entry/exit markers

---

## 🎯 **Use Cases**

### **1. Quick Check**
- Open chartview
- See if bot has positions (green/yellow lines)
- Check current price vs entry price

### **2. Deep Dive**
- Select symbol with position
- Use 1M or 5M timeframe
- Watch price action around entry point

### **3. Signal Monitoring**
- Watch info panel for signal strength
- See if bot is detecting opportunities
- Monitor 24h change

---

## 🔧 **Technical Details**

### **Port:** 1423
### **Backend:** localhost:8000
### **Chart Library:** TradingView Lightweight Charts v4.1.0
### **Update Intervals:**
- Chart reload: 60 seconds
- Real-time price: 5 seconds
- Position markers: 10 seconds
- Info panel: 5 seconds

---

**Status:** ✅ **READY** - All features implemented and working!

