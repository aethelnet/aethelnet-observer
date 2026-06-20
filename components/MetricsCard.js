/**
 * MetricsCard Component
 * Displays a single metric with label, value, and optional trend
 * Web Component: <component-metrics-card>
 * 
 * Attributes:
 * - label: Metric name
 * - value: Numeric value (can be updated via property)
 * - format: 'currency', 'percentage', 'number'
 * - trend: 'positive', 'negative', 'neutral'
 * - change: Optional change value to display
 */

import { formatCurrency, formatPercentage, formatNumber } from '../shared/api.js';

class MetricsCardComponent extends HTMLElement {
    constructor() {
        super();
        this._value = null;
        this._label = '';
        this._format = 'number';
        this._trend = 'neutral';
        this._change = null;
    }
    
    static get observedAttributes() {
        return ['label', 'value', 'format', 'trend', 'change'];
    }
    
    attributeChangedCallback(name, oldValue, newValue) {
        if (name === 'label') {
            this._label = newValue || '';
        } else if (name === 'value') {
            this._value = newValue !== null ? parseFloat(newValue) : null;
        } else if (name === 'format') {
            this._format = newValue || 'number';
        } else if (name === 'trend') {
            this._trend = newValue || 'neutral';
        } else if (name === 'change') {
            this._change = newValue !== null ? parseFloat(newValue) : null;
        }
        this.render();
    }
    
    connectedCallback() {
        // Read initial attributes
        this._label = this.getAttribute('label') || '';
        const valueAttr = this.getAttribute('value');
        this._value = valueAttr !== null ? parseFloat(valueAttr) : null;
        this._format = this.getAttribute('format') || 'number';
        this._trend = this.getAttribute('trend') || 'neutral';
        const changeAttr = this.getAttribute('change');
        this._change = changeAttr !== null ? parseFloat(changeAttr) : null;
        
        this.render();
    }
    
    render() {
        // Format value based on format type
        let formattedValue = '--';
        if (this._value !== null && !isNaN(this._value)) {
            switch (this._format) {
                case 'currency':
                    formattedValue = formatCurrency(this._value);
                    break;
                case 'percentage':
                    formattedValue = formatPercentage(this._value);
                    break;
                case 'number':
                default:
                    formattedValue = formatNumber(this._value);
                    break;
            }
        }
        
        // Determine color based on trend
        let valueColor = '';
        if (this._trend === 'positive') {
            valueColor = 'color: #4ade80;';
        } else if (this._trend === 'negative') {
            valueColor = 'color: #f87171;';
        } else {
            valueColor = 'color: #fff;';
        }
        
        // Auto-detect trend from value if not explicitly set
        if (this._trend === 'neutral' && this._value !== null) {
            if (this._value > 0) {
                valueColor = 'color: #4ade80;';
            } else if (this._value < 0) {
                valueColor = 'color: #f87171;';
            }
        }
        
        // Format change if provided
        let changeHtml = '';
        if (this._change !== null && !isNaN(this._change)) {
            const changeSign = this._change >= 0 ? '+' : '';
            const changeColor = this._change >= 0 ? '#4ade80' : '#f87171';
            changeHtml = `
                <div class="metric-change" style="font-size: 12px; color: ${changeColor}; margin-top: 4px;">
                    ${changeSign}${this._change.toFixed(2)}${this._format === 'percentage' ? '%' : ''}
                </div>
            `;
        }
        
        this.innerHTML = `
            <div class="component-metrics-card" style="background: rgba(20, 20, 30, 0.8); border: 1px solid rgba(74, 222, 128, 0.4); border-radius: 8px; padding: 16px;">
                <div class="metric-label" style="color: #888; font-size: 12px; text-transform: uppercase; margin-bottom: 8px;">
                    ${this._label || 'Metric'}
                </div>
                <div class="metric-value" style="font-size: 24px; font-weight: bold; ${valueColor}">
                    ${formattedValue}
                </div>
                ${changeHtml}
            </div>
        `;
    }
    
    // Getters and setters for properties
    get value() {
        return this._value;
    }
    
    set value(val) {
        this._value = val !== null ? parseFloat(val) : null;
        this.setAttribute('value', val !== null ? val.toString() : '');
        this.render();
    }
    
    get label() {
        return this._label;
    }
    
    set label(val) {
        this._label = val;
        this.setAttribute('label', val);
        this.render();
    }
    
    get format() {
        return this._format;
    }
    
    set format(val) {
        this._format = val;
        this.setAttribute('format', val);
        this.render();
    }
    
    get trend() {
        return this._trend;
    }
    
    set trend(val) {
        this._trend = val;
        this.setAttribute('trend', val);
        this.render();
    }
    
    update(data) {
        if (data.value !== undefined) this.value = data.value;
        if (data.label !== undefined) this.label = data.label;
        if (data.format !== undefined) this.format = data.format;
        if (data.trend !== undefined) this.trend = data.trend;
        if (data.change !== undefined) {
            this._change = data.change;
            this.setAttribute('change', data.change.toString());
        }
        this.render();
    }
}

customElements.define('component-metrics-card', MetricsCardComponent);



