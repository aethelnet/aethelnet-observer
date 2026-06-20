/**
 * System Status Store
 * Centralized state management for system status, trading metrics, positions, market data, and recent trades
 * Adapted from backup frontend pattern to work with JavaScript codebase
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useSystemStatus = defineStore('systemStatus', () => {
    // ===== CONNECTION STATE =====
    const connectionState = ref('connecting') // 'idle' | 'connecting' | 'connected' | 'error' | 'reconnecting'
    const lastHeartbeat = ref(Date.now())
    const errorLog = ref([])

    // ===== SYSTEM INFO (from API) =====
    const systemInfo = ref(null) // { is_running, execution_enabled, testnet_mode, panic_active, etc. }
    const systemInfoLoading = ref(false)
    const systemInfoError = ref(null)
    const systemInfoLastUpdate = ref(null)

    // ===== TRADING METRICS (from API) =====
    const tradingMetrics = ref({
        total_pnl: 0,
        win_rate: 0,
        total_trades: 0,
        space_weather: {
            alpha_flux: 0,
            kp_index: 0,
            solar_wind: 0
        },
        bit_stage: 0
    })
    const tradingMetricsLoading = ref(false)
    const tradingMetricsError = ref(null)
    const tradingMetricsLastUpdate = ref(null)

    // ===== POSITIONS (from API) =====
    const positions = ref([])
    const positionsLoading = ref(false)
    const positionsError = ref(null)
    const positionsLastUpdate = ref(null)

    // ===== MARKET DATA (from API) =====
    const marketData = ref([])
    const marketDataLoading = ref(false)
    const marketDataError = ref(null)
    const marketDataLastUpdate = ref(null)

    // ===== RECENT TRADES (from API) =====
    const recentTrades = ref([])
    const recentTradesLoading = ref(false)
    const recentTradesError = ref(null)
    const recentTradesLastUpdate = ref(null)

    // ===== AUTHORIZATION STATE =====
    const authorizationStatus = ref(null) // { beta_rat, is_authorized, authorization_method, current_user, whitelist, blacklist, etc. }
    const authorizationLoading = ref(false)
    const authorizationError = ref(null)
    const authorizationLastUpdate = ref(null)
    
    // ===== TUNING PARAMS (from TUI/API) =====
    const tuningParams = ref({
        signal_threshold: 0.55,
        bloom_factor: 1.0,
        pillar_weights: {
            rat: 0.4,
            momentum: 0.2,
            brain: 0.2,
            rhyme: 0.1,
            soul: 0.1
        }
    })

    // Periodic refresh interval (optional - can be disabled)
    let authorizationRefreshInterval = null
    const AUTHORIZATION_REFRESH_INTERVAL = 60000 // 60 seconds

    // ===== COMPUTED HELPERS =====
    const isLive = computed(() => connectionState.value === 'connected')
    const statusColor = computed(() => {
        switch (connectionState.value) {
            case 'connected': return 'status-connected'
            case 'connecting':
            case 'reconnecting': return 'status-connecting'
            case 'error': return 'status-error'
            default: return 'status-idle'
        }
    })

    // ===== ACTIONS =====
    function setStatus(status) {
        connectionState.value = status
        if (status === 'connected') {
            lastHeartbeat.value = Date.now()
        }
    }

    function logError(msg) {
        const timestamp = new Date().toLocaleTimeString()
        errorLog.value.push(`[${timestamp}] ${msg}`)
        // Keep only last 50 errors
        if (errorLog.value.length > 50) {
            errorLog.value.shift()
        }
        setStatus('error')
    }

    // System Info Actions
    function setSystemInfo(info) {
        systemInfo.value = info
        systemInfoLastUpdate.value = Date.now()
        systemInfoError.value = null
    }

    function setSystemInfoLoading(loading) {
        systemInfoLoading.value = loading
    }

    function setSystemInfoError(error) {
        systemInfoError.value = error
        if (error) {
            logError(`System Info: ${error}`)
        }
    }

    // Trading Metrics Actions
    function setTradingMetrics(metrics) {
        tradingMetrics.value = metrics
        tradingMetricsLastUpdate.value = Date.now()
        tradingMetricsError.value = null
    }

    function setTradingMetricsLoading(loading) {
        tradingMetricsLoading.value = loading
    }

    function setTradingMetricsError(error) {
        tradingMetricsError.value = error
        if (error) {
            logError(`Trading Metrics: ${error}`)
        }
    }

    // Positions Actions
    function setPositions(pos) {
        positions.value = pos || []
        positionsLastUpdate.value = Date.now()
        positionsError.value = null
    }

    function setPositionsLoading(loading) {
        positionsLoading.value = loading
    }

    function setPositionsError(error) {
        positionsError.value = error
        if (error) {
            logError(`Positions: ${error}`)
        }
    }

    // Market Data Actions
    function setMarketData(data) {
        marketData.value = data || []
        marketDataLastUpdate.value = Date.now()
        marketDataError.value = null
    }

    function setMarketDataLoading(loading) {
        marketDataLoading.value = loading
    }

    function setMarketDataError(error) {
        marketDataError.value = error
        if (error) {
            logError(`Market Data: ${error}`)
        }
    }

    // Recent Trades Actions
    function setRecentTrades(trades) {
        recentTrades.value = trades || []
        recentTradesLastUpdate.value = Date.now()
        recentTradesError.value = null
    }

    function setRecentTradesLoading(loading) {
        recentTradesLoading.value = loading
    }

    function setRecentTradesError(error) {
        recentTradesError.value = error
        if (error) {
            logError(`Recent Trades: ${error}`)
        }
    }

    // Clear all errors
    function clearErrors() {
        systemInfoError.value = null
        tradingMetricsError.value = null
        positionsError.value = null
        marketDataError.value = null
        recentTradesError.value = null
        authorizationError.value = null
    }

    // Authorization Actions
    function setAuthorizationStatus(status) {
        authorizationStatus.value = status
        authorizationLastUpdate.value = Date.now()
        authorizationError.value = null
    }

    function setAuthorizationLoading(loading) {
        authorizationLoading.value = loading
    }

    function setAuthorizationError(error) {
        authorizationError.value = error
        if (error) {
            logError(`Authorization: ${error}`)
        }
    }

    async function fetchAuthorizationStatus() {
        setAuthorizationLoading(true)
        setAuthorizationError(null)
        try {
            // Import here to avoid circular dependency
            const { fetchHiveStatus } = await import('../shared/api.js')
            const status = await fetchHiveStatus()
            if (status && !status.error) {
                setAuthorizationStatus(status)
            } else {
                setAuthorizationError(status?.detail || 'Failed to fetch authorization status')
            }
        } catch (error) {
            setAuthorizationError(error.message || 'Failed to fetch authorization status')
        } finally {
            setAuthorizationLoading(false)
        }
    }

    function startAuthorizationRefresh() {
        // Clear existing interval
        if (authorizationRefreshInterval) {
            clearInterval(authorizationRefreshInterval)
        }
        
        // Set up periodic refresh
        authorizationRefreshInterval = setInterval(() => {
            fetchAuthorizationStatus()
        }, AUTHORIZATION_REFRESH_INTERVAL)
    }

    function stopAuthorizationRefresh() {
        if (authorizationRefreshInterval) {
            clearInterval(authorizationRefreshInterval)
            authorizationRefreshInterval = null
        }
    }

    // Authorization Computed
    const isAuthorized = computed(() => {
        return authorizationStatus.value?.is_authorized === true && 
               authorizationStatus.value?.beta_rat === false
    })

    const isBetaRat = computed(() => {
        return authorizationStatus.value?.beta_rat === true
    })

    const authorizationMethod = computed(() => {
        return authorizationStatus.value?.authorization_method || null
    })

    function setTuningParams(params) {
        tuningParams.value = { ...tuningParams.value, ...params }
    }

    return {
        // Connection State
        connectionState,
        isLive,
        statusColor,
        lastHeartbeat,
        errorLog,
        setStatus,
        logError,
        
        // Tuning Params
        tuningParams,
        setTuningParams,

        // System Info
        systemInfo,
        systemInfoLoading,
        systemInfoError,
        systemInfoLastUpdate,
        setSystemInfo,
        setSystemInfoLoading,
        setSystemInfoError,
        
        // Trading Metrics
        tradingMetrics,
        tradingMetricsLoading,
        tradingMetricsError,
        tradingMetricsLastUpdate,
        setTradingMetrics,
        setTradingMetricsLoading,
        setTradingMetricsError,
        
        // Positions
        positions,
        positionsLoading,
        positionsError,
        positionsLastUpdate,
        setPositions,
        setPositionsLoading,
        setPositionsError,
        
        // Market Data
        marketData,
        marketDataLoading,
        marketDataError,
        marketDataLastUpdate,
        setMarketData,
        setMarketDataLoading,
        setMarketDataError,
        
        // Recent Trades
        recentTrades,
        recentTradesLoading,
        recentTradesError,
        recentTradesLastUpdate,
        setRecentTrades,
        setRecentTradesLoading,
        setRecentTradesError,
        
        // Authorization
        authorizationStatus,
        authorizationLoading,
        authorizationError,
        authorizationLastUpdate,
        isAuthorized,
        isBetaRat,
        authorizationMethod,
        setAuthorizationStatus,
        fetchAuthorizationStatus,
        startAuthorizationRefresh,
        stopAuthorizationRefresh,
        
        // Utility
        clearErrors
    }
})


