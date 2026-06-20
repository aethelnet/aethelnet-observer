// This file contains all the remaining method implementations
// to be inserted into chartview-new.js

// Layer Management Methods
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

// Prediction Methods
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

// Control Deck Parameter Update
handleParameterUpdate(param, value) {
    this.log(`Parameter update: ${param} = ${value}`);
    
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
            this.log(`Signal fidelity (smoothing) updated to ${value}`);
            break;
        case 'masterSensitivity':
            this.log(`Master sensitivity updated to ${value}`);
            break;
        case 'friction':
        case 'elasticity':
            this.log(`Physics parameter ${param} updated to ${value}`);
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

// Event Listeners
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
        this.log(`Parameter update event received: ${param} = ${value}`);
        
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



