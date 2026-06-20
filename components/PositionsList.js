/**
 * PositionsList Component
 * Displays open positions in a grid
 * Web Component: <component-positions-list>
 */

import { fetchPositions } from '../shared/api.js';
import { formatCurrency, formatDuration } from '../shared/api.js';
import { setupWebSocketListener } from '../shared/websocket.js';

class PositionsListComponent extends HTMLElement {
    constructor() {
        super();
        this.data = [];
        this.unsubscribeWebSocket = null;
    }
    
    connectedCallback() {
        this.render();
        this.fetchData();
        this.setupWebSocket();
        
        // Poll every 5 seconds as fallback
        this.pollInterval = setInterval(() => this.fetchData(), 5000);
    }
    
    disconnectedCallback() {
        if (this.unsubscribeWebSocket) {
            this.unsubscribeWebSocket();
        }
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
        }
    }
    
    render() {
        if (!this.data || this.data.length === 0) {
            this.innerHTML = '<p style="color: #888;">No open positions</p>';
            return;
        }
        
        this.innerHTML = `
            <div class="component-positions-list">
                <div style="display: grid; gap: 12px;">
                    ${this.data.map(pos => `
                        <div class="position-card" style="background: rgba(20, 20, 30, 0.8); border: 1px solid rgba(74, 222, 128, 0.4); border-radius: 8px; padding: 12px; transition: all 0.2s;">
                            <div class="position-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                <span class="symbol" style="font-weight: bold; font-size: 16px;">${pos.symbol || 'N/A'}</span>
                                <span class="side ${pos.side?.toLowerCase()}" style="padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; text-transform: uppercase;
                                    ${pos.side === 'LONG' ? 'background: rgba(74, 222, 128, 0.2); color: #4ade80; border: 1px solid rgba(74, 222, 128, 0.4);' : 'background: rgba(248, 113, 113, 0.2); color: #f87171; border: 1px solid rgba(248, 113, 113, 0.4);'}">
                                    ${pos.side || 'N/A'}
                                </span>
                            </div>
                            <div class="position-metrics" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; font-size: 12px;">
                                <div class="metric">
                                    <span class="label" style="color: #888;">Entry:</span>
                                    <span class="value" style="margin-left: 8px;">$${parseFloat(pos.entry_price || 0).toFixed(2)}</span>
                                </div>
                                <div class="metric">
                                    <span class="label" style="color: #888;">Current:</span>
                                    <span class="value" style="margin-left: 8px;">$${parseFloat(pos.current_price || 0).toFixed(2)}</span>
                                </div>
                                <div class="metric">
                                    <span class="label" style="color: #888;">P&L:</span>
                                    <span class="value" style="margin-left: 8px; color: ${(pos.unrealized_pnl || 0) >= 0 ? '#4ade80' : '#f87171'}; font-weight: bold;">
                                        ${formatCurrency(pos.unrealized_pnl || 0)}
                                    </span>
                                </div>
                                <div class="metric">
                                    <span class="label" style="color: #888;">Hold Time:</span>
                                    <span class="value" style="margin-left: 8px;">${formatDuration(pos.hold_time_seconds || 0)}</span>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    async fetchData() {
        try {
            const data = await fetchPositions();
            if (data) {
                this.data = data;
                this.render();
            }
        } catch (error) {
            console.error('[PositionsList] Failed to fetch data:', error);
            this.innerHTML = '<p style="color: #f87171;">Error loading positions</p>';
        }
    }
    
    setupWebSocket() {
        this.unsubscribeWebSocket = setupWebSocketListener('positions', (data) => {
            if (data.positions) {
                this.data = data.positions;
                this.render();
            }
        });
    }
    
    update(data) {
        this.data = data;
        this.render();
    }
}

customElements.define('component-positions-list', PositionsListComponent);



