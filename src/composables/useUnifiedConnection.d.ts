/**
 * TypeScript declarations for src/composables/useUnifiedConnection.js
 */

import { Ref, ComputedRef } from 'vue';

export interface UnifiedConnection {
  isWebSocketActive: Ref<boolean>;
  isHttpPollingActive: Ref<boolean>;
  connectionMode: ComputedRef<'websocket' | 'http' | 'disconnected'>;
  isConnected: ComputedRef<boolean>;
  start: () => void;
  stop: () => void;
}

/**
 * Unified connection composable
 * Manages WebSocket primary connection with HTTP polling fallback
 * @returns Connection state and methods
 */
export function useUnifiedConnection(): UnifiedConnection;

