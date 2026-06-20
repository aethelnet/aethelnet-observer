/**
 * ChartView Module
 * Professional trading chart with Control Deck, predictions, PROPHECY markers, and bounds checking
 * Dynamically loads the full chartview implementation
 */

let chartviewScript = null;
let chartviewStyles = null;
let chartviewState = {
    chart: null,
    intervals: [],
    timeouts: [],
    series: [],
    markers: [],
    cleanup: []
};

/**
 * Load ControlSlider component
 */
async function loadControlSlider() {
    if (window.ControlSlider) return; // Already loaded
    
    try {
        const script = document.createElement('script');
        script.src = './components/ControlSlider.js';
        script.type = 'text/javascript';
        await new Promise((resolve, reject) => {
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    } catch (error) {
        console.warn('[ChartView] Could not load ControlSlider, continuing without it:', error);
    }
}

/**
 * Load Lightweight Charts library
 */
async function loadLightweightCharts() {
    if (window.LightweightCharts) return; // Already loaded
    
    return new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = 'https://unpkg.com/lightweight-charts@4.1.0/dist/lightweight-charts.standalone.production.js';
        script.type = 'text/javascript';
        script.onload = resolve;
        script.onerror = reject;
        document.head.appendChild(script);
    });
}

/**
 * Initialize chartview view
 * @param {HTMLElement} container - Container element to render into
 * @param {Object} params - Route parameters (symbol, showPredictions, showProphecy, etc.)
 */
async function init(container, params = {}) {
    console.log('[ChartView] Initializing...', params);
    
    // Load dependencies
    await Promise.all([
        loadLightweightCharts(),
        loadControlSlider()
    ]);
    
    // Fetch the chartview HTML to extract structure and styles
    try {
        const response = await fetch('./chartview/index.html');
        const html = await response.text();
        
        // Extract styles (between <style> tags)
        const styleMatch = html.match(/<style>([\s\S]*?)<\/style>/);
        if (styleMatch) {
            const styleEl = document.createElement('style');
            styleEl.textContent = styleMatch[1];
            document.head.appendChild(styleEl);
            chartviewStyles = styleEl;
        }
        
        // Extract body content (between <body> and </body>)
        const bodyMatch = html.match(/<body>([\s\S]*?)<\/body>/);
        if (bodyMatch) {
            // Create a temporary container to parse HTML
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = bodyMatch[1];
            
            // Extract the #app div content
            const appDiv = tempDiv.querySelector('#app');
            if (appDiv) {
                // Update navigation links to use hash-based routing
                const navLinks = appDiv.querySelectorAll('.nav a');
                navLinks.forEach(link => {
                    const href = link.getAttribute('href');
                    if (href) {
                        // Convert port-based URLs to hash-based
                        if (href.includes('localhost:1420')) {
                            link.setAttribute('href', '#dashboard');
                            link.removeAttribute('target');
                        } else if (href.includes('localhost:1429')) {
                            link.setAttribute('href', '#scanner');
                            link.removeAttribute('target');
                        } else if (href.includes('localhost:1427')) {
                            link.setAttribute('href', '#opportunities');
                            link.removeAttribute('target');
                        } else if (href.includes('localhost:1428')) {
                            link.setAttribute('href', '#prophecy');
                            link.removeAttribute('target');
                        } else if (href.includes('localhost:1424')) {
                            link.setAttribute('href', '#analytics');
                            link.removeAttribute('target');
                        }
                    }
                });
                
                container.innerHTML = appDiv.innerHTML;
            } else {
                container.innerHTML = bodyMatch[1];
            }
        }
        
        // Extract and execute JavaScript (between <script> tags in body)
        const scriptMatches = html.matchAll(/<script>([\s\S]*?)<\/script>/g);
        for (const match of scriptMatches) {
            const scriptContent = match[1];
            
            // Skip if it's the router or other module scripts
            if (scriptContent.includes('export') || scriptContent.includes('import ')) {
                continue;
            }
            
            // Patch URL parameter handling to use router params
            let patchedScript = scriptContent;
            
            // Replace URLSearchParams initialization with router params
            if (Object.keys(params).length > 0) {
                const paramsString = Object.entries(params)
                    .map(([key, value]) => `${key}=${encodeURIComponent(value)}`)
                    .join('&');
                patchedScript = patchedScript.replace(
                    /const urlParams = new URLSearchParams\(window\.location\.search\);/g,
                    `// Patched: Use router params instead of window.location.search
                    const urlParams = new URLSearchParams('${paramsString}');`
                );
            } else {
                // If no params, use empty search
                patchedScript = patchedScript.replace(
                    /const urlParams = new URLSearchParams\(window\.location\.search\);/g,
                    `// Patched: Use router params instead of window.location.search
                    const urlParams = new URLSearchParams();`
                );
            }
            
            // Initialize state container for cleanup tracking
            if (!window.__chartviewState) {
                window.__chartviewState = {
                    chart: null,
                    intervals: [],
                    cleanup: []
                };
            }
            
            // Wrap setInterval calls to track them
            patchedScript = patchedScript.replace(
                /(\w+)\s*=\s*setInterval\(/g,
                (match, varName) => {
                    return `${varName} = setInterval(`;
                }
            );
            
            // Track intervals by wrapping setInterval
            const originalSetInterval = window.setInterval;
            window.setInterval = function(...args) {
                const id = originalSetInterval.apply(window, args);
                if (window.__chartviewState) {
                    window.__chartviewState.intervals.push(id);
                }
                return id;
            };
            
            // Create and execute script
            const scriptFunc = new Function(patchedScript);
            scriptFunc();
            
            // Try to find chart instance by checking the container
            const chartEl = container.querySelector('#chart');
            if (chartEl && chartEl._chart) {
                window.__chartviewState.chart = chartEl._chart;
            }
            
            // Store cleanup reference
            chartviewScript = { execute: scriptFunc };
            
            // Restore original setInterval
            window.setInterval = originalSetInterval;
        }
        
        console.log('[ChartView] Initialized');
    } catch (error) {
        console.error('[ChartView] Failed to load chartview:', error);
        container.innerHTML = `
            <div style="padding: 40px; text-align: center; color: #f87171;">
                <h2>Error Loading ChartView</h2>
                <p>Failed to load chartview: ${error.message}</p>
                <button onclick="window.location.hash='#dashboard'" style="margin-top: 20px; padding: 10px 20px; background: #4ade80; color: #000; border: none; border-radius: 4px; cursor: pointer;">
                    Go to Dashboard
                </button>
            </div>
        `;
    }
}

/**
 * Cleanup chartview view
 */
async function destroy() {
    console.log('[ChartView] Destroying...');
    
    // Access state container
    const state = window.__chartviewState;
    
    if (state) {
        // Clear all tracked intervals
        if (state.intervals && state.intervals.length > 0) {
            state.intervals.forEach(id => {
                try {
                    clearInterval(id);
                } catch (e) {
                    console.warn('[ChartView] Error clearing interval:', e);
                }
            });
            state.intervals = [];
        }
        
        // Try to find and destroy chart
        const chartEl = document.querySelector('#chart');
        if (chartEl) {
            // Try to access chart via Lightweight Charts API
            try {
                // Chart instances are stored on the container element
                if (chartEl._chart) {
                    chartEl._chart.remove();
                }
            } catch (e) {
                // Chart may not be accessible this way
            }
        }
        
        // Destroy chart if stored in state
        if (state.chart) {
            try {
                state.chart.remove();
            } catch (e) {
                console.warn('[ChartView] Error removing chart:', e);
            }
            state.chart = null;
        }
        
        // Clear all cleanup functions
        if (state.cleanup && state.cleanup.length > 0) {
            state.cleanup.forEach(fn => {
                try {
                    fn();
                } catch (e) {
                    console.warn('[ChartView] Error in cleanup function:', e);
                }
            });
            state.cleanup = [];
        }
        
        // Remove state from window
        delete window.__chartviewState;
    }
    
    // Remove injected styles
    if (chartviewStyles && chartviewStyles.parentNode) {
        chartviewStyles.parentNode.removeChild(chartviewStyles);
        chartviewStyles = null;
    }
    
    console.log('[ChartView] Destroyed');
}

// Export module
export default {
    init,
    destroy
};
