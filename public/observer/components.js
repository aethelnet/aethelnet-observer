/**
 * Aethelnet Observer Custom Web Components
 * Sleek, brutalist, high-performance UI components for the GNN Canvas.
 */

// Metrics Card Component
class MetricsCardComponent extends HTMLElement {
    constructor() {
        super();
        this._value = '--';
        this._label = 'Metric';
        this._trend = 'neutral';
        this._color = 'var(--accent-blue)';
    }

    static get observedAttributes() {
        return ['label', 'value', 'trend', 'color'];
    }

    attributeChangedCallback(name, oldValue, newValue) {
        if (name === 'label') this._label = newValue || 'Metric';
        else if (name === 'value') {
            const oldVal = this._value;
            this._value = newValue || '--';
            if (oldVal !== '--' && oldVal !== newValue) {
                this.triggerFlash();
            }
        }
        else if (name === 'trend') this._trend = newValue || 'neutral';
        else if (name === 'color') this._color = newValue || 'var(--accent-blue)';
        this.render();
    }

    connectedCallback() {
        this._label = this.getAttribute('label') || 'Metric';
        this._value = this.getAttribute('value') || '--';
        this._trend = this.getAttribute('trend') || 'neutral';
        this._color = this.getAttribute('color') || 'var(--accent-blue)';
        this.render();
    }

    triggerFlash() {
        const card = this.querySelector('.metrics-card');
        if (card) {
            card.classList.add('flash-update');
            setTimeout(() => card.classList.remove('flash-update'), 400);
        }
    }

    render() {
        // Determine trend style
        let trendIndicator = '';
        let trendColor = 'var(--text-color)';
        if (this._trend === 'positive') {
            trendIndicator = '▲';
            trendColor = 'var(--accent-blue)';
        } else if (this._trend === 'negative') {
            trendIndicator = '▼';
            trendColor = 'var(--accent-red)';
        }

        this.innerHTML = `
            <style>
                .metrics-card {
                    background: rgba(255, 255, 255, 0.95);
                    border: 3px solid #1A1A1A;
                    box-shadow: 4px 4px 0px #1A1A1A;
                    padding: 12px 16px;
                    min-width: 140px;
                    display: flex;
                    flex-direction: column;
                    justify-content: space-between;
                    font-family: var(--font-mono);
                    transition: all 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                    user-select: none;
                }
                .metrics-card:hover {
                    transform: translate(-2px, -2px);
                    box-shadow: 6px 6px 0px #1A1A1A;
                    border-color: var(--accent-red);
                }
                .metrics-label {
                    font-size: 0.7rem;
                    text-transform: uppercase;
                    color: #666;
                    font-weight: 700;
                    letter-spacing: 1px;
                    margin-bottom: 6px;
                }
                .metrics-value-container {
                    display: flex;
                    align-items: baseline;
                    gap: 6px;
                }
                .metrics-value {
                    font-size: 1.4rem;
                    font-weight: bold;
                    color: #1A1A1A;
                }
                .metrics-trend {
                    font-size: 0.8rem;
                    font-weight: bold;
                    color: ${trendColor};
                }
                .flash-update {
                    background: var(--accent-yellow) !important;
                    transform: scale(1.05) !important;
                }
            </style>
            <div class="metrics-card">
                <div class="metrics-label">${this._label}</div>
                <div class="metrics-value-container">
                    <span class="metrics-value" style="border-bottom: 2px solid ${this._color};">${this._value}</span>
                    ${trendIndicator ? `<span class="metrics-trend">${trendIndicator}</span>` : ''}
                </div>
            </div>
        `;
    }
}

customElements.define('component-metrics-card', MetricsCardComponent);

// System Status Component (Connection indicator + Ping + System Info)
class SystemStatusComponent extends HTMLElement {
    constructor() {
        super();
        this._connected = false;
        this._ping = 0;
        this._fps = 60;
    }

    static get observedAttributes() {
        return ['connected', 'ping', 'fps'];
    }

    attributeChangedCallback(name, oldValue, newValue) {
        if (name === 'connected') this._connected = newValue === 'true';
        else if (name === 'ping') this._ping = parseInt(newValue) || 0;
        else if (name === 'fps') this._fps = parseInt(newValue) || 60;
        this.render();
    }

    connectedCallback() {
        this._connected = this.getAttribute('connected') === 'true';
        this._ping = parseInt(this.getAttribute('ping')) || 0;
        this._fps = parseInt(this.getAttribute('fps')) || 60;
        this.render();
    }

    render() {
        const lightColor = this._connected ? 'var(--accent-blue)' : 'var(--accent-red)';
        const statusText = this._connected ? 'SYNCHRONIZED' : 'OFFLINE';

        this.innerHTML = `
            <style>
                .status-widget {
                    background: rgba(255, 255, 255, 0.95);
                    border: 3px solid #1A1A1A;
                    box-shadow: 4px 4px 0px #1A1A1A;
                    padding: 12px 16px;
                    display: flex;
                    align-items: center;
                    gap: 15px;
                    font-family: var(--font-mono);
                }
                .status-indicator-led {
                    width: 14px;
                    height: 14px;
                    background: ${lightColor};
                    border: 2px solid #1A1A1A;
                    box-shadow: 0 0 8px ${lightColor};
                    animation: pulse-led 2s infinite alternate;
                }
                .status-info {
                    display: flex;
                    flex-direction: column;
                }
                .status-title {
                    font-size: 0.8rem;
                    font-weight: bold;
                    color: #1A1A1A;
                    letter-spacing: 1px;
                }
                .status-meta {
                    font-size: 0.65rem;
                    color: #666;
                    margin-top: 2px;
                }
                @keyframes pulse-led {
                    0% { opacity: 0.6; }
                    100% { opacity: 1; }
                }
            </style>
            <div class="status-widget">
                <div class="status-indicator-led"></div>
                <div class="status-info">
                    <div class="status-title">[ ${statusText} ]</div>
                    <div class="status-meta">PING: ${this._ping}ms | LOAD: ${this._fps} FPS</div>
                </div>
            </div>
        `;
    }
}

customElements.define('component-system-status', SystemStatusComponent);

// Control Slider Component (Bauhaus Styled)
class ControlSliderComponent extends HTMLElement {
    constructor() {
        super();
        this._label = 'Control';
        this._min = 0;
        this._max = 100;
        this._value = 50;
        this._step = 1;
    }

    static get observedAttributes() {
        return ['label', 'min', 'max', 'value', 'step'];
    }

    attributeChangedCallback(name, oldValue, newValue) {
        if (name === 'label') this._label = newValue || 'Control';
        else if (name === 'min') this._min = parseFloat(newValue) || 0;
        else if (name === 'max') this._max = parseFloat(newValue) || 100;
        else if (name === 'value') this._value = parseFloat(newValue) || 50;
        else if (name === 'step') this._step = parseFloat(newValue) || 1;
        this.render();
    }

    connectedCallback() {
        this._label = this.getAttribute('label') || 'Control';
        this._min = parseFloat(this.getAttribute('min')) || 0;
        this._max = parseFloat(this.getAttribute('max')) || 100;
        this._value = parseFloat(this.getAttribute('value')) || 50;
        this._step = parseFloat(this.getAttribute('step')) || 1;
        this.render();
        
        // Listen to slider changes
        this.addEventListener('input', (e) => {
            if (e.target.type === 'range') {
                this._value = parseFloat(e.target.value);
                const valDisplay = this.querySelector('.slider-val');
                if (valDisplay) valDisplay.textContent = this._value;
                
                // Dispatch custom event
                this.dispatchEvent(new CustomEvent('change', {
                    detail: { value: this._value },
                    bubbles: true
                }));
            }
        });
    }

    render() {
        this.innerHTML = `
            <style>
                .slider-container {
                    display: flex;
                    flex-direction: column;
                    gap: 6px;
                    font-family: var(--font-mono);
                    background: #FFF;
                    border: 2px solid #1A1A1A;
                    padding: 8px 12px;
                    user-select: none;
                }
                .slider-header {
                    display: flex;
                    justify-content: space-between;
                    font-size: 0.7rem;
                    font-weight: bold;
                    text-transform: uppercase;
                }
                .slider-bar {
                    -webkit-appearance: none;
                    width: 100%;
                    height: 8px;
                    background: #EEE;
                    border: 2px solid #1A1A1A;
                    outline: none;
                }
                .slider-bar::-webkit-slider-thumb {
                    -webkit-appearance: none;
                    appearance: none;
                    width: 16px;
                    height: 16px;
                    background: var(--accent-red);
                    border: 2px solid #1A1A1A;
                    cursor: pointer;
                }
            </style>
            <div class="slider-container">
                <div class="slider-header">
                    <span>${this._label}</span>
                    <span class="slider-val" style="color: var(--accent-blue);">${this._value}</span>
                </div>
                <input type="range" class="slider-bar" min="${this._min}" max="${this._max}" step="${this._step}" value="${this._value}">
            </div>
        `;
    }
}

customElements.define('component-control-slider', ControlSliderComponent);

// Hebbian Drift Chart Component (Bauhaus Styled Canvas Line Chart)
class HebbianDriftChartComponent extends HTMLElement {
    constructor() {
        super();
        this.history = [];
        this.maxPoints = 45;
    }

    connectedCallback() {
        this.render();
        this.canvas = this.querySelector('canvas');
        this.ctx = this.canvas?.getContext('2d');
        this.startSimulation();
    }

    addValue(val) {
        this.history.push(val);
        if (this.history.length > this.maxPoints) {
            this.history.shift();
        }
        this.draw();
    }

    startSimulation() {
        this.interval = setInterval(() => {
            let drift = 0.05 + Math.random() * 0.08;
            if (window.swarmClient && window.swarmClient.nodes.length > 0) {
                let totalV = 0;
                for (const n of window.swarmClient.nodes) {
                    totalV += Math.sqrt((n.vx || 0)*(n.vx || 0) + (n.vy || 0)*(n.vy || 0));
                }
                drift = (totalV / window.swarmClient.nodes.length) * 0.15;
            }
            this.addValue(drift);
        }, 250);
    }

    disconnectedCallback() {
        if (this.interval) clearInterval(this.interval);
    }

    draw() {
        if (!this.canvas || !this.ctx) return;
        const ctx = this.ctx;
        const w = this.canvas.width;
        const h = this.canvas.height;

        ctx.fillStyle = '#FFFFFF';
        ctx.fillRect(0, 0, w, h);

        ctx.strokeStyle = '#F4F4F0';
        ctx.lineWidth = 1;
        for (let x = 0; x < w; x += 20) {
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, h);
            ctx.stroke();
        }
        for (let y = 0; y < h; y += 15) {
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(w, y);
            ctx.stroke();
        }

        if (this.history.length < 2) return;

        ctx.beginPath();
        ctx.strokeStyle = '#E03C31';
        ctx.lineWidth = 3;
        
        const maxVal = 1.0;
        for (let i = 0; i < this.history.length; i++) {
            const x = (i / (this.maxPoints - 1)) * w;
            const y = h - (Math.min(maxVal, this.history[i]) / maxVal) * (h - 10) - 5;
            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        }
        ctx.stroke();
    }

    render() {
        this.innerHTML = `
            <style>
                .chart-container {
                    display: flex;
                    flex-direction: column;
                    gap: 6px;
                    background: #FFF;
                    border: 2px solid #1A1A1A;
                    padding: 8px 12px;
                    width: 100%;
                    user-select: none;
                }
                .chart-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    font-family: var(--font-mono);
                    font-size: 0.65rem;
                    font-weight: bold;
                    text-transform: uppercase;
                    white-space: nowrap;
                    gap: 4px;
                }
                .chart-canvas {
                    border: 2px solid #1A1A1A;
                    width: 100%;
                    height: 50px;
                    display: block;
                }
            </style>
            <div class="chart-container">
                <div class="chart-header">
                    <span>Hebbian Drift Rate</span>
                    <span style="color: var(--accent-red);">[ LIVE ]</span>
                </div>
                <canvas class="chart-canvas" width="220" height="50"></canvas>
            </div>
        `;
    }
}

customElements.define('component-drift-chart', HebbianDriftChartComponent);
