/**
 * Help System - Reusable tooltip and help panel component
 * Provides consistent help functionality across all frontend views
 */

class HelpSystem {
    constructor() {
        this.tooltips = new Map();
        this.helpModal = null;
        this.init();
    }

    init() {
        // Create tooltip container
        if (!document.getElementById('help-tooltip-container')) {
            const tooltipContainer = document.createElement('div');
            tooltipContainer.id = 'help-tooltip-container';
            tooltipContainer.style.cssText = `
                position: fixed;
                pointer-events: none;
                z-index: 10000;
                display: none;
            `;
            document.body.appendChild(tooltipContainer);
        }

        // Create help modal
        this.createHelpModal();

        // Setup keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'F1') {
                e.preventDefault();
                this.showHelpModal();
            } else if (e.key === '?' && !e.ctrlKey && !e.metaKey) {
                // Only trigger if not in input/textarea
                if (document.activeElement.tagName !== 'INPUT' && 
                    document.activeElement.tagName !== 'TEXTAREA') {
                    e.preventDefault();
                    this.showHelpModal();
                }
            } else if (e.key === 'Escape') {
                this.hideHelpModal();
            }
        });
    }

    createHelpModal() {
        if (document.getElementById('help-modal')) return;

        const modal = document.createElement('div');
        modal.id = 'help-modal';
        modal.style.cssText = `
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            z-index: 10001;
            overflow-y: auto;
        `;

        modal.innerHTML = `
            <div style="
                max-width: 800px;
                margin: 50px auto;
                background: #111;
                border: 1px solid #333;
                border-radius: 8px;
                padding: 30px;
                color: #fff;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <h2 style="color: #4ade80; margin: 0;">Help & Documentation</h2>
                    <button id="help-modal-close" style="
                        background: #333;
                        border: 1px solid #555;
                        color: #fff;
                        padding: 8px 16px;
                        border-radius: 4px;
                        cursor: pointer;
                        font-size: 18px;
                    ">×</button>
                </div>
                <div id="help-modal-content">
                    <!-- Content will be populated -->
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        this.helpModal = modal;

        document.getElementById('help-modal-close').addEventListener('click', () => {
            this.hideHelpModal();
        });

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.hideHelpModal();
            }
        });
    }

    showHelpModal(content = null) {
        if (content) {
            document.getElementById('help-modal-content').innerHTML = content;
        }
        this.helpModal.style.display = 'block';
        document.body.style.overflow = 'hidden';
    }

    hideHelpModal() {
        this.helpModal.style.display = 'none';
        document.body.style.overflow = '';
    }

    /**
     * Add a tooltip to an element
     * @param {HTMLElement} element - Element to attach tooltip to
     * @param {string|Object} text - Tooltip text or config object
     */
    addTooltip(element, text) {
        const config = typeof text === 'string' ? { text } : text;
        
        element.addEventListener('mouseenter', (e) => {
            this.showTooltip(e.target, config.text || text, config.position);
        });

        element.addEventListener('mouseleave', () => {
            this.hideTooltip();
        });

        element.addEventListener('focus', (e) => {
            this.showTooltip(e.target, config.text || text, config.position);
        });

        element.addEventListener('blur', () => {
            this.hideTooltip();
        });
    }

    showTooltip(element, text, position = 'top') {
        const container = document.getElementById('help-tooltip-container');
        container.textContent = text;
        container.style.display = 'block';
        container.style.cssText += `
            background: rgba(20, 20, 30, 0.95);
            border: 1px solid rgba(74, 222, 128, 0.3);
            color: #fff;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 12px;
            max-width: 300px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
        `;

        const rect = element.getBoundingClientRect();
        const tooltipRect = container.getBoundingClientRect();
        
        let top, left;

        switch (position) {
            case 'bottom':
                top = rect.bottom + 8;
                left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
                break;
            case 'left':
                top = rect.top + (rect.height / 2) - (tooltipRect.height / 2);
                left = rect.left - tooltipRect.width - 8;
                break;
            case 'right':
                top = rect.top + (rect.height / 2) - (tooltipRect.height / 2);
                left = rect.right + 8;
                break;
            default: // top
                top = rect.top - tooltipRect.height - 8;
                left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
        }

        // Keep tooltip within viewport
        if (left < 8) left = 8;
        if (left + tooltipRect.width > window.innerWidth - 8) {
            left = window.innerWidth - tooltipRect.width - 8;
        }
        if (top < 8) top = rect.bottom + 8; // Switch to bottom if no room
        if (top + tooltipRect.height > window.innerHeight - 8) {
            top = rect.top - tooltipRect.height - 8;
        }

        container.style.top = `${top}px`;
        container.style.left = `${left}px`;
    }

    hideTooltip() {
        document.getElementById('help-tooltip-container').style.display = 'none';
    }

    /**
     * Add a help icon next to an element
     * @param {HTMLElement} element - Element to add help icon to
     * @param {string} helpText - Help text to show
     */
    addHelpIcon(element, helpText) {
        const helpIcon = document.createElement('span');
        helpIcon.className = 'help-icon';
        helpIcon.textContent = '?';
        helpIcon.style.cssText = `
            display: inline-block;
            width: 16px;
            height: 16px;
            line-height: 16px;
            text-align: center;
            background: rgba(74, 222, 128, 0.2);
            border: 1px solid rgba(74, 222, 128, 0.4);
            border-radius: 50%;
            color: #4ade80;
            font-size: 11px;
            font-weight: bold;
            cursor: help;
            margin-left: 6px;
            vertical-align: middle;
        `;

        this.addTooltip(helpIcon, helpText);
        element.appendChild(helpIcon);
    }
}

// Initialize global help system
window.helpSystem = new HelpSystem();

/*
  help-system.js - Minimal help/tooltip system used by the frontend pages.

  Exposes a simple global: window.helpSystem with these helpers:
    - addTooltip(element, text)        : attach a lightweight tooltip (title fallback)
    - addHelpIcon(container, text)     : append a small help icon next to a label that shows tooltip
    - showHelpModal(htmlContent)       : display a modal with provided HTML content
*/

(function () {
  if (window.helpSystem) return; // don't overwrite if present

  // Create modal container (hidden by default)
  const modal = document.createElement('div');
  modal.id = 'hs-modal';
  modal.style.cssText = [
    'position:fixed', 'inset:0', 'display:none', 'align-items:center', 'justify-content:center',
    'background:rgba(0,0,0,0.6)', 'z-index:20000', 'padding:20px'
  ].join(';');

  const panel = document.createElement('div');
  panel.style.cssText = [
    'max-width:900px', 'width:100%', 'max-height:90vh', 'overflow:auto',
    'background:#0b0b0b', 'color:#fff', 'border-radius:8px', 'padding:20px',
    'box-shadow:0 8px 40px rgba(0,0,0,0.8)'
  ].join(';');

  const closeBtn = document.createElement('button');
  closeBtn.textContent = 'Close';
  closeBtn.style.cssText = 'position:sticky; top:10px; float:right; margin-left:12px;';

  closeBtn.addEventListener('click', () => {
    modal.style.display = 'none';
    panel.querySelector('.hs-content') && (panel.querySelector('.hs-content').innerHTML = '');
  });

  panel.appendChild(closeBtn);
  const content = document.createElement('div');
  content.className = 'hs-content';
  panel.appendChild(content);
  modal.appendChild(panel);
  document.body.appendChild(modal);

  // Basic tooltip using title attribute; also add optional hover box for richer text
  function addTooltip(el, text) {
    if (!el || !text) return;
    el.setAttribute('title', text);
    // Also add aria
    el.setAttribute('aria-label', text);
    // Create a lightweight hover preview for longer help text
    let hoverBox = null;
    el.addEventListener('mouseenter', () => {
      if (hoverBox) return;
      if (text.length < 90) return; // short text: rely on native title
      hoverBox = document.createElement('div');
      hoverBox.className = 'hs-hover';
      hoverBox.style.cssText = [
        'position:fixed','z-index:22000','background:#111','color:#eee',
        'padding:8px 10px','border-radius:6px','max-width:360px','font-size:13px',
        'box-shadow:0 6px 20px rgba(0,0,0,0.6)'
      ].join(';');
      hoverBox.innerHTML = text;
      document.body.appendChild(hoverBox);
      const rect = el.getBoundingClientRect();
      hoverBox.style.left = (rect.right + 8) + 'px';
      hoverBox.style.top = (rect.top) + 'px';
    });
    el.addEventListener('mouseleave', () => {
      if (hoverBox) {
        hoverBox.remove();
        hoverBox = null;
      }
    });
  }

  function addHelpIcon(labelEl, text) {
    if (!labelEl) return;
    const icon = document.createElement('button');
    icon.type = 'button';
    icon.className = 'hs-help-icon';
    icon.style.cssText = [
      'margin-left:6px','background:transparent','border:none','color:#4ade80',
      'cursor:pointer','font-weight:bold','font-size:12px'
    ].join(';');
    icon.textContent = 'ⓘ';
    icon.setAttribute('aria-label', 'Help');
    icon.addEventListener('click', (e) => {
      e.stopPropagation();
      showHelpModal(`<div style="padding:6px 0;">${text}</div>`);
    });
    labelEl.appendChild(icon);
    addTooltip(icon, text);
  }

  function showHelpModal(htmlContent) {
    content.innerHTML = htmlContent || '<div>No help available</div>';
    modal.style.display = 'flex';
    // focus for accessibility
    setTimeout(() => modal.focus(), 50);
  }

  // Expose API
  window.helpSystem = {
    addTooltip,
    addHelpIcon,
    showHelpModal
  };
})();



