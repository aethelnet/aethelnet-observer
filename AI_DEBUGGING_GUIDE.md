---
tags:
  - type/guide
  - type/reference
  - project/auratic-frontend
  - debugging/ai
  - debugging/frontend
  - status/active
aliases:
  - Debugging Guide
  - AI Debug Guide
---

# AI Debugging Guide

**Purpose:** Make it easy for AI tools to understand, debug, and fix issues in the frontend.

**Related:** [[BACKEND_LOGS|Backend Logs]] | [[QUICK_START|Quick Start]] | [[OBSIDIAN_VAULT|Obsidian Vault]]

---

## 🎯 **Design Principles**

### **1. Consistent Logging**
All logs follow this format:
```
[TIMESTAMP] [LEVEL] [CATEGORY] MESSAGE [DATA]
```

**Example:**
```
[2024-12-29T22:15:00.123Z] [INFO] [WebSocket] Connected to ws://localhost:8000/ws
[2024-12-29T22:15:01.456Z] [ERROR] [API] Request failed: 404 Not Found { endpoint: "/api/metrics" }
```

**Categories:**
- `API` - API requests/responses
- `WebSocket` - WebSocket connection/messages
- `Store` - State management
- `Widget:*` - Widget-specific logs

### **2. Structured Errors**
All errors include:
- **Message:** Clear description
- **Code:** Categorizable error code
- **Category:** Error type (API, WebSocket, Validation, Store)
- **Context:** Additional data
- **Suggestions:** How to fix

**Example:**
```json
{
  "name": "ApiError",
  "message": "API request failed: 404 Not Found",
  "code": "API_404",
  "category": "API",
  "context": {
    "endpoint": "/api/metrics",
    "statusCode": 404
  },
  "suggestions": [
    "Check if backend is running on http://localhost:8000",
    "Verify API endpoint is correct"
  ]
}
```

### **3. Searchable Prefixes**
All logs have searchable prefixes:
- `[API]` - Search for all API logs
- `[WebSocket]` - Search for all WebSocket logs
- `[ERROR]` - Search for all errors
- `📋 STRUCTURED_LOG:` - Search for structured JSON logs

---

## 🔍 **How to Debug**

### **1. Check Console Logs**
Open browser console and look for:
- `[ERROR]` - Something broke
- `[WARN]` - Something unexpected
- `[INFO]` - Normal operation
- `[DEBUG]` - Detailed information (dev only)

### **2. Search for Categories**
```javascript
// In console, filter by category
console.log(/* filter by [API] or [WebSocket] */)
```

### **3. Check Structured Logs**
Look for `📋 STRUCTURED_LOG:` entries - these are JSON-formatted for AI tools to parse.

### **4. Export Log History**
```javascript
import { logger } from '@/utils/logger'
const logs = logger.exportLogs()
console.log(logs) // JSON string of all logs
```

---

## 🛠️ **Error Types**

### **ApiError**
- **When:** API request fails
- **Code:** `API_<statusCode>` (e.g., `API_404`, `API_500`)
- **Context:** endpoint, statusCode, responseData
- **Fix:** Check backend, verify endpoint, check network

### **WebSocketError**
- **When:** WebSocket connection fails
- **Code:** `WEBSOCKET_ERROR`
- **Context:** url, readyState
- **Fix:** Check backend WebSocket, verify URL, check network

### **ValidationError**
- **When:** Data doesn't match expected format
- **Code:** `VALIDATION_ERROR`
- **Context:** field, value
- **Fix:** Check data format, verify schema

### **StoreError**
- **When:** State management fails
- **Code:** `STORE_ERROR`
- **Context:** storeName, action
- **Fix:** Check store state, verify action payload

---

## 📋 **Logging Best Practices**

### **Do:**
- ✅ Use appropriate log level (DEBUG, INFO, WARN, ERROR)
- ✅ Include context in logs
- ✅ Use structured logging for complex data
- ✅ Log errors with full context
- ✅ Log important state changes

### **Don't:**
- ❌ Log sensitive data (API keys, passwords)
- ❌ Log too frequently (throttle if needed)
- ❌ Use console.log directly (use logger)
- ❌ Log without context
- ❌ Log in production (use DEBUG level)

---

## 🔧 **Common Issues & Solutions**

### **Issue: API requests failing**
**Look for:**
- `[ERROR] [API]` logs
- Check error code (404, 500, etc.)
- Check suggestions in error object

**Fix:**
- Verify backend is running
- Check API endpoint URL
- Check network connection
- Review backend logs

### **Issue: WebSocket not connecting**
**Look for:**
- `[ERROR] [WebSocket]` logs
- Check connection state
- Check reconnection attempts

**Fix:**
- Verify WebSocket URL
- Check backend WebSocket is running
- Check network connection
- Review reconnection logs

### **Issue: Widget not updating**
**Look for:**
- `[WARN] [Widget:*]` logs
- Check data format
- Check store state

**Fix:**
- Verify data format matches expected
- Check store is updating
- Check WebSocket messages are received
- Review widget logs

---

## 📊 **Log Analysis**

### **For AI Tools:**
1. Search for `[ERROR]` to find all errors
2. Look for `📋 STRUCTURED_LOG:` for JSON logs
3. Check error codes for categorization
4. Review suggestions in error objects
5. Check context for debugging info

### **For Developers:**
1. Use browser console filters
2. Export log history for analysis
3. Check structured logs for details
4. Review error suggestions
5. Check network tab for API calls

---

## 🎯 **Quick Reference**

**Import logger:**
```typescript
import { logger, logApi, logWebSocket, logStore, logWidget } from '@/utils/logger'
```

**Log examples:**
```typescript
logApi.info('Request sent', { endpoint: '/api/metrics' })
logWebSocket.error('Connection failed', error)
logWidget.info('MetricsWidget', 'Data updated', { data })
```

**Error handling:**
```typescript
import { handleError, ApiError } from '@/utils/errors'

try {
  // code
} catch (error) {
  const handled = handleError(error, { context: 'additional info' })
  // handled is now a structured AppError
}
```

---

**Status:** ✅ **AI-DEBUGGING READY** - All logging and error handling is structured for AI tools.

