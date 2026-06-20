/**
 * WebSocket Message Adapter
 * Transforms backend message format to frontend-expected format
 * 
 * Backend sends: { type: "FULL_STATE", payload: {...} }
 * Frontend expects: { type: "status", panic_active: boolean }
 */

/**
 * Transform backend message to frontend format
 * @param {Object} backendMsg - Message from backend
 * @returns {Array<Object>} Array of transformed messages (may emit multiple)
 */
export function transformBackendMessage(backendMsg) {
    if (!backendMsg || !backendMsg.type) {
        return [];
    }
    
    const transformed = [];
    
    switch (backendMsg.type) {
        case 'FULL_STATE':
            // Extract status information
            const payload = backendMsg.payload || {};
            
            // Transform to status message
            transformed.push({
                type: 'status',
                panic_active: payload.failsafe?.panic_active || false,
                backend_connected: true,
                websocket_connected: true
            });
            
            // Transform to failsafe_status if failsafe data exists
            if (payload.failsafe) {
                transformed.push({
                    type: 'failsafe_status',
                    panic_active: payload.failsafe.panic_active || false,
                    ...payload.failsafe
                });
            }
            
            // Transform to metrics if wallet/trading data exists
            if (payload.wallet || payload.trading) {
                const wallet = payload.wallet || {};
                const trading = payload.trading || {};
                
                transformed.push({
                    type: 'metrics',
                    total_pnl: wallet.total_pnl || wallet.main_pnl || 0,
                    shadow_pnl: wallet.shadow_pnl || 0,
                    win_rate: trading.win_rate || 0,
                    total_trades: trading.total_trades || 0,
                    open_positions: trading.open_positions || 0,
                    ...wallet,
                    ...trading
                });
            }
            
            // Transform to positions if positions exist
            if (payload.positions && Array.isArray(payload.positions)) {
                transformed.push({
                    type: 'positions',
                    positions: payload.positions
                });
            }
            
            // Transform to market data if ticker data exists
            if (payload.tickers && Array.isArray(payload.tickers)) {
                transformed.push({
                    type: 'market_data',
                    market_data: payload.tickers.map(ticker => ({
                        symbol: ticker.symbol,
                        price: ticker.price,
                        signal_strength: ticker.signal_strength || ticker.signal || 'NEUTRAL',
                        change_24h: ticker.change_24h || ticker.change || 0,
                        volume: ticker.volume || 0
                    }))
                });
            }
            
            break;
            
        case 'ticker_update':
            // Transform ticker updates to market_data
            if (backendMsg.data && Array.isArray(backendMsg.data)) {
                transformed.push({
                    type: 'market_data',
                    market_data: backendMsg.data.map(ticker => ({
                        symbol: ticker.symbol,
                        price: ticker.price,
                        signal_strength: ticker.signal_strength || ticker.signal || 'NEUTRAL',
                        change_24h: ticker.change_24h || ticker.change || 0,
                        volume: ticker.volume || 0
                    }))
                });
            }
            break;
            
        case 'TRADE_UPDATE':
            // Transform trade updates
            const trades = backendMsg.payload || (Array.isArray(backendMsg.data) ? backendMsg.data : []);
            transformed.push({
                type: 'trades',
                trades: trades
            });
            break;
            
        case 'STRATEGY_UPDATE':
            // Could map to metrics or custom type
            if (backendMsg.payload) {
                transformed.push({
                    type: 'metrics',
                    ...backendMsg.payload
                });
            }
            break;
            
        case 'REGIME_UPDATE':
            // Could map to status or custom type
            // For now, ignore or map to status
            break;
            
        case 'PING':
            // Ignore ping messages
            break;
            
        default:
            // Unknown type - pass through as-is
            transformed.push(backendMsg);
    }
    
    return transformed;
}

/**
 * Setup WebSocket listener with automatic message transformation
 * @param {string|Function} eventType - Event type to filter, or callback function
 * @param {Function} callback - Callback function
 * @returns {Function} Unsubscribe function
 */
export function setupTransformedWebSocketListener(eventType, callback) {
    // If first argument is a function, treat it as the callback
    if (typeof eventType === 'function') {
        callback = eventType;
        eventType = null;
    }
    
    const handler = (event) => {
        const detail = (event && event.detail) || null;
        const backendMsg = (detail && Object.prototype.hasOwnProperty.call(detail, 'message')) 
            ? detail.message 
            : detail;
        
        if (!backendMsg) return;
        
        // Transform backend message to frontend format
        const transformedMessages = transformBackendMessage(backendMsg);
        
        // Call callback for each transformed message
        transformedMessages.forEach(msg => {
            // If eventType specified, filter by type
            if (eventType && msg.type !== eventType) return;
            
            // Call callback with transformed message
            if (typeof callback === 'function') {
                try {
                    callback(msg, event);
                } catch (err) {
                    if (typeof console !== 'undefined' && console.error) {
                        console.error('[WebSocket Adapter] callback error', err);
                    }
                }
            }
        });
    };
    
    document.addEventListener('ws:message', handler);
    
    // Return unsubscribe function
    return () => {
        document.removeEventListener('ws:message', handler);
    };
}



