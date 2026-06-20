# Migration Plan: Adopting Backup Frontend Patterns

## Overview

This document outlines a migration plan to adopt sophisticated patterns from the backup frontend implementation. The backup is located at `/var/home/nhrlyn/Projects/Frontend/input/frontendauratic-prime backup` and contains mature implementations of API handling, WebSocket management, and state management.

## Completed ✅

### 1. API Client Improvements (Completed)
- ✅ Retry logic with exponential backoff (max 3 retries)
- ✅ Request timeout handling (5 seconds)
- ✅ Smart error handling (4xx vs 5xx distinction)
- ✅ Improved `promoteToWhitelist` error handling
- ✅ Consistent error response format

**Files Modified**: `src/shared/api.js`

## In Progress / Next Steps

### 2. Unified Connection Management (Recommended Next)

**Current State**:
- WebSocket exists but is separate from HTTP polling
- No automatic fallback mechanism
- WebSocket connection managed in multiple places (`ws-client.js`, `native-websocket.js`, `websocket.js`)

**Backup Pattern**:
- Unified connection manager that attempts WebSocket first
- Automatic fallback to HTTP polling if WebSocket fails
- Single source of truth for connection state
- Seamless switching between modes

**Implementation Plan**:
1. Create `src/composables/useUnifiedConnection.ts` (Vue 3 composable)
2. Integrate existing WebSocket client with HTTP polling fallback
3. Create connection state management
4. Update components to use unified connection

**Files to Create/Modify**:
- `src/composables/useUnifiedConnection.ts` (new)
- `src/composables/useWebSocket.ts` (may need updates)
- Components using WebSocket (StatusView, etc.)

**Priority**: High - Improves reliability and user experience

---

### 3. Centralized State Management (Medium Priority)

**Current State**:
- State scattered across components
- No centralized store for system status
- Loading states managed per component

**Backup Pattern**:
- Pinia stores for centralized state
- `systemStatus.ts` store with:
  - System info (is_running, execution_enabled, etc.)
  - Trading metrics
  - Positions
  - Market data
  - Recent trades
  - Loading states per data type
  - Error tracking per data type
  - Last update timestamps

**Implementation Plan**:
1. Install Pinia if not already installed
2. Create `src/stores/systemStatus.ts`
3. Migrate state from components to store
4. Update components to use store

**Files to Create/Modify**:
- `src/stores/systemStatus.ts` (new)
- Components using system status (StatusView, etc.)

**Priority**: Medium - Improves maintainability and consistency

---

### 4. Enhanced WebSocket Composable (Medium Priority)

**Current State**:
- WebSocket client exists but lacks sophisticated features
- No message type routing
- Basic reconnection logic

**Backup Pattern**:
- Type-based message handler registration
- Sophisticated reconnection logic with exponential backoff
- Authentication handling
- Connection state tracking (disconnected/connecting/connected/authenticated/error)

**Implementation Plan**:
1. Enhance `src/composables/useWebSocket.ts` (if exists) or create new
2. Add message handler registration system
3. Improve reconnection logic
4. Add authentication support

**Files to Create/Modify**:
- `src/composables/useWebSocket.ts` (create or enhance)

**Priority**: Medium - Improves WebSocket reliability

---

### 5. Type Safety (Low Priority - Future)

**Current State**:
- JavaScript codebase
- No type definitions for API responses

**Backup Pattern**:
- TypeScript interfaces for all API responses
- Type-safe API calls

**Implementation Plan**:
1. Add TypeScript support (if desired)
2. Create type definitions for API responses
3. Gradually migrate to TypeScript

**Files to Create**:
- `src/types/api.d.ts` (type definitions)

**Priority**: Low - Nice to have, not critical

---

## Implementation Priority

### Phase 1: Critical (Completed ✅)
- [x] API client retry logic and timeout
- [x] Error handling improvements
- [x] Promote symbol error handling

### Phase 2: High Priority (Completed ✅)
- [x] Unified connection management (WebSocket + HTTP fallback)
- [x] Connection state management

### Phase 3: Medium Priority (Completed ✅)
- [x] Centralized state management (Pinia stores)
- [x] Enhanced WebSocket composable
- [x] Message routing system

### Phase 4: Low Priority (Future)
- [ ] Type safety (TypeScript)
- [ ] Additional composables from backup

---

## Migration Strategy

### Approach
1. **Incremental**: Adopt patterns one at a time
2. **Backward Compatible**: Maintain existing functionality during migration
3. **Tested**: Test each change before moving to next
4. **Documented**: Document changes as we go

### Testing Strategy
1. Test API improvements (retry, timeout, errors)
2. Test unified connection (WebSocket + HTTP fallback)
3. Test state management (store updates)
4. Integration testing with existing components

---

## Reference Documentation

- **Backup Reference**: `/var/home/nhrlyn/Projects/Trader/backend/FRONTEND_BACKUP_REFERENCE.md`
- **Backup Location**: `/var/home/nhrlyn/Projects/Frontend/input/frontendauratic-prime backup`
- **Current Frontend**: `/var/home/nhrlyn/Projects/Frontend`

---

## Key Files from Backup to Reference

1. **API Client**: `input/frontendauratic-prime backup/src/services/apiClient.ts`
2. **Unified Connection**: `input/frontendauratic-prime backup/src/composables/useUnifiedConnection.ts`
3. **WebSocket**: `input/frontendauratic-prime backup/src/composables/useWebSocket.ts`
4. **System Status Store**: `input/frontendauratic-prime backup/src/stores/systemStatus.ts`
5. **Tauri Integration**: `input/frontendauratic-prime backup/src/composables/useTauri.ts`

---

## Notes

- The backup uses Vue 3 with TypeScript and Pinia
- Current frontend uses Vue 3 with JavaScript
- Patterns can be adapted to JavaScript (as we did with API client)
- Focus on functionality over exact implementation match

---

## Last Updated

- **Date**: 2025-01-XX
- **Status**: Phases 1-4 Complete, Ready for Comprehensive Testing
- **Next**: Test all phases together, then proceed with gradual component migration

