// Theme Management Module
// Handles theme switching, persistence, and system preference synchronization

const ThemeManager = {
    // Current theme state
    currentTheme: 'light',
    
    // Theme configurations
    themes: ['light', 'dark'],

    // Debounce timer for backend sync
    syncTimer: null,

    /**
     * Initialize theme system
     */
    init: function() {
        // 1. Check local storage
        const storedTheme = localStorage.getItem('theme');
        
        // 2. Check system preference
        const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        
        // 3. Determine initial theme
        // If stored theme is invalid, fallback to system preference
        this.currentTheme = (storedTheme && this.themes.includes(storedTheme)) 
            ? storedTheme 
            : (systemPrefersDark ? 'dark' : 'light');
        
        // 4. Apply initial theme
        this.applyTheme(this.currentTheme, false); // false = don't sync to backend on init
        
        // 5. Listen for system preference changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
            if (!localStorage.getItem('theme')) {
                this.applyTheme(e.matches ? 'dark' : 'light');
            }
        });

        // 6. Bind global update function
        window.updateTheme = this.updateTheme.bind(this);
        window.toggleTheme = this.toggleTheme.bind(this);
        
        // 7. Sync toggles on page load
        this.syncToggles();
    },

    /**
     * Apply theme to DOM and persist
     * @param {string} theme - 'light' or 'dark'
     * @param {boolean} shouldSyncBackend - whether to sync with backend
     */
    applyTheme: function(theme, shouldSyncBackend = true) {
        if (!this.themes.includes(theme)) return;

        // Update state
        this.currentTheme = theme;
        
        // Update DOM
        document.documentElement.setAttribute('data-theme', theme);
        
        // Handle Tailwind 'dark' class
        if (theme === 'dark') {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
        
        // Persist to local storage
        localStorage.setItem('theme', theme);
        
        // Sync UI toggles
        this.syncToggles();

        // Sync with backend if requested
        if (shouldSyncBackend) {
            this.debouncedSyncToBackend(theme);
        }
    },

    /**
     * Public function to update theme (called by UI)
     * @param {string} theme - 'light' or 'dark'
     */
    updateTheme: function(theme) {
        this.applyTheme(theme);
    },

    /**
     * Public function to toggle theme (called by checkbox/toggle)
     * @param {HTMLElement} element - The checkbox element (optional)
     */
    toggleTheme: function(element) {
        // If element is provided, use its checked state, otherwise toggle current
        const newTheme = element 
            ? (element.checked ? 'dark' : 'light')
            : (this.currentTheme === 'light' ? 'dark' : 'light');
            
        this.applyTheme(newTheme);
    },

    /**
     * Sync all theme toggles/inputs on the page with current state
     */
    syncToggles: function() {
        // Handle checkbox toggles (checked = dark)
        // Matches .theme-controller and generic toggles that might control theme
        document.querySelectorAll('.theme-controller, input[type="checkbox"][onclick*="toggleTheme"]').forEach(toggle => {
            toggle.checked = this.currentTheme === 'dark';
        });

        // Handle radio buttons
        document.querySelectorAll(`input[name="theme"][value="${this.currentTheme}"]`).forEach(radio => {
            radio.checked = true;
        });
        
        // Handle swap components (DaisyUI swap)
        document.querySelectorAll('.swap').forEach(swap => {
            // If the swap is being used for theme, we might need to manually toggle generic classes
            // But usually swap is controlled by checkbox
            const checkbox = swap.querySelector('input[type="checkbox"]');
            if (checkbox && (checkbox.classList.contains('theme-controller') || checkbox.getAttribute('onclick')?.includes('toggleTheme'))) {
                 checkbox.checked = this.currentTheme === 'dark';
            }
        });
    },

    /**
     * Debounced backend synchronization
     */
    debouncedSyncToBackend: function(theme) {
        clearTimeout(this.syncTimer);
        this.syncTimer = setTimeout(() => {
            this.syncToBackend(theme);
        }, 1000); // 1 second delay
    },

    /**
     * Sync theme preference to backend
     */
    syncToBackend: function(theme) {
        // Check if user endpoint is available (set in base template)
        if (!window.USER_PREFERENCE_URL) return;

        const csrftoken = this.getCookie('csrftoken');
        
        fetch(window.USER_PREFERENCE_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({ theme: theme })
        })
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => console.log('Theme synced:', data))
        .catch(error => console.error('Error syncing theme:', error));
    },

    /**
     * Helper to get cookie by name
     */
    getCookie: function(name) {
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
};

// Initialize on load
// Check if running in browser
if (typeof window !== 'undefined') {
    // Run immediately to prevent FOUC
    ThemeManager.init();
    
    // Expose to window
    window.ThemeManager = ThemeManager;
    
    // Re-sync on DOMContentLoaded (in case toggles weren't ready)
    document.addEventListener('DOMContentLoaded', () => {
        ThemeManager.syncToggles();
    });
}
