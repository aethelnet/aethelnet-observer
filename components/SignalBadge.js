/**
 * SignalBadge Component
 * Displays trading signal with color coding
 * Web Component: <component-signal-badge>
 * 
 * Attributes:
 * - signal: Signal strength (STRONG BUY, BUY, SELL, STRONG SELL, NEUTRAL)
 */

class SignalBadgeComponent extends HTMLElement {
    constructor() {
        super();
        this._signal = 'NEUTRAL';
    }
    
    static get observedAttributes() {
        return ['signal'];
    }
    
    attributeChangedCallback(name, oldValue, newValue) {
        if (name === 'signal') {
            this._signal = (newValue || 'NEUTRAL').toUpperCase();
            this.render();
        }
    }
    
    connectedCallback() {
        this._signal = (this.getAttribute('signal') || 'NEUTRAL').toUpperCase();
        this.render();
    }
    
    render() {
        // Determine CSS class and styles based on signal
        let badgeClass = 'signal-neutral';
        let styles = 'background: rgba(156, 163, 175, 0.2); color: #9ca3af; border: 1px solid rgba(156, 163, 175, 0.4);';
        
        switch (this._signal) {
            case 'STRONG BUY':
                badgeClass = 'signal-strong-buy';
                styles = 'background: rgba(74, 222, 128, 0.2); color: #4ade80; border: 1px solid rgba(74, 222, 128, 0.4);';
                break;
            case 'BUY':
                badgeClass = 'signal-buy';
                styles = 'background: rgba(134, 239, 172, 0.2); color: #86efac; border: 1px solid rgba(134, 239, 172, 0.4);';
                break;
            case 'SELL':
                badgeClass = 'signal-sell';
                styles = 'background: rgba(252, 165, 165, 0.2); color: #fca5a5; border: 1px solid rgba(252, 165, 165, 0.4);';
                break;
            case 'STRONG SELL':
                badgeClass = 'signal-strong-sell';
                styles = 'background: rgba(248, 113, 113, 0.2); color: #f87171; border: 1px solid rgba(248, 113, 113, 0.4);';
                break;
            case 'NEUTRAL':
            default:
                badgeClass = 'signal-neutral';
                styles = 'background: rgba(156, 163, 175, 0.2); color: #9ca3af; border: 1px solid rgba(156, 163, 175, 0.4);';
                break;
        }
        
        this.innerHTML = `
            <span class="component-signal-badge ${badgeClass}" style="display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; text-transform: uppercase; ${styles}">
                ${this._signal}
            </span>
        `;
    }
    
    get signal() {
        return this._signal;
    }
    
    set signal(val) {
        this._signal = (val || 'NEUTRAL').toUpperCase();
        this.setAttribute('signal', this._signal);
        this.render();
    }
    
    update(signal) {
        this.signal = signal;
    }
}

customElements.define('component-signal-badge', SignalBadgeComponent);



