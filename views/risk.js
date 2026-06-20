/**
 * Risk View Module
 * Risk Management Dashboard
 */

async function init(container, params = {}) {
    console.log('[Risk] Initializing...', params);
    
    try {
        const response = await fetch('./risk/index.html');
        const html = await response.text();
        
        const styleMatch = html.match(/<style>([\s\S]*?)<\/style>/);
        if (styleMatch) {
            const styleEl = document.createElement('style');
            styleEl.textContent = styleMatch[1];
            document.head.appendChild(styleEl);
        }
        
        const bodyMatch = html.match(/<body>([\s\S]*?)<\/body>/);
        if (bodyMatch) {
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = bodyMatch[1];
            
            const navLinks = tempDiv.querySelectorAll('.nav a');
            navLinks.forEach(link => {
                const href = link.getAttribute('href');
                if (href) {
                    if (href.includes('localhost:1420')) link.setAttribute('href', '#dashboard');
                    else if (href.includes('localhost:1423')) link.setAttribute('href', '#chartview');
                    else if (href.includes('localhost:1427')) link.setAttribute('href', '#opportunities');
                    else if (href.includes('localhost:1429')) link.setAttribute('href', '#scanner');
                    else if (href.includes('localhost:1424')) link.setAttribute('href', '#analytics');
                    link.removeAttribute('target');
                }
            });
            
            container.innerHTML = tempDiv.innerHTML;
        }
        
        const scriptMatches = html.matchAll(/<script>([\s\S]*?)<\/script>/g);
        for (const match of scriptMatches) {
            const scriptContent = match[1];
            if (scriptContent.includes('export') || scriptContent.includes('import ')) continue;
            const scriptFunc = new Function(scriptContent);
            scriptFunc();
        }
        
        console.log('[Risk] Initialized');
    } catch (error) {
        console.error('[Risk] Failed to load:', error);
        container.innerHTML = `<div style="padding: 40px; text-align: center; color: #f87171;"><h2>Error Loading Risk</h2><p>${error.message}</p></div>`;
    }
}

async function destroy() {
    console.log('[Risk] Destroying...');
    if (window.riskUpdateInterval) {
        clearInterval(window.riskUpdateInterval);
        window.riskUpdateInterval = null;
    }
    console.log('[Risk] Destroyed');
}

export default { init, destroy };
