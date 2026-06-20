/**
 * TradesLog Component
 * Displays recent closed trades
 * Web Component: <component-trades-log>
 * 
 * Attributes:
 * - limit: Maximum number of trades to display (default: 20)
 */

import { fetchRecentTrades } from '../shared/api.js';
import { formatCurrency, formatDuration } from '../shared/api.js';
import { setupWebSocketListener } from '../shared/websocket.js';

class TradesLogComponent extends HTMLElement {
    constructor() {
        super();
        this.data = [];
        this.limit = 20;
        this.unsubscribeWebSocket = null;
    }
    
    static get observedAttributes() {
        return ['limit'];
    }
    
    attributeChangedCallback(name, oldValue, newValue) {
        if (name === 'limit') {
            this.limit = parseInt(newValue) || 20;
            this.fetchData();
        }
    }
    
    connectedCallback() {
        this.limit = parseInt(this.getAttribute('limit')) || 20;
        this.render();
        this.fetchData();
        this.setupWebSocket();
        
        // Poll every 10 seconds as fallback
        this.pollInterval = setInterval(() => this.fetchData(), 10000);
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
            this.innerHTML = '<p style="color: #888;">No recent trades</p>';
            return;
        }
        
        this.innerHTML = `
            <div class="component-trades-log">
                <div class="trades-list" style="max-height: 400px; overflow-y: auto;">
                    ${this.data.slice(0, this.limit).map(trade => `
                        <div class="trade-item" style="padding: 12px 0; border-bottom: 1px solid rgba(255, 255, 255, 0.05); transition: background 0.2s;">
                            <div class="trade-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                                <span class="symbol" style="font-weight: bold; font-size: 16px;">${trade.symbol || 'N/A'}</span>
                                <span class="side" style="padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; text-transform: uppercase;
                                    ${trade.side === 'LONG' ? 'background: rgba(74, 222, 128, 0.2); color: #4ade80;' : 'background: rgba(248, 113, 113, 0.2); color: #f87171;'}">
                                    ${trade.side || 'N/A'}
                                </span>
                                <span class="pnl ${(trade.pnl || 0) >= 0 ? 'positive' : 'negative'}" style="font-size: 16px; font-weight: bold; color: ${(trade.pnl || 0) >= 0 ? '#4ade80' : '#f87171'};">
                                    ${formatCurrency(trade.pnl || 0)}
                                </span>
                            </div>
                            <div class="trade-details" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px; margin-top: 8px; font-size: 12px; color: #888;">
                                <span>Entry: $${parseFloat(trade.entry_price || 0).toFixed(2)}</span>
                                <span>Exit: $${parseFloat(trade.exit_price || 0).toFixed(2)}</span>
                                <span>Hold: ${formatDuration(trade.hold_time_seconds || 0)}</span>
                                <span>Time: ${this.formatTime(trade.timestamp)}</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    async fetchData() {
        try {
            const data = await fetchRecentTrades(this.limit);
            if (data) {
                this.data = data;
                this.render();
            }
        } catch (error) {
            console.error('[TradesLog] Failed to fetch data:', error);
            this.innerHTML = '<p style="color: #f87171;">Error loading trades</p>';
        }
    }
    
    setupWebSocket() {
        this.unsubscribeWebSocket = setupWebSocketListener('trades', (data) => {
            if (data.trades) {
                this.data = data.trades;
                this.render();
            }
        });
    }
    
    formatTime(timestamp) {
        if (!timestamp) return 'N/A';
        try {
            const date = new Date(timestamp);
            const now = new Date();
            const diffMs = now - date;
            const diffMins = Math.floor(diffMs / 60000);
            const diffHours = Math.floor(diffMins / 60);
            
            if (diffMins < 1) return 'Just now';
            if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
            if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
            return date.toLocaleDateString();
        } catch (e) {
            return 'N/A';
        }
    }
    
    update(data) {
        this.data = data;
        this.render();
    }
}

customElements.define('component-trades-log', TradesLogComponent);



