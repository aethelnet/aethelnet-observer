// Navigation helper for cross-port navigation
// Shared across all views to enable navigation between different ports

const VIEW_PORTS = {
    'dashboard': 1420,
    'chartview': 1423,
    'opportunities': 1427,
    'prophecy': 1428,
    'scanner': 1429,
    'analytics': 1424,
    'risk': 1425,
    'execution': 1426,
    'creative': 1421,
    'creative2': 1422,
    'infohub': 1430
};

/**
 * Get the URL for a specific view with optional query parameters
 * @param {string} viewName - Name of the view (e.g., 'chartview', 'dashboard')
 * @param {Object} params - Query parameters to append to the URL
 * @returns {string} Full URL with port number
 */
function getViewUrl(viewName, params = {}) {
    const port = VIEW_PORTS[viewName.toLowerCase()];
    if (!port) {
        console.error(`[Navigation] Unknown view: ${viewName}`);
        return '#';
    }
    
    const basePath = viewName.toLowerCase() === 'dashboard' ? 'index.html' : `${viewName.toLowerCase()}/index.html`;
    const url = `http://localhost:${port}/${basePath}`;
    
    if (Object.keys(params).length > 0) {
        const queryString = new URLSearchParams(params).toString();
        return `${url}?${queryString}`;
    }
    
    return url;
}

/**
 * Navigate to ChartView with optional symbol and layer parameters
 * @param {string|null} symbol - Trading pair symbol (e.g., 'BTCUSDT')
 * @param {boolean} showPredictions - Enable predictions layer
 * @param {boolean} showProphecy - Enable PROPHECY layer
 */
function navigateToChart(symbol = null, showPredictions = false, showProphecy = false) {
    const params = {};
    if (symbol) params.symbol = symbol;
    if (showPredictions) params.showPredictions = 'true';
    if (showProphecy) params.showProphecy = 'true';
    
    window.open(getViewUrl('chartview', params), '_blank');
}

// Make functions available globally
window.getViewUrl = getViewUrl;
window.navigateToChart = navigateToChart;



