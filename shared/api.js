/**
 * Shared API Client
 * Centralized API utilities for all components and views
 */

const API_BASE = 'http://localhost:8000/api';

/**
 * Generic API fetch with error handling
 * @param {string} endpoint - API endpoint (without /api prefix)
 * @param {Object} options - Fetch options
 * @returns {Promise<Object|null>} Response data or null on error
 */
async function apiFetch(endpoint, options = {}) {
    try {
        const url = `${API_BASE}${endpoint}`;
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error(`[API] Failed to fetch ${endpoint}:`, error);
        return null;
    }
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

// Expose helpers to global scope for legacy templates that call them directly (e.g. Vue templates)
if (typeof window !== 'undefined') {
    try {
        window.formatCurrency = formatCurrency;
        window.formatPercentage = formatPercentage;
        window.formatNumber = formatNumber;
        window.formatDuration = formatDuration;
    } catch (e) {
        // If any of the helper functions aren't defined for some reason, don't block execution.
        // This keeps compatibility with environments that only import a subset.
        // eslint-disable-next-line no-console
        console.warn('[API] Failed to attach helper functions to window', e);
    }
}

// Export API base for components that need it
export { API_BASE };



