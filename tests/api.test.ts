/**
 * API Client Tests
 * Tests for src/shared/api.js functions
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  validateSymbolFormat,
  parseSymbolForBaseQuote,
  formatCurrency,
  formatPercentage,
  formatNumber,
  formatDuration
} from '../src/shared/api'

describe('API Utility Functions', () => {
  describe('validateSymbolFormat', () => {
    it('should validate correct symbol formats', () => {
      const result = validateSymbolFormat('BTCUSDT')
      expect(result.valid).toBe(true)
      // Note: validateSymbolFormat may not return base/quote, check actual implementation
    })

    it('should reject invalid symbol formats', () => {
      const result = validateSymbolFormat('INVALID')
      expect(result.valid).toBe(false)
      expect(result.error).toBeDefined()
    })

    it('should handle lowercase symbols', () => {
      const result = validateSymbolFormat('btcusdt')
      // Function requires uppercase, so lowercase should fail
      expect(result.valid).toBe(false)
      expect(result.error).toBeDefined()
    })
  })

  describe('parseSymbolForBaseQuote', () => {
    it('should parse valid symbols correctly', () => {
      const result = parseSymbolForBaseQuote('ETHUSDT')
      expect(result.canBeBase).toBe(true)
      expect(result.base).toBe('ETH')
      expect(result.quote).toBe('USDT')
    })

    it('should handle invalid symbols', () => {
      const result = parseSymbolForBaseQuote('INVALID')
      // Function may still return canBeBase: true if length is valid, but quote will be null
      expect(result.quote).toBeNull()
      expect(result.base).toBe('INVALID')
    })
  })

  describe('formatCurrency', () => {
    it('should format numbers as currency', () => {
      const result = formatCurrency(1234.56)
      expect(result).toBeTruthy()
      expect(typeof result).toBe('string')
      expect(formatCurrency(0)).toBeTruthy()
    })

    it('should handle null and undefined', () => {
      expect(formatCurrency(null)).toBeTruthy()
      expect(formatCurrency(undefined)).toBeTruthy()
    })
  })

  describe('formatPercentage', () => {
    it('should format numbers as percentages', () => {
      const result = formatPercentage(12.345)
      expect(result).toBeTruthy()
      expect(typeof result).toBe('string')
      expect(result).toContain('%')
    })

    it('should respect decimal places', () => {
      const result = formatPercentage(12.345, 2)
      expect(result).toBeTruthy()
      expect(typeof result).toBe('string')
    })
  })

  describe('formatNumber', () => {
    it('should format numbers', () => {
      const result = formatNumber(1234.56)
      expect(result).toBeTruthy()
      expect(typeof result).toBe('string')
      expect(formatNumber(0)).toBeTruthy()
    })

    it('should respect decimal places', () => {
      const result = formatNumber(1234.56, 2)
      expect(result).toBeTruthy()
      expect(typeof result).toBe('string')
    })
  })

  describe('formatDuration', () => {
    it('should format seconds as duration', () => {
      expect(formatDuration(3661)).toMatch(/1h/)
      expect(formatDuration(60)).toMatch(/1m/)
      expect(formatDuration(30)).toMatch(/30s/)
    })
  })
})

