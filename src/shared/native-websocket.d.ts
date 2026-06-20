/**
 * TypeScript declarations for src/shared/native-websocket.js
 */

export interface WebSocketEventDetail {
  code?: number;
  reason?: string;
  wasClean?: boolean;
  error?: any;
  message?: any;
}

export class NativeWebSocketClient {
  constructor(url?: string);
  connect(): void;
  send(data: any): boolean;
  close(): void;
}

declare global {
  interface Window {
    wsClient?: NativeWebSocketClient;
    WSClient?: typeof NativeWebSocketClient;
    AUTO_START_WS?: boolean;
  }
}

export default NativeWebSocketClient;

