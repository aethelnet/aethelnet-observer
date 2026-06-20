# Browser Testing Checklist

**Date:** January 1, 2025  
**Purpose:** Manual browser testing checklist for frontend-backend integration

## Prerequisites

- ✅ Backend server running on `http://localhost:8000`
- ✅ Frontend views accessible
- ✅ Browser DevTools open (Network tab)

## Phase 2: Frontend-Backend Integration Testing

### 2.1 Chartview Predictions Integration

**Test Steps:**
1. Open `http://localhost:1420/chartview/index.html` (or your chartview port)
2. Select a symbol (e.g., BTCUSDT)
3. Enable predictions layer (click "🔮 PREDICTIONS" button)
4. Open DevTools → Network tab
5. Verify API call to `/api/predictions?symbol=BTCUSDT`

**Expected Results:**
- ✅ API call succeeds (200 status)
- ✅ Predictions display on chart as dashed line
- ✅ Prediction markers show at future time points
- ✅ Status indicator shows "Connected (Real Data)"
- ✅ Chart timeline extends to show future predictions

**Error Handling Tests:**
1. Stop backend server
2. Enable predictions layer
3. Verify fallback to mock data
4. Verify status shows "Connected (Mock Data)"
5. Restart backend server
6. Verify automatic recovery to real data

**Performance Tests:**
1. Rapidly change symbols (BTCUSDT → ETHUSDT → SOLUSDT)
2. Verify requests are deduplicated (check Network tab)
3. Verify old requests are cancelled
4. Enable predictions, wait 20 seconds, enable again
5. Verify cached response is used (no new request)

### 2.2 Opportunities View Integration

**Test Steps:**
1. Open `http://localhost:1427/opportunities/index.html`
2. Open DevTools → Network tab
3. Verify API call to `/api/opportunities`

**Expected Results:**
- ✅ API call succeeds (200 status)
- ✅ Opportunities display in grid
- ✅ Summary cards show correct counts
- ✅ Status indicator shows "Connected (Real Data)"
- ✅ Countdown timers update every second

**Filtering Tests:**
1. Change symbol filter
2. Verify API call includes `?symbol=...` parameter
3. Change min confidence slider
4. Verify API call includes `?min_confidence=...` parameter
5. Change sort option
6. Verify client-side sorting works

**Debouncing Test:**
1. Rapidly change filters (symbol, confidence)
2. Verify only one API call after 300ms delay
3. Check Network tab for request timing

**Error Handling Tests:**
1. Stop backend server
2. Refresh opportunities view
3. Verify fallback to mock data
4. Verify status shows "Connected (Mock Data)"
5. Restart backend server
6. Verify automatic recovery (next auto-refresh)

### 2.3 Cross-View Navigation

**Test Steps:**
1. Open opportunities view
2. Click "View Chart" on any opportunity
3. Verify navigation to chartview
4. Verify URL contains `?symbol=...&showPredictions=true`
5. Verify chart opens with correct symbol
6. Verify predictions layer is enabled

**Expected Results:**
- ✅ Navigation works correctly
- ✅ Symbol parameter passed correctly
- ✅ Predictions layer auto-enables
- ✅ Symbol is normalized to uppercase
- ✅ Predictions display for selected symbol

## Phase 3: End-to-End User Flow Testing

### 3.1 Complete User Journey

**Test Flow:**
1. Start from main dashboard (`index.html`)
2. Click "Opportunities" in navigation
3. View opportunities list
4. Apply filter: Symbol = BTCUSDT
5. Apply sort: Confidence (highest first)
6. Click "View Chart" on first opportunity
7. Verify chart opens with BTCUSDT
8. Verify predictions are displayed
9. Change symbol to ETHUSDT
10. Verify predictions update
11. Disable predictions layer
12. Re-enable predictions layer
13. Navigate back to opportunities
14. Verify filters are maintained

**Expected Results:**
- ✅ All navigation works smoothly
- ✅ State is maintained between views
- ✅ Predictions update correctly
- ✅ No console errors

### 3.2 Error Recovery Testing

**Test Flow:**
1. Start with backend online
2. Open opportunities view
3. Verify real data displays
4. Stop backend server
5. Wait for next auto-refresh (15 seconds)
6. Verify graceful fallback to mock data
7. Verify status indicator updates
8. Restart backend server
9. Wait for next auto-refresh
10. Verify automatic recovery to real data

**Expected Results:**
- ✅ Graceful fallback to mock data
- ✅ Status indicator updates correctly
- ✅ No errors in console
- ✅ Automatic recovery when backend returns

### 3.3 Performance Testing

**Test Scenarios:**

1. **Request Deduplication:**
   - Rapidly click "View Chart" multiple times
   - Verify only one API call in Network tab
   - Verify no duplicate requests

2. **Request Cancellation:**
   - Enable predictions for BTCUSDT
   - Immediately change to ETHUSDT
   - Verify BTCUSDT request is cancelled
   - Verify only ETHUSDT request completes

3. **Debouncing:**
   - Rapidly change filters (10 times in 1 second)
   - Verify only one API call after 300ms
   - Check Network tab timing

4. **Caching:**
   - Enable predictions for BTCUSDT
   - Wait 20 seconds
   - Disable and re-enable predictions
   - Verify cached response used (no new request)
   - Wait 35 seconds
   - Re-enable predictions
   - Verify new request made (cache expired)

## Verification Checklist

### Network Tab Verification
- [ ] No duplicate requests
- [ ] Requests cancelled when appropriate
- [ ] Cached responses used when valid
- [ ] Request timing correct (debouncing works)

### Console Verification
- [ ] No JavaScript errors
- [ ] No network errors (when backend online)
- [ ] Appropriate warnings for mock data fallback
- [ ] Log messages helpful for debugging

### Visual Verification
- [ ] Predictions display correctly on chart
- [ ] Opportunities display correctly
- [ ] Status indicators show correct state
- [ ] Countdown timers update smoothly
- [ ] Filters and sorting work visually

### Functional Verification
- [ ] All buttons work
- [ ] Navigation works
- [ ] Filters work
- [ ] Sorting works
- [ ] Error handling works
- [ ] Performance optimizations work

## Known Limitations

**Browser Testing Required:**
- Some tests require manual browser interaction
- Network monitoring requires DevTools
- Visual verification requires human inspection

**Automated Testing:**
- Backend endpoints: ✅ Tested programmatically
- Response format: ✅ Validated
- Code quality: ✅ Verified
- Integration code: ✅ Reviewed

## Status

**Automated Tests:** ✅ All pass  
**Browser Tests:** ⏳ Manual testing required  
**Ready for Release:** ✅ Yes (pending browser verification)



