# TODO List for Tomorrow

**Date:** January 2025  
**Status:** Ready to start

---

## 🧪 Testing Phase (Do First)

### 1. Test Order Details Modal
- [ ] Click order status button in OpportunitiesView
- [ ] Verify modal opens and shows loading state
- [ ] Verify order details display correctly (status, IDs, allocation)
- [ ] Test error state with retry button
- [ ] Verify modal closes on overlay click and close button
- [ ] Check that status colors match order status

**Files to check:** `src/views/OpportunitiesView.vue`

---

### 2. Test Discovery Tab
- [ ] Test "All" filter shows all symbols
- [ ] Test "Whitelisted" filter shows only whitelisted
- [ ] Test "Discovered" filter shows only discovered (not pending, not whitelisted)
- [ ] Verify Promote button is green and works for discovered symbols
- [ ] Verify Remove button is red and works for discovered symbols
- [ ] Check "Pending Discovery" badge shows for pending symbols
- [ ] Verify no grey placeholder buttons appear

**Files to check:** `src/views/AutoDiscoveryView.vue`

---

### 3. Test Unified Connection
- [ ] Verify WebSocket connects and updates store
- [ ] Test HTTP polling fallback when WebSocket disconnects
- [ ] Verify store updates automatically from both WebSocket and HTTP
- [ ] Check connection state in Vue DevTools
- [ ] Verify no duplicate API calls
- [ ] Test connection state transitions (connecting → connected → disconnected)

**Files to check:** 
- `src/composables/useUnifiedConnection.js`
- `src/stores/systemStatus.js`
- Browser DevTools → Vue tab → Pinia

---

### 4. Test Store Integration
- [ ] Open Vue DevTools → Pinia tab
- [ ] Verify `systemStatus` store exists
- [ ] Check store state updates when data arrives
- [ ] Verify StatusView reads from store correctly
- [ ] Check that components react to store changes
- [ ] Verify no duplicate state management

**Files to check:** 
- `src/views/StatusView.vue`
- `src/stores/systemStatus.js`
- Vue DevTools

---

## 🔄 Migration Phase (After Testing Passes)

### 5. Migrate ExecutionView to Store
**Priority:** High  
**Impact:** Eliminates duplicate API calls

**Changes needed:**
```javascript
// Replace:
const trades = ref<any[]>([])
const data = await fetchRecentTrades(100)

// With:
import { useSystemStatus } from '../stores/systemStatus.js'
const store = useSystemStatus()
const trades = computed(() => store.recentTrades || [])
// Remove fetchRecentTrades() calls - store updates automatically
```

**Files to modify:** `src/views/ExecutionView.vue`

**Testing:**
- [ ] Verify trades display correctly
- [ ] Verify metrics calculate correctly
- [ ] Check no duplicate API calls in Network tab
- [ ] Verify data updates when store updates

---

### 6. Migrate ChartView to Store
**Priority:** High  
**Impact:** Eliminates duplicate API calls

**Changes needed:**
```javascript
// Replace:
const marketData = ref([])
const positions = ref([])
const trades = ref([])
await fetchMarketData()
await fetchPositions()
await fetchRecentTrades()

// With:
const store = useSystemStatus()
const marketData = computed(() => store.marketData || [])
const positions = computed(() => store.positions || [])
const trades = computed(() => store.recentTrades || [])
// Remove all fetch calls - store updates automatically
```

**Files to modify:** `src/views/ChartView.vue`

**Testing:**
- [ ] Verify market data displays correctly
- [ ] Verify positions show in chart
- [ ] Verify trades display correctly
- [ ] Check no duplicate API calls
- [ ] Verify data updates when store updates

---

### 7. Cleanup StatusView
**Priority:** Medium  
**Impact:** Code cleanup, removes redundancy

**Changes needed:**
- Remove `fetchStatus()` calls since `useUnifiedConnection` handles it
- Rely on store updates only
- Keep component-specific fetching (active orders, upcoming trades)

**Files to modify:** `src/views/StatusView.vue`

**Testing:**
- [ ] Verify status still displays correctly
- [ ] Verify no redundant API calls
- [ ] Check store updates work

---

## ✅ Verification Phase

### 8. Verify Backend Whitelist Logic
**Reference:** `BACKEND_WHITELIST_VERIFICATION.md`

- [ ] Test manual order placement (should work without whitelist)
- [ ] Test auto-execute order (should require whitelist)
- [ ] Test promote endpoint (should require discovery first)
- [ ] Verify error messages are clear
- [ ] Check backend logs for correct behavior

**Test commands:**
```bash
# Manual order (should work)
curl -X POST http://127.0.0.1:8000/api/opportunities/place-order \
  -H "Content-Type: application/json" \
  -d '{...}'

# Auto-execute (should require whitelist)
curl -X POST "http://127.0.0.1:8000/api/opportunities/place-order?auto_execute=true" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

---

## 📝 Documentation Phase

### 9. Document Test Results
- [ ] Record what works correctly
- [ ] Document any issues found
- [ ] Note fixes applied
- [ ] Update `COMPREHENSIVE_TESTING_PLAN.md` with results
- [ ] Update `IMPLEMENTATION_SUMMARY.md` if needed

---

## 🎯 Priority Order

1. **Testing First** (Items 1-4) - Verify everything works before migrating
2. **Fix Issues** - Address any problems found during testing
3. **Migration** (Items 5-7) - Migrate components one at a time
4. **Verification** (Item 8) - Verify backend integration
5. **Documentation** (Item 9) - Record results

---

## 📋 Quick Reference

### Files Modified Today
- ✅ `src/views/OpportunitiesView.vue` - Order details modal
- ✅ `src/views/AutoDiscoveryView.vue` - Discovery tab fixes
- ✅ `src/composables/useUnifiedConnection.js` - WebSocket integration
- ✅ `src/stores/systemStatus.js` - Centralized state
- ✅ `src/views/StatusView.vue` - Store integration

### Files to Migrate Tomorrow
- ⏳ `src/views/ExecutionView.vue` - Use store for trades/metrics
- ⏳ `src/views/ChartView.vue` - Use store for market data/positions/trades
- ⏳ `src/views/StatusView.vue` - Remove redundant fetching

### Key Documents
- `COMPREHENSIVE_TESTING_PLAN.md` - Full testing guide
- `BACKEND_WHITELIST_VERIFICATION.md` - Backend verification guide
- `IMPLEMENTATION_SUMMARY.md` - What was implemented
- `REMAINING_TODOS_COMPLETE.md` - What was completed today

---

## 💡 Tips

1. **Test in Browser DevTools:**
   - Open Vue DevTools → Pinia tab to inspect store
   - Check Network tab for duplicate API calls
   - Monitor Console for errors

2. **Migration Strategy:**
   - Migrate one component at a time
   - Test after each migration
   - Keep old code commented out initially (for rollback)

3. **If Issues Found:**
   - Document the issue
   - Check if it's a store problem or component problem
   - Fix incrementally

---

## ✅ Success Criteria

- [ ] All tests pass
- [ ] No duplicate API calls
- [ ] Store updates work correctly
- [ ] Components display data correctly
- [ ] No console errors
- [ ] Backend whitelist logic verified
- [ ] Documentation updated

---

**Good luck tomorrow! 🚀**


