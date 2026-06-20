# WebSocket Endpoint Investigation Report

**Date**: 2025-01-XX  
**Issue**: Frontend shows "Inactive" WebSocket status  
**Expected**: `ws://localhost:8000/ws`  
**Status**: 🔴 **ISSUES FOUND**

---

## Executive Summary

The frontend is trying to connect to `ws://localhost:8000/ws`, but the backend exposes `/ws/stream` instead. Additionally, the message format sent by the backend doesn't match what the frontend expects.

---

## Findings

### 1. ✅ WebSocket Endpoint Exists

**Location**: `/var/home/nhrlyn/Projects/Backup/auratic-systems-prime/backend/routers/stream.py`

**Actual Endpoint**: `ws://localhost:8000/ws/stream`  
**Frontend Expects**: `ws://localhost:8000/ws`

**Status**: ❌ **PATH MISMATCH**

### 2. ✅ Endpoint is Properly Registered

**File**: `backend/main.py` (line 68)
```python
app.include_router(stream.router)
```

The `stream.router` includes the `/ws/stream` endpoint, so it IS registered.

**Note**: There's also a `/ws` endpoint in `backend/routers/websocket.py`, but this router is **NOT** included in `main.py`, so it's not active.

**Status**: ✅ **REGISTERED** (but at wrong path)

### 3. ❌ Message Format Mismatch

#### Backend Sends (from `/ws/stream`):
```json
{
  "type": "ticker_update",
  "data": [...]
}

{
  "type": "FULL_STATE",
  "payload": {...}
}

{
  "type": "STRATEGY_UPDATE",
  "payload": {...}
}

{
  "type": "REGIME_UPDATE",
  "payload": {...}
}

{
  "type": "TRADE_UPDATE",
  "payload": [...]
}

{
  "type": "PING",
  "timestamp": 1234567890
}
```

#### Frontend Expects (from `ws-client.js` and components):
```json
{
  "type": "status",
  "panic_active": boolean
}

{
  "type": "failsafe_status",
  "panic_active": boolean
}

{
  "type": "metrics",
  "total_pnl": number,
  "win_rate": number,
  ...
}

{
  "type": "market_data",
  "data": [...]
}

{
  "type": "positions",
  "data": [...]
}

{
  "type": "trades",
  "data": [...]
}
```

**Status**: ❌ **FORMAT MISMATCH**

### 4. Connection Handling

The backend endpoint (`/ws/stream`) does:
- ✅ Accepts connections without authentication (auth is disabled)
- ✅ Sends immediate handshake with `FULL_STATE` message
- ✅ Broadcasts updates via `broadcast_loop()` function
- ✅ Handles client disconnections

**Status**: ✅ **CONNECTION LOGIC WORKS**

### 5. Backend Logs

To check for connection errors, look for:
- `"New WebSocket connection request from {websocket.client}"` - Connection attempts
- `"Client connected. Total: {len(self.active_connections)}"` - Successful connections
- `"Client disconnected. Total: {len(self.active_connections)}"` - Disconnections

**Status**: ⚠️ **CHECK LOGS** (not verified in this investigation)

---

## Root Causes

### Primary Issue: Path Mismatch
- Frontend connects to: `ws://localhost:8000/ws`
- Backend exposes: `ws://localhost:8000/ws/stream`
- **Result**: Connection fails, frontend shows "Inactive"

### Secondary Issue: Message Format
- Backend sends: `"type": "ticker_update"`, `"type": "FULL_STATE"`, etc.
- Frontend expects: `"type": "status"`, `"type": "metrics"`, `"type": "market_data"`, etc.
- **Result**: Even if connected, frontend won't recognize messages

---

## Solutions

### Option 1: Fix Frontend (Recommended for Quick Fix)

**Change**: Update `ws-client.js` to use `/ws/stream`

**File**: `/var/home/nhrlyn/Projects/Frontend/ws-client.js`

**Current** (line 17-26):
```javascript
const DEFAULT_URL = (window.WS_URL) ? window.WS_URL : (function () {
  try {
    const proto = (typeof location !== 'undefined' && location.protocol === 'https:') ? 'wss:' : 'ws:';
    const host = (typeof location !== 'undefined' && location.hostname) ? location.hostname : 'localhost';
    const port = (typeof location !== 'undefined' && location.port) ? `:${location.port}` : '';
    return `${proto}//${host}${port}/ws`;
  } catch (e) {
    return 'ws://localhost:8000/ws';
  }
})();
```

**Change to**:
```javascript
const DEFAULT_URL = (window.WS_URL) ? window.WS_URL : 'ws://localhost:8000/ws/stream';
```

**Or** update `index.html` to set:
```javascript
window.WS_URL = 'ws://localhost:8000/ws/stream';
```

### Option 2: Add `/ws` Endpoint to Backend

**File**: `/var/home/nhrlyn/Projects/Backup/auratic-systems-prime/backend/main.py`

**Add**:
```python
from backend.routers import websocket
app.include_router(websocket.router)  # Adds /ws endpoint
```

**Note**: This endpoint exists but may not send the expected message format either.

### Option 3: Create Adapter Layer (Best Long-term)

Create a new `/ws` endpoint that:
1. Connects to the existing `/ws/stream` internally
2. Transforms messages to match frontend expectations
3. Forwards transformed messages to frontend clients

**Example**:
```python
@router.websocket("/ws")
async def frontend_websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # Transform backend messages to frontend format
    async def transform_and_send(backend_msg):
        if backend_msg.get("type") == "FULL_STATE":
            # Extract status
            payload = backend_msg.get("payload", {})
            status_msg = {
                "type": "status",
                "panic_active": False,  # Extract from payload
                "websocket_connected": True
            }
            await websocket.send_text(json.dumps(status_msg))
            
            # Extract metrics
            if "wallet" in payload:
                metrics_msg = {
                    "type": "metrics",
                    "total_pnl": payload.get("wallet", {}).get("total_pnl", 0),
                    # ... map other fields
                }
                await websocket.send_text(json.dumps(metrics_msg))
        
        elif backend_msg.get("type") == "TRADE_UPDATE":
            await websocket.send_text(json.dumps({
                "type": "trades",
                "data": backend_msg.get("payload", [])
            }))
        
        # ... handle other message types
    
    # Subscribe to backend stream and transform
    # (Implementation depends on backend architecture)
```

---

## Message Format Mapping

To make the frontend work with the current backend, we need to map:

| Backend Type | Frontend Type | Transformation |
|-------------|---------------|----------------|
| `FULL_STATE` | `status` | Extract `panic_active`, `websocket_connected` |
| `FULL_STATE` | `metrics` | Extract wallet/trading metrics |
| `ticker_update` | `market_data` | Transform ticker data format |
| `TRADE_UPDATE` | `trades` | Use `payload` as `data` |
| `STRATEGY_UPDATE` | (none) | Ignore or map to custom type |
| `REGIME_UPDATE` | (none) | Ignore or map to custom type |

---

## Testing Checklist

After implementing a fix:

- [ ] Frontend connects to correct endpoint
- [ ] WebSocket status shows "Active" instead of "Inactive"
- [ ] `SystemStatus` component receives `status` messages
- [ ] `SystemStatus` component receives `failsafe_status` messages
- [ ] Metrics components receive `metrics` messages
- [ ] Market data components receive `market_data` messages
- [ ] Positions components receive `positions` messages
- [ ] Trades components receive `trades` messages
- [ ] No console errors in browser
- [ ] Backend logs show successful connections

---

## Recommended Action Plan

### Immediate (Quick Fix)
1. ✅ Update `ws-client.js` to use `/ws/stream` endpoint
2. ✅ Test connection (should show "Active" now)
3. ⚠️ Note: Components still won't work due to message format mismatch

### Short-term (Make Components Work)
1. Create message adapter in frontend to transform backend messages
2. Or update components to handle backend message types
3. Test each component individually

### Long-term (Proper Solution)
1. Create dedicated `/ws` endpoint in backend
2. Implement message transformation layer
3. Send messages in frontend-expected format
4. Maintain backward compatibility with `/ws/stream`

---

## Files to Modify

### Frontend
- `/var/home/nhrlyn/Projects/Frontend/ws-client.js` - Update default URL
- `/var/home/nhrlyn/Projects/Frontend/components/SystemStatus.js` - Handle backend message types
- `/var/home/nhrlyn/Projects/Frontend/views/dashboard.js` - Map backend messages

### Backend (if creating new endpoint)
- `/var/home/nhrlyn/Projects/Backup/auratic-systems-prime/backend/main.py` - Include websocket router
- `/var/home/nhrlyn/Projects/Backup/auratic-systems-prime/backend/routers/websocket.py` - Update message format
- Or create new adapter endpoint

---

## Verification Commands

### Test WebSocket Connection
```bash
# Using wscat (install: npm install -g wscat)
wscat -c ws://localhost:8000/ws/stream

# Should see messages like:
# {"type":"FULL_STATE","payload":{...}}
# {"type":"ticker_update","data":[...]}
```

### Check Backend Logs
```bash
# Look for connection messages
tail -f /var/home/nhrlyn/Projects/Backup/auratic-systems-prime/backend.log | grep -i websocket
```

### Test Frontend Connection
1. Open browser console
2. Check for WebSocket connection errors
3. Look for `ws:open` or `ws:error` events
4. Verify `window.wsClient` exists and is connected

---

## Status Summary

| Check | Status | Notes |
|-------|--------|-------|
| Endpoint exists | ✅ | At `/ws/stream`, not `/ws` |
| Endpoint registered | ✅ | In `main.py` |
| Message format | ❌ | Backend sends different types |
| Connection logic | ✅ | Works correctly |
| Frontend compatibility | ❌ | Path and format mismatch |

**Overall**: 🔴 **NOT WORKING** - Requires fixes to path and message format

---

## Next Steps

1. **Immediate**: Update frontend to use `/ws/stream` endpoint
2. **Short-term**: Create message adapter or update components
3. **Long-term**: Create proper `/ws` endpoint with correct format

**Priority**: High - Frontend monitoring depends on WebSocket connection





