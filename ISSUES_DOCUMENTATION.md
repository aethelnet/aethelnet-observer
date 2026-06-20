# Issues Documentation

**Date:** January 2025  
**Status:** Comprehensive catalog of all identified issues  
**Last Updated:** January 2025

---

## Summary

| Category | Total | Critical | High | Medium | Low |
|----------|-------|----------|------|--------|-----|
| Broken Functionality | 4 | 1 | 2 | 1 | 0 |
| Performance Bottlenecks | 4 | 0 | 2 | 2 | 0 |
| Missing Error Handling | 5 | 0 | 2 | 3 | 0 |
| Incomplete Features | 5 | 0 | 1 | 3 | 1 |
| Documentation Gaps | 6 | 0 | 1 | 3 | 2 |
| **TOTAL** | **24** | **1** | **8** | **12** | **3** |

---

## 1. Broken Functionality

### 1.1 WebSocket Connection Path Mismatch
- **Severity:** Critical
- **Status:** Not Fixed
- **Location:** 
  - `ws-client.js:17-26` (DEFAULT_URL configuration)
  - `src/composables/useUnifiedConnection.js` (connection logic)
- **Issue:** Frontend connects to `ws://localhost:8000/ws` but backend exposes `/ws/stream`
- **Impact:** 
  - WebSocket status shows "Inactive" 
  - Real-time updates don't work
  - Fallback to HTTP polling works but less efficient
- **Reference:** `WEBSOCKET_INVESTIGATION.md`
- **Recommendation:** 
  - Update `ws-client.js` to use `ws://localhost:8000/ws/stream`
  - Or create adapter endpoint in backend at `/ws` that forwards to `/ws/stream`
- **Code Reference:**
  ```javascript
  // ws-client.js line 17-26
  const DEFAULT_URL = (window.WS_URL) ? window.WS_URL : (function () {
    // ... returns 'ws://localhost:8000/ws'
  })();
  ```

### 1.2 WebSocket Message Format Mismatch
- **Severity:** High
- **Status:** Not Fixed
- **Location:** All WebSocket consumers (StatusView, ChartView, ExecutionView, etc.)
- **Issue:** Backend sends message types `{type: "FULL_STATE", "ticker_update", "TRADE_UPDATE"}` but frontend expects `{type: "status", "metrics", "market_data", "trades"}`
- **Impact:** 
  - Even if connection succeeds, messages aren't recognized
  - Components don't update from WebSocket data
  - All updates fall back to HTTP polling
- **Reference:** `WEBSOCKET_INVESTIGATION.md` (lines 40-110)
- **Recommendation:** 
  - Create message adapter in `useUnifiedConnection.js` to transform backend messages
  - Or update backend to send messages in frontend-expected format
  - Map backend types to frontend types:
    - `FULL_STATE` → `status` + `metrics`
    - `ticker_update` → `market_data`
    - `TRADE_UPDATE` → `trades`
- **Backend Message Format:**
  ```json
  {"type": "FULL_STATE", "payload": {...}}
  {"type": "ticker_update", "data": [...]}
  ```
- **Frontend Expected Format:**
  ```json
  {"type": "status", "panic_active": boolean}
  {"type": "metrics", "total_pnl": number, ...}
  {"type": "market_data", "data": [...]}
  ```

### 1.3 Whitelist Promotion Persistence
- **Severity:** High
- **Status:** Partially Fixed
- **Location:** 
  - `src/views/AutoDiscoveryView.vue` (promote button)
  - Backend: `routers/data.py` (promote endpoint)
- **Issue:** Promoted symbols added to in-memory set but may not persist correctly to config
- **Impact:** 
  - Promoted symbols may not work for automatic trading
  - Manual orders work (no whitelist check)
  - Automatic trading only works for symbols in config
- **Reference:** `DISCOVERY_ENGINE_ANALYSIS.md`
- **Current Status:** 
  - Persists to `promoted_symbols.json` (per `DISCOVERY_ENGINE_ANALYSIS.md` line 114)
  - Needs verification that trading service reads from this file
- **Recommendation:** 
  - Verify end-to-end: Discover → Promote → Auto-trade
  - Test that `get_trading_symbols()` includes promoted symbols
  - Document the unified whitelist system

### 1.4 Uncommitted Implementation
- **Severity:** Medium
- **Status:** Not Fixed
- **Location:** 
  - `chartview/index.html` (608+ lines added, not committed)
  - `opportunities/` directory (untracked)
- **Issue:** Significant implementation exists in working directory but not committed to git
- **Impact:** 
  - Features may be lost if working directory is reset
  - Code review and collaboration difficult
  - Deployment may not include latest features
- **Reference:** `VERIFICATION_REPORT_API_INTEGRATION.md`
- **Details:**
  - Chartview: 2,676 lines (2,068 committed + 608 new)
  - Opportunities: Complete directory with validation, error handling, query parameters
  - Features include: request deduplication, timeout handling, comprehensive validation
- **Recommendation:** 
  - Commit working directory changes
  - Review and test before committing
  - Document what's new vs. what's committed

---

## 2. Performance Bottlenecks

### 2.1 Multiple Independent Polling Intervals
- **Severity:** High
- **Status:** Not Fixed
- **Location:** Multiple view components
- **Issue:** Many components set up independent polling intervals instead of using unified connection store
- **Impact:** 
  - Excessive API calls (potentially 10+ requests per second across all views)
  - Potential rate limiting
  - Increased server load
  - Duplicate data fetching
- **Affected Files:**
  - `src/views/StatusView.vue` - 2 intervals (statusCheckInterval, activeOrdersInterval)
  - `src/views/OpportunitiesView.vue` - 2 intervals (updateInterval, countdownInterval)
  - `src/views/ExecutionView.vue` - refreshInterval (5 seconds)
  - `src/views/ChartView.vue` - refreshInterval (30 seconds)
  - `src/views/AutoDiscoveryView.vue` - updateInterval
- **Reference:** `TODO_FOR_TOMORROW.md` (migration pending)
- **Recommendation:** 
  - Migrate all views to use `useUnifiedConnection()` composable
  - Use `systemStatus` store for shared state
  - Remove individual polling intervals
  - Single source of truth for system data
- **Current Status:** 
  - StatusView migrated (per `TODO_FOR_TOMORROW.md`)
  - Other views still use direct polling

### 2.2 Opportunity Cache Growth (Partially Fixed)
- **Severity:** Medium
- **Status:** Partially Fixed
- **Location:** `src/views/OpportunitiesView.vue:993-1037`
- **Issue:** Cache could grow unbounded if opportunities lack `expires_at` field
- **Impact:** 
  - Memory leaks over time
  - Degraded performance with large cache
- **Reference:** `CODE_REVIEW_FINDINGS.md` Issue 1.2, 4.2
- **Current Status:** 
  - ✅ `MAX_CACHE_SIZE = 1000` constant added (line 349)
  - ✅ `DEFAULT_CACHE_TTL = 1 hour` constant added (line 350)
  - ✅ `clearExpiredOpportunities()` handles missing `expires_at` (lines 1008-1013)
  - ✅ Max cache size enforcement (lines 1025-1035)
  - ⚠️ Needs verification in production
- **Recommendation:** 
  - Monitor cache size in production
  - Verify default TTL is appropriate
  - Consider reducing MAX_CACHE_SIZE if memory is constrained

### 2.3 Stale Cache Entries (Partially Fixed)
- **Severity:** Medium
- **Status:** Partially Fixed
- **Location:** `src/views/OpportunitiesView.vue:1191-1198`
- **Issue:** Old cache entries not removed when not present in new API response
- **Impact:** 
  - Stale opportunities used for order placement
  - Incorrect data shown to users
- **Reference:** `CODE_REVIEW_FINDINGS.md` Issue 1.4, 4.3
- **Current Status:** 
  - ✅ Stale cleanup implemented (lines 1191-1198)
  - ✅ 5-minute threshold prevents removing temporarily missing entries
  - ⚠️ Needs verification that cleanup works correctly
- **Recommendation:** 
  - Test with opportunities that disappear from API
  - Verify cleanup happens on each fetch
  - Consider reducing 5-minute threshold if needed

### 2.4 No Request Deduplication in Some Views
- **Severity:** Medium
- **Status:** Not Fixed
- **Location:** Various view components
- **Issue:** Multiple components may trigger simultaneous API calls for same data
- **Impact:** 
  - Redundant network requests
  - Wasted bandwidth
  - Potential race conditions
- **Current Status:** 
  - ✅ ChartView has request deduplication
  - ✅ OpportunitiesView has request deduplication
  - ❌ StatusView, ExecutionView, AutoDiscoveryView may not have deduplication
- **Recommendation:** 
  - Add request deduplication to all views
  - Use shared request tracking in `api.js`
  - Consider request queue or debouncing

---

## 3. Missing Error Handling

### 3.1 Cache Operation Errors
- **Severity:** High
- **Status:** Not Fixed
- **Location:** `src/views/OpportunitiesView.vue:1118-1120` (getCachedOpportunity removed, but cache miss handling needed)
- **Issue:** `getCachedOpportunity()` function was removed, but no explicit cache miss handling in order placement
- **Impact:** 
  - Order placement may fail silently if cache miss occurs
  - Fallback to full data endpoint should work, but no explicit check
  - No user feedback on cache miss
- **Reference:** `CODE_REVIEW_FINDINGS.md` Issue 3.5
- **Recommendation:** 
  - Add explicit cache miss check before order placement
  - Log cache miss for debugging
  - Verify fallback to full data endpoint works correctly
  - Add user notification if cache miss occurs

### 3.2 Partial Order Fill Handling
- **Severity:** High
- **Status:** Not Fixed
- **Location:** `src/views/OpportunitiesView.vue:700-750` (order placement logic)
- **Issue:** No logic to handle partial order fills or partial fund returns
- **Impact:** 
  - UI may not reflect partial fills correctly
  - Budget allocation may be incorrect
  - User confusion about order status
- **Reference:** `CODE_REVIEW_FINDINGS.md` Issue 2.4
- **Recommendation:** 
  - Add handling for partial order status
  - Update budget allocation for partial fills
  - Display partial fill information in UI
  - Handle partial fund returns correctly

### 3.3 Budget Allocation Refresh
- **Severity:** Medium
- **Status:** Not Fixed
- **Location:** `src/components/OrderPreviewModal.vue:479-494`
- **Issue:** Budget data not refreshed after order placement
- **Impact:** 
  - UI shows stale budget information
  - User may see incorrect available funds
  - May attempt to place orders with insufficient funds
- **Reference:** `CODE_REVIEW_FINDINGS.md` Issue 2.2
- **Recommendation:** 
  - Refresh budget data after successful order placement
  - Update OrderPreviewModal budget display
  - Refresh parent component budget data
  - Add loading state during refresh

### 3.4 WebSocket Reconnection Errors
- **Severity:** Medium
- **Status:** Not Fixed
- **Location:** 
  - `src/composables/useUnifiedConnection.js`
  - `ws-client.js`
- **Issue:** Reconnection attempts may fail silently after max attempts
- **Impact:** 
  - No user notification when WebSocket permanently fails
  - User may not know real-time updates are disabled
  - Fallback to HTTP works but user unaware
- **Current Status:** 
  - ✅ Has fallback to HTTP polling
  - ❌ No user notification of WebSocket failure
- **Recommendation:** 
  - Add toast notification when WebSocket fails permanently
  - Show connection status indicator in UI
  - Allow manual reconnection attempt
  - Log reconnection failures for debugging

### 3.5 View Loading Errors
- **Severity:** Low
- **Status:** Not Fixed
- **Location:** `app.js:130-141`
- **Issue:** Error display in view container but no retry mechanism
- **Impact:** 
  - User must manually navigate away and back
  - No automatic recovery
  - Poor user experience
- **Current Implementation:**
  ```javascript
  // app.js:130-141
  viewContainer.innerHTML = `
    <div style="padding: 40px; text-align: center; color: #f87171;">
      <h2>Error Loading View</h2>
      <p>Failed to load ${route}: ${error.message}</p>
      <button onclick="window.location.hash='#dashboard'">Go to Dashboard</button>
    </div>
  `;
  ```
- **Recommendation:** 
  - Add "Retry" button to error display
  - Implement automatic retry with exponential backoff
  - Show error details in collapsible section
  - Log errors for debugging

---

## 4. Incomplete Features

### 4.1 Sentiment Analysis
- **Severity:** Low
- **Status:** Not Implemented
- **Location:** `SENTIMENT_ANALYSIS_PLACEHOLDER.md`
- **Issue:** Feature planned but not implemented
- **Impact:** 
  - Missing market sentiment integration
  - Cannot filter opportunities by sentiment
  - No sentiment-based risk assessment
- **Reference:** `SENTIMENT_ANALYSIS_PLACEHOLDER.md`
- **Planned Features:**
  - Market sentiment analysis (bullish/bearish/neutral)
  - Symbol-specific sentiment scores
  - Integration with trading system
- **Recommendation:** 
  - Implement when backend sentiment service is available
  - Low priority (nice to have, not critical)
  - Document API endpoints when implemented

### 4.2 Creative2 Labels Toggle
- **Severity:** Low
- **Status:** Deferred
- **Location:** `creative2/index.html`
- **Issue:** Button exists but no handler, no 3D text labels rendered
- **Impact:** 
  - Feature removed/deferred
  - Button removed from UI
- **Reference:** `FUTURE_FEATURES.md`
- **Planned Implementation:**
  - Add Three.js text sprites or canvas-based labels
  - Implement toggle functionality
  - Display market symbols on 3D nodes
- **Recommendation:** 
  - Implement when needed (low priority)
  - Estimated effort: 2-4 hours
  - Node list sidebar already provides symbol identification

### 4.3 ID-Based Order Placement Endpoint
- **Severity:** Medium
- **Status:** Not Implemented
- **Location:** `src/shared/api.js:427-535`
- **Issue:** Frontend uses full data endpoint, ID-based endpoint exists but not used
- **Impact:** 
  - Larger payloads (sending full opportunity object)
  - Slower requests
  - More bandwidth usage
- **Reference:** `MEDIUM_PRIORITY_TASKS_STATUS.md`
- **Current Implementation:**
  ```javascript
  // Always uses full data endpoint
  const endpoint = '/opportunities/place-order';
  const requestBody = JSON.stringify(opportunity); // Full object
  ```
- **Recommendation:** 
  - Try ID-based endpoint first: `/opportunities/{id}/place-order`
  - Fallback to full data endpoint if ID missing or endpoint fails
  - Send only allocation data with ID-based endpoint
  - Reduce payload size significantly

### 4.4 Opportunity Caching for Order Placement
- **Severity:** Medium
- **Status:** Partially Implemented
- **Location:** `src/views/OpportunitiesView.vue`
- **Issue:** Opportunities cached but not fully utilized for order placement optimization
- **Impact:** 
  - Redundant API calls when placing orders
  - May fetch full opportunity data even when cached
- **Reference:** `MEDIUM_PRIORITY_TASKS_STATUS.md`
- **Current Status:** 
  - ✅ Opportunities are cached (opportunityCache)
  - ✅ Cache is populated on fetch
  - ❌ Cache not used for order placement optimization
- **Recommendation:** 
  - Use cached opportunity when placing orders
  - Only fetch if cache miss or cache expired
  - Combine with ID-based endpoint for optimal performance

### 4.5 Unified Connection Store Migration
- **Severity:** Medium
- **Status:** Partially Complete
- **Location:** Multiple view components
- **Issue:** Some views still use direct API polling instead of unified connection store
- **Impact:** 
  - Duplicate state management
  - Redundant API calls
  - Inconsistent data across views
- **Reference:** `TODO_FOR_TOMORROW.md`
- **Current Status:** 
  - ✅ StatusView migrated to use store
  - ❌ ExecutionView still uses direct polling
  - ❌ ChartView still uses direct polling
  - ❌ OpportunitiesView still uses direct polling
  - ❌ AutoDiscoveryView still uses direct polling
- **Recommendation:** 
  - Migrate ExecutionView to use store for trades/metrics
  - Migrate ChartView to use store for market data/positions/trades
  - Migrate OpportunitiesView to use store where applicable
  - Remove redundant fetching from StatusView
  - Single source of truth for all system data

---

## 5. Documentation Gaps

### 5.1 WebSocket Integration Guide
- **Severity:** High
- **Status:** Missing
- **Issue:** No comprehensive guide for WebSocket message format and integration
- **Impact:** 
  - Developers may not understand message format mismatch
  - Difficult to debug WebSocket issues
  - New developers may implement incorrectly
- **Current Status:** 
  - `WEBSOCKET_INVESTIGATION.md` exists but not integrated into main docs
  - No developer guide for WebSocket integration
- **Recommendation:** 
  - Create `WEBSOCKET_INTEGRATION_GUIDE.md`
  - Document message format mapping
  - Include examples of message transformation
  - Add to `DEVELOPER_GUIDE.md`
  - Include troubleshooting section

### 5.2 Error Handling Patterns
- **Severity:** Medium
- **Status:** Missing
- **Issue:** No documented error handling patterns or best practices
- **Impact:** 
  - Inconsistent error handling across components
  - Developers may miss error cases
  - Difficult to maintain consistent UX
- **Current Status:** 
  - Error handling exists but not documented
  - Some components handle errors well, others don't
- **Recommendation:** 
  - Create `ERROR_HANDLING_PATTERNS.md`
  - Document standard error response format
  - Include examples of good error handling
  - Document retry patterns
  - Include user notification guidelines

### 5.3 Performance Optimization Guide
- **Severity:** Medium
- **Status:** Missing
- **Issue:** No guide on reducing API calls, using unified connection, caching strategies
- **Impact:** 
  - Developers may create performance issues unknowingly
  - Redundant API calls may be introduced
  - Memory leaks may be created
- **Recommendation:** 
  - Create `PERFORMANCE_OPTIMIZATION_GUIDE.md`
  - Document when to use unified connection vs direct polling
  - Include caching best practices
  - Document request deduplication patterns
  - Include memory management guidelines

### 5.4 Component Lifecycle Documentation
- **Severity:** Medium
- **Status:** Missing
- **Issue:** No documentation on when to use intervals, cleanup patterns, memory management
- **Impact:** 
  - Memory leaks may be introduced
  - Intervals may not be cleaned up
  - Components may retain references after unmount
- **Recommendation:** 
  - Add lifecycle section to `DEVELOPER_GUIDE.md`
  - Document `onUnmounted` cleanup patterns
  - Include interval management guidelines
  - Document cache cleanup requirements
  - Include examples of proper cleanup

### 5.5 API Endpoint Documentation
- **Severity:** Low
- **Status:** Partial
- **Issue:** Some endpoints documented in `API_MAPPING.md` but not all edge cases
- **Impact:** 
  - Developers may not handle all error cases
  - Edge cases may be missed
  - Inconsistent error handling
- **Current Status:** 
  - `API_MAPPING.md` exists
  - Basic endpoint documentation present
  - Edge cases not fully documented
- **Recommendation:** 
  - Expand `API_MAPPING.md` with edge cases
  - Document all error response formats
  - Include timeout and retry information
  - Document rate limiting behavior

### 5.6 Testing Documentation
- **Severity:** Low
- **Status:** Missing
- **Issue:** `BROWSER_TESTING_CHECKLIST.md` exists but no automated testing guide
- **Impact:** 
  - Manual testing only, no regression prevention
  - Difficult to verify fixes
  - No CI/CD integration
- **Current Status:** 
  - `BROWSER_TESTING_CHECKLIST.md` exists
  - `vitest.config.ts` exists but no test files
  - No automated test documentation
- **Recommendation:** 
  - Create `TESTING_GUIDE.md`
  - Document unit testing patterns
  - Include integration testing examples
  - Document E2E testing setup
  - Include CI/CD integration guide

---

## Recommendations Summary

### Critical Priority (Fix Immediately)
1. **Fix WebSocket Connection Path** (1.1) - Real-time updates don't work
2. **Fix WebSocket Message Format** (1.2) - Messages not recognized

### High Priority (Fix Soon)
3. **Verify Whitelist Promotion** (1.3) - Auto-trading may not work
4. **Migrate to Unified Connection** (2.1) - Excessive API calls
5. **Add Cache Miss Handling** (3.1) - Order placement may fail
6. **Add Partial Fill Handling** (3.2) - UI may show incorrect data
7. **Create WebSocket Integration Guide** (5.1) - Developer confusion

### Medium Priority (Fix When Possible)
8. **Commit Working Directory Changes** (1.4) - Risk of losing work
9. **Verify Cache Fixes** (2.2, 2.3) - Ensure fixes work correctly
10. **Add Request Deduplication** (2.4) - Reduce redundant calls
11. **Refresh Budget After Order** (3.3) - Stale data display
12. **Add WebSocket Error Notification** (3.4) - User awareness
13. **Implement ID-Based Endpoint** (4.3) - Performance improvement
14. **Complete Store Migration** (4.5) - Consistency
15. **Create Error Handling Guide** (5.2) - Consistency
16. **Create Performance Guide** (5.3) - Prevent issues
17. **Create Lifecycle Documentation** (5.4) - Prevent leaks

### Low Priority (Nice to Have)
18. **Add View Retry Mechanism** (3.5) - Better UX
19. **Implement Sentiment Analysis** (4.1) - Future feature
20. **Implement Labels Toggle** (4.2) - Future feature
21. **Expand API Documentation** (5.5) - Better docs
22. **Create Testing Guide** (5.6) - Better testing

---

## Related Documentation

- `CODE_REVIEW_FINDINGS.md` - Detailed code review findings
- `WEBSOCKET_INVESTIGATION.md` - WebSocket connection investigation
- `DISCOVERY_ENGINE_ANALYSIS.md` - Whitelist promotion analysis
- `VERIFICATION_REPORT_API_INTEGRATION.md` - Uncommitted code verification
- `MEDIUM_PRIORITY_TASKS_STATUS.md` - Incomplete features status
- `FUTURE_FEATURES.md` - Deferred features
- `SENTIMENT_ANALYSIS_PLACEHOLDER.md` - Missing features
- `TODO_FOR_TOMORROW.md` - Pending migrations
- `CODE_REVIEW_IMPLEMENTATION_SUMMARY.md` - Fixes that were implemented

---

## Notes

- Issues marked as "Partially Fixed" need verification in production
- Some issues may have been fixed but not verified
- Status is based on code review and documentation analysis
- Actual behavior may differ in production environment
- Regular updates to this document recommended as issues are fixed

