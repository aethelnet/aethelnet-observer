/*
  ws-client.js - Minimal resilient WebSocket client that dispatches DOM events.

  Behavior:
  - Connects to window.WS_URL or default ws://localhost:8000/ws
  - Reconnects with exponential backoff on close/error
  - Dispatches CustomEvent 'ws:open', 'ws:close', 'ws:error', and 'ws:message' on document
  - Message payloads are JSON-parsed when possible and provided in event.detail.message
*/

(function () {
  // #region agent log
  fetch('http://127.0.0.1:7243/ingest/ea1b814b-bb8a-463b-a11f-4c4b4858de01',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ws-client.js:11',message:'ws-client.js file loaded and executing',data:{alreadyLoaded:!!window.__WS_CLIENT_LOADED__,wsUrl:window.WS_URL},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
  // #endregion
  if (window.__WS_CLIENT_LOADED__) return;
  window.__WS_CLIENT_LOADED__ = true;

  // Compute a sensible default WS URL based on the current page protocol/host.
  // If window.WS_URL is set externally, prefer that.
  const DEFAULT_URL = (window.WS_URL) ? window.WS_URL : (function () {
    try {
      const proto = (typeof location !== 'undefined' && location.protocol === 'https:') ? 'wss:' : 'ws:';
      const host = (typeof location !== 'undefined' && location.hostname) ? location.hostname : 'localhost';
      const port = (typeof location !== 'undefined' && location.port) ? `:${location.port}` : '';
      // Backend exposes /ws/stream endpoint
      return `${proto}//${host}${port}/ws/stream`;
    } catch (e) {
      return 'ws://127.0.0.1:8000/ws/stream';
    }
  })();

  class WSClient {
    constructor(url) {
      this.url = url || DEFAULT_URL;
      this.ws = null;
      this.attempt = 0;
      this.maxDelay = 30000;
      this.forcedClose = false;
      this.errorLogged = false;
      this.maxAttemptsBeforeSilent = 3; // After 3 attempts, stop logging errors
      this.connect();
    }

    connect() {
      try {
        this.ws = new WebSocket(this.url);
      } catch (err) {
        this._emit('ws:error', { error: err });
        this._scheduleReconnect();
        return;
      }

      this.ws.addEventListener('open', () => {
        this.attempt = 0;
        this.errorLogged = false; // Reset on successful connection
        
        // --- IRON GATE AUTHENTICATION ---
        // The backend expects an AUTH payload within 3 seconds, or it drops the connection.
        const token = localStorage.getItem('ADMIN_TOKEN') || 'CHANGE_ME_NOW';
        this.ws.send(JSON.stringify({ type: "AUTH", token: token }));
        
        this._emit('ws:open', { url: this.url });
        if (typeof console !== 'undefined' && console.info && this.attempt > 0) {
          console.info('WebSocket connected to', this.url);
        }
      });

      this.ws.addEventListener('message', (ev) => {
        let payload = ev.data;
        try {
          payload = JSON.parse(ev.data);
        } catch (e) {
          // leave as raw text
        }
        this._emit('ws:message', { raw: ev.data, message: payload });
      });

      this.ws.addEventListener('close', (ev) => {
        this._emit('ws:close', { code: ev.code, reason: ev.reason, wasClean: ev.wasClean });
        if (!this.forcedClose) this._scheduleReconnect();
      });

      this.ws.addEventListener('error', (err) => {
        // Only log first few errors to reduce console noise
        if (!this.errorLogged && this.attempt < this.maxAttemptsBeforeSilent) {
          if (typeof console !== 'undefined' && console.warn) {
            console.warn('WebSocket connection failed (backend WebSocket endpoint may not be available). The app will continue using API polling.');
            this.errorLogged = true;
          }
        }
        this._emit('ws:error', { error: err });
        // underlying close will follow; schedule handled in close
      });
    }

    _scheduleReconnect() {
      this.attempt++;
      
      // Stop trying after many failed attempts (silent mode)
      if (this.attempt > 20) {
        // WebSocket endpoint likely not available, stop trying
        if (typeof console !== 'undefined' && console.debug && this.attempt === 21) {
          console.debug('WebSocket endpoint not available. App continues with API polling.');
        }
        return; // Stop reconnecting
      }
      
      const delay = Math.min(1000 * Math.pow(1.8, this.attempt), this.maxDelay);
      setTimeout(() => {
        if (!this.forcedClose) {
          this.connect();
        }
      }, delay);
    }

    send(obj) {
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return false;
      try {
        const data = (typeof obj === 'string') ? obj : JSON.stringify(obj);
        this.ws.send(data);
        return true;
      } catch (e) {
        this._emit('ws:error', { error: e });
        return false;
      }
    }

    close() {
      this.forcedClose = true;
      if (this.ws) this.ws.close(1000, 'client-close');
    }

    _emit(name, detail) {
      try {
        document.dispatchEvent(new CustomEvent(name, { detail }));
      } catch (e) {
        // ignore
      }
    }
  }

  // Auto-instantiate and expose as window.wsClient
  // To prevent the client from auto-starting set window.AUTO_START_WS = false before this script runs.
  try {
    // #region agent log
    fetch('http://127.0.0.1:7243/ingest/ea1b814b-bb8a-463b-a11f-4c4b4858de01',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ws-client.js:138',message:'About to instantiate WSClient',data:{autoStart:window.AUTO_START_WS,wsUrl:window.WS_URL,defaultUrl:DEFAULT_URL},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'E'})}).catch(()=>{});
    // #endregion
    if (window.AUTO_START_WS === false) {
      // Expose constructor for manual instantiation without connecting immediately.
      window.wsClient = null;
      window.WSClient = WSClient;
      // #region agent log
      fetch('http://127.0.0.1:7243/ingest/ea1b814b-bb8a-463b-a11f-4c4b4858de01',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ws-client.js:142',message:'WSClient auto-start disabled',data:{},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'E'})}).catch(()=>{});
      // #endregion
      if (typeof console !== 'undefined' && console.info) {
        console.info('ws-client auto-start disabled (window.AUTO_START_WS === false). Use window.WSClient to create an instance.');
      }
    } else {
      window.wsClient = new WSClient(window.WS_URL || DEFAULT_URL);
      // #region agent log
      fetch('http://127.0.0.1:7243/ingest/ea1b814b-bb8a-463b-a11f-4c4b4858de01',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ws-client.js:147',message:'WSClient instantiated successfully',data:{hasClient:!!window.wsClient,wsUrl:window.wsClient?.url},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'E'})}).catch(()=>{});
      // #endregion
    }
  } catch (e) {
    // #region agent log
    fetch('http://127.0.0.1:7243/ingest/ea1b814b-bb8a-463b-a11f-4c4b4858de01',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ws-client.js:150',message:'WSClient instantiation failed',data:{error:e.message,stack:e.stack},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'E'})}).catch(()=>{});
    // #endregion
    // Use warn to reduce noise; also emit a ws:error event for any listeners.
    if (typeof console !== 'undefined' && console.warn) console.warn('ws-client failed to start', e);
    try {
      document.dispatchEvent(new CustomEvent('ws:error', { detail: { error: e } }));
    } catch (err) {
      // no-op
    }
  }
})();
