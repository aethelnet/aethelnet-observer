/**
 * Native WebSocket Client
 * Replaces ws-client.js with native WebSocket implementation
 * Maintains same DOM event API for compatibility
 */


const getWsUrl = () => {
  if (typeof window !== 'undefined') {
    const configuredBackend = localStorage.getItem('SOVEREIGN_BACKEND_URL');
    if (configuredBackend) {
      // Convert backend URL (e.g. http://host:8000/api) to WS url (e.g. ws://host:8000/ws/stream)
      return configuredBackend.replace(/^http/, 'ws').replace(/\/api\/?$/, '') + '/ws/stream';
    }
    
    const host = window.location.host; // includes port
    const protocol = window.location.protocol;
    const wsProtocol = protocol === 'https:' ? 'wss:' : 'ws:';
    
    if (host) {
      // Force connection to mainnet server .130 as requested by the user
      return `ws://130.61.202.29:8000/ws/stream`;
    }
  }
  return 'ws://130.61.202.29:8000/ws/stream';
};

const WS_URL = getWsUrl();

class NativeWebSocketClient {
  constructor(url = WS_URL) {
    this.url = url;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 10;
    this.reconnectDelay = 1000;
    this.maxReconnectDelay = 30000;
    this.forcedClose = false;
    this.reconnectTimeout = null;
    
    
    this.connect();
  }

  connect() {
    if (this.forcedClose) return;
    
    try {
      
      this.ws = new WebSocket(this.url);
      
      this.ws.onopen = () => {
        // Send Auth Handshake immediately to prevent backend from closing connection
        this.ws.send(JSON.stringify({ type: "AUTH", token: localStorage.getItem('SOVEREIGN_ADMIN_TOKEN') || import.meta.env.VITE_ADMIN_TOKEN || '397915a57a45b746b856532444fd9b29' }));
        
        this.reconnectAttempts = 0;
        this._emit('ws:open', {});
      };
      
      this.ws.onclose = (event) => {
        
        this._emit('ws:close', { code: event.code, reason: event.reason, wasClean: event.wasClean });
        
        if (!this.forcedClose) {
          this._scheduleReconnect();
        }
      };
      
      this.ws.onerror = (error) => {
        
        this._emit('ws:error', { error });
      };
      
      this.ws.onmessage = (event) => {
        let message;
        try {
          message = JSON.parse(event.data);
        } catch (e) {
          message = event.data;
        }
        
        
        this._emit('ws:message', { message });
      };
      
    } catch (err) {
      
      this._emit('ws:error', { error: err });
      if (!this.forcedClose) {
        this._scheduleReconnect();
      }
    }
  }

  _scheduleReconnect() {
    if (this.forcedClose || this.reconnectAttempts >= this.maxReconnectAttempts) {
      return;
    }
    
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
    }
    
    const delay = Math.min(
      this.reconnectDelay * Math.pow(2, this.reconnectAttempts),
      this.maxReconnectDelay
    );
    
    this.reconnectAttempts++;
    
    
    this.reconnectTimeout = setTimeout(() => {
      this.connect();
    }, delay);
  }

  send(data) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      return false;
    }
    
    try {
      const payload = typeof data === 'string' ? data : JSON.stringify(data);
      this.ws.send(payload);
      return true;
    } catch (err) {
      this._emit('ws:error', { error: err });
      return false;
    }
  }

  close() {
    this.forcedClose = true;
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    if (this.ws) {
      this.ws.close(1000, 'client-close');
    }
  }

  _emit(eventName, detail) {
    try {
      if (typeof document !== 'undefined') {
        document.dispatchEvent(new CustomEvent(eventName, { detail }));
      }
    } catch (e) {
      // Ignore errors
    }
  }
}

// Auto-instantiate if window.AUTO_START_WS is not false
let wsClientInstance = null;

if (typeof window !== 'undefined') {
  
  if (window.AUTO_START_WS !== false) {
    wsClientInstance = new NativeWebSocketClient(WS_URL);
    window.wsClient = wsClientInstance;
    
  } else {
    window.WSClient = NativeWebSocketClient;
  }
}

export default NativeWebSocketClient;
export { NativeWebSocketClient };



