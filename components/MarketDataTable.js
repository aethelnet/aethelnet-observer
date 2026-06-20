/**
 * MarketDataTable Component
 * Displays market data in a table format
 * Web Component: <component-market-data-table>
 */

import { fetchMarketData } from '../shared/api.js';
import { setupWebSocketListener } from '../shared/websocket.js';

class MarketDataTableComponent extends HTMLElement {
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
            this.innerHTML = '<p style="color: #888;">Loading market data...</p>';
            return;
        }
        
        this.innerHTML = `
            <div class="component-market-data-table">
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="border-bottom: 1px solid rgba(74, 222, 128, 0.4);">
                            <th style="text-align: left; padding: 10px; color: #888; font-size: 12px; font-weight: 600;">Symbol</th>
                            <th style="text-align: right; padding: 10px; color: #888; font-size: 12px; font-weight: 600;">Price</th>
                            <th style="text-align: center; padding: 10px; color: #888; font-size: 12px; font-weight: 600;">Signal</th>
                            <th style="text-align: right; padding: 10px; color: #888; font-size: 12px; font-weight: 600;">24h Change</th>
                            <th style="text-align: right; padding: 10px; color: #888; font-size: 12px; font-weight: 600;">Volume</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${this.data.map(item => `
                            <tr style="border-bottom: 1px solid rgba(255, 255, 255, 0.05); transition: background 0.2s;">
                                <td style="padding: 10px; font-size: 14px; font-weight: bold;">${item.symbol || 'N/A'}</td>
                                <td style="padding: 10px; text-align: right; font-size: 14px;">$${parseFloat(item.price || 0).toFixed(2)}</td>
                                <td style="padding: 10px; text-align: center;">
                                    <component-signal-badge signal="${item.signal_strength || 'NEUTRAL'}"></component-signal-badge>
                                </td>
                                <td style="padding: 10px; text-align: right; font-size: 14px; color: ${(item.change_24h || 0) >= 0 ? '#4ade80' : '#f87171'};">
                                    ${(item.change_24h || 0) >= 0 ? '+' : ''}${(item.change_24h || 0).toFixed(2)}%
                                </td>
                                <td style="padding: 10px; text-align: right; font-size: 14px; color: #888;">
                                    ${this.formatVolume(item.volume || 0)}
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }
    
    async fetchData() {
        try {
            const data = await fetchMarketData();
            if (data) {
                this.data = data;
                this.render();
            }
        } catch (error) {
            console.error('[MarketDataTable] Failed to fetch data:', error);
            this.innerHTML = '<p style="color: #f87171;">Error loading market data</p>';
        }
    }
    
    setupWebSocket() {
        this.unsubscribeWebSocket = setupWebSocketListener('market_data', (data) => {
            if (data.market_data) {
                this.data = data.market_data;
                this.render();
            }
        });
    }
    
    formatVolume(volume) {
        if (volume >= 1000000) {
            return `${(volume / 1000000).toFixed(2)}M`;
        } else if (volume >= 1000) {
            return `${(volume / 1000).toFixed(2)}K`;
        }
        return volume.toFixed(2);
    }
    
    update(data) {
        this.data = data;
        this.render();
    }
}

customElements.define('component-market-data-table', MarketDataTableComponent);



