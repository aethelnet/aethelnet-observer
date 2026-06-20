/**
 * Unified Connection Manager
 * Provides WebSocket primary connection with automatic HTTP polling fallback
 * Adapts backup frontend pattern to work with current DOM event-based WebSocket system
 */

import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { setupConnectionListener, isWebSocketConnected } from '../shared/websocket.js'
import { useWebSocket } from './useWebSocket.js'
import { 
    fetchFailsafeStatus,
    fetchDashboardStatus,
    fetchTradingConfig,
    fetchMetrics,
    fetchPositions,
    fetchMarketData,
    fetchRecentTrades
} from '../shared/api.js'
import { useSystemStatus } from '../stores/systemStatus.js'

const API_POLL_INTERVAL = 5000 // 5 seconds
const HTTP_FALLBACK_DELAY = 2000 // Start HTTP polling after 2s if WS fails

/**
 * Unified connection composable
 * Manages WebSocket primary connection with HTTP polling fallback
 * @returns {Object} Connection state and methods
 */
export function useUnifiedConnection() {
    // Get store instance
    const store = useSystemStatus()
    
    // Use enhanced WebSocket composable for message routing
    const ws = useWebSocket()
    
    // Connection state
    const isWebSocketActive = ref(false)
    const isHttpPollingActive = ref(false)
    const connectionMode = computed(() => {
        if (isWebSocketActive.value) return 'websocket'
        if (isHttpPollingActive.value) return 'http'
        return 'disconnected'
    })
    const isConnected = computed(() => isWebSocketActive.value || isHttpPollingActive.value)

    // HTTP polling interval
    let apiPollInterval = null
    let httpFallbackTimeout = null
    let connectionUnsub = null
    let wsMessageUnsub = null

    // ===== HTTP POLLING FUNCTIONS =====
    
    /**
     * Poll all API endpoints and update store
     */
    const pollAllApis = async () => {
        // Set loading states
        store.setSystemInfoLoading(true)
        store.setTradingMetricsLoading(true)
        store.setPositionsLoading(true)
        store.setMarketDataLoading(true)
        store.setRecentTradesLoading(true)
        
        try {
            // Fetch all system status endpoints in parallel
            const [failsafeStatus, dashboardStatus, tradingConfig, metrics, positions, marketData, trades] = await Promise.all([
                fetchFailsafeStatus().catch((err) => {
                    console.debug('[UnifiedConnection] Failsafe status fetch failed (non-critical):', err)
                    return null
                }),
                fetchDashboardStatus().catch((err) => {
                    console.debug('[UnifiedConnection] Dashboard status fetch failed (non-critical):', err)
                    return null
                }),
                fetchTradingConfig().catch((err) => {
                    console.debug('[UnifiedConnection] Trading config fetch failed (non-critical):', err)
                    return null
                }),
                fetchMetrics().catch((err) => {
                    store.setTradingMetricsError(err.message || 'Failed to fetch metrics')
                    return null
                }),
                fetchPositions().catch((err) => {
                    store.setPositionsError(err.message || 'Failed to fetch positions')
                    return null
                }),
                fetchMarketData().catch((err) => {
                    store.setMarketDataError(err.message || 'Failed to fetch market data')
                    return null
                }),
                fetchRecentTrades().catch((err) => {
                    store.setRecentTradesError(err.message || 'Failed to fetch recent trades')
                    return null
                })
            ])
            
            // Merge all system info sources into a single object
            // Priority: dashboardStatus > tradingConfig > failsafeStatus
            // This ensures execution_enabled and engines.shadow are preserved
            const currentSystemInfo = store.systemInfo || {}
            const mergedSystemInfo = {
                ...currentSystemInfo, // Preserve existing data
                ...failsafeStatus, // Base status (panic_active, etc.)
                ...dashboardStatus, // Override with dashboard status (execution_enabled, etc.)
                ...tradingConfig, // Override with trading config (engines.shadow, etc.)
            }
            
            // Normalize merged status data to ensure consistent structure
            const normalizedStatus = {
                ...mergedSystemInfo,
                // Ensure is_running is set if backend_connected exists
                is_running: mergedSystemInfo.is_running !== undefined ? mergedSystemInfo.is_running : 
                           (mergedSystemInfo.backend_connected !== false ? true : false),
                // Ensure backend_connected is set if is_running exists
                backend_connected: mergedSystemInfo.backend_connected !== undefined ? mergedSystemInfo.backend_connected :
                                 (mergedSystemInfo.is_running === true ? true : undefined),
                // Preserve execution_enabled from dashboard status
                execution_enabled: dashboardStatus?.execution_enabled !== undefined 
                    ? dashboardStatus.execution_enabled 
                    : mergedSystemInfo.execution_enabled,
                // Preserve engines from trading config
                engines: tradingConfig?.engines || mergedSystemInfo.engines
            }
            
            // Only update if we got at least one valid response
            if (failsafeStatus || dashboardStatus || tradingConfig) {
                store.setSystemInfo(normalizedStatus)
            } else {
                // If all status fetches failed, set error
                store.setSystemInfoError('Failed to fetch system status from all endpoints')
            }
            if (metrics && !metrics.error) {
                store.setTradingMetrics(metrics)
            }
            if (positions && Array.isArray(positions)) {
                store.setPositions(positions)
            } else if (positions === null || positions === undefined) {
                // Empty array is valid, but null/undefined means no data
                store.setPositions([])
            }
            if (marketData && Array.isArray(marketData)) {
                store.setMarketData(marketData)
            } else if (marketData === null || marketData === undefined) {
                store.setMarketData([])
            }
            if (trades && Array.isArray(trades)) {
                store.setRecentTrades(trades)
            } else if (trades === null || trades === undefined) {
                store.setRecentTrades([])
            }
        } catch (error) {
            // Silently fail - HTTP polling is a fallback, not critical
            console.debug('[UnifiedConnection] API poll error (non-critical):', error)
        } finally {
            // Clear loading states
            store.setSystemInfoLoading(false)
            store.setTradingMetricsLoading(false)
            store.setPositionsLoading(false)
            store.setMarketDataLoading(false)
            store.setRecentTradesLoading(false)
        }
    }

    /**
     * Start HTTP polling fallback
     */
    const startHttpPolling = () => {
        if (apiPollInterval) return // Already polling
        
        isHttpPollingActive.value = true
        console.log('[UnifiedConnection] Starting HTTP polling fallback')
        
        // Initial poll
        pollAllApis()
        
        // Set up interval
        apiPollInterval = setInterval(pollAllApis, API_POLL_INTERVAL)
    }

    /**
     * Stop HTTP polling
     */
    const stopHttpPolling = () => {
        if (apiPollInterval) {
            clearInterval(apiPollInterval)
            apiPollInterval = null
        }
        isHttpPollingActive.value = false
        console.log('[UnifiedConnection] Stopped HTTP polling')
    }

    // ===== WEBSOCKET INTEGRATION =====

    /**
     * Merge system info updates while preserving critical fields
     * Preserves execution_enabled and engines.shadow from existing data
     */
    const mergeSystemInfo = (newInfo) => {
        const currentInfo = store.systemInfo || {}
        return {
            ...currentInfo, // Preserve existing data (including execution_enabled, engines.shadow)
            ...newInfo, // Apply new updates
            // Explicitly preserve execution_enabled if not in new data
            execution_enabled: newInfo.execution_enabled !== undefined 
                ? newInfo.execution_enabled 
                : currentInfo.execution_enabled,
            // Explicitly preserve engines if not in new data
            engines: newInfo.engines || currentInfo.engines
        }
    }

    /**
     * Handle WebSocket messages and update store
     * Routes messages from useWebSocket to store updates
     */
    const setupWebSocketMessageHandlers = () => {
        // Handle FULL_STATE messages (complete system state)
        wsMessageUnsub = ws.onMessage('FULL_STATE', (message) => {
            if (message.payload || message.data) {
                const state = message.payload || message.data
                
                // Map backend keys to frontend expected keys
                // Backend sends: marketStatus, engineStatus, executionMode, activeAvatar, autoPilot
                const sysInfo = state.system_info || {
                    is_running: state.engineStatus === 'RUNNING',
                    execution_enabled: state.executionMode !== 'PAPER',
                    testnet_mode: state.executionMode === 'PAPER',
                    status: state.marketStatus,
                    activeAvatar: state.activeAvatar,
                    autoPilot: state.autoPilot
                }
                store.setSystemInfo(mergeSystemInfo(sysInfo))
                
                // Backend sends: strategyMetrics
                if (state.strategyMetrics || state.metrics) {
                    store.setTradingMetrics(state.strategyMetrics || state.metrics)
                }
                
                // Backend sends: wallet
                if (state.wallet) {
                    store.setPositions(state.wallet) // Or map wallet accordingly
                } else if (state.positions) {
                    store.setPositions(state.positions)
                }
                
                // Backend sends: market_data (maybe not in FULL_STATE, but keep fallback)
                if (state.market_data) store.setMarketData(state.market_data)
                
                // Backend sends: trades
                if (state.trades || state.recent_trades) {
                    store.setRecentTrades(state.trades || state.recent_trades)
                }
                
                // Backend sends: hive
                if (state.hive) {
                    store.setAuthorizationStatus(state.hive)
                }
            }
        })

        // Handle individual update messages
        ws.onMessage('SYSTEM_STATUS', (message) => {
            if (message.payload || message.data) {
                store.setSystemInfo(mergeSystemInfo(message.payload || message.data))
            }
        })

        ws.onMessage('METRICS_UPDATE', (message) => {
            if (message.payload || message.data) {
                store.setTradingMetrics(message.payload || message.data)
            }
        })

        ws.onMessage('POSITIONS_UPDATE', (message) => {
            if (message.payload || message.data) {
                store.setPositions(message.payload || message.data)
            }
        })

        ws.onMessage('MARKET_DATA_UPDATE', (message) => {
            if (message.payload || message.data) {
                store.setMarketData(message.payload || message.data)
            }
        })

        ws.onMessage('TRADES_UPDATE', (message) => {
            if (message.payload || message.data) {
                store.setRecentTrades(message.payload || message.data)
            }
        })

        // Handle HIVE_STATE messages (authorization updates)
        // Expected format: { type: "HIVE_STATE", payload: { whitelist, blacklist, current_user, beta_rat, is_authorized, authorization_method } }
        // OR: { type: "HIVE_STATE", data: { ... } }
        ws.onMessage('HIVE_STATE', (message) => {
            if (message.payload || message.data) {
                const hiveState = message.payload || message.data
                store.setAuthorizationStatus(hiveState)
            }
        })

        // Handle TUNING_PARAMS_UPDATED messages (from TUI/API)
        ws.onMessage('TUNING_PARAMS_UPDATED', (message) => {
            if (message.payload || message.data) {
                const params = message.payload || message.data
                store.setTuningParams(params)
            }
        })

        // Connect WebSocket
        ws.connect()
    }

    /**
     * Handle WebSocket connection changes
     */
    const handleWebSocketConnection = (connected) => {
        if (connected) {
            isWebSocketActive.value = true
            store.setStatus('connected')
            console.log('[UnifiedConnection] WebSocket connected - stopping HTTP polling')
            // Stop HTTP polling when WebSocket is active
            stopHttpPolling()
        } else {
            isWebSocketActive.value = false
            store.setStatus('disconnected')
            console.log('[UnifiedConnection] WebSocket disconnected - will start HTTP fallback')
            // Start HTTP fallback after delay
            if (httpFallbackTimeout) clearTimeout(httpFallbackTimeout)
            httpFallbackTimeout = setTimeout(() => {
                if (!isWebSocketActive.value) {
                    store.setStatus('connecting')
                    startHttpPolling()
                }
            }, HTTP_FALLBACK_DELAY)
        }
    }

    // ===== CONNECTION MANAGEMENT =====

    /**
     * Initialize connection
     */
    const init = () => {
        // Set up WebSocket message handlers for automatic store updates
        setupWebSocketMessageHandlers()
        
        // Watch WebSocket connection status from useWebSocket
        watch(() => ws.isConnected.value, (connected) => {
            handleWebSocketConnection(connected)
        }, { immediate: true })
        
        // Check initial WebSocket state
        const wsConnected = isWebSocketConnected()
        if (wsConnected) {
            isWebSocketActive.value = true
            store.setStatus('connected')
            console.log('[UnifiedConnection] WebSocket already connected')
        } else {
            store.setStatus('connecting')
            // Start HTTP polling as fallback (will stop when WS connects)
            httpFallbackTimeout = setTimeout(() => {
                if (!isWebSocketActive.value) {
                    startHttpPolling()
                }
            }, HTTP_FALLBACK_DELAY)
        }

        // Listen for WebSocket connection changes (backup listener)
        connectionUnsub = setupConnectionListener(handleWebSocketConnection)
    }

    /**
     * Manual refresh function
     */
    const refresh = async () => {
        if (isWebSocketActive.value) {
            // WebSocket is active - data should come via WebSocket
            // Could send a message to request full state if needed
            console.log('[UnifiedConnection] Refresh requested - WebSocket active')
        } else {
            // Poll APIs directly
            console.log('[UnifiedConnection] Refresh requested - polling APIs')
            await pollAllApis()
        }
    }

    /**
     * Cleanup
     */
    const cleanup = () => {
        if (connectionUnsub) {
            connectionUnsub()
            connectionUnsub = null
        }
        if (wsMessageUnsub) {
            wsMessageUnsub()
            wsMessageUnsub = null
        }
        ws.close()
        stopHttpPolling()
        if (httpFallbackTimeout) {
            clearTimeout(httpFallbackTimeout)
            httpFallbackTimeout = null
        }
    }

    // Initialize on mount
    onMounted(() => {
        init()
    })

    // Cleanup on unmount
    onBeforeUnmount(() => {
        cleanup()
    })

    return {
        // Connection state
        isConnected,
        connectionMode,
        isWebSocketActive: computed(() => isWebSocketActive.value),
        isHttpPollingActive: computed(() => isHttpPollingActive.value),
        
        // WebSocket composable (for advanced message handling)
        ws,
        
        // Actions
        refresh,
        
        // Internal methods (for testing/debugging)
        startHttpPolling,
        stopHttpPolling
    }
}

