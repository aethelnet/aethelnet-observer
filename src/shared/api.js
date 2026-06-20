/**
 * Shared API Client
 * Centralized API utilities for all components and views
 */

const getApiBase = () => {
    if (typeof window !== 'undefined') {
        let configuredBackend = localStorage.getItem('SOVEREIGN_BACKEND_URL');
        if (configuredBackend) {
            return configuredBackend;
        }
        
        const host = window.location.host; // includes port
        if (host) {
            if (host.includes('localhost') || host.includes('127.0.0.1')) {
                return `http://127.0.0.1:8001/api`;
            }
            // If they are accessing via LAN IP, use that IP on port 8001
            return `http://${window.location.hostname}:8001/api`;
        }
    }
    return 'http://127.0.0.1:8001/api';
};

const API_BASE = getApiBase();
console.error("DEBUG: window.location.host is " + (typeof window !== 'undefined' ? window.location.host : 'undefined'));
console.error("DEBUG: API_BASE evaluated to: " + API_BASE);

// Retry configuration
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // 1 second
const REQUEST_TIMEOUT = 15000; // 15 seconds (increased for heavy CPU load during AI inference)

/**
 * Default valid quote currencies (can be overridden)
 * Note: These are common quote currencies. The backend validates symbols,
 * so this is primarily for client-side validation. Backend may support additional quotes.
 */
const DEFAULT_VALID_QUOTES = ['USDT', 'USDC', 'BUSD', 'BTC', 'ETH', 'EUR', 'SOL'];

/**
 * Sleep helper for retry delays
 * @param {number} ms - Milliseconds to sleep
 * @returns {Promise<void>}
 */
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Generic API fetch with error handling, retry logic, and timeout
 * @param {string} endpoint - API endpoint (without /api prefix)
 * @param {Object} options - Fetch options
 * @returns {Promise<Object|null>} Response data or null on error
 */
async function apiFetch(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    
    // Retry loop
    for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
        try {
            // Create AbortController for timeout
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);
            
            const response = await fetch(url, {
                ...options,
                signal: controller.signal,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers,
                },
            });
            
            clearTimeout(timeoutId);
            
            // Don't retry on client errors (4xx) - return immediately
            if (response.status >= 400 && response.status < 500) {
                // Handle 404 errors immediately (they often don't have JSON bodies)
                if (response.status === 404) {
                    // Try to get error detail from JSON if available, otherwise use status text
                    let errorDetail = response.statusText || 'Not Found';
                    try {
                        const contentType = response.headers.get('content-type');
                        if (contentType && contentType.includes('application/json')) {
                            const jsonData = await response.json();
                            errorDetail = jsonData.detail || errorDetail;
                        }
                    } catch (e) {
                        // Ignore JSON parse errors for 404s - use status text instead
                    }
                    return { error: true, status: 404, detail: errorDetail || `Endpoint not found: ${endpoint}. The backend may be updating or the endpoint may have changed.` };
                }
                
                // Handle other 4xx errors
                const contentType = response.headers.get('content-type');
                const hasJson = contentType && contentType.includes('application/json');
                
                let data = null;
                if (hasJson) {
                    try {
                        data = await response.json();
                    } catch (parseError) {
                        // If JSON parsing fails, use status text
                    }
                }
                
                // Extract error message from various possible response formats
                let errorDetail = response.statusText || 'Request failed';
                if (data) {
                    if (data.detail) {
                        errorDetail = data.detail;
                    } else if (data.message) {
                        errorDetail = data.message;
                    } else if (data.error) {
                        errorDetail = typeof data.error === 'string' ? data.error : JSON.stringify(data.error);
                    } else if (typeof data === 'string') {
                        errorDetail = data;
                    }
                }
                
                // Log full error for debugging
                console.error(`[API] Error ${response.status} from ${endpoint}:`, {
                    status: response.status,
                    statusText: response.statusText,
                    data: data,
                    errorDetail: errorDetail
                });
                
                return { error: true, status: response.status, detail: errorDetail };
            }
            
            // Retry on server errors (5xx) if we haven't exceeded max retries
            if (response.status >= 500 && attempt < MAX_RETRIES) {
                console.warn(`[API] Server error ${response.status} from ${endpoint}, retrying... (attempt ${attempt + 1}/${MAX_RETRIES})`);
                await sleep(RETRY_DELAY * (attempt + 1));
                continue;
            }
            
            // Check if response has JSON content
            const contentType = response.headers.get('content-type');
            const hasJson = contentType && contentType.includes('application/json');
            
            let data = null;
            if (hasJson) {
                try {
                    data = await response.json();
                } catch (parseError) {
                    // If JSON parsing fails, return error with status text
                    if (!response.ok) {
                        return { error: true, status: response.status, detail: response.statusText || 'Invalid response format' };
                    }
                }
            }
            
            if (!response.ok) {
                // Extract error message from various possible response formats
                let errorDetail = response.statusText || 'Request failed';
                if (data) {
                    // Try different common error response formats
                    if (data.detail) {
                        errorDetail = data.detail;
                    } else if (data.message) {
                        errorDetail = data.message;
                    } else if (data.error) {
                        errorDetail = typeof data.error === 'string' ? data.error : JSON.stringify(data.error);
                    } else if (typeof data === 'string') {
                        errorDetail = data;
                    } else {
                        // For 500 errors, try to get more details
                        if (response.status === 500) {
                            errorDetail = data.detail || data.message || JSON.stringify(data) || 'Internal server error';
                        }
                    }
                }
                
                // Log full error for debugging
                console.error(`[API] Error ${response.status} from ${endpoint}:`, {
                    status: response.status,
                    statusText: response.statusText,
                    data: data,
                    errorDetail: errorDetail
                });
                
                // Return error object with appropriate detail
                return { error: true, status: response.status, detail: errorDetail };
            }
            
            return data;
        } catch (error) {
            // Handle AbortError (timeout)
            if (error.name === 'AbortError') {
                if (attempt < MAX_RETRIES) {
                    console.warn(`[API] Request timeout for ${endpoint}, retrying... (attempt ${attempt + 1}/${MAX_RETRIES})`);
                    await sleep(RETRY_DELAY * (attempt + 1));
                    continue;
                }
                console.error(`[API] Request timeout for ${endpoint} after ${MAX_RETRIES} retries`);
                return { error: true, detail: 'Request timeout' };
            }
            
            // Handle network errors
            if (error instanceof TypeError && error.message.includes('fetch')) {
                if (attempt < MAX_RETRIES) {
                    console.warn(`[API] Network error for ${endpoint}, retrying... (attempt ${attempt + 1}/${MAX_RETRIES})`);
                    await sleep(RETRY_DELAY * (attempt + 1));
                    continue;
                }
                console.error(`[API] Network error for ${endpoint} after ${MAX_RETRIES} retries:`, error);
                return { error: true, detail: 'Network error: Unable to connect to backend' };
            }
            
            // Unexpected error - retry if we haven't exceeded max retries
            if (attempt < MAX_RETRIES) {
                console.warn(`[API] Unexpected error for ${endpoint}, retrying... (attempt ${attempt + 1}/${MAX_RETRIES}):`, error.message);
                await sleep(RETRY_DELAY * (attempt + 1));
                continue;
            }
            
            console.error(`[API] Failed to fetch ${endpoint} after ${MAX_RETRIES} retries:`, error);
            return { error: true, detail: error.message || 'Unexpected error' };
        }
    }
    
    // Should never reach here, but just in case
    return { error: true, detail: 'Max retries exceeded' };
}

/**
 * Fetch dashboard metrics
 * @returns {Promise<Object|null>} Metrics data
 */
export async function fetchMetrics() {
    return await apiFetch('/dashboard/metrics');
}

/**
 * Fetch market data for all symbols
 * @returns {Promise<Array|null>} Market data array
 */
export async function fetchMarketData() {
    return await apiFetch('/dashboard/market-data');
}

/**
 * Fetch open positions
 * @returns {Promise<Array|null>} Positions array
 */
export async function fetchPositions() {
    return await apiFetch('/dashboard/positions');
}

/**
 * Fetch recent trades
 * @param {number} limit - Maximum number of trades to fetch
 * @returns {Promise<Array|null>} Trades array
 */
export async function fetchRecentTrades(limit = 20) {
    return await apiFetch(`/dashboard/recent-trades?limit=${limit}`);
}

/**
 * Fetch failsafe/panic status
 * @returns {Promise<Object|null>} Status data
 */
export async function fetchFailsafeStatus() {
    return await apiFetch('/failsafe/status');
}

/**
 * Fetch system status from /api/dashboard/status
 * This endpoint contains execution_enabled and other system info
 * @returns {Promise<Object|null>} System status object
 */
export async function fetchDashboardStatus() {
    return await apiFetch('/dashboard/status');
}

/**
 * Fetch trading configuration from /api/trading/config
 * This endpoint contains engine status (main, shadow, etc.)
 * @returns {Promise<Object|null>} Trading configuration object
 */
export async function fetchTradingConfig() {
    return await apiFetch('/trading/config');
}

/**
 * Activate panic mode (emergency stop)
 * @returns {Promise<Object|null>} Response data
 */
export async function activatePanic() {
    return await apiFetch('/failsafe/panic', { method: 'POST' });
}

/**
 * Resume trading (deactivate panic mode)
 * @returns {Promise<Object|null>} Response data
 */
export async function resumeTrading() {
    return await apiFetch('/failsafe/resume', { method: 'POST' });
}

/**
 * Fetch predictions for a symbol
 * @param {string} symbol - Trading symbol (e.g., 'BTCUSDT')
 * @returns {Promise<Object|null>} Predictions data
 */
export async function fetchPredictions(symbol = null) {
    const endpoint = symbol ? `/predictions?symbol=${symbol}` : '/predictions';
    return await apiFetch(endpoint);
}

/**
 * Fetch trade opportunities
 * @param {Object} filters - Filter options (symbol, min_confidence, urgency)
 * @returns {Promise<Array|null>} Opportunities array
 */
export async function fetchOpportunities(filters = {}) {
    const params = new URLSearchParams();
    if (filters.symbol) params.append('symbol', filters.symbol);
    if (filters.min_confidence) params.append('min_confidence', filters.min_confidence);
    if (filters.urgency) params.append('urgency', filters.urgency);
    
    const queryString = params.toString();
    const endpoint = queryString ? `/opportunities?${queryString}` : '/opportunities';
    return await apiFetch(endpoint);
}

/**
 * Run a tuning simulation for a symbol
 * @param {string} symbol - Trading symbol
 * @param {number} threshold - Signal threshold
 * @param {number} bloomFactor - Bloom factor
 * @param {Object} pillarWeights - Weights for signal pillars
 * @returns {Promise<Object|null>} Simulation result with markers and trajectories
 */
export async function runTuningSimulation(symbol, threshold, bloomFactor, pillarWeights = null) {
    return await apiFetch('/simulation/tuning', {
        method: 'POST',
        body: JSON.stringify({
            symbol,
            threshold,
            bloom_factor: bloomFactor,
            pillar_weights: pillarWeights
        })
    });
}

/**
 * Fetch symbol opportunities (new unified endpoint)
 * Returns symbols with their market data and opportunities combined
 * @returns {Promise<Array|null>} Symbol opportunities array
 */
export async function fetchSymbolOpportunities() {
    return await apiFetch('/opportunities/symbols');
}

/**
 * Fetch auto-discovery status
 * @returns {Promise<Object|null>} Auto-discovery status data
 */
export async function fetchAutoDiscoveryStatus() {
    return await apiFetch('/auto-discovery/status');
}

/**
 * Fetch auto-discovery diagnostics (debug endpoint)
 * @returns {Promise<Object|null>} Diagnostics data
 */
export async function fetchAutoDiscoveryDiagnostics() {
    return await apiFetch('/debug/auto-discovery/diagnostics');
}

/**
 * Manually trigger an auto-discovery scan
 * @returns {Promise<Object|null>} Scan result
 */
export async function triggerAutoDiscoveryScan() {
    return await apiFetch('/auto-discovery/scan', { method: 'POST' });
}

/**
 * Fetch auto-discovery symbols
 * @returns {Promise<Object|null>} Auto-discovery symbols data (contains symbols object)
 */
export async function fetchAutoDiscoverySymbols() {
    return await apiFetch('/auto-discovery/symbols');
}

/**
 * Fetch all available trading symbols from backend
 * @returns {Promise<Array<string>|null>} Array of all available symbols
 */
export async function fetchAllSymbols() {
    const result = await apiFetch('/symbols');
    if (result && result.symbols && Array.isArray(result.symbols)) {
        return result.symbols;
    }
    return null;
}

/**
 * Get comprehensive analysis for a symbol
 * @param {string} symbol - Trading symbol (e.g., 'BTCUSDT')
 * @returns {Promise<Object|null>} Analysis data with predictions, opportunities, and status
 */
export async function getSymbolAnalysis(symbol) {
    if (!symbol) return null;
    
    const symbolUpper = symbol.toUpperCase();
    
    // Validate symbol format
    const validation = validateSymbolFormat(symbolUpper);
    if (!validation.valid) {
        return { error: true, status: 400, detail: validation.error };
    }
    
    try {
        // Fetch all data in parallel
        const [predictions, opportunities, autoDiscoveryStatus] = await Promise.all([
            fetchPredictions(symbolUpper),
            fetchOpportunities({ symbol: symbolUpper }),
            fetchAutoDiscoveryStatus()
        ]);
        
        // Determine symbol status
        const whitelist = autoDiscoveryStatus?.stats?.symbols ? 
            Object.keys(autoDiscoveryStatus.stats.symbols) : [];
        const isWhitelisted = whitelist.includes(symbolUpper);
        const isDiscovered = autoDiscoveryStatus?.stats?.symbols?.[symbolUpper] !== undefined;
        
        return {
            symbol: symbolUpper,
            predictions: predictions?.predictions || [],
            currentPrice: predictions?.current_price || 0,
            opportunities: Array.isArray(opportunities) ? opportunities : [],
            isWhitelisted,
            isDiscovered,
            analysis: {
                hasPredictions: (predictions?.predictions || []).length > 0,
                hasOpportunities: (Array.isArray(opportunities) ? opportunities : []).length > 0,
                lastUpdate: predictions?.last_update || null
            }
        };
    } catch (error) {
        console.error('[api] Failed to get symbol analysis:', error);
        return { error: true, detail: error.message || 'Failed to analyze symbol' };
    }
}

/**
 * Get current base and quote currencies configuration
 * Note: This reads from auto-discovery status to infer current config
 * @returns {Promise<Object|null>} { baseCurrencies: string[], quoteCurrencies: string[] }
 */
export async function getBaseQuoteConfig() {
    try {
        const status = await fetchAutoDiscoveryStatus();
        if (!status) return null;
        
        // Parse whitelist to infer base/quote (heuristic)
        // Or create backend endpoint to return current BASE_CURRENCIES/QUOTE_CURRENCIES
        // For now, return common defaults
        return {
            baseCurrencies: ['BTC', 'ETH', 'SOL', 'ADA', 'DOT', 'LINK', 'AVAX', 'MATIC'],
            quoteCurrencies: ['USDC', 'EUR'],
            note: 'Current config from .env. Use promotion API to add symbols to whitelist.'
        };
    } catch (error) {
        console.error('[api] Failed to get base/quote config:', error);
        return null;
    }
}

/**
 * Check if symbol can be added as base or quote
 * @param {string} symbol - Full symbol (e.g., 'BTCUSDT')
 * @returns {Object} { canBeBase: boolean, canBeQuote: boolean, base: string, quote: string }
 */
export function parseSymbolForBaseQuote(symbol) {
    if (!symbol || typeof symbol !== 'string') {
        return { canBeBase: false, canBeQuote: false, base: null, quote: null };
    }
    
    const symbolUpper = symbol.toUpperCase();
    const validQuotes = DEFAULT_VALID_QUOTES;
    
    // Try to extract base and quote
    for (const quote of validQuotes) {
        if (symbolUpper.endsWith(quote)) {
            const base = symbolUpper.slice(0, -quote.length);
            return {
                canBeBase: base.length >= 2 && base.length <= 10,
                canBeQuote: false, // Quote is already determined
                base,
                quote
            };
        }
    }
    
    // If no quote found, might be a base currency
    return {
        canBeBase: symbolUpper.length >= 2 && symbolUpper.length <= 10,
        canBeQuote: false,
        base: symbolUpper,
        quote: null
    };
}

/**
 * Validate trading symbol format
 * @param {string} symbol - Symbol to validate
 * @param {string[]} validQuotes - Optional array of valid quote currencies (defaults to DEFAULT_VALID_QUOTES)
 * @returns {Object} { valid: boolean, error?: string }
 */
export function validateSymbolFormat(symbol, validQuotes = DEFAULT_VALID_QUOTES) {
    if (!symbol || typeof symbol !== 'string') {
        return { valid: false, error: 'Symbol must be a non-empty string' };
    }
    
    const symbolUpper = symbol.toUpperCase();
    
    // Must be uppercase
    if (symbol !== symbolUpper) {
        return { valid: false, error: 'Symbol must be uppercase (e.g., BTCUSDC not btcusdc)' };
    }
    
    // Length check (6-20 characters)
    if (symbol.length < 6 || symbol.length > 20) {
        return { valid: false, error: 'Symbol must be 6-20 characters long' };
    }
    
    // Alphanumeric only
    if (!/^[A-Z0-9]+$/.test(symbol)) {
        return { valid: false, error: 'Symbol must contain only letters and numbers (e.g., BTCUSDC not BTC-USDC)' };
    }
    
    // Must end with valid quote currency (if validation enabled)
    if (validQuotes && validQuotes.length > 0) {
        const endsWithQuote = validQuotes.some(quote => symbol.endsWith(quote));
        if (!endsWithQuote) {
            return { valid: false, error: `Symbol must end with a valid quote currency: ${validQuotes.join(', ')}` };
        }
    }
    
    return { valid: true };
}

/**
 * Promote a symbol to whitelist
 * @param {string} symbol - Trading symbol (e.g., 'BTCUSDT')
 * @returns {Promise<Object|null>} Response data
 */
export async function promoteToWhitelist(symbol) {
    // Validate symbol format
    const validation = validateSymbolFormat(symbol);
    if (!validation.valid) {
        return { error: true, status: 400, detail: validation.error };
    }
    
    const result = await apiFetch(`/auto-discovery/promote/${symbol}`, { method: 'POST' });
    
    // Handle 404 errors (symbol not found in discovered symbols or endpoint not found)
    if (result?.status === 404 && result?.error) {
        const errorMessage = result.detail || result.error || '';
        // Check for specific "not found in discovered symbols" message
        if (errorMessage.includes('not found in discovered symbols') || 
            errorMessage.toLowerCase().includes('symbol') && errorMessage.toLowerCase().includes('not found')) {
            const symbolMatch = errorMessage.match(/Symbol (\w+) not found/i);
            const symbolName = symbolMatch ? symbolMatch[1] : symbol;
            return {
                error: true,
                status: 404,
                detail: `${symbolName} needs to be discovered again by the auto-discovery engine before it can be promoted. Please wait a few seconds for the engine to re-discover it.`
            };
        }
        // Generic 404 - likely endpoint not found or symbol not in discovered list
        return {
            error: true,
            status: 404,
            detail: `${symbol} could not be promoted. The symbol may need to be re-discovered by the auto-discovery engine, or the backend endpoint may be unavailable. Please try again in a moment.`
        };
    }
    
    // Handle "already whitelisted" case in success response
    if (!result?.error && result?.message && 
        (result.message.toLowerCase().includes('already') || 
         result.message.toLowerCase().includes('whitelisted'))) {
        return {
            success: true,
            message: result.message,
            alreadyWhitelisted: true
        };
    }
    
    // Handle "already whitelisted" case in error response
    if (result?.error && result?.detail) {
        const errorDetail = result.detail.toLowerCase();
        if (errorDetail.includes('already') && errorDetail.includes('whitelist')) {
            return {
                error: true,
                status: result.status || 400,
                detail: result.detail,
                alreadyWhitelisted: true
            };
        }
    }
    
    return result;
}

/**
 * Remove a symbol from auto-discovery
 * @param {string} symbol - Trading symbol (e.g., 'BTCUSDT')
 * @returns {Promise<Object|null>} Response data
 */
export async function removeFromDiscovery(symbol) {
    // Validate symbol format
    const validation = validateSymbolFormat(symbol);
    if (!validation.valid) {
        return { error: true, status: 400, detail: validation.error };
    }
    
    return await apiFetch(`/auto-discovery/remove/${symbol}`, { method: 'POST' });
}

/**
 * Fetch budget allocation from auto-discovery status
 * @returns {Promise<Object|null>} Budget allocation data
 */
export async function fetchBudgetAllocation() {
    const status = await apiFetch('/auto-discovery/status');
    if (status?.error) return null;
    return status?.budget_allocation || null;
}

/**
 * Check authorization/hive status
 * @returns {Promise<Object|null>} Authorization status with shape:
 *   { ok: boolean, current_user: string, beta_rat: boolean, is_authorized: boolean, 
 *     authorization_method: string|null, whitelist: string[], blacklist: string[] }
 */
export async function fetchHiveStatus() {
    return await apiFetch('/stream/hive/status');
}

/**
 * Add user to whitelist
 * @param {string} username - Username to add
 * @returns {Promise<Object|null>} Response data with shape:
 *   { ok: boolean, message: string, whitelist: string[] }
 */
export async function addHiveAlly(username) {
    if (!username || typeof username !== 'string' || username.trim().length === 0) {
        return { error: true, status: 400, detail: 'Username must be a non-empty string' };
    }
    
    return await apiFetch('/stream/hive/add-ally', {
        method: 'POST',
        body: JSON.stringify({ username: username.trim() })
    });
}

/**
 * Remove user from whitelist
 * @param {string} username - Username to remove
 * @returns {Promise<Object|null>} Response data with shape:
 *   { ok: boolean, message: string, whitelist: string[] }
 */
export async function revokeHiveAlly(username) {
    if (!username || typeof username !== 'string' || username.trim().length === 0) {
        return { error: true, status: 400, detail: 'Username must be a non-empty string' };
    }
    
    return await apiFetch('/stream/hive/revoke-ally', {
        method: 'POST',
        body: JSON.stringify({ username: username.trim() })
    });
}

/**
 * Get system configuration (API keys, tokens, etc.)
 * Uses /api/dashboard/status as the config endpoint doesn't exist
 * @returns {Promise<Object|null>} Configuration object
 */
export async function fetchSystemConfig() {
    // Use dashboard/status endpoint since /api/config doesn't exist
    const status = await apiFetch('/dashboard/status');
    if (status && !status.error) {
        return status;
    }
    // Fallback to trading/config if available
    const tradingConfig = await apiFetch('/trading/config');
    return tradingConfig;
}

/**
 * Update system configuration (API keys, tokens, etc.)
 * @param {Object} config - Configuration object with key-value pairs
 * @returns {Promise<Object|null>} Response data
 */
export async function updateSystemConfig(config) {
    if (!config || typeof config !== 'object') {
        return { error: true, status: 400, detail: 'Config must be an object' };
    }
    
    return await apiFetch('/config', {
        method: 'POST',
        body: JSON.stringify(config)
    });
}

/**
 * Place order from opportunity
 * Tries ID-based endpoint first if opportunity ID exists, falls back to full data endpoint
 * @param {Object} opportunity - Full opportunity object (or object with ID and allocation)
 * @param {boolean} autoExecute - Auto-execute when conditions met
 * @returns {Promise<Object|null>} Order placement response
 */
export async function placeOpportunityOrder(opportunity, autoExecute = false) {
    
    const opportunityId = opportunity?.id;
    
    // Try ID-based endpoint first if ID exists
    if (opportunityId) {
        // Note: Cache miss is handled by fallback to full data endpoint
        // The ID-based endpoint will return 404 if opportunity not found in backend cache
        // This is expected behavior and triggers automatic fallback
        try {
            const params = new URLSearchParams();
            if (autoExecute) params.append('auto_execute', 'true');
            const queryString = params.toString();
            const endpoint = queryString 
                ? `/opportunities/${opportunityId}/place-order?${queryString}`
                : `/opportunities/${opportunityId}/place-order`;
            
            // Send only allocation data if provided, otherwise empty body
            const requestBody = opportunity.allocation 
                ? JSON.stringify({ allocation: opportunity.allocation })
                : '{}';
            
            const result = await apiFetch(endpoint, {
                method: 'POST',
                body: requestBody
            });
            
            // If successful, return result
            if (!result?.error) {
                return result;
            }
            
            // If error is "not found" or 404, fall through to full data endpoint
            // Other errors (5xx, network) also fall through for reliability
            if (result.status === 404 || result.detail?.includes('not found') || result.detail?.includes('does not exist')) {
                console.log('[api] Opportunity not found in cache, falling back to full data endpoint');
            } else {
                // For other errors (5xx, validation), still try fallback for reliability
                console.log('[api] ID-based endpoint returned error, falling back to full data endpoint:', result.detail || result.error);
            }
        } catch (err) {
            // Network errors or other exceptions - fall through to full data endpoint
            console.log('[api] ID-based endpoint failed, falling back to full data endpoint:', err.message);
        }
    }
    
    // Fallback to full data endpoint (original behavior)
    const params = new URLSearchParams();
    if (autoExecute) params.append('auto_execute', 'true');
    const queryString = params.toString();
    const endpoint = queryString 
        ? `/opportunities/place-order?${queryString}`
        : '/opportunities/place-order';
    
    const requestBody = JSON.stringify(opportunity);
    const result = await apiFetch(endpoint, { 
        method: 'POST',
        body: requestBody
    });
    
    // Enhanced error message extraction for better user experience
    if (result?.error) {
        const errorDetail = result.detail || result.error || 'Failed to place order';
        let userFriendlyMessage = errorDetail;
        
        // Extract and enhance common error messages
        if (errorDetail.includes('Insufficient funds') || errorDetail.includes('insufficient')) {
            // Backend already provides detailed message with available/requested amounts
            userFriendlyMessage = errorDetail;
        } else if (errorDetail.includes('Invalid allocation source') || errorDetail.includes('invalid allocation')) {
            // Backend already provides valid sources list
            userFriendlyMessage = errorDetail;
        } else if (errorDetail.includes('Reserve pool allocation requires')) {
            // Backend already provides confirmation requirement
            userFriendlyMessage = errorDetail;
        } else if (errorDetail.includes('not found') || errorDetail.includes('does not exist')) {
            userFriendlyMessage = `Order placement failed: ${errorDetail}. Please refresh the opportunities list and try again.`;
        } else if (errorDetail.includes('timeout') || errorDetail.includes('Timeout')) {
            userFriendlyMessage = `Order placement timed out. The request was retried but still failed. Please check your connection and try again.`;
        } else if (errorDetail.includes('Network error') || errorDetail.includes('network')) {
            userFriendlyMessage = `Network error: Unable to connect to backend. Please check your connection and try again.`;
        }
        
        // Return consistent error format with enhanced message
        return {
            error: true,
            status: result.status || 500,
            detail: userFriendlyMessage
        };
    }
    
    // Success - return result as-is (already has consistent format from apiFetch)
    return result;
}

/**
 * Get order status for an opportunity
 * @param {string} opportunityId - Opportunity ID
 * @returns {Promise<Object|null>} Order status data (includes allocation if available)
 */
export async function getOpportunityOrderStatus(opportunityId) {
    return await apiFetch(`/opportunities/${opportunityId}/order-status`);
}

/**
 * Fetch upcoming opportunities (with entry windows in the future, no active orders)
 * @returns {Promise<Array>} Array of upcoming opportunity objects
 */
export async function fetchUpcomingTrades() {
    try {
        const symbols = await fetchSymbolOpportunities()
        if (!symbols || !Array.isArray(symbols)) {
            console.log('[api] fetchUpcomingTrades: No symbols data or not an array')
            return []
        }
        
        const upcomingTrades = []
        const now = new Date()
        
        symbols.forEach(symbol => {
            if (symbol.opportunities && Array.isArray(symbol.opportunities)) {
                symbol.opportunities.forEach(opp => {
                    // Only include opportunities with no active order
                    const hasActiveOrder = opp.order_status && 
                        ['pending', 'active', 'filled'].includes(opp.order_status)
                    
                    if (hasActiveOrder) return // Skip if already has active order
                    
                    // Check for entry window start time
                    let entryStart = null
                    if (opp.entry_time_window?.start) {
                        entryStart = new Date(opp.entry_time_window.start)
                    } else if (opp.entry_window_start) {
                        entryStart = new Date(opp.entry_window_start)
                    }
                    
                    // Also check expires_at as fallback for opportunities without explicit entry windows
                    let expiresAt = null
                    if (opp.expires_at) {
                        try {
                            expiresAt = new Date(opp.expires_at)
                        } catch (e) {
                            console.warn('[api] Invalid expires_at date:', opp.expires_at)
                        }
                    }
                    
                    // If entry start is in the future, it's upcoming
                    // OR if entry has started but it hasn't expired yet, it's still an active opportunity
                    // OR if expires_at is in the future and no entry window, use that
                    // OR if no entry window but opportunity is still valid (not expired)
                    const isUpcoming = (entryStart && !isNaN(entryStart.getTime()) && entryStart > now) ||
                                      (entryStart && !isNaN(entryStart.getTime()) && entryStart <= now && expiresAt && !isNaN(expiresAt.getTime()) && expiresAt > now) ||
                                      (!entryStart && expiresAt && !isNaN(expiresAt.getTime()) && expiresAt > now) ||
                                      (!entryStart && !expiresAt && opp.id) // Show opportunities without time windows as "upcoming"
                    
                    if (isUpcoming) {
                        // Use entry start, expires_at, or current time + 1 hour as fallback
                        let startTime = entryStart || expiresAt
                        if (!startTime) {
                            // If no time window, set to 1 hour from now as placeholder
                            startTime = new Date(now.getTime() + 3600000)
                        }
                        
                        upcomingTrades.push({
                            opportunityId: opp.id,
                            symbol: opp.symbol || symbol.symbol,
                            entryStart: startTime.toISOString(), // Store as ISO string for serialization
                            entryEnd: opp.entry_time_window?.end || opp.entry_window_end || opp.expires_at,
                            opportunityType: opp.opportunity_type || opp.direction,
                            confidence: opp.confidence,
                            targetPrice: opp.target_price,
                            potentialProfit: opp.potential_profit_percent
                        })
                    }
                })
            }
        })
        
        console.log(`[api] fetchUpcomingTrades: Found ${upcomingTrades.length} upcoming trades`)
        
        // Sort by entry start time (soonest first)
        upcomingTrades.sort((a, b) => new Date(a.entryStart).getTime() - new Date(b.entryStart).getTime())
        
        return upcomingTrades
    } catch (error) {
        console.error('[api] Failed to fetch upcoming trades:', error)
        return []
    }
}

/**
 * Fetch active orders (pending, active, filled) from opportunities
 * @returns {Promise<Array>} Array of active order objects
 */
export async function fetchActiveOrders() {
    try {
        const symbols = await fetchSymbolOpportunities()
        if (!symbols || !Array.isArray(symbols)) {
            return []
        }
        
        const activeOrders = []
        const activeStatuses = ['pending', 'active', 'filled']
        
        symbols.forEach(symbol => {
            if (symbol.opportunities && Array.isArray(symbol.opportunities)) {
                symbol.opportunities.forEach(opp => {
                    if (opp.id && opp.order_status && activeStatuses.includes(opp.order_status)) {
                        activeOrders.push({
                            opportunityId: opp.id,
                            symbol: opp.symbol || symbol.symbol,
                            status: opp.order_status,
                            allocation: null // Will be loaded separately
                        })
                    }
                })
            }
        })
        
        return activeOrders
    } catch (error) {
        console.error('[api] Failed to fetch active orders:', error)
        return []
    }
}

/**
 * Wait for orders to complete by polling their status
 * @param {Array<string>} opportunityIds - Array of opportunity IDs to wait for
 * @param {Function} onProgress - Callback function called with progress updates
 * @param {number} pollInterval - Polling interval in milliseconds (default: 5000)
 * @param {number} maxWaitTime - Maximum wait time in milliseconds (default: 3600000 = 1 hour)
 * @returns {Promise<Object>} Completion status with completed and pending arrays
 */
export async function waitForOrdersCompletion(opportunityIds, onProgress = null, pollInterval = 5000, maxWaitTime = 3600000) {
    const startTime = Date.now()
    const completed = []
    const pending = [...opportunityIds]
    const finalStatuses = ['completed', 'cancelled']
    
    while (pending.length > 0 && (Date.now() - startTime) < maxWaitTime) {
        // Check each pending order
        const checkPromises = pending.map(async (id) => {
            try {
                const status = await getOpportunityOrderStatus(id)
                if (status && status.order_status && finalStatuses.includes(status.order_status)) {
                    return { id, status: status.order_status, completed: true }
                }
                return { id, status: status?.order_status || 'unknown', completed: false }
            } catch (error) {
                console.error(`[api] Failed to check order status for ${id}:`, error)
                return { id, status: 'error', completed: false }
            }
        })
        
        const results = await Promise.all(checkPromises)
        
        // Move completed orders
        results.forEach(result => {
            if (result.completed) {
                const index = pending.indexOf(result.id)
                if (index > -1) {
                    pending.splice(index, 1)
                    completed.push(result.id)
                }
            }
        })
        
        // Call progress callback
        if (onProgress) {
            onProgress({
                completed: completed.length,
                total: opportunityIds.length,
                pending: pending.length,
                completedIds: [...completed],
                pendingIds: [...pending]
            })
        }
        
        // If still pending, wait before next poll
        if (pending.length > 0) {
            await new Promise(resolve => setTimeout(resolve, pollInterval))
        }
    }
    
    return {
        completed: completed,
        pending: pending,
        timedOut: pending.length > 0,
        elapsedTime: Date.now() - startTime
    }
}

/**
 * Reallocate funds from manual pools to autopilot (auto_discovery)
 * @param {Array<string>} pools - Pools to reallocate from (default: ['trading_pool', 'whitelist', 'reserve'])
 * @returns {Promise<Object|null>} Reallocation results
 */
export async function reallocateToAutopilot(pools = ['trading_pool', 'whitelist', 'reserve']) {
    try {
        return await apiFetch('/wallet/budget/reallocate-to-autopilot', {
            method: 'POST',
            body: JSON.stringify({ pools })
        })
    } catch (error) {
        console.error('[api] Failed to reallocate to autopilot:', error)
        return null
    }
}

/**
 * Format currency value
 * @param {number} value - Numeric value
 * @returns {string} Formatted currency string
 */
export function formatCurrency(value) {
    if (value === null || value === undefined) return '--';
    const sign = value >= 0 ? '+' : '';
    return `${sign}$${value.toFixed(2)}`;
}

/**
 * Format percentage value
 * @param {number} value - Decimal value (0-1)
 * @param {number} decimals - Number of decimal places
 * @returns {string} Formatted percentage string
 */
export function formatPercentage(value, decimals = 1) {
    if (value === null || value === undefined) return '--';
    return `${(value * 100).toFixed(decimals)}%`;
}

/**
 * Format number value
 * @param {number} value - Numeric value
 * @param {number} decimals - Number of decimal places
 * @returns {string} Formatted number string
 */
export function formatNumber(value, decimals = 0) {
    if (value === null || value === undefined) return '--';
    return value.toFixed(decimals);
}

/**
 * Format time duration
 * @param {number} seconds - Duration in seconds
 * @returns {string} Formatted duration string
 */
export function formatDuration(seconds) {
    if (!seconds || seconds < 0) return '0s';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
        return `${hours}h ${minutes}m`;
    } else if (minutes > 0) {
        return `${minutes}m ${secs}s`;
    } else {
        return `${secs}s`;
    }
}

/**
 * Fetch recent system/backend logs
 * @param {number} lines - Number of lines to retrieve
 * @returns {Promise<Object|null>} Logs response
 */
export async function fetchRecentLogs(lines = 150) {
    return await apiFetch(`/debug/logs?lines=${lines}`);
}

// Export API base for components that need it
export { API_BASE };


