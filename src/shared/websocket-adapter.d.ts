/**
 * TypeScript declarations for src/shared/websocket-adapter.js
 */

export interface BackendMessage {
  type: string;
  payload?: any;
  data?: any;
  [key: string]: any;
}

export interface TransformedMessage {
  type: string;
  [key: string]: any;
}

/**
 * Transform backend message to frontend format
 * @param backendMsg - Message from backend
 * @returns Array of transformed messages (may emit multiple)
 */
export function transformBackendMessage(backendMsg: BackendMessage): TransformedMessage[];

/**
 * Setup transformed WebSocket listener
 * @param eventType - Event type to filter
 * @param callback - Callback function
 * @returns Unsubscribe function
 */
export function setupTransformedWebSocketListener(
  eventType: string,
  callback: (message: TransformedMessage) => void
): () => void;

