/**
 * Node token for authenticated writes to an aethelnet-node.
 *
 * aethelnet-node requires `Authorization: Bearer <AETHELNET_AUTH_TOKEN>` for state-changing
 * requests (and `{"type": "AUTH", "token": ...}` for WebSocket commands) whenever the node has a
 * token configured. A node bound to localhost without a token accepts writes from this machine,
 * so local development needs no setup.
 *
 * Token sources, first match wins:
 *   1. localStorage AETHELNET_NODE_TOKEN (set from the System Logs HUD)
 *   2. VITE_AETHELNET_TOKEN (e.g. in .env.local, never committed)
 *   3. legacy names: localStorage SOVEREIGN_ADMIN_TOKEN, VITE_ADMIN_TOKEN
 */

export const NODE_TOKEN_KEY = 'AETHELNET_NODE_TOKEN'

const NODE_PATH_PREFIXES = ['/api/lgnn/', '/api/ontology/', '/api/ingest/', '/api/dossier/', '/p2p/', '/api/p2p/']
const SAFE_METHODS = new Set(['GET', 'HEAD', 'OPTIONS'])
const MARKER = '__aethelnetNodeAuth'

function fromStorage(key: string): string {
  try {
    return localStorage.getItem(key) || ''
  } catch {
    return ''
  }
}

function fromEnv(name: string): string {
  try {
    const env = (import.meta as any).env || {}
    return env[name] || ''
  } catch {
    return ''
  }
}

export function getNodeToken(): string {
  return (
    fromStorage(NODE_TOKEN_KEY) ||
    fromEnv('VITE_AETHELNET_TOKEN') ||
    fromStorage('SOVEREIGN_ADMIN_TOKEN') ||
    fromEnv('VITE_ADMIN_TOKEN')
  ).trim()
}

export function setNodeToken(token: string): void {
  try {
    const value = token.trim()
    if (value) localStorage.setItem(NODE_TOKEN_KEY, value)
    else localStorage.removeItem(NODE_TOKEN_KEY)
  } catch {
    /* storage unavailable (private mode): the env token still applies */
  }
}

/** Origins the dashboard talks to as "the node". The token is never sent anywhere else. */
function nodeOrigins(): Set<string> {
  const origins = new Set<string>(['http://127.0.0.1:8000', 'http://localhost:8000'])
  if (typeof window !== 'undefined' && window.location) {
    origins.add(window.location.origin)
    const host = window.location.hostname === 'localhost' ? '127.0.0.1' : window.location.hostname || '127.0.0.1'
    origins.add(`http://${host}:8000`)
    origins.add(`https://${host}:8000`)
  }
  const backend = fromStorage('SOVEREIGN_BACKEND_URL')
  if (backend) {
    try {
      origins.add(new URL(backend).origin)
    } catch {
      /* ignore malformed override */
    }
  }
  return origins
}

/** True for state-changing requests to node API paths (plus NaaS, which executes node content). */
export function needsNodeAuth(url: string, method = 'GET'): boolean {
  let parsed: URL
  try {
    const base = typeof window !== 'undefined' && window.location ? window.location.href : 'http://127.0.0.1/'
    parsed = new URL(url, base)
  } catch {
    return false
  }
  if (!nodeOrigins().has(parsed.origin)) return false
  const path = parsed.pathname
  if (!NODE_PATH_PREFIXES.some((prefix) => path.startsWith(prefix))) return false
  return !SAFE_METHODS.has(method.toUpperCase()) || path.startsWith('/api/lgnn/naas/')
}

type FetchLike = (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>

/**
 * Wraps fetch so that node writes carry the token. Components keep calling plain fetch().
 * With no token configured nothing changes, so local setups behave exactly as before.
 */
export function installNodeAuthFetch(target: { fetch: FetchLike } = globalThis as any): void {
  const current = target.fetch as FetchLike & { [MARKER]?: boolean }
  if (typeof current !== 'function' || current[MARKER]) return
  const original = current.bind(target)

  const wrapped = ((input: RequestInfo | URL, init: RequestInit = {}) => {
    const token = getNodeToken()
    if (!token) return original(input, init)
    const isRequest = typeof Request !== 'undefined' && input instanceof Request
    const url = isRequest ? (input as Request).url : String(input)
    const method = init.method || (isRequest ? (input as Request).method : 'GET')
    if (!needsNodeAuth(url, method)) return original(input, init)
    const headers = new Headers(init.headers || (isRequest ? (input as Request).headers : undefined))
    if (!headers.has('Authorization')) headers.set('Authorization', `Bearer ${token}`)
    return original(input, { ...init, headers })
  }) as FetchLike & { [MARKER]?: boolean }

  wrapped[MARKER] = true
  target.fetch = wrapped
}
