# Phase 3 Implementation Plan: Centralized State Management

## Overview

Implement Pinia stores for centralized state management, adapting the backup frontend pattern to work with the current JavaScript codebase. This will provide a single source of truth for system status, trading metrics, positions, market data, and recent trades.

## Current State Analysis

### Existing State Management
- State scattered across components (StatusView, OpportunitiesView, etc.)
- Each component manages its own state
- No centralized loading/error state management
- Duplicate state management logic across components

### Pinia Setup
- ✅ Pinia is already installed (`pinia@3.0.4`)
- ✅ Pinia is already configured in `src/main.ts`
- ✅ Ready to create stores

## Implementation Plan

### 1. Create System Status Store

**File**: `src/stores/systemStatus.js` (new)

**State to Manage**:
- Connection state (`idle` | `connecting` | `connected` | `error` | `reconnecting`)
- System info (is_running, execution_enabled, testnet_mode, etc.)
- Trading metrics (total_pnl, win_rate, etc.)
- Positions array
- Market data array
- Recent trades array
- Loading states per data type
- Error states per data type
- Last update timestamps per data type

**Actions to Implement**:
- `setStatus(status)` - Update connection state
- `setSystemInfo(info)` - Update system info
- `setTradingMetrics(metrics)` - Update trading metrics
- `setPositions(positions)` - Update positions
- `setMarketData(data)` - Update market data
- `setRecentTrades(trades)` - Update recent trades
- Loading state setters for each data type
- Error state setters for each data type
- `clearErrors()` - Clear all errors

**Computed Properties**:
- `isLive` - Whether system is connected
- `statusColor` - Color class based on connection state

### 2. Integrate Store with Unified Connection

**File**: `src/composables/useUnifiedConnection.js` (modify)

**Changes**:
- Import and use `useSystemStatus` store
- Update store when polling APIs
- Set loading states during API calls
- Set error states on API failures
- Update last update timestamps

### 3. Migrate Components to Use Store

**Files to Update**:
- `src/views/StatusView.vue` - Use store for system status
- Other components as needed (gradual migration)

**Migration Strategy**:
- Add store alongside existing state initially
- Gradually replace local state with store
- Keep backward compatibility during transition

## Implementation Details

### Store Structure

```javascript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useSystemStatus = defineStore('systemStatus', () => {
  // Connection state
  const connectionState = ref('connecting')
  const lastHeartbeat = ref(Date.now())
  const errorLog = ref([])

  // System info
  const systemInfo = ref(null)
  const systemInfoLoading = ref(false)
  const systemInfoError = ref(null)
  const systemInfoLastUpdate = ref(null)

  // Trading metrics
  const tradingMetrics = ref(null)
  const tradingMetricsLoading = ref(false)
  const tradingMetricsError = ref(null)
  const tradingMetricsLastUpdate = ref(null)

  // Positions
  const positions = ref([])
  const positionsLoading = ref(false)
  const positionsError = ref(null)
  const positionsLastUpdate = ref(null)

  // Market data
  const marketData = ref([])
  const marketDataLoading = ref(false)
  const marketDataError = ref(null)
  const marketDataLastUpdate = ref(null)

  // Recent trades
  const recentTrades = ref([])
  const recentTradesLoading = ref(false)
  const recentTradesError = ref(null)
  const recentTradesLastUpdate = ref(null)

  // Computed
  const isLive = computed(() => connectionState.value === 'connected')

  // Actions
  function setStatus(status) { ... }
  function setSystemInfo(info) { ... }
  // ... etc

  return {
    // State
    connectionState,
    systemInfo,
    tradingMetrics,
    positions,
    marketData,
    recentTrades,
    // Loading states
    systemInfoLoading,
    tradingMetricsLoading,
    // ... etc
    // Actions
    setStatus,
    setSystemInfo,
    // ... etc
  }
})
```

### Integration with Unified Connection

```javascript
// In useUnifiedConnection.js
import { useSystemStatus } from '../stores/systemStatus.js'

const pollAllApis = async () => {
  const store = useSystemStatus()
  
  // Set loading states
  store.setSystemInfoLoading(true)
  store.setTradingMetricsLoading(true)
  // ... etc
  
  try {
    const [status, metrics, positions, marketData, trades] = await Promise.all([
      fetchFailsafeStatus().catch(() => null),
      fetchMetrics().catch(() => null),
      fetchPositions().catch(() => null),
      fetchMarketData().catch(() => null),
      fetchRecentTrades().catch(() => null)
    ])
    
    // Update store
    if (status) store.setSystemInfo(status)
    if (metrics) store.setTradingMetrics(metrics)
    if (positions) store.setPositions(positions)
    if (marketData) store.setMarketData(marketData)
    if (trades) store.setRecentTrades(trades)
  } catch (error) {
    // Set error states
    store.setSystemInfoError(error.message)
    // ... etc
  } finally {
    // Clear loading states
    store.setSystemInfoLoading(false)
    store.setTradingMetricsLoading(false)
    // ... etc
  }
}
```

### Component Migration Example

```javascript
// Before (StatusView.vue)
const backendConnected = ref(false)
const panicActive = ref(false)

async function fetchStatus() {
  const status = await fetchFailsafeStatus()
  backendConnected.value = true
  panicActive.value = status.panic_active || false
}

// After (StatusView.vue)
import { useSystemStatus } from '../stores/systemStatus.js'

const store = useSystemStatus()

// Use store state
const backendConnected = computed(() => store.systemInfo?.is_running || false)
const panicActive = computed(() => store.systemInfo?.panic_active || false)

// Store is updated automatically by unified connection
// No need for manual fetchStatus() calls
```

## Files to Create/Modify

### New Files
1. **`src/stores/systemStatus.js`**
   - Main system status store
   - All state, actions, and computed properties

### Modified Files
1. **`src/composables/useUnifiedConnection.js`**
   - Integrate with systemStatus store
   - Update store when polling APIs
   - Set loading/error states

2. **`src/views/StatusView.vue`**
   - Use store instead of local state
   - Remove duplicate state management
   - Use computed properties from store

## Migration Strategy

### Phase 3a: Create Store (No Breaking Changes)
1. Create `systemStatus.js` store
2. Store is available but not used yet
3. No component changes

### Phase 3b: Integrate with Unified Connection
1. Update `useUnifiedConnection` to use store
2. Store is populated automatically
3. Components can optionally use store

### Phase 3c: Migrate Components
1. Update StatusView to use store
2. Remove local state management
3. Test thoroughly

### Phase 3d: Migrate Other Components (Future)
1. Update other components gradually
2. Remove duplicate state management
3. Centralize all state in store

## Benefits

1. **Single Source of Truth**: All system state in one place
2. **Consistency**: Same state across all components
3. **Maintainability**: Easier to debug and update
4. **Performance**: Shared reactive state (no duplication)
5. **Developer Experience**: Easier to inspect state (Vue DevTools)

## Testing Strategy

1. **Store Creation**: Verify store is created correctly
2. **Store Updates**: Verify store updates when APIs are called
3. **Component Integration**: Verify components can read from store
4. **Loading States**: Verify loading states work correctly
5. **Error States**: Verify error states work correctly
6. **No Regressions**: Verify existing functionality still works

## Dependencies

- ✅ Pinia (already installed)
- ✅ Vue 3 (already installed)
- Existing: `src/shared/api.js` (API functions)
- Existing: `src/composables/useUnifiedConnection.js` (unified connection)

## Notes

- Store uses JavaScript (not TypeScript) to match current codebase
- Can be enhanced with TypeScript later if desired
- Gradual migration - components can opt-in
- Backward compatible - existing code continues to work

## Next Steps After Phase 3

- Phase 4: Enhanced WebSocket Composable
- Additional stores for other domains (opportunities, auto-discovery, etc.)
- Type safety (TypeScript) if desired


