/**
 * Main Application Router
 * Hash-based routing for single-page application
 */

// Route configuration
const routes = {
    'dashboard': () => import('./views/dashboard.js'),
    'chartview': () => import('./views/chartview.js'),
    'opportunities': () => import('./views/opportunities.js'),
    'scanner': () => import('./views/scanner.js'),
    'analytics': () => import('./views/analytics.js'),
    'prophecy': () => import('./views/prophecy.js'),
    'risk': () => import('./views/risk.js'),
    'execution': () => import('./views/execution.js'),
    'creative': () => import('./views/creative.js')
};

// Current view state
let currentView = null;
let currentViewModule = null;
let viewContainer = null;

/**
 * Parse hash route and parameters
 * @param {string} hash - Hash string (e.g., "#chartview?symbol=BTCUSDT")
 * @returns {Object} { route, params }
 */
function parseRoute(hash) {
    if (!hash || hash === '#') {
        return { route: 'dashboard', params: {} };
    }
    
    // Remove # and split route from params
    const [routePart, queryPart] = hash.substring(1).split('?');
    const route = routePart || 'dashboard';
    
    // Parse query parameters
    const params = {};
    if (queryPart) {
        const searchParams = new URLSearchParams(queryPart);
        for (const [key, value] of searchParams.entries()) {
            params[key] = value;
        }
    }
    
    return { route, params };
}

/**
 * Navigate to a route
 * @param {string} route - Route name
 * @param {Object} params - Query parameters
 */
function navigateTo(route, params = {}) {
    let hash = `#${route}`;
    if (Object.keys(params).length > 0) {
        const queryString = new URLSearchParams(params).toString();
        hash += `?${queryString}`;
    }
    window.location.hash = hash;
}

/**
 * Cleanup current view
 */
async function cleanupCurrentView() {
    if (currentView && currentViewModule && typeof currentViewModule.destroy === 'function') {
        try {
            await currentViewModule.destroy();
        } catch (error) {
            console.error('[Router] Error destroying view:', error);
        }
    }
    
    // Clear container
    if (viewContainer) {
        viewContainer.innerHTML = '';
    }
    
    currentView = null;
    currentViewModule = null;
}

/**
 * Load and render a view
 * @param {string} route - Route name
 * @param {Object} params - Route parameters
 */
async function loadView(route, params = {}) {
    // Get view container (may not be ready on first call)
    if (!viewContainer) {
        viewContainer = document.getElementById('view-container');
    }
    
    if (!viewContainer) {
        console.error('[Router] View container not found');
        return;
    }
    
    // Cleanup previous view
    await cleanupCurrentView();
    
    // Check if route exists
    if (!routes[route]) {
        console.warn(`[Router] Unknown route: ${route}, redirecting to dashboard`);
        navigateTo('dashboard');
        return;
    }
    
    try {
        // Load view module
        const module = await routes[route]();
        const viewModule = module.default || module;
        
        if (!viewModule || typeof viewModule.init !== 'function') {
            throw new Error(`View module ${route} does not export an init function`);
        }
        
        // Initialize view
        currentView = route;
        currentViewModule = viewModule;
        
        await viewModule.init(viewContainer, params);
        
        // Update active navigation
        updateActiveNav(route);
        
        console.log(`[Router] Loaded view: ${route}`, params);
    } catch (error) {
        console.error(`[Router] Error loading view ${route}:`, error);
        viewContainer.innerHTML = `
            <div style="padding: 40px; text-align: center; color: #f87171;">
                <h2>Error Loading View</h2>
                <p>Failed to load ${route}: ${error.message}</p>
                <button onclick="window.location.hash='#dashboard'" style="margin-top: 20px; padding: 10px 20px; background: #4ade80; color: #000; border: none; border-radius: 4px; cursor: pointer;">
                    Go to Dashboard
                </button>
            </div>
        `;
    }
}

/**
 * Update active navigation link
 * @param {string} route - Active route
 */
function updateActiveNav(route) {
    const navLinks = document.querySelectorAll('.nav a[data-route]');
    navLinks.forEach(link => {
        const linkRoute = link.getAttribute('data-route');
        if (linkRoute === route) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

/**
 * Handle hash change
 */
function handleHashChange() {
    const hash = window.location.hash;
    const { route, params } = parseRoute(hash);
    loadView(route, params);
}

/**
 * Initialize router
 */
function initRouter() {
    // Handle initial load
    if (window.location.hash) {
        handleHashChange();
    } else {
        // Default to dashboard
        navigateTo('dashboard');
    }
    
    // Listen for hash changes
    window.addEventListener('hashchange', handleHashChange);
    
    console.log('[Router] Initialized');
}

// Export for use in navigation.js
window.router = {
    navigateTo,
    getCurrentRoute: () => currentView,
    getCurrentParams: () => {
        const { params } = parseRoute(window.location.hash);
        return params;
    }
};

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initRouter);
} else {
    initRouter();
}

