# Comprehensive Testing Plan: Phases 2, 3, and 4

## Overview

Test all implemented features together:
- Phase 2: Unified Connection Management (WebSocket + HTTP fallback)
- Phase 3: Centralized State Management (Pinia stores)
- Phase 4: Enhanced WebSocket Composable (Message routing)

## Test Scenarios

### Test 1: Store Initialization and State Management

**Objective**: Verify Pinia store is created and accessible

**Steps**:
1. Open browser DevTools → Vue tab
2. Navigate to StatusView
3. Check if `systemStatus` store is visible
4. Inspect store state

**Expected Results**:
- Store is visible in Vue DevTools
- Store has all expected state properties:
  - `connectionState`, `systemInfo`, `tradingMetrics`, `positions`, `marketData`, `recentTrades`
  - Loading states for each data type
  - Error states for each data type
  - Last update timestamps

**Verification**:
- Vue DevTools shows store
- Store state is reactive and updates correctly

---

### Test 2: Unified Connection with Store Integration

**Objective**: Verify unified connection updates store automatically

**Steps**:
1. Navigate to StatusView
2. Open browser console
3. Open Vue DevTools → Inspect store
4. Wait for unified connection to poll APIs

**Expected Results**:
- Console shows: `[UnifiedConnection] Starting HTTP polling fallback` (if WebSocket not connected)
- Store updates automatically:
  - `systemInfo` is populated
  - `tradingMetrics` is populated
  - `positions` is populated
  - `marketData` is populated
  - `recentTrades` is populated
- Loading states change: `true` → `false` after data loads
- Last update timestamps are set

**Verification**:
- Check Vue DevTools store state
- Verify data appears in store
- Check loading states transition correctly
- Verify timestamps are recent

---

### Test 3: WebSocket Primary with Store Updates

**Objective**: Verify WebSocket updates store when connected

**Steps**:
1. Ensure WebSocket is connected
2. Monitor store in Vue DevTools
3. Wait for WebSocket messages

**Expected Results**:
- WebSocket connects successfully
- HTTP polling does NOT start
- Store updates via WebSocket messages
- `connectionState` in store is `'connected'`
- Store data updates in real-time

**Verification**:
- Console shows: `[UnifiedConnection] WebSocket connected - stopping HTTP polling`
- No HTTP polling interval running
- Store updates when WebSocket messages arrive
- Vue DevTools shows store updates

---

### Test 4: HTTP Fallback with Store Updates

**Objective**: Verify HTTP polling updates store when WebSocket fails

**Steps**:
1. Disable WebSocket (stop backend or close connection)
2. Wait 2+ seconds
3. Monitor store in Vue DevTools

**Expected Results**:
- After 2 seconds: `[UnifiedConnection] Starting HTTP polling fallback`
- HTTP polling starts every 5 seconds
- Store updates every 5 seconds:
  - `systemInfo` updates
  - `tradingMetrics` updates
  - Other data updates
- Loading states cycle: `true` → `false` → `true` → `false`
- Last update timestamps update every 5 seconds

**Verification**:
- Console shows polling logs
- Network tab shows API requests every 5 seconds
- Vue DevTools shows store updates
- Timestamps update every 5 seconds

---

### Test 5: Component Using Store (StatusView)

**Objective**: Verify StatusView uses store correctly

**Steps**:
1. Navigate to StatusView
2. Verify UI displays correctly
3. Check computed properties from store

**Expected Results**:
- StatusView displays backend connection status (from `store.systemInfo`)
- StatusView displays panic mode (from `store.systemInfo.panic_active`)
- StatusView displays WebSocket status
- All data is reactive and updates automatically
- No manual polling needed (unified connection handles it)

**Verification**:
- UI shows correct connection status
- UI shows correct panic mode
- Data updates automatically
- No console errors

---

### Test 6: Enhanced WebSocket Composable

**Objective**: Verify message routing works

**Steps**:
1. Use `useWebSocket` composable in a component
2. Register message handlers for specific types
3. Send test messages via WebSocket

**Expected Results**:
- Message handlers can be registered with `onMessage(type, handler)`
- Handlers are called when messages of that type arrive
- Wildcard handler (`'*'`) receives all messages
- Handlers can be unregistered with `offMessage(type, handler)`

**Verification**:
- Handlers are called correctly
- Message routing works as expected
- No errors in console

---

### Test 7: Mode Switching with Store

**Objective**: Verify seamless switching updates store correctly

**Steps**:
1. Start with WebSocket disconnected (HTTP polling active)
2. Connect WebSocket
3. Disconnect WebSocket again
4. Monitor store throughout

**Expected Results**:
- HTTP polling active → Store updates via HTTP
- WebSocket connects → HTTP polling stops, store updates via WebSocket
- `connectionState` in store changes: `'connecting'` → `'connected'` → `'disconnected'`
- Data continues to update seamlessly
- No data loss during transitions

**Verification**:
- Store `connectionState` updates correctly
- Data updates continue without interruption
- No duplicate updates
- Console shows correct transition logs

---

### Test 8: Error Handling in Store

**Objective**: Verify error states are tracked in store

**Steps**:
1. Cause an API error (stop backend or invalid endpoint)
2. Monitor store error states

**Expected Results**:
- `systemInfoError` is set when system info fetch fails
- `tradingMetricsError` is set when metrics fetch fails
- Error log is populated
- `connectionState` may change to `'error'`
- Errors are logged with timestamps

**Verification**:
- Store error states are set correctly
- Error log contains error messages
- UI can display error states
- Errors clear when data loads successfully

---

### Test 9: Loading States in Store

**Objective**: Verify loading states work correctly

**Steps**:
1. Monitor store loading states
2. Trigger API calls
3. Observe loading state transitions

**Expected Results**:
- Loading states set to `true` when API calls start
- Loading states set to `false` when API calls complete
- Loading states can be used in UI to show spinners
- Each data type has its own loading state

**Verification**:
- Loading states transition correctly
- Can be used in components to show loading indicators
- No stuck loading states

---

### Test 10: Integration Test - Full Flow

**Objective**: Verify everything works together

**Steps**:
1. Start application
2. Navigate through different views
3. Monitor store, connection, and UI
4. Test various scenarios (WebSocket on/off, API errors, etc.)

**Expected Results**:
- Unified connection manages WebSocket + HTTP fallback
- Store is populated automatically
- Components read from store
- UI updates reactively
- No regressions in existing functionality
- All features work together seamlessly

**Verification**:
- All test scenarios pass
- No console errors
- No regressions
- Smooth user experience

---

## Browser Console Commands for Testing

```javascript
// Access store in console (if exposed)
// In StatusView component:
// const store = useSystemStatus()

// Check store state
// store.systemInfo
// store.tradingMetrics
// store.connectionState

// Check unified connection
// unifiedConnection.connectionMode.value
// unifiedConnection.isConnected.value

// Check WebSocket
// window.wsClient?.ws?.readyState // 1 = OPEN
```

---

## Vue DevTools Inspection

1. **Open Vue DevTools**:
   - Install Vue DevTools browser extension
   - Open DevTools → Vue tab

2. **Inspect Store**:
   - Navigate to "Pinia" section
   - Find `systemStatus` store
   - Inspect state, getters, actions

3. **Monitor Updates**:
   - Watch state changes in real-time
   - Verify reactive updates
   - Check loading/error states

---

## Expected Console Logs

### Unified Connection:
```
[UnifiedConnection] WebSocket already connected
// OR
[UnifiedConnection] Starting HTTP polling fallback
[UnifiedConnection] WebSocket connected - stopping HTTP polling
[UnifiedConnection] Stopped HTTP polling
```

### Store Updates:
- Store updates happen silently (no logs)
- Check Vue DevTools to see updates
- Loading states change: `true` → `false`

### WebSocket:
```
[WebSocket] Connected. Authenticating...
[WebSocket] Message received: { type: '...', payload: ... }
```

---

## Success Criteria

✅ Store is created and accessible
✅ Unified connection updates store automatically
✅ Components can read from store
✅ WebSocket updates store in real-time
✅ HTTP polling updates store as fallback
✅ Loading states work correctly
✅ Error states work correctly
✅ Mode switching works seamlessly
✅ No regressions in existing functionality
✅ All features work together

---

## Issues to Watch For

1. **Store not updating**:
   - Check if unified connection is calling store methods
   - Verify API responses are correct format
   - Check for errors in console

2. **Loading states stuck**:
   - Check if `finally` block is executing
   - Verify error handling doesn't skip cleanup

3. **Components not reactive**:
   - Verify components use `computed` for store values
   - Check if store is imported correctly

4. **Duplicate updates**:
   - Check if both WebSocket and HTTP are updating store
   - Verify HTTP polling stops when WebSocket connects

5. **Type errors**:
   - TypeScript errors are expected (JS/TS mix)
   - Runtime should work fine

---

## Next Steps After Testing

If all tests pass:
- Document any issues found
- Update migration plan with completion status
- Consider additional stores for other domains

If issues found:
- Document issues
- Fix before proceeding
- Re-test after fixes


