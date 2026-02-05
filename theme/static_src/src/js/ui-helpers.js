/**
 * Global UI Helper Functions
 * Standardizes Modals, Toasts, and HTMX Confirmations across Frontend and Admin
 */

// Ensure global modals exist in the DOM
window.ensureGlobalModals = function() {
    const hasConfirm = document.getElementById('global_confirm_modal');
    const hasAlert = document.getElementById('global_alert_modal');
    
    if (!hasConfirm || !hasAlert) {
        // Only inject if not already present (e.g. via include)
        const wrapper = document.createElement('div');
        wrapper.innerHTML = `
        <dialog id="global_confirm_modal" class="modal">
            <div class="modal-box">
                <h3 class="font-bold text-lg flex items-center gap-2 text-warning" id="global_confirm_title">
                    <span class="material-symbols-outlined">warning</span>
                    确认操作
                </h3>
                <p class="py-4 text-base-content/80" id="global_confirm_message">确定要执行此操作吗？</p>
                <div class="modal-action">
                    <button type="button" class="btn btn-ghost" data-modal-close="global_confirm_modal">取消</button>
                    <button type="button" id="global_confirm_btn" class="btn btn-error text-white shadow-lg shadow-error/20">确定</button>
                </div>
            </div>
            <form method="dialog" class="modal-backdrop">
                <button>close</button>
            </form>
        </dialog>
        <dialog id="global_alert_modal" class="modal">
            <div class="modal-box">
                <h3 class="font-bold text-lg flex items-center gap-2 text-info">
                    <span class="material-symbols-outlined">info</span>
                    提示
                </h3>
                <p class="py-4 text-base-content/80" id="global_alert_message"></p>
                <div class="modal-action">
                    <button type="button" class="btn btn-primary" data-modal-close="global_alert_modal">确定</button>
                </div>
            </div>
            <form method="dialog" class="modal-backdrop">
                <button>close</button>
            </form>
        </dialog>
        `;
        document.body.appendChild(wrapper);
    }
    
    // Bind close buttons for dynamically created or existing modals
    // Use event delegation to handle current and future elements
    if (!window.globalModalCloseListenerBound) {
        document.body.addEventListener('click', (evt) => {
            const btn = evt.target.closest('[data-modal-close]');
            if (btn) {
                evt.preventDefault();
                const modalId = btn.getAttribute('data-modal-close');
                const modal = document.getElementById(modalId);
                if (modal) modal.close();
            }
        });
        window.globalModalCloseListenerBound = true;
    }
};

// Re-inject modals after HTMX swap (in case of full body swap)
document.addEventListener('htmx:afterSwap', () => {
    ensureGlobalModals();
});

// Show Confirmation Modal
window.showConfirmModal = function(title, message, onConfirm) {
    ensureGlobalModals();
    const modal = document.getElementById('global_confirm_modal');
    const titleEl = document.getElementById('global_confirm_title');
    const msgEl = document.getElementById('global_confirm_message');
    const btn = document.getElementById('global_confirm_btn');
    
    if (!modal || !titleEl || !msgEl || !btn) return;
    
    // Update content
    // Use innerHTML for title to support icons, textContent for message for safety
    if (title.includes('<')) {
        titleEl.innerHTML = title;
    } else {
        titleEl.innerHTML = `<span class="material-symbols-outlined">warning</span> ${title}`;
    }
    msgEl.textContent = message;
    
    // Clone button to remove old event listeners
    const newBtn = btn.cloneNode(true);
    btn.parentNode.replaceChild(newBtn, btn);
    
    newBtn.onclick = () => {
        if (typeof onConfirm === 'function') {
            onConfirm();
        } else if (typeof onConfirm === 'string') {
            // Handle URL navigation
            window.location.href = onConfirm;
        }
        modal.close();
    };
    
    modal.showModal();
};

// Show Alert Modal
window.showGlobalAlert = function(message) {
    ensureGlobalModals();
    const modal = document.getElementById('global_alert_modal');
    const msgEl = document.getElementById('global_alert_message');
    
    if (!modal || !msgEl) return;
    
    msgEl.textContent = message;
    modal.showModal();
};

// Show Toast Notification
window.showToast = function(message, type = 'success') {
    window.dispatchEvent(new CustomEvent('show-toast', {
        detail: { message, type }
    }));
};

// HTMX Confirmation Helper
// Usage: <button hx-post="..." hx-trigger="confirmed" onclick="confirmHtmx(this, 'Msg')">
window.confirmHtmx = function(element, message) {
    // Prevent default HTMX trigger immediately
    if (window.event) {
        window.event.preventDefault();
        window.event.stopPropagation();
    }
    
    showConfirmModal(
        '确认操作',
        message || '确定要执行此操作吗？',
        () => {
            // Trigger the actual HTMX request
            if (window.htmx) {
                htmx.trigger(element, 'confirmed');
            }
        }
    );
};

// Legacy/Standard Delete Helper (for non-HTMX forms)
window.confirmDelete = function(url, message) {
    window.showConfirmModal(
        '确认删除', 
        message || '确定要删除此项目吗？此操作无法撤销。',
        () => {
            if (url.startsWith('javascript:')) {
                eval(url);
            } else {
                // Create and submit a POST form
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = url;
                form.style.display = 'none';
                
                // Disable HTMX for this form
                form.setAttribute('hx-boost', 'false');
                form.setAttribute('hx-disable', 'true');
                
                // Add CSRF Token
                const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]')?.value || 
                                  getCookie('csrftoken');
                                  
                if (csrfToken) {
                    const csrfInput = document.createElement('input');
                    csrfInput.type = 'hidden';
                    csrfInput.name = 'csrfmiddlewaretoken';
                    csrfInput.value = csrfToken;
                    form.appendChild(csrfInput);
                }
                
                document.body.appendChild(form);
                form.submit();
            }
        }
    );
};

// Legacy Helper: confirmAction (used in post_detail.html)
window.confirmAction = function(url, message, title) {
    window.showConfirmModal(
        title || '确认操作',
        message || '确定要执行此操作吗？',
        () => {
            if (url.startsWith('javascript:')) {
                eval(url);
            } else {
                // Create and submit a POST form
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = url;
                form.style.display = 'none';
                form.setAttribute('hx-boost', 'false');
                form.setAttribute('hx-disable', 'true');
                
                const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]')?.value || 
                                  getCookie('csrftoken');
                if (csrfToken) {
                    const csrfInput = document.createElement('input');
                    csrfInput.type = 'hidden';
                    csrfInput.name = 'csrfmiddlewaretoken';
                    csrfInput.value = csrfToken;
                    form.appendChild(csrfInput);
                }
                
                document.body.appendChild(form);
                form.submit();
            }
        }
    );
};

// Helper to get cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    ensureGlobalModals();
});

// Color Picker Component (Alpine.js)
document.addEventListener('alpine:init', () => {
    Alpine.data('colorPicker', ({ initialColor, name }) => ({
        name: name,
        // HSV State
        hue: 0,        // 0-360
        sat: 0,        // 0-100
        val: 100,      // 0-100
        alpha: 1,      // 0-1
        
        // Dragging State
        isDraggingSat: false,
        isDraggingHue: false,
        isDraggingAlpha: false,

        // Computed/Derived
        hexColor: '#000000', // This will now potentially be Hex8
        hexInput: '#000000',
        rgb: { r: 0, g: 0, b: 0 },
        
        // Recommended Swatches
        swatches: [
            '#000000', '#ffffff', '#ef4444', '#f97316', '#f59e0b', '#84cc16', 
            '#22c55e', '#10b981', '#06b6d4', '#0ea5e9', '#3b82f6', '#6366f1', 
            '#8b5cf6', '#d946ef', '#ec4899', '#f43f5e'
        ],

        init() {
            this.setColor(initialColor);
            
            // Global mouse events
            window.addEventListener('mousemove', (e) => this.handleDrag(e));
            window.addEventListener('mouseup', () => this.stopDrag());
            window.addEventListener('touchmove', (e) => this.handleDrag(e));
            window.addEventListener('touchend', () => this.stopDrag());
        },

        get huePercentage() {
            return (this.hue / 360) * 100;
        },

        get satX() {
            return this.sat;
        },

        get satY() {
            return 100 - this.val;
        },

        setColor(color) {
            // Legacy Tailwind Color Mapping
            const legacyColors = {
                'primary': '#4f46e5',
                'secondary': '#ec4899',
                'accent': '#06b6d4',
                'neutral': '#3b82f6',
                'info': '#6366f1',
                'success': '#22c55e',
                'warning': '#f59e0b',
                'error': '#ef4444'
            };

            if (!color) color = '#000000';
            
            // Handle legacy class names
            if (legacyColors[color]) {
                color = legacyColors[color];
            }

            if (color.startsWith('rgb')) {
                // Parse RGB/RGBA
                const parts = color.match(/[\d.]+/g);
                if (parts && parts.length >= 3) {
                    const r = parseInt(parts[0]);
                    const g = parseInt(parts[1]);
                    const b = parseInt(parts[2]);
                    const a = parts.length > 3 ? parseFloat(parts[3]) : 1;
                    color = this.rgbaToHex(r, g, b, a);
                }
            }
            
            if (!color.startsWith('#')) {
                 const ctx = document.createElement('canvas').getContext('2d');
                 ctx.fillStyle = color;
                 if (ctx.fillStyle !== '#000000' || color === 'black') {
                     color = ctx.fillStyle;
                 }
            }
            
            this.hexInput = color;
            this.updateFromHexInput();
        },

        updateFromHexInput() {
            let hex = this.hexInput;
            if (!hex.startsWith('#')) hex = '#' + hex;
            
            // Validate Hex6 or Hex8
            if (/^#[0-9A-F]{6}([0-9A-F]{2})?$/i.test(hex)) {
                // Extract Alpha if present
                if (hex.length === 9) {
                    this.alpha = parseInt(hex.slice(7, 9), 16) / 255;
                    this.hexColor = hex.slice(0, 7); // Base color for preview calculations
                } else {
                    this.alpha = 1;
                    this.hexColor = hex;
                }
                
                this.rgb = this.hexToRgb(this.hexColor);
                const hsv = this.rgbToHsv(this.rgb.r, this.rgb.g, this.rgb.b);
                this.hue = hsv.h;
                this.sat = hsv.s;
                this.val = hsv.v;
                
                // Final full hex update
                this.updateFinalHex();
            }
        },

        updateColorFromHsv() {
            const rgb = this.hsvToRgb(this.hue, this.sat, this.val);
            this.rgb = rgb;
            this.hexColor = this.rgbToHex(rgb.r, rgb.g, rgb.b);
            this.updateFinalHex();
        },
        
        updateFinalHex() {
            if (this.alpha < 1) {
                const alphaHex = Math.round(this.alpha * 255).toString(16).padStart(2, '0').toUpperCase();
                this.hexInput = this.hexColor + alphaHex;
            } else {
                this.hexInput = this.hexColor;
            }
        },

        // Drag Handlers
        startDragSat(e) {
            this.isDraggingSat = true;
            this.handleSatDrag(e);
        },

        startDragHue(e) {
            this.isDraggingHue = true;
            this.handleHueDrag(e);
        },
        
        startDragAlpha(e) {
            this.isDraggingAlpha = true;
            this.handleAlphaDrag(e);
        },

        stopDrag() {
            this.isDraggingSat = false;
            this.isDraggingHue = false;
            this.isDraggingAlpha = false;
        },

        handleDrag(e) {
            if (this.isDraggingSat) this.handleSatDrag(e);
            if (this.isDraggingHue) this.handleHueDrag(e);
            if (this.isDraggingAlpha) this.handleAlphaDrag(e);
        },

        handleSatDrag(e) {
            const rect = this.$refs.satArea.getBoundingClientRect();
            const clientX = e.touches ? e.touches[0].clientX : e.clientX;
            const clientY = e.touches ? e.touches[0].clientY : e.clientY;

            let x = (clientX - rect.left) / rect.width;
            let y = (clientY - rect.top) / rect.height;

            x = Math.max(0, Math.min(1, x));
            y = Math.max(0, Math.min(1, y));

            this.sat = x * 100;
            this.val = 100 - (y * 100);
            this.updateColorFromHsv();
        },

        handleHueDrag(e) {
            const rect = this.$refs.hueSlider.getBoundingClientRect();
            const clientX = e.touches ? e.touches[0].clientX : e.clientX;
            
            let x = (clientX - rect.left) / rect.width;
            x = Math.max(0, Math.min(1, x));

            this.hue = x * 360;
            this.updateColorFromHsv();
        },
        
        handleAlphaDrag(e) {
            const rect = this.$refs.alphaSlider.getBoundingClientRect();
            const clientX = e.touches ? e.touches[0].clientX : e.clientX;
            
            let x = (clientX - rect.left) / rect.width;
            x = Math.max(0, Math.min(1, x));
            
            this.alpha = x;
            this.updateFinalHex();
        },

        // Utilities
        hexToRgb(hex) {
            const bigint = parseInt(hex.slice(1), 16);
            return {
                r: (bigint >> 16) & 255,
                g: (bigint >> 8) & 255,
                b: bigint & 255
            };
        },

        rgbToHex(r, g, b) {
            return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1).toUpperCase();
        },
        
        rgbaToHex(r, g, b, a) {
            const hex = this.rgbToHex(r, g, b);
            if (a < 1) {
                const alpha = Math.round(a * 255).toString(16).padStart(2, '0').toUpperCase();
                return hex + alpha;
            }
            return hex;
        },

        hsvToRgb(h, s, v) {
            s /= 100;
            v /= 100;
            const k = (n) => (n + h / 60) % 6;
            const f = (n) => v * (1 - s * Math.max(0, Math.min(k(n), 4 - k(n), 1)));
            return {
                r: Math.round(f(5) * 255),
                g: Math.round(f(3) * 255),
                b: Math.round(f(1) * 255)
            };
        },

        rgbToHsv(r, g, b) {
            r /= 255; g /= 255; b /= 255;
            const v = Math.max(r, g, b), c = v - Math.min(r, g, b);
            const h = c && ((v === r) ? (g - b) / c : ((v === g) ? 2 + (b - r) / c : 4 + (r - g) / c));
            return {
                h: 60 * (h < 0 ? h + 6 : h),
                s: v && c / v * 100,
                v: v * 100
            };
        }
    }));
});
