/**
 * Shared WebSocket Wrapper
 * Provides convenient event handlers for WebSocket messages
 * Works with existing ws-client.js which dispatches DOM events
 */

/**
 * Setup WebSocket message listener
 * @param {string|Function} eventType - Event type to filter, or callback function
 * @param {Function} callback - Callback function (if eventType is string)
 * @returns {Function} Unsubscribe function
 */
export function setupWebSocketListener(eventType, callback) {
    // If first argument is a function, treat it as the callback
    if (typeof eventType === 'function') {
        callback = eventType;
        eventType = null;
    }
    
    const handler = (event) => {
        // Defensive access: some emitters set detail to the message directly,
        // others wrap it as { message: ... }.
        const detail = (event && event.detail) || null;
        const data = (detail && Object.prototype.hasOwnProperty.call(detail, 'message')) ? detail.message : detail;
        if (!data) return;
        
        // If eventType specified, filter by type
        if (eventType && data.type !== eventType) return;
        
        // Call callback with data (guard and protect against exceptions)
        if (typeof callback !== 'function') return;
        try {
            callback(data, event);
        } catch (err) {
            // Don't let listener errors break the app
            if (typeof console !== 'undefined' && console.error) {
                console.error('[WebSocket] listener callback error', err);
            }
        }
    };
    
    // If callback not provided, return a no-op unsubscribe
    if (typeof callback !== 'function') {
        return () => {};
    }
    
    document.addEventListener('ws:message', handler);
    
    // Return unsubscribe function
    return () => {
        document.removeEventListener('ws:message', handler);
    };
}

/**
 * Setup WebSocket connection status listener
 * @param {Function} callback - Callback function (connected: boolean)
 * @returns {Function} Unsubscribe function
 */
export function setupConnectionListener(callback) {
    let isConnected = false;
    
    // If callback not a function, short-circuit and return no-op unsubscribe
    if (typeof callback !== 'function') {
        return () => {};
    }
    
    // Helper to send status only when it changes
    const sendStatus = (status) => {
        if (isConnected === status) return;
        isConnected = status;
        try {
            callback(status);
        } catch (err) {
            if (typeof console !== 'undefined' && console.error) {
                console.error('[WebSocket] connection listener callback error', err);
            }
        }
    };
    
    const openHandler = () => sendStatus(true);
    const closeHandler = () => sendStatus(false);
    const errorHandler = () => sendStatus(false);
    
    document.addEventListener('ws:open', openHandler);
    document.addEventListener('ws:close', closeHandler);
    document.addEventListener('ws:error', errorHandler);
    
    // Check initial state
    if (window.wsClient && window.wsClient.ws && window.wsClient.ws.readyState === WebSocket.OPEN) {
        sendStatus(true);
    }
    
    // Return unsubscribe function
    return () => {
        document.removeEventListener('ws:open', openHandler);
        document.removeEventListener('ws:close', closeHandler);
        document.removeEventListener('ws:error', errorHandler);
    };
}

/**
 * Send message via WebSocket
 * @param {Object|string} data - Data to send
 * @returns {boolean} Success status
 */
export function sendWebSocketMessage(data) {
    if (!window.wsClient) {
        console.warn('[WebSocket] Client not available');
        return false;
    }
    
    // If underlying socket isn't open, don't attempt to send
    if (!window.wsClient.ws || window.wsClient.ws.readyState !== WebSocket.OPEN) {
        console.warn('[WebSocket] Not connected');
        return false;
    }
    
    try {
        return window.wsClient.send(data);
    } catch (err) {
        if (typeof console !== 'undefined' && console.error) {
            console.error('[WebSocket] send error', err);
        }
        return false;
    }
}

/**
 * Check if WebSocket is connected
 * @returns {boolean} Connection status
 */
export function isWebSocketConnected() {
    if (!window.wsClient || !window.wsClient.ws) {
        return false;
    }
    return window.wsClient.ws.readyState === WebSocket.OPEN;
}

/**
 * Wait for WebSocket connection
 * @param {number} timeout - Maximum wait time in milliseconds
 * @returns {Promise<boolean>} Connection status
 */
export function waitForConnection(timeout = 5000) {
    return new Promise((resolve) => {
        if (isWebSocketConnected()) {
            resolve(true);
            return;
        }
        
        const unsubscribe = setupConnectionListener((connected) => {
            if (connected) {
                unsubscribe();
                resolve(true);
            }
        });
        
        setTimeout(() => {
            unsubscribe();
            resolve(false);
        }, timeout);
    });
}



