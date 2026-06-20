// ControlSlider - Vanilla JS Slider Component
// Extracted from Vue component, converted to vanilla JS

class ControlSlider {
    constructor(container, options = {}) {
        this.container = container;
        this.value = options.value || options.min || 0;
        this.min = options.min || 0;
        this.max = options.max || 100;
        this.step = options.step || 0.1;
        this.label = options.label || '';
        this.unit = options.unit || '';
        this.accentColor = options.accentColor || 'teal';
        
        this.isDragging = false;
        this.onChange = options.onChange || (() => {});
        
        this.render();
        this.attachEvents();
    }
    
    render() {
        const percentage = ((this.value - this.min) / (this.max - this.min)) * 100;
        
        this.container.innerHTML = `
            <div class="control-slider">
                <div class="control-slider-label-row">
                    <span class="control-slider-label" aria-label="${this.label}">${this.label}</span>
                    <span class="control-slider-value" aria-live="polite">
                        ${this.value.toFixed(1)}<span class="control-slider-unit">${this.unit}</span>
                    </span>
                </div>
                <div class="control-slider-track" data-slider-track
                     role="slider"
                     aria-valuemin="${this.min}"
                     aria-valuemax="${this.max}"
                     aria-valuenow="${this.value}"
                     aria-label="${this.label}"
                     tabindex="0">
                    <svg class="control-slider-svg" preserveAspectRatio="none">
                        <line x1="0" y1="50%" x2="100%" y2="50%" stroke="#1f2937" stroke-width="2" />
                        ${Array.from({ length: 11 }, (_, i) => `
                            <line 
                                x1="${i * 10}%" 
                                y1="30%" 
                                x2="${i * 10}%" 
                                y2="70%" 
                                stroke="#374151" 
                                stroke-width="1" 
                            />
                        `).join('')}
                        <line 
                            x1="0" 
                            y1="50%" 
                            x2="${percentage}%" 
                            y2="50%" 
                            stroke="#00ff9d" 
                            stroke-width="2" 
                            class="control-slider-fill"
                        />
                    </svg>
                    <div 
                        class="control-slider-handle" 
                        data-slider-handle
                        style="left: ${percentage}%"
                    >
                        <div class="control-slider-handle-dot"></div>
                    </div>
                </div>
            </div>
        `;
        
        this.track = this.container.querySelector('[data-slider-track]');
        this.handle = this.container.querySelector('[data-slider-handle]');
        this.fillLine = this.container.querySelector('.control-slider-fill');
    }
    
    updateValueFromClientX(clientX) {
        if (!this.track) return;
        
        const rect = this.track.getBoundingClientRect();
        const x = Math.max(0, Math.min(clientX - rect.left, rect.width));
        const pct = x / rect.width;
        
        let rawValue = this.min + pct * (this.max - this.min);
        
        // Snap to step
        const steppedValue = Math.round(rawValue / this.step) * this.step;
        
        // Clamp
        const clamped = Math.max(this.min, Math.min(this.max, steppedValue));
        
        this.setValue(clamped);
    }
    
    setValue(newValue) {
        const clamped = Math.max(this.min, Math.min(this.max, newValue));
        if (this.value === clamped) return;
        
        this.value = clamped;
        this.updateDisplay();
        this.onChange(this.value);
    }
    
    updateDisplay() {
        if (!this.handle || !this.fillLine) return;
        
        const percentage = ((this.value - this.min) / (this.max - this.min)) * 100;
        this.handle.style.left = `${percentage}%`;
        this.fillLine.setAttribute('x2', `${percentage}%`);
        
        // Update value display
        const valueEl = this.container.querySelector('.control-slider-value');
        if (valueEl) {
            valueEl.innerHTML = `${this.value.toFixed(1)}<span class="control-slider-unit">${this.unit}</span>`;
        }
        
        // Update ARIA attributes
        if (this.track) {
            this.track.setAttribute('aria-valuenow', this.value);
        }
    }
    
    attachEvents() {
        if (!this.track) return;
        
        // Keyboard events for accessibility
        this.track.addEventListener('keydown', (e) => {
            let newValue = this.value;
            if (e.key === 'ArrowLeft' || e.key === 'ArrowDown') {
                e.preventDefault();
                newValue = this.value - this.step;
            } else if (e.key === 'ArrowRight' || e.key === 'ArrowUp') {
                e.preventDefault();
                newValue = this.value + this.step;
            } else if (e.key === 'Home') {
                e.preventDefault();
                newValue = this.min;
            } else if (e.key === 'End') {
                e.preventDefault();
                newValue = this.max;
            } else {
                return; // Not a key we handle
            }
            this.setValue(newValue);
        });
        
        this.track.addEventListener('mousedown', (e) => {
            e.preventDefault();
            this.isDragging = true;
            this.updateValueFromClientX(e.clientX);
            
            const onMouseMove = (e) => {
                if (this.isDragging) {
                    this.updateValueFromClientX(e.clientX);
                }
            };
            
            const onMouseUp = () => {
                this.isDragging = false;
                window.removeEventListener('mousemove', onMouseMove);
                window.removeEventListener('mouseup', onMouseUp);
            };
            
            window.addEventListener('mousemove', onMouseMove);
            window.addEventListener('mouseup', onMouseUp);
        });
        
        this.track.addEventListener('click', (e) => {
            if (!this.isDragging) {
                this.updateValueFromClientX(e.clientX);
            }
        });
    }
    
    getValue() {
        return this.value;
    }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ControlSlider;
}


