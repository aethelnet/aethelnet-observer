/**
 * PnLChart Component
 * Displays P&L over time as a line chart
 * Web Component: <component-pnl-chart>
 * 
 * Requires Chart.js to be loaded
 */

import { fetchMetrics } from '../shared/api.js';
import { setupWebSocketListener } from '../shared/websocket.js';

class PnLChartComponent extends HTMLElement {
    constructor() {
        super();
        this.chart = null;
        this.data = null;
        this.timeframe = '24h';
        this.unsubscribeWebSocket = null;
    }
    
    static get observedAttributes() {
        return ['timeframe'];
    }
    
    attributeChangedCallback(name, oldValue, newValue) {
        if (name === 'timeframe') {
            this.timeframe = newValue || '24h';
            this.fetchData();
        }
    }
    
    connectedCallback() {
        this.timeframe = this.getAttribute('timeframe') || '24h';
        this.render();
        this.initChart();
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
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
    }
    
    render() {
        this.innerHTML = `
            <div class="component-pnl-chart">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                    <h3 style="font-size: 18px; margin: 0;">P&L Over Time</h3>
                    <div class="chart-controls" style="display: flex; gap: 8px;">
                        <button data-timeframe="1h" class="timeframe-btn ${this.timeframe === '1h' ? 'active' : ''}" 
                                style="padding: 6px 12px; border: 1px solid rgba(74, 222, 128, 0.4); border-radius: 4px; background: ${this.timeframe === '1h' ? 'rgba(74, 222, 128, 0.2)' : 'transparent'}; color: #4ade80; cursor: pointer; font-size: 12px;">
                            1 Hour
                        </button>
                        <button data-timeframe="24h" class="timeframe-btn ${this.timeframe === '24h' ? 'active' : ''}" 
                                style="padding: 6px 12px; border: 1px solid rgba(74, 222, 128, 0.4); border-radius: 4px; background: ${this.timeframe === '24h' ? 'rgba(74, 222, 128, 0.2)' : 'transparent'}; color: #4ade80; cursor: pointer; font-size: 12px;">
                            24 Hours
                        </button>
                        <button data-timeframe="7d" class="timeframe-btn ${this.timeframe === '7d' ? 'active' : ''}" 
                                style="padding: 6px 12px; border: 1px solid rgba(74, 222, 128, 0.4); border-radius: 4px; background: ${this.timeframe === '7d' ? 'rgba(74, 222, 128, 0.2)' : 'transparent'}; color: #4ade80; cursor: pointer; font-size: 12px;">
                            7 Days
                        </button>
                        <button data-timeframe="30d" class="timeframe-btn ${this.timeframe === '30d' ? 'active' : ''}" 
                                style="padding: 6px 12px; border: 1px solid rgba(74, 222, 128, 0.4); border-radius: 4px; background: ${this.timeframe === '30d' ? 'rgba(74, 222, 128, 0.2)' : 'transparent'}; color: #4ade80; cursor: pointer; font-size: 12px;">
                            30 Days
                        </button>
                    </div>
                </div>
                <canvas id="pnl-chart-canvas" style="max-height: 400px;"></canvas>
            </div>
        `;
        
        // Setup timeframe button handlers
        this.querySelectorAll('.timeframe-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const tf = btn.getAttribute('data-timeframe');
                this.timeframe = tf;
                this.setAttribute('timeframe', tf);
                this.render();
                this.initChart();
                this.fetchData();
            });
        });
    }
    
    initChart() {
        const canvas = this.querySelector('#pnl-chart-canvas');
        if (!canvas) return;
        
        if (typeof Chart === 'undefined') {
            console.warn('[PnLChart] Chart.js not loaded');
            return;
        }
        
        // Destroy existing chart
        if (this.chart) {
            this.chart.destroy();
        }
        
        this.chart = new Chart(canvas, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Main P&L',
                    data: [],
                    borderColor: '#4ade80',
                    backgroundColor: 'rgba(74, 222, 128, 0.1)',
                    tension: 0.4,
                    fill: true
                }, {
                    label: 'Shadow P&L',
                    data: [],
                    borderColor: '#fbbf24',
                    backgroundColor: 'rgba(251, 191, 36, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        labels: { color: '#fff' }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    x: { 
                        ticks: { color: '#888' }, 
                        grid: { color: '#222' } 
                    },
                    y: { 
                        ticks: { 
                            color: '#888',
                            callback: function(value) {
                                return '$' + value.toFixed(2);
                            }
                        }, 
                        grid: { color: '#222' } 
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
        });
    }
    
    async fetchData() {
        try {
            const metrics = await fetchMetrics();
            if (!metrics) return;
            
            this.data = metrics;
            
            // Update chart with historical data if available
            if (this.chart && metrics.pnl_history) {
                const labels = metrics.pnl_history.map((_, i) => {
                    // Create time labels based on timeframe
                    const now = new Date();
                    const time = new Date(now.getTime() - (metrics.pnl_history.length - i) * 60000); // Assume 1 min intervals
                    return time.toLocaleTimeString();
                });
                
                this.chart.data.labels = labels;
                this.chart.data.datasets[0].data = metrics.pnl_history.map(h => h.main_pnl || h.total_pnl || 0);
                this.chart.data.datasets[1].data = metrics.pnl_history.map(h => h.shadow_pnl || 0);
                this.chart.update('none');
            } else if (this.chart) {
                // If no history, just show current values
                const now = new Date();
                this.chart.data.labels = [now.toLocaleTimeString()];
                this.chart.data.datasets[0].data = [metrics.total_pnl || 0];
                this.chart.data.datasets[1].data = [metrics.shadow_pnl || 0];
                this.chart.update('none');
            }
        } catch (error) {
            console.error('[PnLChart] Failed to fetch data:', error);
        }
    }
    
    setupWebSocket() {
        this.unsubscribeWebSocket = setupWebSocketListener('metrics', (data) => {
            if (data.metrics) {
                this.data = data.metrics;
                this.fetchData();
            }
        });
    }
    
    update(data) {
        this.data = data;
        if (this.chart && data.pnl_history) {
            const labels = data.pnl_history.map((_, i) => {
                const now = new Date();
                const time = new Date(now.getTime() - (data.pnl_history.length - i) * 60000);
                return time.toLocaleTimeString();
            });
            this.chart.data.labels = labels;
            this.chart.data.datasets[0].data = data.pnl_history.map(h => h.main_pnl || h.total_pnl || 0);
            this.chart.data.datasets[1].data = data.pnl_history.map(h => h.shadow_pnl || 0);
            this.chart.update('none');
        }
    }
}

customElements.define('component-pnl-chart', PnLChartComponent);



