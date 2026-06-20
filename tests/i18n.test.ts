import { describe, it, expect, beforeEach } from 'vitest'
import { t, setLocale } from '../src/i18n'

describe('i18n System', () => {
    beforeEach(() => {
        setLocale('en')
    })

    it('should translate simple key', () => {
        expect(t('nodes.types.market')).toBe('Market Hub')
    })

    it('should handle nested keys', () => {
        expect(t('ui.pins.tooltip.pinned')).toBe('Pinned to dashboard')
    })

    it('should return key if missing', () => {
        expect(t('missing.key')).toBe('missing.key')
    })

    it('should interpolate parameters', () => {
        // "symbol": "{{name}} is a tradable asset currently priced at {{price}}. Detection confidence is {{confidence}}%."
        const result = t('nodes.tldr.symbol', {
            name: 'BTC',
            price: '$100,000',
            confidence: '99'
        })
        expect(result).toBe('BTC is a tradable asset currently priced at $100,000. Detection confidence is 99%.')
    })

    it('should ignore unused parameters', () => {
        expect(t('nodes.types.market', { foo: 'bar' })).toBe('Market Hub')
    })

    it('should handle undefined parameters gracefully', () => {
        const result = t('nodes.tldr.symbol', {
            name: 'BTC',
            // price missing
            confidence: '99'
        })
        expect(result).toContain('{{price}}')
        expect(result).toContain('BTC')
    })

    it('should translate German', () => {
        setLocale('de')
        expect(t('nodes.types.market')).toBe('Marktplatz')
        expect(t('ui.pins.pin')).toBe('Anpinnen')
        setLocale('en') // Reset
    })
})
