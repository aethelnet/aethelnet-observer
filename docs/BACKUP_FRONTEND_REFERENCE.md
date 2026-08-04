# Backup Frontend Reference

## Overview

A backup of a more mature frontend implementation is located at:
- **Location**: `/var/home/nhrlyn/Projects/Frontend/input/frontendauratic-prime backup`
- **Source**: Originally from `/var/home/nhrlyn/Projects/Backup/auratic-systems-prime`

This backup contains sophisticated API handling patterns, WebSocket management, and state management implementations that can serve as inspiration for the current frontend.

## Key Features in Backup

### 1. Advanced API Client
- Retry logic with exponential backoff
- Request timeout handling
- Smart error handling (distinguishes 4xx vs 5xx)
- Type-safe API calls with TypeScript

### 2. Unified Connection Management
- WebSocket primary connection
- HTTP polling fallback
- Automatic switching between modes
- Centralized state management

### 3. Better Error Handling
- User-friendly error messages
- Special case handling (e.g., "not found in discovered symbols")
- Consistent error response structure

### 4. State Management
- Pinia stores for centralized state
- Loading states per data type
- Error tracking per data type
- Last update timestamps

## Documentation

Full documentation has been created in the backend project:
- **Backend Documentation**: `/var/home/nhrlyn/Projects/Trader/backend/FRONTEND_BACKUP_REFERENCE.md`

This document contains:
- Detailed implementation patterns
- API call strategies
- Type definitions
- Recommendations for current frontend
- File structure reference

## Quick Access

To review the backup implementation:
```bash
cd /var/home/nhrlyn/Projects/Frontend/input/frontendauratic-prime\ backup
```

Key files to review:
- `src/services/apiClient.ts` - API client implementation
- `src/composables/useUnifiedConnection.ts` - Connection management
- `src/composables/useWebSocket.ts` - WebSocket handling
- `src/stores/systemStatus.ts` - State management


