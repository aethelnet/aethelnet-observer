/**
 * TypeScript declarations for src/shared/websocket.js
 */

export type WebSocketMessage = {
  type: string;
  [key: string]: any;
};

export type WebSocketListener = (data: WebSocketMessage) => void;

/**
 * Setup WebSocket message listener
 * @param eventType - Event type to filter, or callback function
 * @param callback - Callback function (if eventType is string)
 * @returns Unsubscribe function
 */
export function setupWebSocketListener(
  eventType: string | WebSocketListener,
  callback?: WebSocketListener
): () => void;

/**
 * Setup connection state listener
 * @param callback - Callback function called with connection state
 * @returns Unsubscribe function
 */
export function setupConnectionListener(
  callback: (connected: boolean) => void
): () => void;

/**
 * Send message via WebSocket
 * @param data - Message data to send
 */
export function sendWebSocketMessage(data: any): void;

/**
 * Check if WebSocket is connected
 * @returns true if connected, false otherwise
 */
export function isWebSocketConnected(): boolean;

/**
 * Wait for WebSocket connection
 * @param timeout - Maximum time to wait in milliseconds
 * @returns Promise that resolves when connected or rejects on timeout
 */
export function waitForConnection(timeout?: number): Promise<void>;

