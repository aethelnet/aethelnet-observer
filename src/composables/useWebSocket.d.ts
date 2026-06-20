/**
 * TypeScript declarations for src/composables/useWebSocket.js
 */

import { Ref, ComputedRef } from 'vue';

export interface WebSocketMessage {
  type: string;
  payload?: any;
  data?: any;
  [key: string]: any;
}

export interface UseWebSocketReturn {
  isConnected: ComputedRef<boolean>;
  connectionState: Ref<'idle' | 'connecting' | 'connected' | 'error' | 'reconnecting'>;
  error: Ref<Error | null>;
  connect: () => void;
  disconnect: () => void;
  send: (data: any) => void;
  onMessage: (type: string | '*', handler: (message: WebSocketMessage) => void) => () => void;
  onOpen: (handler: () => void) => () => void;
  onClose: (handler: () => void) => () => void;
  onError: (handler: (error: Error) => void) => () => void;
}

/**
 * Enhanced WebSocket composable with message routing
 * @param url - WebSocket URL
 * @param token - Optional authentication token
 * @returns WebSocket state and methods
 */
export function useWebSocket(url?: string, token?: string | null): UseWebSocketReturn;

