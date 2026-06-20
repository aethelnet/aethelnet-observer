/**
 * SystemStatus Component
 * Displays system health and connection status
 * Web Component: <component-system-status>
 */

import { fetchFailsafeStatus, activatePanic, resumeTrading } from '../shared/api.js';
import { setupConnectionListener, isWebSocketConnected } from '../shared/websocket.js';
import { setupTransformedWebSocketListener } from '../shared/websocket-adapter.js';

class SystemStatusComponent extends HTMLElement {
    constructor() {
        super();
        this.data = null;
        this.unsubscribeWebSocket = null;
        this.statusCheckInterval = null;
    }
    
    connectedCallback() {
        this.render();
        this.fetchStatus();
        this.setupWebSocket();
        
        // Poll status every 10 seconds as fallback
        this.statusCheckInterval = setInterval(() => {
            this.fetchStatus();
        }, 10000);
    }
    
    disconnectedCallback() {
        if (this.unsubscribeWebSocket) {
            this.unsubscribeWebSocket();
        }
        if (this.statusCheckInterval) {
            clearInterval(this.statusCheckInterval);
        }
    }
    
    render() {
        const backendStatus = this.data?.backend_connected !== false ? 'connected' : 'disconnected';
        const wsStatus = isWebSocketConnected() ? 'connected' : 'disconnected';
        const tradingMode = this.data?.panic_active ? 'paused' : 'active';
        const panicMode = this.data?.panic_active ? 'active' : 'inactive';
        
        this.innerHTML = `
            <div class="component-system-status">
                <h3>System Status</h3>
                <div class="status-grid" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-top: 12px;">
                    <div class="status-item" style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0;">
                        <span class="label" style="color: #888;">Backend</span>
                        <span class="value status-${backendStatus}" style="padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; 
                            ${backendStatus === 'connected' ? 'background: rgba(74, 222, 128, 0.2); color: #4ade80;' : 'background: rgba(248, 113, 113, 0.2); color: #f87171;'}">
                            ${backendStatus === 'connected' ? 'Connected' : 'Disconnected'}
                        </span>
                    </div>
                    <div class="status-item" style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0;">
                        <span class="label" style="color: #888;">WebSocket</span>
                        <span class="value status-${wsStatus}" style="padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold;
                            ${wsStatus === 'connected' ? 'background: rgba(74, 222, 128, 0.2); color: #4ade80;' : 'background: rgba(248, 113, 113, 0.2); color: #f87171;'}">
                            ${wsStatus === 'connected' ? 'Active' : 'Inactive'}
                        </span>
                    </div>
                    <div class="status-item" style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0;">
                        <span class="label" style="color: #888;">Trading Mode</span>
                        <button class="status-toggle status-${tradingMode}" 
                                data-action="trading-toggle"
                                style="padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; border: none; cursor: pointer;
                                    ${tradingMode === 'active' ? 'background: rgba(74, 222, 128, 0.2); color: #4ade80;' : 'background: rgba(251, 191, 36, 0.2); color: #fbbf24;'}
                                    transition: all 0.2s;"
                                onmouseover="this.style.transform='scale(1.05)'; this.style.opacity='0.9';"
                                onmouseout="this.style.transform='scale(1)'; this.style.opacity='1';"
                                title="Click to toggle trading execution (${tradingMode === 'active' ? 'Pause' : 'Resume'})">
                            ${tradingMode === 'active' ? 'Active' : 'Paused'}
                        </button>
                    </div>
                    <div class="status-item" style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0;">
                        <span class="label" style="color: #888;">Panic Mode</span>
                        <span class="value status-${panicMode}" style="padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold;
                            ${panicMode === 'active' ? 'background: rgba(248, 113, 113, 0.2); color: #f87171;' : 'background: rgba(74, 222, 128, 0.2); color: #4ade80;'}">
                            ${panicMode === 'active' ? 'Active' : 'Inactive'}
                        </span>
                    </div>
                </div>
            </div>
        `;
        
        // Setup click handlers after rendering
        this.setupClickHandlers();
    }
    
    async fetchStatus() {
        try {
            const status = await fetchFailsafeStatus();
            if (status) {
                this.data = {
                    ...status,
                    backend_connected: true
                };
            } else {
                this.data = {
                    backend_connected: false,
                    panic_active: false
                };
            }
            this.render();
        } catch (error) {
            console.error('[SystemStatus] Failed to fetch status:', error);
            this.data = {
                backend_connected: false,
                panic_active: false
            };
            this.render();
        }
    }
    
    setupWebSocket() {
        // Listen for WebSocket connection changes
        const connectionUnsub = setupConnectionListener((connected) => {
            this.render(); // Re-render to update WebSocket status
        });
        
        // Listen for status updates via WebSocket (using adapter to transform backend messages)
        const statusUnsub = setupTransformedWebSocketListener('status', (data) => {
            this.data = {
                ...this.data,
                ...data,
                backend_connected: true
            };
            this.render();
        });
        
        // Listen for failsafe_status updates
        const failsafeUnsub = setupTransformedWebSocketListener('failsafe_status', (data) => {
            this.data = {
                ...this.data,
                ...data,
                backend_connected: true
            };
            this.render();
        });
        
        // Combine unsubscribe functions
        this.unsubscribeWebSocket = () => {
            if (connectionUnsub) connectionUnsub();
            if (statusUnsub) statusUnsub();
            if (failsafeUnsub) failsafeUnsub();
        };
    }
    
    setupClickHandlers() {
        const tradingToggle = this.querySelector('[data-action="trading-toggle"]');
        
        if (tradingToggle) {
            tradingToggle.addEventListener('click', () => this.handleTradingToggle());
        }
    }
    
    async handleTradingToggle() {
        const isPanic = this.data?.panic_active || false;
        const currentMode = isPanic ? 'Paused' : 'Active';
        const newMode = isPanic ? 'Active' : 'Paused';
        
        // Confirmation dialog
        const confirmed = confirm(
            `Toggle Trading Execution?\n\n` +
            `Current: ${currentMode}\n` +
            `New: ${newMode}\n\n` +
            `This will ${isPanic ? 'resume' : 'pause'} trading execution.`
        );
        
        if (!confirmed) return;
        
        // Disable button during request
        const button = this.querySelector('[data-action="trading-toggle"]');
        if (button) {
            button.disabled = true;
            button.style.opacity = '0.5';
            button.style.cursor = 'wait';
        }
        
        try {
            if (isPanic) {
                // Resume trading (enable execution)
                await resumeTrading();
                console.log('[SystemStatus] Trading execution resumed');
            } else {
                // Pause trading (disable execution)
                await activatePanic();
                console.log('[SystemStatus] Trading execution paused');
            }
            
            // Refresh status to get updated state
            await this.fetchStatus();
        } catch (error) {
            console.error('[SystemStatus] Failed to toggle trading:', error);
            alert('Failed to toggle trading execution. Check backend connection.');
        } finally {
            // Re-enable button
            if (button) {
                button.disabled = false;
                button.style.opacity = '1';
                button.style.cursor = 'pointer';
            }
        }
    }
    
    update(data) {
        this.data = data;
        this.render();
    }
}

customElements.define('component-system-status', SystemStatusComponent);

