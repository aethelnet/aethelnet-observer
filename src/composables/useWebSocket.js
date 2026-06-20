/**
 * Enhanced WebSocket Composable
 * Provides type-based message handler registration and sophisticated connection management
 * Works with existing DOM event-based WebSocket system
 */

import { ref, onBeforeUnmount } from 'vue'
import { setupWebSocketListener, setupConnectionListener, sendWebSocketMessage, isWebSocketConnected } from '../shared/websocket.js'

/**
 * WebSocket message interface
 * @typedef {Object} WebSocketMessage
 * @property {string} type - Message type
 * @property {*} payload - Message payload
 * @property {*} data - Alternative data field
 */

/**
 * Message handler function type
 * @typedef {Function} MessageHandler
 * @param {WebSocketMessage} message - WebSocket message
 */

const getWsUrl = () => {
    if (typeof window !== 'undefined') {
        let configuredBackend = localStorage.getItem('SOVEREIGN_BACKEND_URL');
        if (configuredBackend && (configuredBackend.includes('localhost') || configuredBackend.includes('127.0.0.1'))) {
            localStorage.removeItem('SOVEREIGN_BACKEND_URL');
            configuredBackend = null;
        }
        
        if (configuredBackend) {
            // Convert backend URL (e.g. http://host:8000/api) to WS url (e.g. ws://host:8000/ws/stream)
            return configuredBackend.replace(/^http/, 'ws').replace(/\/api\/?$/, '') + '/ws/stream';
        }
        
        const host = window.location.host; // includes port
        const protocol = window.location.protocol;
        const wsProtocol = protocol === 'https:' ? 'wss:' : 'ws:';
        
        if (host) {
            // Route directly to the host/port serving the application (CORS-safe).
            // In dev mode, Vite's dev server on port 1420 will proxy this to the backend.
            return `${wsProtocol}//${host}/ws/stream`;
        }
    }
    return 'ws://127.0.0.1:8001/ws/stream';
};

const WS_URL = getWsUrl();

/**
 * Enhanced WebSocket composable
 * Provides message routing and connection state management
 * @param {string} url - WebSocket URL (optional, defaults to WS_URL)
 * @param {string|null} token - Authentication token (optional)
 * @returns {Object} WebSocket state and methods
 */
export function useWebSocket(url = WS_URL, token = null) {
    const isConnected = ref(false)
    const isAuthenticated = ref(false)
    const connectionStatus = ref('disconnected') // 'disconnected' | 'connecting' | 'connected' | 'authenticated' | 'error'
    const lastMessage = ref(null)
    
    // Message handlers map: type -> array of handlers
    const messageHandlers = new Map()
    
    // Unsubscribe functions
    let connectionUnsub = null
    let messageUnsub = null

    /**
     * Register message handler for specific message type
     * @param {string} type - Message type to listen for
     * @param {MessageHandler} handler - Handler function
     * @returns {Function} Unsubscribe function
     */
    const onMessage = (type, handler) => {
        if (!messageHandlers.has(type)) {
            messageHandlers.set(type, [])
        }
        messageHandlers.get(type).push(handler)
        
        // Return unsubscribe function
        return () => {
            const handlers = messageHandlers.get(type)
            if (handlers) {
                const index = handlers.indexOf(handler)
                if (index > -1) {
                    handlers.splice(index, 1)
                }
            }
        }
    }

    /**
     * Unregister message handler
     * @param {string} type - Message type
     * @param {MessageHandler} handler - Handler function to remove
     */
    const offMessage = (type, handler) => {
        const handlers = messageHandlers.get(type)
        if (handlers) {
            const index = handlers.indexOf(handler)
            if (index > -1) {
                handlers.splice(index, 1)
            }
        }
    }

    /**
     * Handle incoming WebSocket messages
     * Routes messages to registered handlers based on type
     * @param {*} data - Message data from WebSocket
     */
    const handleMessage = (data) => {
        // Handle different message formats
        let message = null
        
        if (typeof data === 'string') {
            try {
                message = JSON.parse(data)
            } catch (e) {
                console.warn('[WebSocket] Failed to parse message as JSON:', data)
                return
            }
        } else if (data && typeof data === 'object') {
            message = data
        } else {
            console.warn('[WebSocket] Unknown message format:', data)
            return
        }
        
        // Update last message
        lastMessage.value = message
        
        // Handle authentication response
        if (message.type === 'FULL_STATE' || message.type === 'AUTH_SUCCESS') {
            isAuthenticated.value = true
            connectionStatus.value = 'authenticated'
        }
        
        // Route to type-specific handlers
        const handlers = messageHandlers.get(message.type)
        if (handlers && handlers.length > 0) {
            handlers.forEach(handler => {
                try {
                    handler(message)
                } catch (error) {
                    console.error(`[WebSocket] Error in message handler for ${message.type}:`, error)
                }
            })
        }
        
        // Also call handlers for '*' (all messages)
        const allHandlers = messageHandlers.get('*')
        if (allHandlers && allHandlers.length > 0) {
            allHandlers.forEach(handler => {
                try {
                    handler(message)
                } catch (error) {
                    console.error('[WebSocket] Error in wildcard message handler:', error)
                }
            })
        }
    }

    /**
     * Handle WebSocket connection changes
     * @param {boolean} connected - Connection status
     */
    const handleConnection = (connected) => {
        isConnected.value = connected
        if (connected) {
            connectionStatus.value = 'connected'
            // Send authentication if token is provided
            if (token) {
                send({ type: 'AUTH', token })
            }
        } else {
            connectionStatus.value = 'disconnected'
            isAuthenticated.value = false
        }
    }

    /**
     * Update authentication token
     * @param {string|null} newToken - New token
     */
    const updateToken = (newToken) => {
        token = newToken
        // If connected, send new auth message
        if (isConnected.value && token) {
            send({ type: 'AUTH', token })
        }
    }

    /**
     * Send message via WebSocket
     * @param {string|Object} typeOrMessage - Message type or full message object
     * @param {*} payload - Message payload (if type is string)
     * @returns {boolean} Success status
     */
    const send = (typeOrMessage, payload) => {
        let message = null
        
        if (typeof typeOrMessage === 'string') {
            message = { type: typeOrMessage, payload }
        } else {
            message = typeOrMessage
        }
        
        return sendWebSocketMessage(message)
    }

    /**
     * Connect to WebSocket
     * Note: Connection is managed by existing ws-client.js
     * This composable just listens to connection events
     */
    const connect = () => {
        // Connection is handled by existing ws-client.js
        // We just need to set up listeners
        if (!connectionUnsub) {
            connectionUnsub = setupConnectionListener(handleConnection)
        }
        
        // Check initial connection state
        const connected = isWebSocketConnected()
        if (connected) {
            handleConnection(true)
        }
    }

    /**
     * Close WebSocket connection
     * Note: Actual closing is handled by ws-client.js
     */
    const close = () => {
        // Cleanup listeners
        if (connectionUnsub) {
            connectionUnsub()
            connectionUnsub = null
        }
        if (messageUnsub) {
            messageUnsub()
            messageUnsub = null
        }
        
        isConnected.value = false
        isAuthenticated.value = false
        connectionStatus.value = 'disconnected'
    }

    // Set up message listener
    messageUnsub = setupWebSocketListener(handleMessage)
    
    // Set up connection listener
    connect()

    // Cleanup on unmount
    onBeforeUnmount(() => {
        close()
        messageHandlers.clear()
    })

    return {
        isConnected,
        isAuthenticated,
        connectionStatus,
        lastMessage,
        connect,
        close,
        send,
        onMessage,
        offMessage,
        updateToken
    }
}


