# Phase 2 Testing Plan: Unified Connection Management

## Overview

Test the unified connection management implementation to verify:
1. WebSocket primary connection works
2. HTTP polling fallback activates when WebSocket fails
3. Seamless switching between connection modes
4. No regressions in existing functionality

## Test Scenarios

### Test 1: WebSocket Primary Connection

**Objective**: Verify WebSocket connection works and HTTP polling doesn't start

**Steps**:
1. Start the frontend application
2. Ensure backend is running with WebSocket enabled
3. Open browser console
4. Navigate to StatusView

**Expected Results**:
- WebSocket connects successfully
- Console shows: `[UnifiedConnection] WebSocket already connected` or `[UnifiedConnection] WebSocket connected - stopping HTTP polling`
- HTTP polling does NOT start
- `connectionMode` should be `'websocket'`
- StatusView displays correct connection status

**Verification**:
- Check browser console for unified connection logs
- Verify no HTTP polling interval is running
- StatusView shows WebSocket as active

---

### Test 2: HTTP Polling Fallback

**Objective**: Verify HTTP polling starts when WebSocket is unavailable

**Steps**:
1. Stop backend WebSocket server (or disable WebSocket)
2. Refresh frontend application
3. Wait 2+ seconds
4. Open browser console

**Expected Results**:
- After 2 seconds, console shows: `[UnifiedConnection] Starting HTTP polling fallback`
- HTTP polling starts every 5 seconds
- `connectionMode` should be `'http'`
- StatusView still shows data (via HTTP polling)
- Console shows API polling logs every 5 seconds

**Verification**:
- Check browser console for polling logs
- Verify data updates every 5 seconds
- Network tab shows API requests every 5 seconds
- StatusView displays data correctly

---

### Test 3: Mode Switching (WebSocket → HTTP)

**Objective**: Verify seamless transition when WebSocket disconnects

**Steps**:
1. Start with WebSocket connected
2. Disconnect WebSocket (stop backend or close connection)
3. Wait 2+ seconds
4. Observe transition

**Expected Results**:
- Console shows: `[UnifiedConnection] WebSocket disconnected - will start HTTP fallback`
- After 2 seconds: `[UnifiedConnection] Starting HTTP polling fallback`
- HTTP polling begins
- `connectionMode` changes from `'websocket'` to `'http'`
- Data continues to update via HTTP polling

**Verification**:
- Check console logs for transition messages
- Verify HTTP polling starts automatically
- Data updates continue without interruption

---

### Test 4: Mode Switching (HTTP → WebSocket)

**Objective**: Verify seamless transition when WebSocket reconnects

**Steps**:
1. Start with WebSocket disconnected (HTTP polling active)
2. Start backend WebSocket server (or reconnect)
3. Observe transition

**Expected Results**:
- WebSocket connects
- Console shows: `[UnifiedConnection] WebSocket connected - stopping HTTP polling`
- HTTP polling stops
- `connectionMode` changes from `'http'` to `'websocket'`
- Console shows: `[UnifiedConnection] Stopped HTTP polling`

**Verification**:
- Check console logs for transition messages
- Verify HTTP polling stops
- Network tab shows no more polling requests
- WebSocket messages are received

---

### Test 5: Component Integration (StatusView)

**Objective**: Verify StatusView works correctly with unified connection

**Steps**:
1. Navigate to StatusView
2. Verify all data displays correctly
3. Test with WebSocket connected
4. Test with WebSocket disconnected (HTTP fallback)

**Expected Results**:
- StatusView displays backend connection status
- StatusView displays WebSocket connection status
- StatusView displays trading mode (Active/Paused)
- All data updates correctly
- No console errors
- No regressions in existing functionality

**Verification**:
- All UI elements render correctly
- Data updates in real-time (WebSocket) or via polling (HTTP)
- No JavaScript errors in console
- Existing features still work

---

### Test 6: Manual Refresh

**Objective**: Verify manual refresh function works

**Steps**:
1. Use unified connection in a component
2. Call `refresh()` method
3. Verify data updates

**Expected Results**:
- If WebSocket active: Logs "Refresh requested - WebSocket active"
- If HTTP polling active: Logs "Refresh requested - polling APIs" and polls immediately
- Data updates correctly

**Verification**:
- Check console for refresh logs
- Verify data updates after refresh call

---

## Manual Testing Checklist

- [ ] WebSocket connects successfully
- [ ] HTTP polling doesn't start when WebSocket is connected
- [ ] HTTP polling starts after 2 seconds when WebSocket is unavailable
- [ ] HTTP polling stops when WebSocket reconnects
- [ ] Seamless transition between WebSocket and HTTP modes
- [ ] StatusView displays correct connection status
- [ ] All data updates correctly in both modes
- [ ] No console errors
- [ ] No regressions in existing functionality
- [ ] Manual refresh works correctly

---

## Browser Console Commands for Testing

```javascript
// Check unified connection state (if exposed in component)
// In StatusView, unifiedConnection should be available

// Check WebSocket status
window.wsClient?.ws?.readyState // Should be 1 (OPEN) when connected

// Monitor network requests
// Open Network tab and filter for API requests
// Should see requests every 5 seconds when HTTP polling is active
```

---

## Expected Console Logs

### WebSocket Connected:
```
[UnifiedConnection] WebSocket already connected
// OR
[UnifiedConnection] WebSocket connected - stopping HTTP polling
```

### HTTP Polling Active:
```
[UnifiedConnection] Starting HTTP polling fallback
// Then every 5 seconds, API requests are made
```

### Mode Switching:
```
[UnifiedConnection] WebSocket disconnected - will start HTTP fallback
[UnifiedConnection] Starting HTTP polling fallback
// OR
[UnifiedConnection] WebSocket connected - stopping HTTP polling
[UnifiedConnection] Stopped HTTP polling
```

---

## Issues to Watch For

1. **HTTP polling starts even when WebSocket is connected**
   - Check WebSocket connection detection
   - Verify `isWebSocketConnected()` function

2. **HTTP polling doesn't start when WebSocket fails**
   - Check fallback timeout (should be 2 seconds)
   - Verify `startHttpPolling()` is called

3. **HTTP polling doesn't stop when WebSocket reconnects**
   - Check WebSocket connection listener
   - Verify `stopHttpPolling()` is called

4. **Data doesn't update in HTTP mode**
   - Check API endpoints are correct
   - Verify `pollAllApis()` function
   - Check network requests in browser

5. **Component errors or regressions**
   - Check browser console for errors
   - Verify existing functionality still works
   - Check component state updates

---

## Success Criteria

✅ All test scenarios pass
✅ No console errors
✅ No regressions in existing functionality
✅ Seamless connection mode switching
✅ Data updates correctly in both modes
✅ StatusView works correctly with unified connection

---

## Next Steps After Testing

If all tests pass:
- Proceed to Phase 3: State Management implementation
- Document any issues found
- Update migration plan with test results

If issues found:
- Document issues
- Fix before proceeding to Phase 3
- Re-test after fixes


