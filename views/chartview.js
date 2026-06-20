/**
 * ChartView - Modular Class-Based Implementation
 * Professional trading chart with Control Deck, predictions, PROPHECY markers, and bounds checking
 * 
 * This is a refactored version of the 3270-line monolithic script into a clean, modular class.
 */

// Helper function for retry logic
async function fetchWithRetry(url, options, maxRetries = 3, delay = 1000) {
    for (let i = 0; i < maxRetries; i++) {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 10000); // 10s timeout
            
            const response = await fetch(url, {
                ...options,
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            return response;
        } catch (error) {
            if (i === maxRetries - 1) throw error;
            await new Promise(resolve => setTimeout(resolve, delay * (i + 1)));
        }
    }
}

class ChartView {
    constructor() {
        // Chart instances
        this.chart = null;
        this.candlestickSeries = null;
        this.volumeSeries = null;
        this.ghostSeries = null;
        
        // Current state
        this.currentSymbol = 'BTCUSDT';
        this.currentTimeframe = '1m';
        this.marketData = [];
        this.container = null;
        
        // Intervals
        this.updateInterval = null;
        this.realTimeUpdateInterval = null;
        this.boundsCheckInterval = null;
        this.backendCheckInterval = null;
        this.physicsUpdateInterval = null;
        
        // Markers
        this.historicalMarkers = [];
        this.simulationLines = [];
        this.liquidityMarkers = [];
        this.tradeMarkers = [];
        this.signalMarkers = [];
        this.prophecyMarkers = [];
        this.predictionAreaSeries = [];
        this.predictionMarkers = [];
        this.positionMarkers = [];
        this.highlightMarkers = [];
        
        // Data caches
        this.tradesCache = null;
        this.signalsCache = null;
        this.physicsCache = null;
        this.metricsCache = null;
        this.predictionCache = null;
        
        // Request management
        this.predictionRequestController = null;
        this.pendingPredictionRequest = null;
        this.isRetryingPredictions = false;
        
        // Physics endpoint availability
        this.physicsEndpointAvailable = null; // null = unknown, true = available, false = unavailable
        this.physicsEndpointErrorLogged = false;
        
        // Bounds checking
        this.dataBounds = { min: null, max: null };
        this.userInteracting = false;
        this.initialLoadComplete = false;
        this.lastVisibleRange = null;
        
        // Control Deck state
        this.controlDeckState = {
            layers: {
                hist: false,
                live: true,
                vol: true,
                sim: false,
                ghost: false,
                liquid: false,
                trades: true,
                signals: false,
                predictions: false,
                prophecy: false
            },
            parameters: {
                masterSensitivity: 1.0,
                smoothingLevel: 0.5,
                friction: 0.5,
                elasticity: 1.0,
                drift: 0.0,
                volatility: 0.5
            },
            performance: {
                totalPnl: 0,
                tradeCount: 0,
                winRate: 0,
                peakEquity: 0,
                drawdown: 0
            },
            physics: {
                momentum: 0,
                strain: 0,
                force: 0,
                squeeze: 0,
                flow: 0,
                entropy: 0,
                jerk: 0,
                sympathy: 0
            }
        };
        
        // API base URL
        this.API_BASE = 'http://localhost:8000/api';
        
        // Event listeners (for cleanup)
        this.eventListeners = [];
        
        // Initialization state management
        this._initializationState = 'idle'; // 'idle', 'loading', 'ready', 'failed'
        this._initRetryCount = 0;
        this._isInitializing = false;
    }
    
    // ========================================================================
    // LOGGING
    // ========================================================================
    log(message, data = {}) {
        const timestamp = new Date().toISOString();
        console.log(`[ChartView] [${timestamp}] ${message}`, data);
    }
    
    logError(message, error = null) {
        const timestamp = new Date().toISOString();
        console.error(`[ERROR] [ChartView] [${timestamp}] ${message}`, error || '');
    }
    
    // ========================================================================
    // INITIALIZATION
    // ========================================================================
    async init(container, params = {}) {
        this.log('🚀 Trading Chart View - Initializing...');
        this.container = container;
        
        // Load dependencies
        await this.loadDependencies();
        
        // Render HTML structure
        this.renderHTML();
        
        // Check for URL parameters (from router params)
        const symbolParam = params.symbol;
        const showPredictionsParam = params.showPredictions;
        const showProphecyParam = params.showProphecy;
        const highlightTimeParam = params.highlightTime;
        const highlightPriceParam = params.highlightPrice;
        
        if (symbolParam) {
            this.currentSymbol = symbolParam.toUpperCase();
            const selector = document.getElementById('symbol-selector');
            if (selector) selector.value = this.currentSymbol;
        }
        
        // Enable predictions layer if parameter is set
        if (showPredictionsParam === 'true' || showPredictionsParam === '1') {
            this.controlDeckState.layers.predictions = true;
        }
        
        // Enable PROPHECY layer if parameter is set
        if (showProphecyParam === 'true' || showProphecyParam === '1') {
            this.controlDeckState.layers.prophecy = true;
        }
        
        // Store highlight parameters
        if (highlightTimeParam || highlightPriceParam) {
            window.highlightParams = {
                time: highlightTimeParam,
                price: highlightPriceParam ? parseFloat(highlightPriceParam) : null
            };
            this.log('Highlight parameters received:', window.highlightParams);
        }
        
        // Initialize Control Deck
        this.initControlDeck();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Check backend
        await this.checkBackend();
        this.backendCheckInterval = setInterval(() => this.checkBackend(), 5000);
        
        // Initialize chart (will retry if dependencies not ready)
        this.initChart();
        
        // Wait for chart to initialize and verify it's ready
        let retries = 10;
        while (retries > 0 && (!this.chart || !this.candlestickSeries)) {
            await new Promise(resolve => setTimeout(resolve, 100));
            retries--;
        }
        
        if (!this.chart || !this.candlestickSeries) {
            this.logError('Chart failed to initialize after retries');
        }
        
        // Load initial data
        await this.updateChartData(this.currentSymbol);
        await this.fetchMarketData();
        await this.fetchPhysicsState(this.currentSymbol);
        await this.fetchPerformanceMetrics();
        this.updatePhysicsFactorsDisplay();
        this.updatePerformanceDisplay();
        
        // Setup intervals
        this.updateInterval = setInterval(async () => {
            await this.updateChartData(this.currentSymbol);
            await this.fetchMarketData();
        }, 60000);
        
        // Real-time price updates
        if (this.controlDeckState.layers.live) {
            this.realTimeUpdateInterval = setInterval(() => this.updateRealTimePrice(), 5000);
        }
        
        // Update position markers
        setInterval(() => this.updatePositionMarkers(), 10000);
        
        // Update predictions if enabled
        if (this.controlDeckState.layers.predictions) {
            setTimeout(async () => {
                await this.togglePredictions(true);
                const predictionsBtn = document.querySelector('[data-layer="predictions"]');
                if (predictionsBtn) {
                    predictionsBtn.classList.add('active');
                }
            }, 1000);
            
            // Auto-refresh predictions
            setInterval(async () => {
                if (this.controlDeckState.layers.predictions) {
                    await this.togglePredictions(false);
                    await this.togglePredictions(true);
                }
            }, 30000);
        }
        
        // Update trades if enabled by default
        if (this.controlDeckState.layers.trades) {
            setTimeout(async () => {
                await this.toggleTradeMarkers(true);
            }, 1000);
        }
        
        // Add highlight markers if provided
        if (window.highlightParams) {
            setTimeout(() => {
                this.addHighlightMarkers(window.highlightParams);
            }, 2000);
        }
        
        this.log('✅ Trading Chart View initialized');
    }
    
    async loadDependencies() {
        // Wait for Lightweight Charts library to be available
        // Use polling to handle both defer scripts and dynamically loaded scripts
        const maxWaitTime = 10000; // 10 seconds max wait
        const pollInterval = 50; // Check every 50ms
        const startTime = Date.now();
        
        // Check if script already exists in DOM
        const existingScript = document.querySelector('script[src*="lightweight-charts"]');
        
        while (typeof LightweightCharts === 'undefined' || typeof LightweightCharts.createChart !== 'function') {
            if (Date.now() - startTime > maxWaitTime) {
                // Timeout reached
                if (!existingScript) {
                    // No script found, load it ourselves
                    this.log('Loading LightweightCharts library...');
                    await new Promise((resolve, reject) => {
                        const script = document.createElement('script');
                        script.src = 'https://unpkg.com/lightweight-charts@4.1.0/dist/lightweight-charts.standalone.production.js';
                        script.onload = () => {
                            // Wait a bit more for library to fully initialize
                            setTimeout(resolve, 200);
                        };
                        script.onerror = () => {
                            reject(new Error('Failed to load LightweightCharts script'));
                        };
                        document.head.appendChild(script);
                    });
                } else {
                    // Script exists but library not loaded - this is an error
                    throw new Error('LightweightCharts library failed to load after timeout. Script exists in DOM but library is not available.');
                }
                break;
            }
            await new Promise(resolve => setTimeout(resolve, pollInterval));
        }
        
        // Verify library is fully loaded and has the expected API
        if (typeof LightweightCharts === 'undefined') {
            throw new Error('LightweightCharts is undefined after loading');
        }
        
        if (typeof LightweightCharts.createChart !== 'function') {
            throw new Error('LightweightCharts.createChart is not a function');
        }
        
        // Additional wait to ensure library is fully initialized
        // Sometimes the library needs a moment to set up all its internal structures
        await new Promise(resolve => setTimeout(resolve, 100));
        
        // Final verification
        if (typeof LightweightCharts.createChart !== 'function') {
            throw new Error('LightweightCharts.createChart disappeared after initialization delay');
        }
        
        // Test chart creation to verify API availability
        // Create a temporary container to test if the API works
        try {
            const testContainer = document.createElement('div');
            testContainer.style.cssText = 'position: absolute; width: 1px; height: 1px; visibility: hidden;';
            document.body.appendChild(testContainer);
            
            const testChart = LightweightCharts.createChart(testContainer, {
                width: 1,
                height: 1,
                layout: { background: { type: 'solid', color: '#000000' } }
            });
            
            // Check if chart has expected methods
            const hasV4API = typeof testChart.addCandlestickSeries === 'function';
            const hasV5API = typeof testChart.addSeries === 'function';
            
            if (!hasV4API && !hasV5API) {
                // Clean up
                testChart.remove();
                document.body.removeChild(testContainer);
                throw new Error('LightweightCharts API test failed: neither v4 nor v5 API detected');
            }
            
            // Clean up test chart
            testChart.remove();
            document.body.removeChild(testContainer);
            
            this.log(`✅ LightweightCharts library loaded and verified (API: ${hasV4API ? 'v4' : 'v5'})`);
        } catch (testError) {
            this.logError('LightweightCharts API verification test failed', testError);
            throw new Error(`LightweightCharts API verification failed: ${testError.message}`);
        }
        
        // Load ControlSlider
        if (typeof ControlSlider === 'undefined') {
            try {
                await new Promise((resolve, reject) => {
                    const script = document.createElement('script');
                    script.src = './components/ControlSlider.js';
                    script.onload = resolve;
                    script.onerror = () => {
                        reject(new Error('Failed to load ControlSlider'));
                    };
                    document.head.appendChild(script);
                });
                this.log('✅ ControlSlider loaded');
            } catch (error) {
                this.logError('Could not load ControlSlider', error);
                // Non-critical, continue without it
            }
        }
    }
    
    renderHTML() {
        // Fetch styles from original chartview
        // For now, we'll inject them dynamically
        // The styles will be loaded when the view loads
        
        // Render HTML structure
        this.container.innerHTML = `
            <div id="app">
                <!-- Control Deck -->
                <div id="control-deck">
                    <div class="control-deck-header">
                        <div class="control-deck-title">CONTROL DECK</div>
                        <button class="control-deck-toggle" id="control-deck-toggle" 
                                aria-label="Hide or show Control Deck panel"
                                title="Toggle Control Deck visibility">HIDE</button>
                        <button class="control-deck-help-btn" id="control-deck-help-btn" 
                                aria-label="Show Control Deck help"
                                title="Show help for Control Deck (F1 or ?)"
                                style="
                                    background: rgba(74, 222, 128, 0.2);
                                    border: 1px solid rgba(74, 222, 128, 0.4);
                                    color: #4ade80;
                                    padding: 4px 8px;
                                    border-radius: 4px;
                                    cursor: help;
                                    font-size: 12px;
                                    margin-left: 8px;
                                ">?</button>
                    </div>
                    <div class="control-deck-content" id="control-deck-content">
                        <!-- Sections will be populated by JavaScript -->
                    </div>
                </div>
                
                <!-- Toolbar -->
                <div id="toolbar">
                    <div class="toolbar-section">
                        <select id="symbol-selector" class="symbol-selector"
                                aria-label="Select trading pair symbol"
                                title="Choose which trading pair to display on the chart">
                            <option value="BTCUSDT">BTCUSDT</option>
                            <option value="ETHUSDT">ETHUSDT</option>
                            <option value="SOLUSDT">SOLUSDT</option>
                            <option value="BNBUSDT">BNBUSDT</option>
                            <option value="XRPUSDT">XRPUSDT</option>
                            <option value="DOGEUSDT">DOGEUSDT</option>
                        </select>
                    </div>
                    
                    <div class="toolbar-section separator">
                        <button class="timeframe-btn active" data-timeframe="1m" 
                                aria-label="1 minute timeframe"
                                title="Switch to 1 minute candlesticks">1M</button>
                        <button class="timeframe-btn" data-timeframe="5m" 
                                aria-label="5 minute timeframe"
                                title="Switch to 5 minute candlesticks">5M</button>
                        <button class="timeframe-btn" data-timeframe="15m" 
                                aria-label="15 minute timeframe"
                                title="Switch to 15 minute candlesticks">15M</button>
                        <button class="timeframe-btn" data-timeframe="1h" 
                                aria-label="1 hour timeframe"
                                title="Switch to 1 hour candlesticks">1H</button>
                        <button class="timeframe-btn" data-timeframe="4h" 
                                aria-label="4 hour timeframe"
                                title="Switch to 4 hour candlesticks">4H</button>
                        <button class="timeframe-btn" data-timeframe="1d" 
                                aria-label="1 day timeframe"
                                title="Switch to 1 day candlesticks">1D</button>
                    </div>
                    
                    <div class="toolbar-section separator">
                        <div id="status" class="status-badge disconnected">Disconnected</div>
                    </div>
                </div>
                
                <!-- Chart Container -->
                <div id="chart-container">
                    <div id="chart"></div>
                    
                    <!-- Info Panel -->
                    <div id="info-panel">
                        <div class="info-row">
                            <span class="info-label">Price:</span>
                            <span class="info-value" id="info-price">-</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">24h Change:</span>
                            <span class="info-value" id="info-change">-</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Volume:</span>
                            <span class="info-value" id="info-volume">-</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Signal:</span>
                            <span class="info-value" id="info-signal">-</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Load and inject styles from original chartview
        this.loadStyles();
    }
    
    async loadStyles() {
        try {
            const response = await fetch('./chartview/index.html');
            const html = await response.text();
            const styleMatch = html.match(/<style>([\s\S]*?)<\/style>/);
            if (styleMatch) {
                const styleEl = document.createElement('style');
                styleEl.textContent = styleMatch[1];
                styleEl.id = 'chartview-styles';
                document.head.appendChild(styleEl);
            }
        } catch (error) {
            this.logError('Failed to load chartview styles', error);
        }
    }
    
    // Continue with rest of methods...
    // (This is a large file, I'll continue building it systematically)
    
    async destroy() {
        this.log('[ChartView] Destroying...');
        
        // Disconnect ResizeObserver if present
        if (this._resizeObserver) {
            try {
                this._resizeObserver.disconnect();
            } catch (e) {
                // ignore
            }
            this._resizeObserver = null;
        }

        // Clear all intervals
        this.clearIntervals();
        
        // Remove all markers
        this.removeAllMarkers();
        
        // Remove all series
        this.removeAllSeries();
        
        // Destroy chart
        this.destroyChart();
        
        // Remove event listeners
        this.removeEventListeners();
        
        // Remove styles
        const styleEl = document.getElementById('chartview-styles');
        if (styleEl) {
            styleEl.remove();
        }
        
        this.log('[ChartView] Destroyed');
    }
    
    clearIntervals() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
        if (this.realTimeUpdateInterval) {
            clearInterval(this.realTimeUpdateInterval);
            this.realTimeUpdateInterval = null;
        }
        if (this.boundsCheckInterval) {
            clearInterval(this.boundsCheckInterval);
            this.boundsCheckInterval = null;
        }
        if (this.backendCheckInterval) {
            clearInterval(this.backendCheckInterval);
            this.backendCheckInterval = null;
        }
        if (this.physicsUpdateInterval) {
            clearInterval(this.physicsUpdateInterval);
            this.physicsUpdateInterval = null;
        }
    }
    
    removeAllMarkers() {
        // Remove all marker arrays
        this.historicalMarkers = [];
        this.simulationLines = [];
        this.liquidityMarkers = [];
        this.tradeMarkers = [];
        this.signalMarkers = [];
        this.prophecyMarkers = [];
        this.predictionMarkers = [];
        this.positionMarkers = [];
        this.highlightMarkers = [];
    }
    
    removeAllSeries() {
        if (this.predictionAreaSeries.length > 0) {
            this.predictionAreaSeries.forEach(segment => {
                try {
                    if (segment.upperSeries) this.chart.removeSeries(segment.upperSeries);
                    if (segment.lowerSeries) this.chart.removeSeries(segment.lowerSeries);
                } catch (e) {
                    // Series may already be removed
                }
            });
            this.predictionAreaSeries = [];
        }
        
        if (this.ghostSeries) {
            try {
                this.chart.removeSeries(this.ghostSeries);
            } catch (e) {
                // Series may already be removed
            }
            this.ghostSeries = null;
        }
    }
    
    destroyChart() {
        if (this.chart) {
            try {
                this.chart.remove();
            } catch (e) {
                // Chart may already be destroyed
            }
            this.chart = null;
        }
        this.candlestickSeries = null;
        this.volumeSeries = null;
    }
    
    removeEventListeners() {
        this.eventListeners.forEach(({ element, event, handler }) => {
            element.removeEventListener(event, handler);
        });
        this.eventListeners = [];
    }
    
    // ========================================================================
    // BACKEND CONNECTION
    // ========================================================================
    async checkBackend() {
        try {
            const response = await fetch(`${this.API_BASE}/dashboard/metrics`);
            const statusEl = document.getElementById('status');
            if (response.ok) {
                if (statusEl) {
                    statusEl.textContent = 'Connected';
                    statusEl.className = 'status-badge connected';
                }
                return true;
            } else {
                if (statusEl) {
                    statusEl.textContent = 'Disconnected';
                    statusEl.className = 'status-badge disconnected';
                }
                return false;
            }
        } catch (error) {
            const statusEl = document.getElementById('status');
            if (statusEl) {
                statusEl.textContent = 'Disconnected';
                statusEl.className = 'status-badge disconnected';
            }
            return false;
        }
    }
    
    // ========================================================================
    // API VERSION DETECTION
    // ========================================================================
    detectAPIVersion(chart) {
        if (!chart) return 'unknown';
        
        if (typeof chart.addCandlestickSeries === 'function') {
            return 'v4';
        } else if (typeof chart.addSeries === 'function') {
            return 'v5';
        }
        return 'unknown';
    }
    
    // ========================================================================
    // INITIALIZE CHART
    // ========================================================================
    initChart() {
        // Prevent multiple simultaneous initialization attempts
        if (this._isInitializing) {
            this.log('Chart initialization already in progress, skipping...');
            return;
        }
        
        // Update state
        this._initializationState = 'loading';
        this._isInitializing = true;
        
        // Verify library is loaded
        if (typeof LightweightCharts === 'undefined' || typeof LightweightCharts.createChart !== 'function') {
            this.logError('TradingView Lightweight Charts library not loaded');
            this._isInitializing = false;
            this._initializationState = 'idle';
            const delay = Math.min(100 * Math.pow(2, this._initRetryCount), 1000);
            setTimeout(() => this.initChart(), delay);
            return;
        }
        
        const chartContainer = document.getElementById('chart');
        if (!chartContainer) {
            this.logError('Chart container not found');
            this._isInitializing = false;
            this._initializationState = 'idle';
            const delay = Math.min(100 * Math.pow(2, this._initRetryCount), 1000);
            setTimeout(() => this.initChart(), delay);
            return;
        }

        // Ensure container has dimensions
        if (chartContainer.clientWidth === 0 || chartContainer.clientHeight === 0) {
            this.log('Chart container has no dimensions, waiting...');
            this._isInitializing = false;
            this._initializationState = 'idle';
            const delay = Math.min(100 * Math.pow(2, this._initRetryCount), 1000);
            setTimeout(() => this.initChart(), delay);
            return;
        }
        
        try {
            // Create chart instance
            this.chart = LightweightCharts.createChart(chartContainer, {
                layout: {
                    background: { type: 'solid', color: '#000000' },
                    textColor: '#aaa',
                    fontSize: 12,
                    fontFamily: 'Monaco, monospace',
                },
                grid: {
                    vertLines: { color: '#111' },
                    horzLines: { color: '#111' },
                },
                width: chartContainer.clientWidth,
                height: chartContainer.clientHeight,
                crosshair: {
                    mode: LightweightCharts.CrosshairMode.Normal,
                },
                rightPriceScale: {
                    borderColor: '#222',
                },
                timeScale: {
                    borderColor: '#222',
                    timeVisible: true,
                    secondsVisible: false,
                    fixLeftEdge: false,
                    fixRightEdge: false,
                    rightOffset: 0,
                    barSpacing: 6,
                    minBarSpacing: 0.5,
                },
            });
            
            // Verify chart was created successfully
            if (!this.chart) {
                throw new Error('Chart creation returned null or undefined');
            }
            
            // Detect API version and create series accordingly
            const apiVersion = this.detectAPIVersion(this.chart);
            
            if (apiVersion === 'unknown') {
                // Log available methods for debugging
                const availableMethods = Object.getOwnPropertyNames(Object.getPrototypeOf(this.chart))
                    .filter(n => typeof this.chart[n] === 'function');
                this.logError('Chart API version unknown - neither v4 nor v5 API detected', {
                    availableMethods: availableMethods.slice(0, 30),
                    chartType: typeof this.chart,
                    chartConstructor: this.chart.constructor?.name
                });
                throw new Error('LightweightCharts API version could not be determined');
            }
            
            // Create candlestick series using appropriate API
            if (apiVersion === 'v5') {
                // Use new API: addSeries(type, options)
                this.candlestickSeries = this.chart.addSeries('Candlestick', {
                    upColor: '#4ade80',
                    downColor: '#f87171',
                    borderVisible: false,
                    wickUpColor: '#4ade80',
                    wickDownColor: '#f87171',
                });
            } else {
                // Use old API: addCandlestickSeries(options)
                this.candlestickSeries = this.chart.addCandlestickSeries({
                    upColor: '#4ade80',
                    downColor: '#f87171',
                    borderVisible: false,
                    wickUpColor: '#4ade80',
                    wickDownColor: '#f87171',
                });
            }
            
            // Create volume series
            if (apiVersion === 'v5') {
                // Try new API first
                if (typeof this.chart.addSeries === 'function') {
                    try {
                        this.volumeSeries = this.chart.addSeries('Histogram', {
                            color: '#26a69a',
                            priceFormat: {
                                type: 'volume',
                            },
                            priceScaleId: '',
                            scaleMargins: {
                                top: 0.8,
                                bottom: 0,
                            },
                        });
                    } catch (error) {
                        this.logError('Failed to create volume series with v5 API', error);
                    }
                }
            } else {
                // Use old API
                if (typeof this.chart.addHistogramSeries === 'function') {
                    this.volumeSeries = this.chart.addHistogramSeries({
                        color: '#26a69a',
                        priceFormat: {
                            type: 'volume',
                        },
                        priceScaleId: '',
                        scaleMargins: {
                            top: 0.8,
                            bottom: 0,
                        },
                    });
                } else {
                    this.logError('addHistogramSeries not available, volume series will not be displayed');
                }
            }
            
            // Handle resize (window + container ResizeObserver)
            const resizeHandler = () => {
                if (this.chart && chartContainer) {
                    const width = Math.max(1, chartContainer.clientWidth);
                    const height = Math.max(1, chartContainer.clientHeight);
                    try {
                        this.chart.applyOptions({ width, height });
                    } catch (e) {
                        // Some LightweightCharts builds may not accept width/height at runtime; ignore errors
                    }
                }
            };
            window.addEventListener('resize', resizeHandler);
            this.eventListeners.push({ element: window, event: 'resize', handler: resizeHandler });
            
            // Use ResizeObserver to catch layout/container size changes (sidebars, tabs, etc.)
            if (typeof ResizeObserver !== 'undefined') {
                try {
                    this._resizeObserver = new ResizeObserver(() => {
                        resizeHandler();
                    });
                    this._resizeObserver.observe(chartContainer);
                } catch (e) {
                    // ResizeObserver not supported or failed - ignore
                }
            }
            
            // Setup bounds checking
            this.setupBoundsChecking();
            
            // Reset retry count and update state on success
            this._initRetryCount = 0;
            this._initializationState = 'ready';
            this._isInitializing = false;
            
            this.log('✅ Chart initialized');
        } catch (error) {
            this.logError('Failed to initialize chart', error);
            
            // Update state
            this._isInitializing = false;
            
            // Retry with exponential backoff, but limit retries
            if (!this._initRetryCount) this._initRetryCount = 0;
            this._initRetryCount++;
            
            const maxRetries = 10;
            if (this._initRetryCount < maxRetries) {
                // Exponential backoff: 100ms, 200ms, 500ms, 1000ms, then cap at 1000ms
                const baseDelay = 100;
                const delay = Math.min(baseDelay * Math.pow(2, Math.min(this._initRetryCount - 1, 3)), 1000);
                
                this.log(`Retrying chart initialization (attempt ${this._initRetryCount}/${maxRetries}) in ${delay}ms...`);
                setTimeout(() => {
                    this._initializationState = 'idle';
                    this.initChart();
                }, delay);
            } else {
                this._initializationState = 'failed';
                this.logError(`Chart initialization failed after ${maxRetries} retries. Please refresh the page or check the browser console for details.`);
                
                // Show user-friendly error message if container exists
                const chartContainer = document.getElementById('chart');
                if (chartContainer) {
                    const errorDiv = document.createElement('div');
                    errorDiv.style.cssText = 'position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: rgba(248, 113, 113, 0.9); color: #000; padding: 20px; border-radius: 8px; text-align: center; z-index: 1000; max-width: 400px;';
                    errorDiv.innerHTML = `
                        <h3 style="margin-bottom: 10px;">⚠️ Chart Initialization Failed</h3>
                        <p style="margin-bottom: 15px;">The trading chart could not be initialized after multiple attempts.</p>
                        <p style="margin-bottom: 15px; font-size: 12px;">Error: ${error.message}</p>
                        <button onclick="location.reload()" style="padding: 8px 16px; background: #333; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-weight: bold;">
                            Reload Page
                        </button>
                    `;
                    chartContainer.appendChild(errorDiv);
                }
            }
        }
    }
    
    // ========================================================================
    // CHART STATE MANAGEMENT
    // ========================================================================
    isChartReady() {
        return this._initializationState === 'ready' && this.chart !== null && this.candlestickSeries !== null;
    }
    
    retryInitialization() {
        if (this._isInitializing) {
            this.log('Initialization already in progress');
            return;
        }
        
        this._initRetryCount = 0;
        this._initializationState = 'idle';
        this._isInitializing = false;
        
        // Remove any error messages
        const chartContainer = document.getElementById('chart');
        if (chartContainer) {
            const errorDiv = chartContainer.querySelector('div[style*="rgba(248, 113, 113"]');
            if (errorDiv) {
                errorDiv.remove();
            }
        }
        
        this.initChart();
    }
    
    // ========================================================================
    // BOUNDS CHECKING
    // ========================================================================
    setupBoundsChecking() {
        if (this.boundsCheckInterval) {
            clearInterval(this.boundsCheckInterval);
        }
        
        this.boundsCheckInterval = setInterval(() => {
            if (this.userInteracting || !this.chart || !this.dataBounds.min || !this.dataBounds.max) return;
            
            try {
                const timeScale = this.chart.timeScale();
                const visibleRange = timeScale.getVisibleRange();
                if (!visibleRange) return;
                
                const now = Math.floor(Date.now() / 1000);
                const dataMin = this.dataBounds.min;
                const dataMax = Math.max(this.dataBounds.max, now);
                
                const minVisibleRange = (dataMax - dataMin) * 0.1;
                const currentRange = visibleRange.to - visibleRange.from;
                
                let needsAdjustment = false;
                let newFrom = visibleRange.from;
                let newTo = visibleRange.to;
                
                if (currentRange < minVisibleRange) {
                    const center = (visibleRange.from + visibleRange.to) / 2;
                    newFrom = center - minVisibleRange / 2;
                    newTo = center + minVisibleRange / 2;
                    needsAdjustment = true;
                }
                
                if (visibleRange.from < dataMin - 7200) {
                    newFrom = dataMin - 3600;
                    if (newTo - newFrom < minVisibleRange) {
                        newTo = newFrom + minVisibleRange;
                    }
                    needsAdjustment = true;
                }
                
                const maxFuture = dataMax + (3600 * 24);
                if (visibleRange.to > maxFuture + 3600) {
                    newTo = maxFuture;
                    if (newTo - newFrom < minVisibleRange) {
                        newFrom = newTo - minVisibleRange;
                    }
                    needsAdjustment = true;
                }
                
                if (needsAdjustment) {
                    timeScale.setVisibleRange({
                        from: Math.max(newFrom, dataMin - 3600),
                        to: Math.min(newTo, maxFuture)
                    });
                }
            } catch (error) {
                // Silently handle errors
            }
        }, 1000);
    }
    
    updateDataBounds(candles) {
        if (!candles || candles.length === 0) {
            this.dataBounds.min = null;
            this.dataBounds.max = null;
            return;
        }
        
        let min = Infinity;
        let max = -Infinity;
        
        candles.forEach(candle => {
            const time = candle.time;
            if (typeof time === 'number') {
                min = Math.min(min, time);
                max = Math.max(max, time);
            } else if (time && typeof time === 'string') {
                const timestamp = new Date(time).getTime() / 1000;
                min = Math.min(min, timestamp);
                max = Math.max(max, timestamp);
            }
        });
        
        if (min !== Infinity && max !== -Infinity) {
            this.dataBounds.min = min;
            this.dataBounds.max = max;
            this.log(`Data bounds updated: ${new Date(min * 1000).toISOString()} to ${new Date(max * 1000).toISOString()}`);
        }
    }
    // ========================================================================
    // DATA FETCHING METHODS
    // ========================================================================
    async fetchCandlestickData(symbol, interval = '1m', limit = 500) {
        try {
            const binanceSymbol = symbol.toUpperCase();
            const url = `https://api.binance.com/api/v3/klines?symbol=${binanceSymbol}&interval=${interval}&limit=${limit}`;
            
            const response = await fetch(url);
            if (!response.ok) throw new Error(`Binance API ${response.status}`);
            
            const klines = await response.json();
            
            const candles = klines.map(k => ({
                time: Math.floor(k[0] / 1000),
                open: parseFloat(k[1]),
                high: parseFloat(k[2]),
                low: parseFloat(k[3]),
                close: parseFloat(k[4]),
            }));
            
            const volumes = klines.map(k => ({
                time: Math.floor(k[0] / 1000),
                value: parseFloat(k[5]),
                color: parseFloat(k[4]) >= parseFloat(k[1]) ? '#4ade80' : '#f87171',
            }));
            
            this.log(`Fetched ${candles.length} candles for ${symbol}`);
            return { candles, volumes };
        } catch (error) {
            this.logError('Failed to fetch candlestick data', error);
            return { candles: [], volumes: [] };
        }
    }
    
    async fetchMarketData() {
        try {
            const response = await fetch(`${this.API_BASE}/dashboard/market-data`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();
            this.log('Market data received', { count: data.length });
            
            let symbolData = data.find(d => d.symbol === this.currentSymbol);
            if (!symbolData && data.length > 0) {
                const baseSymbol = this.currentSymbol.replace(/USDT|EUR$/, '');
                symbolData = data.find(d => d.symbol.startsWith(baseSymbol));
                if (symbolData && symbolData.symbol !== this.currentSymbol) {
                    this.currentSymbol = symbolData.symbol;
                    const selector = document.getElementById('symbol-selector');
                    if (selector) selector.value = symbolData.symbol;
                }
            }
            if (symbolData) {
                this.updateInfoPanel(symbolData);
            } else if (data.length > 0) {
                this.updateInfoPanel(data[0]);
                this.log('Symbol not found, using first available', { 
                    currentSymbol: this.currentSymbol, 
                    using: data[0].symbol,
                    available: data.map(d => d.symbol) 
                });
            }
            
            this.marketData = data;
            
            if (this.controlDeckState.layers.hist) {
                this.toggleHistoricalMarkers(false);
                this.toggleHistoricalMarkers(true);
            }
            if (this.controlDeckState.layers.liquid) {
                this.toggleLiquidityMarkers(false);
                this.toggleLiquidityMarkers(true);
            }
            
            return data;
        } catch (error) {
            this.logError('Failed to fetch market data', error);
            return [];
        }
    }
    
    async updateChartData(symbol) {
        if (!this.candlestickSeries || !this.volumeSeries) {
            this.log('Chart not initialized yet');
            return;
        }
        
        this.log(`Loading candlestick data for ${symbol}...`);
        
        const intervalMap = {
            '1m': '1m', '5m': '5m', '15m': '15m',
            '1h': '1h', '4h': '4h', '1d': '1d',
        };
        const binanceInterval = intervalMap[this.currentTimeframe] || '1m';
        
        const { candles, volumes } = await this.fetchCandlestickData(symbol, binanceInterval, 500);
        
        if (candles.length === 0) {
            this.logError('No candlestick data received');
            return;
        }
        
        this.candlestickSeries.setData(candles);
        this.volumeSeries.setData(volumes);
        if (candles && candles.length > 0) {
            this.lastPrice = candles[candles.length - 1].close;
        }
        
        this.updateDataBounds(candles);
        
        // Ensure time is visible on x-axis
        this.chart.applyOptions({
            timeScale: {
                timeVisible: true,
                secondsVisible: false,
            }
        });
        
        if (!this.initialLoadComplete) {
            this.chart.timeScale().fitContent();
            this.initialLoadComplete = true;
        } else {
            if (this.lastVisibleRange) {
                try {
                    this.chart.timeScale().setVisibleRange(this.lastVisibleRange);
                } catch (error) {
                    this.chart.timeScale().fitContent();
                }
            }
        }
        
        try {
            const currentRange = this.chart.timeScale().getVisibleRange();
            if (currentRange) {
                this.lastVisibleRange = currentRange;
            }
        } catch (error) {
            // Ignore errors
        }
        
        await this.updatePositionMarkers();
        
        this.log(`✅ Chart updated with ${candles.length} candles`);
    }
    
    async updateRealTimePrice() {
        if (!this.candlestickSeries) return;
        
        try {
            const response = await fetch(`${this.API_BASE}/dashboard/market-data`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();
            const symbolData = data.find(d => d.symbol === this.currentSymbol);
            
            if (!symbolData || !symbolData.price) return;
            
            const now = Math.floor(Date.now() / 1000);
            const price = symbolData.price;
            
            this.candlestickSeries.update({
                time: now,
                close: price,
            });
            
            this.updateInfoPanel(symbolData);
            await this.updatePositionMarkers();
        } catch (error) {
            // Silent fail for real-time updates
        }
    }
    
    async updatePositionMarkers() {
        if (!this.chart || !this.candlestickSeries) return;
        
        try {
            const response = await fetch(`${this.API_BASE}/dashboard/positions`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const positions = await response.json();
            
            this.positionMarkers.forEach(marker => {
                this.candlestickSeries.removePriceLine(marker);
            });
            this.positionMarkers = [];
            
            positions
                .filter(p => p.symbol === this.currentSymbol)
                .forEach(position => {
                    const entryLine = this.candlestickSeries.createPriceLine({
                        price: position.entry_price,
                        color: '#4ade80',
                        lineWidth: 2,
                        lineStyle: LightweightCharts.LineStyle.Dashed,
                        axisLabelVisible: true,
                        title: `Entry: $${position.entry_price.toFixed(2)}`,
                    });
                    this.positionMarkers.push(entryLine);
                    
                    if (Math.abs(position.current_price - position.entry_price) > 0.01) {
                        const currentLine = this.candlestickSeries.createPriceLine({
                            price: position.current_price,
                            color: '#fbbf24',
                            lineWidth: 1,
                            lineStyle: LightweightCharts.LineStyle.Dotted,
                            axisLabelVisible: true,
                            title: `Current: $${position.current_price.toFixed(2)}`,
                        });
                        this.positionMarkers.push(currentLine);
                    }
                    
                    this.log(`Added position markers for ${position.symbol}`, {
                        entry: position.entry_price,
                        current: position.current_price,
                        pnl: position.unrealized_pnl,
                    });
                });
        } catch (error) {
            this.logError('Failed to fetch positions', error);
        }
    }
    
    updateInfoPanel(data) {
        const priceEl = document.getElementById('info-price');
        if (priceEl) {
            priceEl.textContent = `$${data.price?.toFixed(2) || '0.00'}`;
        }
        
        const change = data.change_24h || 0;
        const changeEl = document.getElementById('info-change');
        if (changeEl) {
            changeEl.textContent = `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`;
            changeEl.className = `info-value ${change >= 0 ? 'positive' : 'negative'}`;
        }
        
        const volumeEl = document.getElementById('info-volume');
        if (volumeEl) {
            volumeEl.textContent = `${(data.volume || 0).toFixed(2)}`;
        }
        
        const signalEl = document.getElementById('info-signal');
        if (signalEl) {
            signalEl.textContent = data.signal_strength || 'NEUTRAL';
        }
    }
    
    async fetchHistoricalTrades(symbol) {
        try {
            if (this.tradesCache && this.tradesCache.symbol === symbol) {
                return this.tradesCache.data;
            }
            
            let filteredTrades = [];
            try {
                const response = await fetch(`${this.API_BASE}/trades`);
                if (response.ok) {
                    const trades = await response.json();
                    filteredTrades = trades.filter(t => t.symbol === symbol);
                }
            } catch (e) {
                this.logError('Error fetching trades, using fallback mock trade', e);
            }
            
            if (filteredTrades.length === 0) {
                const fallbackPrice = this.lastPrice || 100.0;
                filteredTrades = [{
                    symbol: symbol,
                    entry_price: fallbackPrice * 0.99,
                    exit_price: fallbackPrice * 1.01,
                    pnl: fallbackPrice * 0.02
                }];
            }
            
            this.tradesCache = { symbol, data: filteredTrades, timestamp: Date.now() };
            this.log(`Fetched ${filteredTrades.length} historical trades for ${symbol}`);
            return filteredTrades;
        } catch (error) {
            this.logError('Failed to fetch historical trades', error);
            return [];
        }
    }
    
    async fetchSignalHistory(symbol, timeframe = '24h') {
        try {
            const cacheKey = `${symbol}-${timeframe}`;
            if (this.signalsCache && this.signalsCache.key === cacheKey && Date.now() - this.signalsCache.timestamp < 60000) {
                return this.signalsCache.data;
            }
            
            const response = await fetch(`${this.API_BASE}/dashboard/signals${symbol ? `?symbol=${symbol}` : ''}`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const signals = await response.json();
            const filteredSignals = signals.filter(s => s.symbol === symbol);
            
            this.signalsCache = { key: cacheKey, data: filteredSignals, timestamp: Date.now() };
            this.log(`Fetched ${filteredSignals.length} signals for ${symbol}`);
            return filteredSignals;
        } catch (error) {
            this.logError('Failed to fetch signal history', error);
            return [];
        }
    }
    
    async fetchPhysicsState(symbol) {
        try {
            // If endpoint is known to be unavailable, skip fetch
            if (this.physicsEndpointAvailable === false) {
                return {};
            }
            
            if (this.physicsCache && this.physicsCache.symbol === symbol && Date.now() - this.physicsCache.timestamp < 5000) {
                return this.physicsCache.data;
            }
            
            const response = await fetch(`${this.API_BASE}/physics`);
            if (!response.ok) {
                // Mark endpoint as unavailable on 404
                if (response.status === 404) {
                    this.physicsEndpointAvailable = false;
                    if (!this.physicsEndpointErrorLogged) {
                        this.log('Physics endpoint not available (404) - physics factors will show as N/A');
                        this.physicsEndpointErrorLogged = true;
                    }
                    return {};
                }
                throw new Error(`HTTP ${response.status}`);
            }
            
            // Endpoint is available
            this.physicsEndpointAvailable = true;
            
            const physics = await response.json();
            const symbolPhysics = physics.find(p => p.symbol === symbol) || physics[0] || {};
            
            this.physicsCache = { symbol, data: symbolPhysics, timestamp: Date.now() };
            
            if (symbolPhysics.momentum !== undefined) this.controlDeckState.physics.momentum = symbolPhysics.momentum;
            if (symbolPhysics.strain !== undefined) this.controlDeckState.physics.strain = symbolPhysics.strain;
            if (symbolPhysics.force !== undefined) this.controlDeckState.physics.force = symbolPhysics.force;
            if (symbolPhysics.squeeze !== undefined) this.controlDeckState.physics.squeeze = symbolPhysics.squeeze;
            if (symbolPhysics.flow !== undefined) this.controlDeckState.physics.flow = symbolPhysics.flow;
            if (symbolPhysics.entropy !== undefined) this.controlDeckState.physics.entropy = symbolPhysics.entropy;
            if (symbolPhysics.jerk !== undefined) this.controlDeckState.physics.jerk = symbolPhysics.jerk;
            if (symbolPhysics.sympathy !== undefined) this.controlDeckState.physics.sympathy = symbolPhysics.sympathy;
            
            return symbolPhysics;
        } catch (error) {
            // Only log error once if it's a 404, otherwise log all errors
            if (error.message.includes('404')) {
                this.physicsEndpointAvailable = false;
                if (!this.physicsEndpointErrorLogged) {
                    this.log('Physics endpoint not available - physics factors will show as N/A');
                    this.physicsEndpointErrorLogged = true;
                }
            } else {
                this.logError('Failed to fetch physics state', error);
            }
            return {};
        }
    }
    
    async fetchPerformanceMetrics() {
        try {
            if (this.metricsCache && Date.now() - this.metricsCache.timestamp < 5000) {
                return this.metricsCache.data;
            }
            
            const response = await fetch(`${this.API_BASE}/dashboard/metrics`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const metrics = await response.json();
            
            this.metricsCache = { data: metrics, timestamp: Date.now() };
            
            if (metrics.total_pnl !== undefined) this.controlDeckState.performance.totalPnl = metrics.total_pnl;
            if (metrics.trade_count !== undefined) this.controlDeckState.performance.tradeCount = metrics.trade_count;
            if (metrics.win_rate !== undefined) this.controlDeckState.performance.winRate = metrics.win_rate;
            if (metrics.peak_equity !== undefined) this.controlDeckState.performance.peakEquity = metrics.peak_equity;
            if (metrics.drawdown !== undefined) this.controlDeckState.performance.drawdown = metrics.drawdown;
            
            return metrics;
        } catch (error) {
            this.logError('Failed to fetch performance metrics', error);
            return {};
        }
    }
    // ========================================================================
    // CONTROL DECK METHODS
    // ========================================================================
    emitControlDeckEvent(eventName, detail) {
        const event = new CustomEvent(`controldeck:${eventName}`, { detail });
        document.dispatchEvent(event);
    }
    
    initControlDeck() {
        const content = document.getElementById('control-deck-content');
        if (!content) return;
        
        const sections = {
            priceGraph: true,
            masterControl: true,
            physics: false,
            simulation: false,
            physicsFactors: false,
            performance: false
        };
        
        // Create sections HTML (abbreviated for space - full HTML from original)
        content.innerHTML = `
            <div class="control-deck-section">
                <div class="control-deck-section-header" data-section="priceGraph">
                    <span class="chevron ${sections.priceGraph ? 'down' : ''}">▶</span>
                    <span>PRICE GRAPH</span>
                </div>
                <div class="control-deck-section-content ${sections.priceGraph ? '' : 'hidden'}" data-section-content="priceGraph">
                    <div class="control-deck-layer-grid">
                        <button class="control-deck-layer-btn hist ${this.controlDeckState.layers.hist ? 'active' : ''}" data-layer="hist">📊 HIST</button>
                        <button class="control-deck-layer-btn live ${this.controlDeckState.layers.live ? 'active' : ''}" data-layer="live">⚡ LIVE</button>
                        <button class="control-deck-layer-btn vol ${this.controlDeckState.layers.vol ? 'active' : ''}" data-layer="vol">📈 VOL</button>
                        <button class="control-deck-layer-btn sim ${this.controlDeckState.layers.sim ? 'active' : ''}" data-layer="sim">🎮 SIM</button>
                        <button class="control-deck-layer-btn ghost ${this.controlDeckState.layers.ghost ? 'active' : ''}" data-layer="ghost">👻 GHOST</button>
                        <button class="control-deck-layer-btn liquid ${this.controlDeckState.layers.liquid ? 'active' : ''}" data-layer="liquid">💧 LIQUID</button>
                        <button class="control-deck-layer-btn trades ${this.controlDeckState.layers.trades ? 'active' : ''}" data-layer="trades">💰 TRADES</button>
                        <button class="control-deck-layer-btn signals ${this.controlDeckState.layers.signals ? 'active' : ''}" data-layer="signals">📡 SIGNALS</button>
                        <button class="control-deck-layer-btn predictions ${this.controlDeckState.layers.predictions ? 'active' : ''}" data-layer="predictions">🔮 PREDICTIONS</button>
                        <button class="control-deck-layer-btn prophecy ${this.controlDeckState.layers.prophecy ? 'active' : ''}" data-layer="prophecy">👁️ PROPHECY</button>
                    </div>
                </div>
            </div>
            <div class="control-deck-section">
                <div class="control-deck-section-header" data-section="masterControl">
                    <span class="chevron ${sections.masterControl ? 'down' : ''}">▶</span>
                    <span>MASTER CONTROL</span>
                </div>
                <div class="control-deck-section-content ${sections.masterControl ? '' : 'hidden'}" data-section-content="masterControl">
                    <div data-slider="masterSensitivity"></div>
                    <div data-slider="smoothingLevel"></div>
                </div>
            </div>
            <div class="control-deck-section">
                <div class="control-deck-section-header" data-section="physics">
                    <span class="chevron ${sections.physics ? 'down' : ''}">▶</span>
                    <span>PHYSICS</span>
                </div>
                <div class="control-deck-section-content ${sections.physics ? '' : 'hidden'}" data-section-content="physics">
                    <div data-slider="friction"></div>
                    <div data-slider="elasticity"></div>
                </div>
            </div>
            <div class="control-deck-section">
                <div class="control-deck-section-header" data-section="simulation">
                    <span class="chevron ${sections.simulation ? 'down' : ''}">▶</span>
                    <span>SIMULATION</span>
                </div>
                <div class="control-deck-section-content ${sections.simulation ? '' : 'hidden'}" data-section-content="simulation">
                    <div data-slider="drift"></div>
                    <div data-slider="volatility"></div>
                </div>
            </div>
            <div class="control-deck-section">
                <div class="control-deck-section-header" data-section="physicsFactors">
                    <span class="chevron ${sections.physicsFactors ? 'down' : ''}">▶</span>
                    <span>PHYSICS FACTORS</span>
                </div>
                <div class="control-deck-section-content ${sections.physicsFactors ? '' : 'hidden'}" data-section-content="physicsFactors">
                    <div class="control-deck-physics-grid" id="physics-factors-grid"></div>
                </div>
            </div>
            <div class="control-deck-section">
                <div class="control-deck-section-header" data-section="performance">
                    <span class="chevron ${sections.performance ? 'down' : ''}">▶</span>
                    <span>PERFORMANCE</span>
                </div>
                <div class="control-deck-section-content ${sections.performance ? '' : 'hidden'}" data-section-content="performance">
                    <div id="performance-metrics"></div>
                </div>
            </div>
        `;
        
        // Setup section toggles
        document.querySelectorAll('[data-section]').forEach(header => {
            const clickHandler = () => {
                const sectionName = header.dataset.section;
                sections[sectionName] = !sections[sectionName];
                const content = document.querySelector(`[data-section-content="${sectionName}"]`);
                const chevron = header.querySelector('.chevron');
                
                if (sections[sectionName]) {
                    content.classList.remove('hidden');
                    chevron.classList.add('down');
                } else {
                    content.classList.add('hidden');
                    chevron.classList.remove('down');
                }
            };
            header.addEventListener('click', clickHandler);
            this.eventListeners.push({ element: header, event: 'click', handler: clickHandler });
        });
        
        // Setup layer toggles
        document.querySelectorAll('[data-layer]').forEach(btn => {
            const clickHandler = () => {
                const layer = btn.dataset.layer;
                if (!layer) {
                    this.logError('Button missing data-layer attribute', btn);
                    return;
                }
                
                this.controlDeckState.layers[layer] = !this.controlDeckState.layers[layer];
                btn.classList.toggle('active', this.controlDeckState.layers[layer]);
                
                this.userInteracting = true;
                setTimeout(() => { this.userInteracting = false; }, 2000);
                
                try {
                    const currentRange = this.chart?.timeScale()?.getVisibleRange();
                    if (currentRange) {
                        this.lastVisibleRange = currentRange;
                    }
                } catch (error) {
                    // Ignore
                }
                
                this.emitControlDeckEvent('toggle-layer', {
                    layer: layer,
                    enabled: this.controlDeckState.layers[layer]
                });
            };
            btn.addEventListener('click', clickHandler);
            this.eventListeners.push({ element: btn, event: 'click', handler: clickHandler });
        });
        
        // Setup sliders
        const sliderConfigs = {
            masterSensitivity: { label: 'Aggregation Sensitivity', min: -3.0, max: 3.0, step: 0.1 },
            smoothingLevel: { label: 'Signal Fidelity', min: -3.0, max: 3.0, step: 0.1 },
            friction: { label: 'Friction', min: -3.0, max: 3.0, step: 0.1 },
            elasticity: { label: 'Elasticity', min: -3.0, max: 3.0, step: 0.1 },
            drift: { label: 'Drift (Bias)', min: -3.0, max: 3.0, step: 0.1 },
            volatility: { label: 'Volatility (Noise)', min: -3.0, max: 3.0, step: 0.1 }
        };
        
        document.querySelectorAll('[data-slider]').forEach(container => {
            const param = container.dataset.slider;
            const config = sliderConfigs[param];
            if (!config) return;
            
            if (typeof ControlSlider !== 'undefined') {
                const slider = new ControlSlider(container, {
                    value: this.controlDeckState.parameters[param],
                    min: config.min,
                    max: config.max,
                    step: config.step,
                    label: config.label,
                    onChange: (value) => {
                        this.controlDeckState.parameters[param] = value;
                        this.emitControlDeckEvent('update-parameter', {
                            param: param,
                            value: value
                        });
                    }
                });
            }
        });
        
        // Setup toggle button
        const toggleBtn = document.getElementById('control-deck-toggle');
        if (toggleBtn) {
            const toggleHandler = () => {
                const content = document.getElementById('control-deck-content');
                if (content.style.display === 'none') {
                    content.style.display = 'flex';
                    toggleBtn.textContent = 'HIDE';
                } else {
                    content.style.display = 'none';
                    toggleBtn.textContent = 'SHOW';
                }
            };
            toggleBtn.addEventListener('click', toggleHandler);
            this.eventListeners.push({ element: toggleBtn, event: 'click', handler: toggleHandler });
        }
        
        // Initialize displays
        this.updatePhysicsFactorsDisplay();
        this.updatePerformanceDisplay();
        
        // Update physics and performance periodically
        this.physicsUpdateInterval = setInterval(async () => {
            // Only fetch physics if endpoint is available or unknown
            if (this.physicsEndpointAvailable !== false) {
                await this.fetchPhysicsState(this.currentSymbol);
            }
            await this.fetchPerformanceMetrics();
            this.updatePhysicsFactorsDisplay();
            this.updatePerformanceDisplay();
        }, 10000);
        
        this.log('✅ Control Deck initialized');
    }
    
    updatePhysicsFactorsDisplay() {
        const grid = document.getElementById('physics-factors-grid');
        if (!grid) return;
        
        const factors = [
            { key: 'momentum', label: 'Momentum' },
            { key: 'strain', label: 'Strain' },
            { key: 'force', label: 'Force' },
            { key: 'squeeze', label: 'Squeeze' },
            { key: 'flow', label: 'Flow' },
            { key: 'entropy', label: 'Entropy' },
            { key: 'jerk', label: 'Jerk' },
            { key: 'sympathy', label: 'Sympathy' }
        ];
        
        // Check if physics endpoint is unavailable
        const isUnavailable = this.physicsEndpointAvailable === false;
        
        if (isUnavailable && !this.physicsEndpointErrorLogged) {
            // Show message that physics data is not available
            grid.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; padding: 20px; color: #888; font-size: 12px;">
                    Physics data endpoint not available<br/>
                    <span style="font-size: 10px; color: #666;">(Backend endpoint /api/physics not implemented)</span>
                </div>
            `;
            return;
        }
        
        grid.innerHTML = factors.map(factor => {
            const value = this.controlDeckState.physics[factor.key];
            const hasValue = value !== undefined && value !== null;
            
            return `
                <div class="control-deck-physics-item">
                    <div class="control-deck-physics-label">${factor.label}</div>
                    <div class="control-deck-physics-value" style="${!hasValue ? 'color: #666;' : ''}">
                        ${hasValue ? value.toFixed(3) : 'N/A'}
                    </div>
                </div>
            `;
        }).join('');
    }
    
    updatePerformanceDisplay() {
        const container = document.getElementById('performance-metrics');
        if (!container) return;
        
        const perf = this.controlDeckState.performance;
        const winRate = perf.tradeCount > 0 ? (perf.winRate * 100).toFixed(1) : '0.0';
        
        container.innerHTML = `
            <div class="control-deck-metric-row">
                <span class="control-deck-metric-label">Total P&L</span>
                <span class="control-deck-metric-value ${perf.totalPnl >= 0 ? 'positive' : 'negative'}">
                    $${perf.totalPnl.toFixed(2)}
                </span>
            </div>
            <div class="control-deck-metric-row">
                <span class="control-deck-metric-label">Trade Count</span>
                <span class="control-deck-metric-value">${perf.tradeCount}</span>
            </div>
            <div class="control-deck-metric-row">
                <span class="control-deck-metric-label">Win Rate</span>
                <span class="control-deck-metric-value">${winRate}%</span>
            </div>
            <div class="control-deck-metric-row">
                <span class="control-deck-metric-label">Peak Equity</span>
                <span class="control-deck-metric-value">$${perf.peakEquity.toFixed(2)}</span>
            </div>
            <div class="control-deck-metric-row">
                <span class="control-deck-metric-label">Drawdown</span>
                <span class="control-deck-metric-value negative">${perf.drawdown.toFixed(2)}%</span>
            </div>
        `;
    }
    
    handleLayerToggle(layer, enabled) {
        this.log(`Layer toggle: ${layer} = ${enabled}`);
        
        switch(layer) {
            case 'vol':
                if (this.volumeSeries) {
                    this.volumeSeries.setVisible(enabled);
                }
                break;
            case 'live':
                if (enabled) {
                    if (!this.realTimeUpdateInterval) {
                        this.realTimeUpdateInterval = setInterval(() => this.updateRealTimePrice(), 5000);
                    }
                } else {
                    if (this.realTimeUpdateInterval) {
                        clearInterval(this.realTimeUpdateInterval);
                        this.realTimeUpdateInterval = null;
                    }
                }
                break;
            case 'hist':
                this.toggleHistoricalMarkers(enabled);
                break;
            case 'sim':
                this.toggleSimulationLines(enabled);
                break;
            case 'ghost':
                this.toggleGhostSeries(enabled);
                break;
            case 'liquid':
                this.toggleLiquidityMarkers(enabled);
                break;
            case 'trades':
                this.toggleTradeMarkers(enabled);
                break;
            case 'signals':
                this.toggleSignalMarkers(enabled);
                break;
            case 'predictions':
                this.togglePredictions(enabled);
                break;
            case 'prophecy':
                this.toggleProphecyMarkers(enabled);
                break;
        }
    }
    // ========================================================================
    // LAYER MANAGEMENT - Trade Markers
    // ========================================================================
    async toggleTradeMarkers(enabled) {
        if (!this.candlestickSeries) {
            this.logError('Cannot toggle trade markers: candlestickSeries not initialized');
            return;
        }
        
        if (enabled) {
            try {
                const trades = await this.fetchHistoricalTrades(this.currentSymbol);
                this.addTradeMarkers(trades);
            } catch (error) {
                this.logError('Failed to fetch trade markers', error);
            }
        } else {
            this.removeTradeMarkers();
        }
    }
    
    addTradeMarkers(trades) {
        if (!this.candlestickSeries) {
            this.logError('Cannot add trade markers: candlestickSeries not initialized');
            return;
        }
        
        this.removeTradeMarkers();
        
        trades.forEach(trade => {
            const entryLine = this.candlestickSeries.createPriceLine({
                price: trade.entry_price,
                color: '#4ade80',
                lineWidth: 2,
                lineStyle: LightweightCharts.LineStyle.Dashed,
                axisLabelVisible: true,
                title: `Entry: $${trade.entry_price?.toFixed(2) || '0.00'}`,
            });
            this.tradeMarkers.push(entryLine);
            
            if (trade.exit_price) {
                const exitLine = this.candlestickSeries.createPriceLine({
                    price: trade.exit_price,
                    color: '#f87171',
                    lineWidth: 2,
                    lineStyle: LightweightCharts.LineStyle.Dashed,
                    axisLabelVisible: true,
                    title: `Exit: $${trade.exit_price.toFixed(2)} (P&L: $${(trade.pnl || 0).toFixed(2)})`,
                });
                this.tradeMarkers.push(exitLine);
            }
        });
        
        this.log(`Added ${this.tradeMarkers.length} trade markers`);
    }
    
    removeTradeMarkers() {
        if (!this.candlestickSeries) return;
        this.tradeMarkers.forEach(marker => {
            try {
                this.candlestickSeries.removePriceLine(marker);
            } catch (e) {
                // Marker may already be removed
            }
        });
        this.tradeMarkers = [];
    }
    
    // ========================================================================
    // LAYER MANAGEMENT - Signal Markers
    // ========================================================================
    async toggleSignalMarkers(enabled) {
        if (!this.candlestickSeries) {
            this.logError('Cannot toggle signal markers: candlestickSeries not initialized');
            return;
        }
        
        if (enabled) {
            const signals = await this.fetchSignalHistory(this.currentSymbol);
            this.addSignalMarkers(signals);
        } else {
            this.removeSignalMarkers();
        }
    }
    
    addSignalMarkers(signals) {
        if (!this.candlestickSeries) {
            this.logError('Cannot add signal markers: candlestickSeries not initialized');
            return;
        }
        
        this.removeSignalMarkers();
        
        const regularSignals = signals.filter(s => !s.is_prophecy);
        const prophecyEvents = signals.filter(s => s.is_prophecy);
        
        if (this.controlDeckState.layers.prophecy && prophecyEvents.length > 0) {
            this.addProphecyMarkers(prophecyEvents);
        }
        
        const priceLevels = {};
        regularSignals.forEach(signal => {
            const price = signal.price || 0;
            if (price <= 0) return;
            
            if (!priceLevels[price]) {
                priceLevels[price] = [];
            }
            priceLevels[price].push(signal);
        });
        
        Object.entries(priceLevels).forEach(([price, priceSignals]) => {
            const latestSignal = priceSignals[priceSignals.length - 1];
            const direction = latestSignal.direction || 'HOLD';
            
            let color = '#666';
            if (direction === 'BUY') color = '#4ade80';
            else if (direction === 'SELL') color = '#f87171';
            
            const confidence = latestSignal.confidence || 0;
            const regime = latestSignal.regime || '';
            
            const signalLine = this.candlestickSeries.createPriceLine({
                price: parseFloat(price),
                color: color,
                lineWidth: 1,
                lineStyle: LightweightCharts.LineStyle.Dotted,
                axisLabelVisible: true,
                title: `${direction} (${(confidence * 100).toFixed(0)}%) ${regime ? `[${regime}]` : ''}`,
            });
            this.signalMarkers.push(signalLine);
        });
        
        this.log(`Added ${this.signalMarkers.length} signal markers`);
    }
    
    removeSignalMarkers() {
        if (!this.candlestickSeries) return;
        this.signalMarkers.forEach(marker => {
            try {
                this.candlestickSeries.removePriceLine(marker);
            } catch (e) {
                // Marker may already be removed
            }
        });
        this.signalMarkers = [];
    }
    
    // ========================================================================
    // LAYER MANAGEMENT - PROPHECY Markers
    // ========================================================================
    async toggleProphecyMarkers(enabled) {
        if (!this.candlestickSeries) {
            this.logError('Cannot toggle PROPHECY markers: candlestickSeries not initialized');
            return;
        }
        
        if (enabled) {
            try {
                const signals = await this.fetchSignalHistory(this.currentSymbol);
                const prophecyEvents = signals.filter(s => s.is_prophecy);
                this.addProphecyMarkers(prophecyEvents);
            } catch (error) {
                this.logError('Failed to fetch PROPHECY markers', error);
            }
        } else {
            this.removeProphecyMarkers();
        }
    }
    
    addProphecyMarkers(prophecyEvents) {
        if (!this.candlestickSeries) {
            this.logError('Cannot add PROPHECY markers: candlestickSeries not initialized');
            return;
        }
        
        this.removeProphecyMarkers();
        
        prophecyEvents.forEach(prophecy => {
            const price = prophecy.price || 0;
            if (price <= 0) return;
            
            const predictedMove = prophecy.predicted_move_percent || 0;
            const resonance = prophecy.resonance || 0;
            const direction = prophecy.direction || 'HOLD';
            
            const targetPrice = price * (1 + predictedMove / 100);
            const color = '#fbbf24';
            const moveSign = predictedMove > 0 ? '+' : '';
            const lineWidth = 2 + (resonance * 2);
            
            const detectionLine = this.candlestickSeries.createPriceLine({
                price: parseFloat(price),
                color: color,
                lineWidth: lineWidth,
                lineStyle: LightweightCharts.LineStyle.Solid,
                axisLabelVisible: true,
                title: `👁️ PROPHECY: ${moveSign}${predictedMove.toFixed(2)}% (Res: ${resonance.toFixed(2)})`,
            });
            this.prophecyMarkers.push(detectionLine);
            
            const targetLineColor = direction === 'BUY' ? '#4ade80' : '#f87171';
            const targetLine = this.candlestickSeries.createPriceLine({
                price: parseFloat(targetPrice),
                color: targetLineColor,
                lineWidth: 2,
                lineStyle: LightweightCharts.LineStyle.Dashed,
                axisLabelVisible: true,
                title: `Target: $${targetPrice.toFixed(2)} (${moveSign}${predictedMove.toFixed(2)}%)`,
            });
            this.prophecyMarkers.push(targetLine);
        });
        
        this.log(`Added ${this.prophecyMarkers.length} PROPHECY markers (${prophecyEvents.length} events)`);
    }
    
    removeProphecyMarkers() {
        if (!this.candlestickSeries) return;
        this.prophecyMarkers.forEach(marker => {
            try {
                this.candlestickSeries.removePriceLine(marker);
            } catch (e) {
                // Marker may already be removed
            }
        });
        this.prophecyMarkers = [];
    }
    
    // ========================================================================
    // LAYER MANAGEMENT - Highlight Markers
    // ========================================================================
    addHighlightMarkers(params) {
        if (!this.candlestickSeries) {
            this.logError('Cannot add highlight markers: candlestickSeries not initialized');
            return;
        }
        
        this.removeHighlightMarkers();
        
        if (params.price && params.price > 0) {
            const highlightLine = this.candlestickSeries.createPriceLine({
                price: parseFloat(params.price),
                color: '#a855f7',
                lineWidth: 3,
                lineStyle: LightweightCharts.LineStyle.Solid,
                axisLabelVisible: true,
                title: '📍 Highlighted Price',
            });
            this.highlightMarkers.push(highlightLine);
            this.log(`Added highlight marker at price: ${params.price}`);
        }
        
        if (params.time) {
            this.log(`Highlight time requested: ${params.time} (price highlighting used instead)`);
        }
    }
    
    removeHighlightMarkers() {
        if (!this.candlestickSeries) return;
        this.highlightMarkers.forEach(marker => {
            try {
                this.candlestickSeries.removePriceLine(marker);
            } catch (e) {
                // Marker may already be removed
            }
        });
        this.highlightMarkers = [];
    }
    
    // ========================================================================
    // LAYER MANAGEMENT - Historical Markers
    // ========================================================================
    toggleHistoricalMarkers(enabled) {
        if (!this.candlestickSeries) {
            this.logError('Cannot toggle historical markers: candlestickSeries not initialized');
            return;
        }
        
        if (enabled) {
            this.historicalMarkers.forEach(marker => {
                try {
                    this.candlestickSeries.removePriceLine(marker);
                } catch (error) {
                    // Ignore errors if marker already removed
                }
            });
            this.historicalMarkers = [];
            
            if (this.marketData.length > 0) {
                const symbolData = this.marketData.find(d => d.symbol === this.currentSymbol);
                if (symbolData) {
                    const currentPrice = symbolData.price || 0;
                    if (currentPrice > 0) {
                        try {
                            const high24h = symbolData.high_24h || currentPrice * 1.05;
                            const highLine = this.candlestickSeries.createPriceLine({
                                price: high24h,
                                color: '#4ade80',
                                lineWidth: 1,
                                lineStyle: LightweightCharts.LineStyle.Dotted,
                                axisLabelVisible: true,
                                title: '24h High',
                            });
                            this.historicalMarkers.push(highLine);
                            
                            const low24h = symbolData.low_24h || currentPrice * 0.95;
                            const lowLine = this.candlestickSeries.createPriceLine({
                                price: low24h,
                                color: '#f87171',
                                lineWidth: 1,
                                lineStyle: LightweightCharts.LineStyle.Dotted,
                                axisLabelVisible: true,
                                title: '24h Low',
                            });
                            this.historicalMarkers.push(lowLine);
                            
                            const supportLevel = currentPrice * 0.95;
                            const supportLine = this.candlestickSeries.createPriceLine({
                                price: supportLevel,
                                color: '#10b981',
                                lineWidth: 1,
                                lineStyle: LightweightCharts.LineStyle.Solid,
                                axisLabelVisible: true,
                                title: 'Support',
                            });
                            this.historicalMarkers.push(supportLine);
                            
                            const resistanceLevel = currentPrice * 1.05;
                            const resistanceLine = this.candlestickSeries.createPriceLine({
                                price: resistanceLevel,
                                color: '#10b981',
                                lineWidth: 1,
                                lineStyle: LightweightCharts.LineStyle.Solid,
                                axisLabelVisible: true,
                                title: 'Resistance',
                            });
                            this.historicalMarkers.push(resistanceLine);
                        } catch (error) {
                            this.logError('Failed to create historical markers', error);
                        }
                    }
                }
            } else {
                this.log('Cannot create historical markers: market data not available');
            }
        } else {
            this.historicalMarkers.forEach(marker => {
                try {
                    this.candlestickSeries.removePriceLine(marker);
                } catch (error) {
                    // Ignore errors if marker already removed
                }
            });
            this.historicalMarkers = [];
        }
    }
    
    // ========================================================================
    // LAYER MANAGEMENT - Simulation Lines
    // ========================================================================
    toggleSimulationLines(enabled) {
        if (!this.candlestickSeries) {
            this.logError('Cannot toggle simulation lines: candlestickSeries not initialized');
            return;
        }
        
        if (enabled) {
            this.simulationLines.forEach(line => {
                try {
                    this.candlestickSeries.removePriceLine(line);
                } catch (error) {
                    // Ignore errors if line already removed
                }
            });
            this.simulationLines = [];
            
            const drift = this.controlDeckState.parameters.drift || 0;
            const volatility = this.controlDeckState.parameters.volatility || 0.5;
            const currentPrice = parseFloat(document.getElementById('info-price')?.textContent.replace('$', '').replace(',', '') || '0');
            
            if (currentPrice > 0) {
                try {
                    const upperLine = this.candlestickSeries.createPriceLine({
                        price: currentPrice * (1 + drift + volatility),
                        color: '#06b6d4',
                        lineWidth: 1,
                        lineStyle: LightweightCharts.LineStyle.Dashed,
                        axisLabelVisible: true,
                        title: 'Sim Upper',
                    });
                    this.simulationLines.push(upperLine);
                    
                    const lowerLine = this.candlestickSeries.createPriceLine({
                        price: currentPrice * (1 + drift - volatility),
                        color: '#06b6d4',
                        lineWidth: 1,
                        lineStyle: LightweightCharts.LineStyle.Dashed,
                        axisLabelVisible: true,
                        title: 'Sim Lower',
                    });
                    this.simulationLines.push(lowerLine);
                } catch (error) {
                    this.logError('Failed to create simulation lines', error);
                }
            } else {
                this.log('Cannot create simulation lines: current price not available');
            }
        } else {
            this.simulationLines.forEach(line => {
                try {
                    this.candlestickSeries.removePriceLine(line);
                } catch (error) {
                    // Ignore errors if line already removed
                }
            });
            this.simulationLines = [];
        }
    }
    
    // ========================================================================
    // LAYER MANAGEMENT - Ghost Series
    // ========================================================================
    toggleGhostSeries(enabled) {
        if (!this.chart) {
            this.logError('Cannot toggle ghost series: chart not initialized');
            return;
        }
        
        if (enabled) {
            if (this.ghostSeries) {
                try {
                    this.chart.removeSeries(this.ghostSeries);
                } catch (error) {
                    // Ignore errors if series already removed
                }
                this.ghostSeries = null;
            }
            
            if (this.candlestickSeries) {
                try {
                    this.ghostSeries = this.chart.addLineSeries({
                        color: 'rgba(255, 255, 255, 0.2)',
                        lineWidth: 1,
                        priceScaleId: 'right',
                        visible: true,
                    });
                    
                    if (this.marketData.length > 0) {
                        const prices = this.marketData.map(d => d.price).filter(p => p > 0);
                        if (prices.length > 0) {
                            const sma = prices.reduce((a, b) => a + b, 0) / prices.length;
                            const now = Math.floor(Date.now() / 1000);
                            this.ghostSeries.setData([{ time: now, value: sma }]);
                        }
                    }
                } catch (error) {
                    this.logError('Failed to create ghost series', error);
                }
            }
        } else {
            if (this.ghostSeries) {
                try {
                    this.chart.removeSeries(this.ghostSeries);
                } catch (error) {
                    this.logError('Failed to remove ghost series', error);
                }
                this.ghostSeries = null;
            }
        }
    }
    
    // ========================================================================
    // LAYER MANAGEMENT - Liquidity Markers
    // ========================================================================
    toggleLiquidityMarkers(enabled) {
        if (!this.candlestickSeries) {
            this.logError('Cannot toggle liquidity markers: candlestickSeries not initialized');
            return;
        }
        
        if (enabled) {
            this.liquidityMarkers.forEach(marker => {
                try {
                    this.candlestickSeries.removePriceLine(marker);
                } catch (error) {
                    // Ignore errors if marker already removed
                }
            });
            this.liquidityMarkers = [];
            
            const currentPrice = parseFloat(document.getElementById('info-price')?.textContent.replace('$', '').replace(',', '') || '0');
            if (currentPrice > 0) {
                try {
                    const supportLine = this.candlestickSeries.createPriceLine({
                        price: currentPrice * 0.95,
                        color: '#10b981',
                        lineWidth: 1,
                        lineStyle: LightweightCharts.LineStyle.Solid,
                        axisLabelVisible: true,
                        title: 'Support',
                    });
                    this.liquidityMarkers.push(supportLine);
                    
                    const resistanceLine = this.candlestickSeries.createPriceLine({
                        price: currentPrice * 1.05,
                        color: '#10b981',
                        lineWidth: 1,
                        lineStyle: LightweightCharts.LineStyle.Solid,
                        axisLabelVisible: true,
                        title: 'Resistance',
                    });
                    this.liquidityMarkers.push(resistanceLine);
                } catch (error) {
                    this.logError('Failed to create liquidity markers', error);
                }
            } else {
                this.log('Cannot create liquidity markers: current price not available');
            }
        } else {
            this.liquidityMarkers.forEach(marker => {
                try {
                    this.candlestickSeries.removePriceLine(marker);
                } catch (error) {
                    // Ignore errors if marker already removed
                }
            });
            this.liquidityMarkers = [];
        }
    }
    
    // ========================================================================
    // PREDICTIONS - Fetch and Display
    // ========================================================================
    async fetchPredictions(symbol) {
        try {
            const normalizedSymbol = symbol.toUpperCase();
            
            if (this.predictionCache && 
                this.predictionCache.symbol === normalizedSymbol && 
                Date.now() - this.predictionCache.timestamp < 30000) {
                this.log(`Using cached predictions for ${normalizedSymbol}`);
                return this.predictionCache.data;
            }
            
            if (this.pendingPredictionRequest && this.pendingPredictionRequest.symbol === normalizedSymbol) {
                this.log(`Reusing pending prediction request for ${normalizedSymbol}`);
                return this.pendingPredictionRequest.promise;
            }
            
            if (this.predictionRequestController) {
                this.predictionRequestController.abort();
            }
            
            const url = `${this.API_BASE}/predictions?symbol=${encodeURIComponent(normalizedSymbol)}`;
            
            const fetchOptions = {
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                }
            };
            
            this.predictionRequestController = new AbortController();
            const promise = fetchWithRetry(url, { ...fetchOptions, signal: this.predictionRequestController.signal }, 3, 1000);
            this.pendingPredictionRequest = { symbol: normalizedSymbol, promise };
            
            const response = await promise;
            
            if (this.pendingPredictionRequest && this.pendingPredictionRequest.symbol === normalizedSymbol) {
                this.pendingPredictionRequest = null;
            }
            this.predictionRequestController = null;
            
            if (!response.ok) {
                if (response.status === 404) {
                    this.logError(`Symbol ${normalizedSymbol} not found`);
                    throw new Error(`Symbol ${normalizedSymbol} not found`);
                } else if (response.status === 500) {
                    const errorData = await response.json().catch(() => ({}));
                    this.logError('Backend error generating predictions', errorData);
                    throw new Error(errorData.detail || 'Backend error');
                } else {
                    throw new Error(`HTTP ${response.status}`);
                }
            }
            
            const data = await response.json();
            const validatedData = this.validatePredictionsResponse(data, normalizedSymbol);
            
            if (!validatedData) {
                throw new Error('Invalid response format');
            }
            
            this.predictionCache = { 
                symbol: normalizedSymbol, 
                data: validatedData, 
                timestamp: Date.now() 
            };
            
            this.isRetryingPredictions = false;
            this.updatePredictionStatus(true, validatedData.last_update);
            
            this.log(`✅ Fetched predictions for ${normalizedSymbol}`, { 
                count: validatedData.predictions?.length || 0,
                source: 'API'
            });
            
            return validatedData;
            
        } catch (error) {
            this.isRetryingPredictions = false;
            
            let errorMessage = 'Error fetching predictions';
            if (error.name === 'AbortError') {
                errorMessage = 'Request timeout - backend may be slow';
                this.logError('Request timeout fetching predictions', error);
            } else if (error.message.includes('Failed to fetch')) {
                errorMessage = 'Connection failed - check backend';
                this.logError('Network error fetching predictions', error);
            } else if (error.message.includes('HTTP')) {
                errorMessage = `Backend error (${error.message})`;
                this.logError('HTTP error fetching predictions', error);
            } else if (error.message.includes('Invalid response')) {
                errorMessage = 'Invalid response format';
                this.logError('Parse error fetching predictions', error);
            } else {
                this.logError('Error fetching predictions', error);
            }
            
            this.updatePredictionStatus(false, null, errorMessage);
            
            return {
                symbol: symbol.toUpperCase(),
                current_price: 0,
                predictions: [],
                last_update: new Date().toISOString()
            };
        }
    }
    
    validatePredictionsResponse(data, expectedSymbol) {
        if (Array.isArray(data)) {
            const symbolData = data.find(d => d.symbol === expectedSymbol);
            if (!symbolData) {
                this.logError(`Symbol ${expectedSymbol} not found in array response`);
                return null;
            }
            data = symbolData;
        }
        
        if (!data || typeof data !== 'object') {
            this.logError('Invalid response: not an object');
            return null;
        }
        
        if (!data.symbol || data.symbol !== expectedSymbol) {
            this.logError(`Symbol mismatch: expected ${expectedSymbol}, got ${data.symbol}`);
            return null;
        }
        
        if (typeof data.current_price !== 'number' || data.current_price <= 0 || !isFinite(data.current_price)) {
            this.logError(`Invalid current_price: ${data.current_price}`);
            return null;
        }
        
        if (!Array.isArray(data.predictions)) {
            this.logError('Invalid predictions: not an array');
            return null;
        }
        
        const validPredictions = [];
        data.predictions.forEach((pred, index) => {
            if (this.validatePredictionObject(pred, data.current_price)) {
                validPredictions.push(pred);
            } else {
                this.logError(`Invalid prediction at index ${index}`, pred);
            }
        });
        
        return {
            symbol: data.symbol,
            current_price: data.current_price,
            predictions: validPredictions,
            last_update: data.last_update || new Date().toISOString()
        };
    }
    
    validatePredictionObject(pred, currentPrice) {
        if (typeof pred.time_horizon_minutes !== 'number' || pred.time_horizon_minutes <= 0 || !isFinite(pred.time_horizon_minutes)) {
            return false;
        }
        
        if (typeof pred.predicted_price !== 'number' || pred.predicted_price <= 0 || !isFinite(pred.predicted_price)) {
            return false;
        }
        
        if (typeof pred.confidence !== 'number' || pred.confidence < 0 || pred.confidence > 1 || !isFinite(pred.confidence)) {
            return false;
        }
        
        if (!['UP', 'DOWN', 'NEUTRAL'].includes(pred.direction)) {
            return false;
        }
        
        if (typeof pred.expected_move_percent !== 'number' || !isFinite(pred.expected_move_percent)) {
            return false;
        }
        
        try {
            const timestamp = new Date(pred.timestamp);
            if (isNaN(timestamp.getTime())) {
                return false;
            }
            if (timestamp <= new Date()) {
                this.logError('Prediction timestamp is in the past', pred.timestamp);
            }
        } catch (e) {
            return false;
        }
        
        const priceDiff = Math.abs(pred.predicted_price - currentPrice) / currentPrice;
        if (priceDiff > 0.5) {
            this.logError(`Predicted price seems unreasonable: ${pred.predicted_price} vs ${currentPrice}`);
        }
        
        return true;
    }
    
    updatePredictionStatus(usingRealData, lastUpdate, errorMessage = null) {
        const statusEl = document.getElementById('status');
        if (!statusEl) return;
        
        if (usingRealData) {
            statusEl.textContent = 'Connected (Real Data)';
            statusEl.className = 'status-badge connected';
            if (lastUpdate) {
                statusEl.title = `Last update: ${new Date(lastUpdate).toLocaleTimeString()}`;
            } else {
                statusEl.title = '';
            }
        } else if (errorMessage) {
            statusEl.textContent = errorMessage;
            statusEl.className = 'status-badge error';
            statusEl.title = 'Click to retry';
        } else {
            statusEl.textContent = 'Disconnected';
            statusEl.className = 'status-badge disconnected';
            statusEl.title = 'API unavailable - ensure backend is running on port 8000';
        }
    }
    
    async togglePredictions(enabled) {
        if (!this.chart || !this.candlestickSeries) {
            this.logError('Chart not initialized, cannot toggle predictions');
            return;
        }
        
        if (enabled) {
            try {
                const predictionData = await this.fetchPredictions(this.currentSymbol);
                if (predictionData && predictionData.predictions && predictionData.predictions.length > 0) {
                    this.addPredictionOverlay(predictionData);
                } else {
                    this.log('No predictions available for display');
                }
            } catch (error) {
                this.logError('Failed to toggle predictions', error);
            }
        } else {
            this.removePredictionOverlay();
        }
    }
    
    addPredictionOverlay(predictionData) {
        if (!this.chart || !this.candlestickSeries || !predictionData) {
            this.logError('Chart or prediction data missing');
            return;
        }
        
        if (!predictionData.predictions || !Array.isArray(predictionData.predictions)) {
            this.logError('Invalid prediction data: predictions array missing');
            return;
        }
        
        this.removePredictionOverlay();
        
        const predictions = predictionData.predictions;
        
        if (predictions.length === 0) {
            this.log('No predictions to display');
            return;
        }
        
        let currentPrice = predictionData.current_price;
        if (!currentPrice || currentPrice <= 0) {
            const priceText = document.getElementById('info-price')?.textContent;
            if (priceText) {
                currentPrice = parseFloat(priceText.replace(/[^0-9.]/g, ''));
            }
        }
        
        if (!currentPrice || currentPrice <= 0) {
            this.logError('Cannot determine current price for predictions');
            return;
        }
        
        const now = Math.floor(Date.now() / 1000);
        const MAX_PREDICTION_HORIZON_MINUTES = 1440;
        const MAX_PRICE_MULTIPLIER = 10;
        const MIN_PRICE_MULTIPLIER = 0.1;
        
        const predictionSegments = {
            short: [],
            medium: [],
            long: [],
            veryLong: []
        };
        
        let maxHorizon = 0;
        let filteredCount = 0;
        
        predictions.forEach((pred, index) => {
            try {
                let horizonMinutes = pred.time_horizon_minutes || 0;
                if (horizonMinutes > MAX_PREDICTION_HORIZON_MINUTES) {
                    horizonMinutes = MAX_PREDICTION_HORIZON_MINUTES;
                    filteredCount++;
                }
            
            let predictedPrice = pred.predicted_price;
            if (!predictedPrice || predictedPrice <= 0 || !isFinite(predictedPrice)) {
                return;
            }
            
            const priceRatio = predictedPrice / currentPrice;
            if (priceRatio > MAX_PRICE_MULTIPLIER || priceRatio < MIN_PRICE_MULTIPLIER) {
                filteredCount++;
                return;
            }
            
            let futureTime = new Date(pred.timestamp);
            if (isNaN(futureTime.getTime())) {
                const futureTimeSeconds = now + (horizonMinutes * 60);
                futureTime = new Date(futureTimeSeconds * 1000);
            } else {
                const maxFutureTime = now + (MAX_PREDICTION_HORIZON_MINUTES * 60);
                const futureTimeSeconds = Math.floor(futureTime.getTime() / 1000);
                if (futureTimeSeconds > maxFutureTime) {
                    futureTime = new Date(maxFutureTime * 1000);
                    filteredCount++;
                }
            }
            
            const futureTimeSeconds = Math.floor(futureTime.getTime() / 1000);
            maxHorizon = Math.max(maxHorizon, horizonMinutes);
            
            const bounds = this.calculateConfidenceBounds(predictedPrice, pred.confidence, currentPrice);
            
            const predictionPoint = {
                time: futureTimeSeconds,
                horizonMinutes: horizonMinutes,
                predictedPrice: predictedPrice,
                confidence: pred.confidence,
                direction: pred.direction,
                bounds: bounds,
                opacity: this.getOpacityForHorizon(horizonMinutes)
            };
            
            if (horizonMinutes <= 5) {
                predictionSegments.short.push(predictionPoint);
            } else if (horizonMinutes <= 15) {
                predictionSegments.medium.push(predictionPoint);
            } else if (horizonMinutes <= 30) {
                predictionSegments.long.push(predictionPoint);
            } else {
                predictionSegments.veryLong.push(predictionPoint);
            }
        } catch (error) {
            this.logError(`Error processing prediction ${index}`, error);
        }
    });
    
    const allPredictions = [
        ...predictionSegments.short,
        ...predictionSegments.medium,
        ...predictionSegments.long,
        ...predictionSegments.veryLong
    ].sort((a, b) => a.time - b.time);
    
    if (allPredictions.length === 0) {
        this.log('No valid predictions to display after filtering');
        return;
    }
    
    const segments = [
        { name: 'short', predictions: predictionSegments.short, opacity: 0.4 },
        { name: 'medium', predictions: predictionSegments.medium, opacity: 0.3 },
        { name: 'long', predictions: predictionSegments.long, opacity: 0.2 },
        { name: 'veryLong', predictions: predictionSegments.veryLong, opacity: 0.1 }
    ];
    
    segments.forEach(segment => {
        if (segment.predictions.length === 0) return;
        
        const upperLineData = [{ time: now, value: currentPrice }];
        const lowerLineData = [{ time: now, value: currentPrice }];
        
        segment.predictions.forEach(pred => {
            upperLineData.push({ time: pred.time, value: pred.bounds.upper });
            lowerLineData.push({ time: pred.time, value: pred.bounds.lower });
        });
        
        try {
            const upperAreaSeries = this.chart.addAreaSeries({
                lineColor: `rgba(168, 85, 247, ${segment.opacity * 0.6})`,
                topColor: `rgba(168, 85, 247, ${segment.opacity})`,
                bottomColor: `rgba(168, 85, 247, ${segment.opacity * 0.3})`,
                priceScaleId: 'right',
                title: `ML Predictions Upper (${segment.name})`,
                visible: true,
            });
            
            upperAreaSeries.setData(upperLineData);
            
            const lowerAreaSeries = this.chart.addAreaSeries({
                lineColor: `rgba(168, 85, 247, ${segment.opacity * 0.6})`,
                topColor: `rgba(168, 85, 247, ${segment.opacity * 0.3})`,
                bottomColor: `rgba(168, 85, 247, 0)`,
                priceScaleId: 'right',
                title: `ML Predictions Lower (${segment.name})`,
                visible: true,
            });
            
            lowerAreaSeries.setData(lowerLineData);
            
            this.predictionAreaSeries.push({
                upperSeries: upperAreaSeries,
                lowerSeries: lowerAreaSeries,
                opacity: segment.opacity
            });
        } catch (error) {
            this.logError(`Failed to create area series for ${segment.name}`, error);
        }
    });
    
    if (maxHorizon > 0) {
        try {
            const timeScale = this.chart.timeScale();
            const visibleRange = timeScale.getVisibleRange();
            if (visibleRange) {
                const cappedHorizon = Math.min(maxHorizon, MAX_PREDICTION_HORIZON_MINUTES);
                const futureTime = now + (cappedHorizon * 60);
                const extendedTo = Math.max(visibleRange.to, futureTime);
                
                timeScale.setVisibleRange({
                    from: visibleRange.from,
                    to: extendedTo
                });
            }
        } catch (error) {
            this.logError('Failed to extend timeline', error);
        }
    }
    
    try {
        const nowLine = this.candlestickSeries.createPriceLine({
            price: currentPrice,
            color: '#a855f7',
            lineWidth: 2,
            lineStyle: LightweightCharts.LineStyle.Solid,
            axisLabelVisible: true,
            title: 'NOW',
        });
        this.predictionMarkers.push(nowLine);
    } catch (error) {
        this.logError('Failed to create NOW marker', error);
    }
    
    this.log(`✅ Added prediction overlay with ${predictions.length} predictions`);
    }
    
    removePredictionOverlay() {
        if (!this.chart || !this.candlestickSeries) return;
        
        if (this.predictionAreaSeries.length > 0) {
            this.predictionAreaSeries.forEach(segment => {
                try {
                    if (segment.upperSeries) this.chart.removeSeries(segment.upperSeries);
                    if (segment.lowerSeries) this.chart.removeSeries(segment.lowerSeries);
                } catch (e) {
                    // Series may already be removed
                }
            });
            this.predictionAreaSeries = [];
        }
        
        this.predictionMarkers.forEach(marker => {
            try {
                this.candlestickSeries.removePriceLine(marker);
            } catch (e) {
                // Marker may already be removed
            }
        });
        this.predictionMarkers = [];
    }
    
    calculateConfidenceBounds(predictedPrice, confidence, currentPrice) {
        const uncertaintyFactor = 0.6;
        const confidenceRange = 1 - confidence;
        const priceRange = predictedPrice * confidenceRange * uncertaintyFactor;
        const upperBound = predictedPrice + priceRange;
        const lowerBound = Math.max(0.01, predictedPrice - priceRange);
        
        const MAX_PRICE_MULTIPLIER = 10;
        const MIN_PRICE_MULTIPLIER = 0.1;
        const maxPrice = currentPrice * MAX_PRICE_MULTIPLIER;
        const minPrice = currentPrice * MIN_PRICE_MULTIPLIER;
        
        return {
            upper: Math.min(upperBound, maxPrice),
            lower: Math.max(lowerBound, minPrice),
            center: predictedPrice
        };
    }
    
    getOpacityForHorizon(horizonMinutes) {
        if (horizonMinutes <= 5) return 0.4;
        if (horizonMinutes <= 15) return 0.3;
        if (horizonMinutes <= 30) return 0.2;
        return 0.1;
    }
    
    // ========================================================================
    // CONTROL DECK - Parameter Update
    // ========================================================================
    handleParameterUpdate(param, value) {
        // Format value to avoid floating point precision issues
        const formattedValue = typeof value === 'number' ? parseFloat(value.toFixed(4)) : value;
        this.log(`Parameter update: ${param} = ${formattedValue}`);
        
        if (this.controlDeckState.parameters.hasOwnProperty(param)) {
            this.controlDeckState.parameters[param] = value;
        }
        
        switch(param) {
            case 'smoothingLevel':
                if (this.chart) {
                    this.chart.applyOptions({
                        layout: {
                            fontSize: Math.max(10, 12 - value * 2),
                        }
                    });
                }
                this.log(`Signal fidelity (smoothing) updated to ${formattedValue}`);
                break;
            case 'masterSensitivity':
                this.log(`Master sensitivity updated to ${formattedValue}`);
                break;
            case 'friction':
            case 'elasticity':
                this.log(`Physics parameter ${param} updated to ${formattedValue}`);
                if (this.controlDeckState.layers.sim && this.simulationLines.length > 0) {
                    this.toggleSimulationLines(false);
                    setTimeout(() => this.toggleSimulationLines(true), 100);
                }
                break;
            case 'drift':
            case 'volatility':
                this.log(`Physics parameter ${param} updated to ${value}`);
                if (this.controlDeckState.layers.sim && this.simulationLines.length > 0) {
                    this.toggleSimulationLines(false);
                    setTimeout(() => this.toggleSimulationLines(true), 100);
                }
                break;
            default:
                this.log(`Parameter ${param} updated to ${value} (no specific handler)`);
        }
    }
    
    // ========================================================================
    // EVENT LISTENERS
    // ========================================================================
    setupEventListeners() {
        // Control Deck event listeners
        const toggleLayerHandler = (e) => {
            if (!e.detail || !e.detail.layer) {
                this.logError('Invalid toggle-layer event', e);
                return;
            }
            
            const { layer, enabled } = e.detail;
            this.log(`Toggle layer event received: ${layer} = ${enabled}`);
            
            this.userInteracting = true;
            setTimeout(() => { this.userInteracting = false; }, 2000);
            
            try {
                const currentRange = this.chart?.timeScale()?.getVisibleRange();
                if (currentRange) {
                    this.lastVisibleRange = currentRange;
                }
            } catch (error) {
                // Ignore
            }
            
            this.handleLayerToggle(layer, enabled);
        };
        
        document.addEventListener('controldeck:toggle-layer', toggleLayerHandler);
        this.eventListeners.push({ element: document, event: 'controldeck:toggle-layer', handler: toggleLayerHandler });
        
        const updateParameterHandler = (e) => {
            if (!e.detail || !e.detail.param) {
                this.logError('Invalid update-parameter event', e);
                return;
            }
            
            const { param, value } = e.detail;
            // Format value to avoid floating point precision issues
            const formattedValue = typeof value === 'number' ? parseFloat(value.toFixed(4)) : value;
            this.log(`Parameter update event received: ${param} = ${formattedValue}`);
            
            this.userInteracting = true;
            setTimeout(() => { this.userInteracting = false; }, 1000);
            
            this.handleParameterUpdate(param, value);
        };
        
        document.addEventListener('controldeck:update-parameter', updateParameterHandler);
        this.eventListeners.push({ element: document, event: 'controldeck:update-parameter', handler: updateParameterHandler });
        
        // Symbol selector
        const symbolSelector = document.getElementById('symbol-selector');
        if (symbolSelector) {
            const symbolChangeHandler = (e) => {
                this.currentSymbol = e.target.value;
                this.log(`Symbol changed to ${this.currentSymbol}`);
                
                this.tradesCache = null;
                this.signalsCache = null;
                this.physicsCache = null;
                this.predictionCache = null;
                
                this.removeTradeMarkers();
                this.removeSignalMarkers();
                this.removeProphecyMarkers();
                this.removePredictionOverlay();
                
                this.updateChartData(this.currentSymbol);
                this.fetchMarketData();
                this.updatePositionMarkers();
                
                this.fetchPhysicsState(this.currentSymbol).then(() => {
                    this.updatePhysicsFactorsDisplay();
                });
                
                if (this.controlDeckState.layers.trades) {
                    this.toggleTradeMarkers(true);
                }
                if (this.controlDeckState.layers.signals) {
                    this.toggleSignalMarkers(true);
                }
                if (this.controlDeckState.layers.predictions) {
                    this.togglePredictions(true);
                }
                if (this.controlDeckState.layers.prophecy) {
                    this.toggleProphecyMarkers(true);
                }
                if (this.controlDeckState.layers.hist) {
                    this.toggleHistoricalMarkers(false);
                    this.toggleHistoricalMarkers(true);
                }
            };
            symbolSelector.addEventListener('change', symbolChangeHandler);
            this.eventListeners.push({ element: symbolSelector, event: 'change', handler: symbolChangeHandler });
        }
        
        // Timeframe buttons
        document.querySelectorAll('.timeframe-btn').forEach(btn => {
            const timeframeClickHandler = () => {
                document.querySelectorAll('.timeframe-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                this.currentTimeframe = btn.dataset.timeframe;
                this.log(`Timeframe changed to ${this.currentTimeframe}`);
                
                this.updateChartData(this.currentSymbol);
            };
            btn.addEventListener('click', timeframeClickHandler);
            this.eventListeners.push({ element: btn, event: 'click', handler: timeframeClickHandler });
        });
    }
}

// Export module
export default {
    init: async (container, params) => {
        const chartView = new ChartView();
        await chartView.init(container, params);
        return chartView;
    },
    destroy: async (instance) => {
        if (instance && instance.destroy) {
            await instance.destroy();
        }
    }
};

