/**
 * Dashboard View Module
 * Main dashboard with performance metrics, P&L chart, and control panel
 * Uses new component system and shared API client
 */

import { 
    fetchMetrics, 
    fetchMarketData, 
    fetchRecentTrades, 
    fetchFailsafeStatus,
    fetchPositions,
    activatePanic,
    resumeTrading,
    formatCurrency,
    formatPercentage,
    formatDuration
} from '../shared/api.js';
import { setupWebSocketListener } from '../shared/websocket.js';

// Import components so they're registered
import '../components/SystemStatus.js';
import '../components/MetricsCard.js';
import '../components/SignalBadge.js';
import '../components/MarketDataTable.js';
import '../components/PositionsList.js';
import '../components/TradesLog.js';

let pnlChart = null;
let pnlUpdateInterval = null;
let tradingStatusInterval = null;
let wsUnsubscribers = [];

/**
 * Initialize dashboard view
 * @param {HTMLElement} container - Container element to render into
 * @param {Object} params - Route parameters
 */
async function init(container, params = {}) {
    console.log('[Dashboard] Initializing...');
    
    // Render dashboard HTML structure
    container.innerHTML = `
        <div class="container">
            <header>
                <h1>Dashboard</h1>
                <p>Main monitoring dashboard with performance metrics and controls</p>
            </header>
            
            <!-- System Status -->
            <div id="system-status-container" style="margin-bottom: 20px;"></div>
            
            <!-- Metrics Summary -->
            <div class="summary-cards" id="metrics-summary" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 30px;">
                <!-- MetricsCard components will be inserted here -->
            </div>
            
            <!-- P&L Chart -->
            <div class="chart-container">
                <h2>P&L Over Time</h2>
                <canvas id="pnlChart" aria-label="P&L Over Time Chart" role="img"></canvas>
            </div>
            
            <!-- Market Data and Positions Grid -->
            <div class="grid">
                <!-- Market Data Table -->
                <div class="card">
                    <h2>Market Data</h2>
                    <div id="market-data-container">
                        <p style="color: #888;">Loading market data...</p>
                    </div>
                </div>
                
                <!-- Positions List -->
                <div class="card">
                    <h2>Open Positions</h2>
                    <div id="positions-container">
                        <p style="color: #888;">Loading positions...</p>
                    </div>
                </div>
            </div>
            
            <!-- Control Panel -->
            <div class="card" style="margin-bottom: 20px;">
                <h2>Control Panel</h2>
                <div style="display: flex; gap: 15px; flex-wrap: wrap;">
                    <button id="emergency-stop-btn" class="btn btn-danger" style="flex: 1; min-width: 150px;" 
                            aria-label="Emergency Stop - Immediately halt all trading activity"
                            data-help="Emergency Stop: Immediately halts all trading activity. This is a critical safety feature that stops all open positions and prevents new trades. Use only in emergency situations. Trading can be resumed manually after stopping.">
                        🛑 Emergency Stop
                    </button>
                    <button id="trading-toggle-btn" class="btn btn-secondary" style="flex: 1; min-width: 150px;" 
                            aria-label="Toggle Trading - Enable or disable trading"
                            data-help="Trading Toggle: Enable or disable the trading system. When disabled, the system will not execute new trades but will continue monitoring the market. Current status is shown next to the button.">
                        ⏸️ Trading: <span id="trading-status">Unknown</span>
                    </button>
                </div>
            </div>
            
            <!-- Recent Trades -->
            <div class="card">
                <h2>Recent Trades</h2>
                <div id="trades-container">
                    <p style="color: #888;">Loading trades...</p>
                </div>
            </div>
        </div>
    `;
    
    // Initialize components
    await initComponents();
    
    // Initialize chart
    initChart();
    
    // Fetch initial data
    await fetchAllData();
    updateTradingStatus();
    
    // Setup intervals
    pnlUpdateInterval = setInterval(() => fetchAllData(), 5000);
    tradingStatusInterval = setInterval(updateTradingStatus, 10000);
    
    // Setup event listeners
    setupEventListeners();
    
    // Setup help system
    setupHelpSystem();
    
    // Setup WebSocket listeners
    setupWebSocketUpdates();
    
    console.log('[Dashboard] Initialized');
}

/**
 * Initialize Web Components
 */
async function initComponents() {
    // Create SystemStatus component
    const systemStatusContainer = document.getElementById('system-status-container');
    if (systemStatusContainer) {
        const systemStatus = document.createElement('component-system-status');
        systemStatusContainer.appendChild(systemStatus);
    }
    
    // Create MetricsCard components
    const metricsSummary = document.getElementById('metrics-summary');
    if (metricsSummary) {
        // These will be populated with data in fetchAllData
    }
}

/**
 * Fetch all dashboard data
 */
async function fetchAllData() {
    await Promise.all([
        fetchMetricsData(),
        fetchMarketDataDisplay(),
        fetchPositionsDisplay(),
        fetchTradesDisplay()
    ]);
}

/**
 * Fetch and display metrics
 */
async function fetchMetricsData() {
    try {
        const metrics = await fetchMetrics();
        if (!metrics) return;
        
        const metricsSummary = document.getElementById('metrics-summary');
        if (!metricsSummary) return;
        
        // Clear and recreate metric cards
        metricsSummary.innerHTML = '';
        
        // Main P&L
        const mainPnlCard = document.createElement('component-metrics-card');
        mainPnlCard.setAttribute('label', 'Main P&L');
        mainPnlCard.setAttribute('value', metrics.total_pnl || 0);
        mainPnlCard.setAttribute('format', 'currency');
        mainPnlCard.setAttribute('trend', metrics.total_pnl >= 0 ? 'positive' : 'negative');
        metricsSummary.appendChild(mainPnlCard);
        
        // Shadow P&L
        const shadowPnlCard = document.createElement('component-metrics-card');
        shadowPnlCard.setAttribute('label', 'Shadow P&L');
        shadowPnlCard.setAttribute('value', metrics.shadow_pnl || 0);
        shadowPnlCard.setAttribute('format', 'currency');
        shadowPnlCard.setAttribute('trend', metrics.shadow_pnl >= 0 ? 'positive' : 'negative');
        metricsSummary.appendChild(shadowPnlCard);
        
        // Win Rate
        const winRateCard = document.createElement('component-metrics-card');
        winRateCard.setAttribute('label', 'Win Rate');
        winRateCard.setAttribute('value', metrics.win_rate || 0);
        winRateCard.setAttribute('format', 'percentage');
        winRateCard.setAttribute('trend', (metrics.win_rate || 0) >= 0.5 ? 'positive' : 'neutral');
        metricsSummary.appendChild(winRateCard);
        
        // Total Trades
        const totalTradesCard = document.createElement('component-metrics-card');
        totalTradesCard.setAttribute('label', 'Total Trades');
        totalTradesCard.setAttribute('value', metrics.total_trades || 0);
        totalTradesCard.setAttribute('format', 'number');
        totalTradesCard.setAttribute('trend', 'neutral');
        metricsSummary.appendChild(totalTradesCard);
        
        // Update chart if we have historical data
        if (pnlChart && metrics.pnl_history) {
            const labels = metrics.pnl_history.map((_, i) => i);
            pnlChart.data.labels = labels;
            pnlChart.data.datasets[0].data = metrics.pnl_history.map(h => h.main_pnl || h.total_pnl || 0);
            pnlChart.data.datasets[1].data = metrics.pnl_history.map(h => h.shadow_pnl || 0);
            pnlChart.update('none');
        }
    } catch (error) {
        console.error('[Dashboard] Failed to fetch metrics:', error);
    }
}

/**
 * Fetch and display market data
 */
async function fetchMarketDataDisplay() {
    try {
        const marketData = await fetchMarketData();
        const container = document.getElementById('market-data-container');
        if (!container) return;
        
        if (!marketData || marketData.length === 0) {
            container.innerHTML = '<p style="color: #888;">No market data available</p>';
            return;
        }
        
        // Display market data table
        container.innerHTML = `
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="border-bottom: 1px solid rgba(74, 222, 128, 0.4);">
                        <th style="text-align: left; padding: 10px; color: #888; font-size: 12px;">Symbol</th>
                        <th style="text-align: right; padding: 10px; color: #888; font-size: 12px;">Price</th>
                        <th style="text-align: center; padding: 10px; color: #888; font-size: 12px;">Signal</th>
                        <th style="text-align: right; padding: 10px; color: #888; font-size: 12px;">24h Change</th>
                    </tr>
                </thead>
                <tbody>
                    ${marketData.slice(0, 10).map(item => `
                        <tr style="border-bottom: 1px solid rgba(255, 255, 255, 0.05);">
                            <td style="padding: 10px;">${item.symbol || 'N/A'}</td>
                            <td style="padding: 10px; text-align: right;">$${parseFloat(item.price || 0).toFixed(2)}</td>
                            <td style="padding: 10px; text-align: center;">
                                <component-signal-badge signal="${item.signal_strength || 'NEUTRAL'}"></component-signal-badge>
                            </td>
                            <td style="padding: 10px; text-align: right; color: ${(item.change_24h || 0) >= 0 ? '#4ade80' : '#f87171'};">
                                ${(item.change_24h || 0) >= 0 ? '+' : ''}${(item.change_24h || 0).toFixed(2)}%
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    } catch (error) {
        console.error('[Dashboard] Failed to fetch market data:', error);
        const container = document.getElementById('market-data-container');
        if (container) {
            container.innerHTML = '<p style="color: #f87171;">Error loading market data</p>';
        }
    }
}

/**
 * Fetch and display positions
 */
async function fetchPositionsDisplay() {
    try {
        const positions = await fetchPositions();
        const container = document.getElementById('positions-container');
        if (!container) return;
        
        if (!positions || positions.length === 0) {
            container.innerHTML = '<p style="color: #888;">No open positions</p>';
            return;
        }
        
        container.innerHTML = `
            <div style="display: grid; gap: 12px;">
                ${positions.map(pos => `
                    <div style="background: rgba(20, 20, 30, 0.8); border: 1px solid rgba(74, 222, 128, 0.4); border-radius: 8px; padding: 12px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span style="font-weight: bold;">${pos.symbol || 'N/A'}</span>
                            <span style="padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;
                                ${pos.side === 'LONG' ? 'background: rgba(74, 222, 128, 0.2); color: #4ade80;' : 'background: rgba(248, 113, 113, 0.2); color: #f87171;'}">
                                ${pos.side || 'N/A'}
                            </span>
                        </div>
                        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; font-size: 12px;">
                            <div>
                                <span style="color: #888;">Entry:</span>
                                <span style="margin-left: 8px;">$${parseFloat(pos.entry_price || 0).toFixed(2)}</span>
                            </div>
                            <div>
                                <span style="color: #888;">Current:</span>
                                <span style="margin-left: 8px;">$${parseFloat(pos.current_price || 0).toFixed(2)}</span>
                            </div>
                            <div>
                                <span style="color: #888;">P&L:</span>
                                <span style="margin-left: 8px; color: ${(pos.unrealized_pnl || 0) >= 0 ? '#4ade80' : '#f87171'};">
                                    ${formatCurrency(pos.unrealized_pnl || 0)}
                                </span>
                            </div>
                            <div>
                                <span style="color: #888;">Hold:</span>
                                <span style="margin-left: 8px;">${formatDuration(pos.hold_time_seconds || 0)}</span>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    } catch (error) {
        console.error('[Dashboard] Failed to fetch positions:', error);
        const container = document.getElementById('positions-container');
        if (container) {
            container.innerHTML = '<p style="color: #f87171;">Error loading positions</p>';
        }
    }
}

/**
 * Fetch and display trades
 */
async function fetchTradesDisplay() {
    try {
        const trades = await fetchRecentTrades(20);
        const container = document.getElementById('trades-container');
        if (!container) return;
        
        if (!trades || trades.length === 0) {
            container.innerHTML = '<p style="color: #888;">No recent trades</p>';
            return;
        }
        
        container.innerHTML = `
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="border-bottom: 1px solid rgba(74, 222, 128, 0.4);">
                        <th style="text-align: left; padding: 10px; color: #888; font-size: 12px;">Time</th>
                        <th style="text-align: left; padding: 10px; color: #888; font-size: 12px;">Symbol</th>
                        <th style="text-align: left; padding: 10px; color: #888; font-size: 12px;">Side</th>
                        <th style="text-align: right; padding: 10px; color: #888; font-size: 12px;">Entry</th>
                        <th style="text-align: right; padding: 10px; color: #888; font-size: 12px;">Exit</th>
                        <th style="text-align: right; padding: 10px; color: #888; font-size: 12px;">P&L</th>
                    </tr>
                </thead>
                <tbody>
                    ${trades.map(trade => `
                        <tr style="border-bottom: 1px solid rgba(255, 255, 255, 0.05);">
                            <td style="padding: 10px; font-size: 12px;">${new Date(trade.timestamp).toLocaleTimeString()}</td>
                            <td style="padding: 10px; font-size: 12px;">${trade.symbol || 'N/A'}</td>
                            <td style="padding: 10px; font-size: 12px; color: ${trade.side === 'LONG' ? '#4ade80' : '#f87171'};">
                                ${trade.side || 'N/A'}
                            </td>
                            <td style="padding: 10px; text-align: right; font-size: 12px;">$${parseFloat(trade.entry_price || 0).toFixed(2)}</td>
                            <td style="padding: 10px; text-align: right; font-size: 12px;">$${parseFloat(trade.exit_price || 0).toFixed(2)}</td>
                            <td style="padding: 10px; text-align: right; font-size: 12px; color: ${(trade.pnl || 0) >= 0 ? '#4ade80' : '#f87171'};">
                                ${formatCurrency(trade.pnl || 0)}
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    } catch (error) {
        console.error('[Dashboard] Failed to fetch trades:', error);
        const container = document.getElementById('trades-container');
        if (container) {
            container.innerHTML = '<p style="color: #f87171;">Error loading trades</p>';
        }
    }
}


/**
 * Initialize P&L chart
 */
function initChart() {
    const ctx = document.getElementById('pnlChart');
    if (!ctx) return;
    
    if (typeof Chart === 'undefined') {
        console.warn('[Dashboard] Chart.js not loaded');
        return;
    }
    
    pnlChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Main P&L',
                data: [],
                borderColor: '#4ade80',
                backgroundColor: 'rgba(74, 222, 128, 0.1)',
                tension: 0.4
            }, {
                label: 'Shadow P&L',
                data: [],
                borderColor: '#fbbf24',
                backgroundColor: 'rgba(251, 191, 36, 0.1)',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    labels: { color: '#fff' }
                }
            },
            scales: {
                x: { ticks: { color: '#888' }, grid: { color: '#222' } },
                y: { ticks: { color: '#888' }, grid: { color: '#222' } }
            }
        }
    });
}

/**
 * Setup WebSocket updates
 */
function setupWebSocketUpdates() {
    // Listen for metrics updates
    const unsubscribeMetrics = setupWebSocketListener('metrics', (data) => {
        fetchMetricsData();
    });
    wsUnsubscribers.push(unsubscribeMetrics);
    
    // Listen for market data updates
    const unsubscribeMarket = setupWebSocketListener('market_data', (data) => {
        fetchMarketDataDisplay();
    });
    wsUnsubscribers.push(unsubscribeMarket);
    
    // Listen for position updates
    const unsubscribePositions = setupWebSocketListener('positions', (data) => {
        fetchPositionsDisplay();
    });
    wsUnsubscribers.push(unsubscribePositions);
    
    // Listen for trade updates
    const unsubscribeTrades = setupWebSocketListener('trades', (data) => {
        fetchTradesDisplay();
    });
    wsUnsubscribers.push(unsubscribeTrades);
}

/**
 * Cleanup dashboard view
 */
async function destroy() {
    console.log('[Dashboard] Destroying...');
    
    // Clear intervals
    if (pnlUpdateInterval) {
        clearInterval(pnlUpdateInterval);
        pnlUpdateInterval = null;
    }
    if (tradingStatusInterval) {
        clearInterval(tradingStatusInterval);
        tradingStatusInterval = null;
    }
    
    // Unsubscribe from WebSocket
    wsUnsubscribers.forEach(unsub => unsub());
    wsUnsubscribers = [];
    
    // Destroy chart
    if (pnlChart) {
        pnlChart.destroy();
        pnlChart = null;
    }
    
    console.log('[Dashboard] Destroyed');
}

function handleEmergencyStop() {
    const confirmed = confirm('⚠️ EMERGENCY STOP\n\nThis will immediately halt all trading activity.\n\nAre you sure you want to proceed?');
    if (!confirmed) return;
    
    activatePanic()
        .then(data => {
            alert('Emergency stop activated. Trading has been halted.');
            console.log('[Dashboard] Emergency stop:', data);
            updateTradingStatus();
        })
        .catch(err => {
            console.error('[Dashboard] Failed to activate emergency stop:', err);
            alert('Error: Could not activate emergency stop. Check backend connection.');
        });
}

function handleTradingToggle() {
    fetchFailsafeStatus()
        .then(data => {
            const isPanic = data?.panic_active || false;
            const action = isPanic ? resumeTrading() : activatePanic();
            return action;
        })
        .then(data => {
            console.log('[Dashboard] Trading toggle:', data);
            updateTradingStatus();
        })
        .catch(err => {
            console.error('[Dashboard] Failed to toggle trading:', err);
            alert('Error: Could not toggle trading. Check backend connection.');
        });
}

function updateTradingStatus() {
    fetchFailsafeStatus()
        .then(data => {
            const status = data?.panic_active ? 'PAUSED' : 'ACTIVE';
            const statusEl = document.getElementById('trading-status');
            if (statusEl) {
                statusEl.textContent = status;
            }
        })
        .catch(err => console.error('[Dashboard] Failed to fetch trading status:', err));
}

function setupEventListeners() {
    const emergencyBtn = document.getElementById('emergency-stop-btn');
    const toggleBtn = document.getElementById('trading-toggle-btn');
    
    if (emergencyBtn) {
        emergencyBtn.addEventListener('click', handleEmergencyStop);
    }
    if (toggleBtn) {
        toggleBtn.addEventListener('click', handleTradingToggle);
    }
}

function setupHelpSystem() {
    if (window.helpSystem) {
        const emergencyBtn = document.getElementById('emergency-stop-btn');
        const toggleBtn = document.getElementById('trading-toggle-btn');
        
        if (emergencyBtn) {
            window.helpSystem.addTooltip(emergencyBtn, emergencyBtn.dataset.help);
        }
        if (toggleBtn) {
            window.helpSystem.addTooltip(toggleBtn, toggleBtn.dataset.help);
        }
    }
}

// Export module
export default {
    init,
    destroy
};
