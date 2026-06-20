/**
 * Store Tests
 * Tests for src/stores/systemStatus.js
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useSystemStatus } from '../src/stores/systemStatus'

describe('SystemStatus Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should initialize with default state', () => {
    const store = useSystemStatus()
    expect(store.connectionState).toBe('connecting')
    expect(store.systemInfo).toBeNull()
    expect(store.tradingMetrics).toBeNull()
    expect(store.positions).toEqual([])
    expect(store.marketData).toEqual([])
    expect(store.recentTrades).toEqual([])
  })

  it('should update system info', () => {
    const store = useSystemStatus()
    const testInfo = {
      is_running: true,
      execution_enabled: true,
      panic_active: false
    }
    
    store.setSystemInfo(testInfo)
    expect(store.systemInfo).toEqual(testInfo)
    expect(store.systemInfoError).toBeNull()
  })

  it('should update trading metrics', () => {
    const store = useSystemStatus()
    const testMetrics = {
      total_pnl: 1000,
      win_rate: 0.75,
      total_trades: 100
    }
    
    store.setTradingMetrics(testMetrics)
    expect(store.tradingMetrics).toEqual(testMetrics)
    expect(store.tradingMetricsError).toBeNull()
  })

  it('should update positions', () => {
    const store = useSystemStatus()
    const testPositions = [
      { symbol: 'BTCUSDT', size: 1.5 },
      { symbol: 'ETHUSDT', size: 10 }
    ]
    
    store.setPositions(testPositions)
    expect(store.positions).toEqual(testPositions)
    expect(store.positionsError).toBeNull()
  })

  it('should compute isAuthorized correctly', () => {
    const store = useSystemStatus()
    
    // Initially not authorized
    expect(store.isAuthorized).toBe(false)
    
    // Set authorized status
    store.setAuthorizationStatus({
      beta_rat: false,
      is_authorized: true
    })
    expect(store.isAuthorized).toBe(true)
    
    // Beta rat should not be authorized
    store.setAuthorizationStatus({
      beta_rat: true,
      is_authorized: false
    })
    expect(store.isAuthorized).toBe(false)
  })

  it('should compute isBetaRat correctly', () => {
    const store = useSystemStatus()
    
    expect(store.isBetaRat).toBe(false)
    
    store.setAuthorizationStatus({
      beta_rat: true,
      is_authorized: false
    })
    expect(store.isBetaRat).toBe(true)
  })

  it('should clear errors', () => {
    const store = useSystemStatus()
    
    store.setSystemInfoError('Test error')
    store.setTradingMetricsError('Test error')
    
    store.clearErrors()
    
    expect(store.systemInfoError).toBeNull()
    expect(store.tradingMetricsError).toBeNull()
  })
})

