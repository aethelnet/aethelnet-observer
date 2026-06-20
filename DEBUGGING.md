# HTML Dashboard Debugging Guide

**Date:** December 29, 2024  
**Purpose:** Help debug the HTML dashboard

---

## 🔍 **How to Debug**

### **1. Open Browser Console**
- Press `F12` or `Ctrl+Shift+I`
- Go to "Console" tab
- Look for logs with `[API]` or `[ERROR]` prefixes

### **2. Check for Errors**

**Common Issues:**

**CORS Error:**
```
Access to fetch at 'http://localhost:8000/api/dashboard/metrics' from origin 'http://localhost:1420' has been blocked by CORS policy
```
**Fix:** Backend needs to allow `http://localhost:1420` in CORS settings

**404 Not Found:**
```
Failed to fetch metrics: Error: HTTP 404
```
**Fix:** Check backend is running on port 8000, endpoint is `/api/dashboard/metrics`

**Connection Refused:**
```
Failed to fetch metrics: TypeError: Failed to fetch
```
**Fix:** Backend not running or wrong URL

---

## 📊 **Expected Console Output**

**When Working:**
```
[API] Fetching metrics from http://localhost:8000/api/dashboard/metrics
[API] Metrics received: {total_pnl: -27.38, win_rate: 0.372, total_trades: 43}
[API] Fetching market data from http://localhost:8000/api/dashboard/market-data
[API] Market data received: 7 symbols
```

**When Failing:**
```
[ERROR] Failed to fetch metrics: Error: HTTP 404
[ERROR] Failed to fetch market data: TypeError: Failed to fetch
```

---

## 🎯 **Quick Checks**

1. **Backend Running?**
   ```bash
   curl http://localhost:8000/api/dashboard/metrics
   ```

2. **Correct Endpoint?**
   - Should be: `/api/dashboard/metrics` (not `/api/metrics`)

3. **CORS Configured?**
   - Backend should allow `http://localhost:1420`

4. **Data Format?**
   - `win_rate` should be 0-1 (decimal)
   - `total_pnl` (not `main_pnl`)

---

**Status:** ✅ **READY** - Check browser console for detailed logs.

