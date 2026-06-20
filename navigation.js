// Navigation helper for hash-based routing
// Updated to use router instead of port-based URLs

/**
 * Navigate to a view using hash-based routing
 * @param {string} viewName - Name of the view (e.g., 'chartview', 'dashboard')
 * @param {Object} params - Query parameters to append to the hash
 */
function navigateToView(viewName, params = {}) {
    if (window.router && window.router.navigateTo) {
        window.router.navigateTo(viewName, params);
    } else {
        // Fallback: use hash directly
        let hash = `#${viewName}`;
        if (Object.keys(params).length > 0) {
            const queryString = new URLSearchParams(params).toString();
            hash += `?${queryString}`;
        }
        window.location.hash = hash;
    }
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
    navigateToView('chartview', params);
}

/**
 * Navigate to Opportunities view with optional symbol filter
 * @param {string|null} symbol - Trading pair symbol to filter by
 */
function navigateToOpportunities(symbol = null) {
    const params = {};
    if (symbol) params.symbol = symbol;
    navigateToView('opportunities', params);
}

/**
 * Navigate to PROPHECY view with optional symbol filter
 * @param {string|null} symbol - Trading pair symbol to filter by
 */
function navigateToProphecy(symbol = null) {
    const params = {};
    if (symbol) params.symbol = symbol;
    navigateToView('prophecy', params);
}

/**
 * Navigate to Scanner view
 */
function navigateToScanner() {
    navigateToView('scanner');
}

/**
 * Navigate to Dashboard
 */
function navigateToDashboard() {
    navigateToView('dashboard');
}

/**
 * Navigate to Analytics view
 */
function navigateToAnalytics() {
    navigateToView('analytics');
}

/**
 * Navigate to Risk Management view
 */
function navigateToRisk() {
    navigateToView('risk');
}

/**
 * Navigate to Execution Monitor view
 */
function navigateToExecution() {
    navigateToView('execution');
}

/**
 * Navigate to Creative view
 */
function navigateToCreative() {
    navigateToView('creative');
}

/**
 * Generate navigation links HTML (hash-based)
 * @param {string|null} currentView - Current view name to mark as active
 * @returns {string} HTML string with navigation links
 */
function generateNavLinks(currentView = null) {
    const links = [
        { name: 'Dashboard', view: 'dashboard' },
        { name: 'Chartview', view: 'chartview' },
        { name: 'Scanner', view: 'scanner' },
        { name: 'Opportunities', view: 'opportunities' },
        { name: 'PROPHECY', view: 'prophecy' },
        { name: 'Analytics', view: 'analytics' }
    ];
    
    return links.map(link => {
        const hash = `#${link.view}`;
        const isActive = currentView && currentView.toLowerCase() === link.view.toLowerCase();
        return `<a href="${hash}" ${isActive ? 'class="active"' : ''} data-route="${link.view}" title="Navigate to ${link.name}">${link.name}</a>`;
    }).join('\n');
}

