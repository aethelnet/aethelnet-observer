/**
 * Node token tests
 * Tests for src/shared/nodeAuth.ts (token lookup and the fetch wrapper)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  NODE_TOKEN_KEY,
  getNodeToken,
  setNodeToken,
  needsNodeAuth,
  installNodeAuthFetch
} from '../src/shared/nodeAuth'

function fakeTarget() {
  const calls: Array<{ input: any; init: RequestInit }> = []
  const target = {
    fetch: vi.fn((input: any, init: RequestInit = {}) => {
      calls.push({ input, init })
      return Promise.resolve(new Response('{}'))
    })
  }
  installNodeAuthFetch(target as any)
  return { target, calls }
}

function authHeader(init: RequestInit): string | null {
  return new Headers(init.headers).get('Authorization')
}

describe('nodeAuth', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  describe('getNodeToken / setNodeToken', () => {
    it('is empty by default (no shared fallback token)', () => {
      expect(getNodeToken()).toBe('')
    })

    it('stores, trims and clears the token', () => {
      setNodeToken('  abc  ')
      expect(localStorage.getItem(NODE_TOKEN_KEY)).toBe('abc')
      expect(getNodeToken()).toBe('abc')
      setNodeToken('')
      expect(localStorage.getItem(NODE_TOKEN_KEY)).toBeNull()
    })

    it('falls back to the legacy SOVEREIGN_ADMIN_TOKEN key', () => {
      localStorage.setItem('SOVEREIGN_ADMIN_TOKEN', 'legacy')
      expect(getNodeToken()).toBe('legacy')
      localStorage.setItem(NODE_TOKEN_KEY, 'new')
      expect(getNodeToken()).toBe('new')
    })
  })

  describe('needsNodeAuth', () => {
    it('flags writes to node API paths', () => {
      expect(needsNodeAuth('http://127.0.0.1:8000/api/lgnn/node', 'POST')).toBe(true)
      expect(needsNodeAuth('http://127.0.0.1:8000/api/lgnn/node', 'DELETE')).toBe(true)
      expect(needsNodeAuth('/api/lgnn/snapshot/create', 'POST')).toBe(true)
      expect(needsNodeAuth('http://localhost:8000/api/ontology/multigraph/edge', 'POST')).toBe(true)
    })

    it('treats NaaS GETs as protected (they execute node content)', () => {
      expect(needsNodeAuth('http://127.0.0.1:8000/api/lgnn/naas/my_app', 'GET')).toBe(true)
    })

    it('leaves reads and non-node paths alone', () => {
      expect(needsNodeAuth('http://127.0.0.1:8000/api/lgnn/graph', 'GET')).toBe(false)
      expect(needsNodeAuth('http://127.0.0.1:8000/api/metrics', 'POST')).toBe(false)
      expect(needsNodeAuth('/api/v3/ticker/price', 'POST')).toBe(false)
    })

    it('never targets foreign origins', () => {
      expect(needsNodeAuth('https://api.binance.com/api/lgnn/node', 'POST')).toBe(false)
      expect(needsNodeAuth('https://evil.example/api/lgnn/node', 'POST')).toBe(false)
    })

    it('includes a configured backend override', () => {
      localStorage.setItem('SOVEREIGN_BACKEND_URL', 'https://node.example.org/api')
      expect(needsNodeAuth('https://node.example.org/api/lgnn/edge', 'POST')).toBe(true)
    })
  })

  describe('installNodeAuthFetch', () => {
    it('changes nothing when no token is configured', async () => {
      const { target, calls } = fakeTarget()
      await target.fetch('http://127.0.0.1:8000/api/lgnn/node', { method: 'POST' })
      expect(authHeader(calls[0].init)).toBeNull()
    })

    it('adds the bearer token to node writes only', async () => {
      setNodeToken('secret-1')
      const { target, calls } = fakeTarget()
      await target.fetch('http://127.0.0.1:8000/api/lgnn/node', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })
      await target.fetch('http://127.0.0.1:8000/api/lgnn/graph')
      await target.fetch('https://api.binance.com/api/v3/ticker', { method: 'POST' })

      expect(authHeader(calls[0].init)).toBe('Bearer secret-1')
      expect(new Headers(calls[0].init.headers).get('Content-Type')).toBe('application/json')
      expect(authHeader(calls[1].init)).toBeNull()
      expect(authHeader(calls[2].init)).toBeNull()
    })

    it('keeps an explicit Authorization header', async () => {
      setNodeToken('secret-1')
      const { target, calls } = fakeTarget()
      await target.fetch('/api/lgnn/edge', { method: 'POST', headers: { Authorization: 'Bearer other' } })
      expect(authHeader(calls[0].init)).toBe('Bearer other')
    })

    it('is idempotent', () => {
      const { target } = fakeTarget()
      const once = target.fetch
      installNodeAuthFetch(target as any)
      expect(target.fetch).toBe(once)
    })
  })
})
