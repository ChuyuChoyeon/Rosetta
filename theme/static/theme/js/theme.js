(function(global) {
    // Available themes that are considered "dark"
    const DARK_THEMES = [
        'dark', 'synthwave', 'halloween', 'forest', 'aqua', 'black', 'luxury',
        'dracula', 'business', 'night', 'coffee', 'dim', 'sunset'
    ];

    function isDarkTheme(theme) {
        return DARK_THEMES.includes(theme);
    }

    function applyTheme(theme) {
        try {
            document.documentElement.setAttribute('data-theme', theme);
            if (isDarkTheme(theme)) {
                document.documentElement.classList.add('dark');
            } else {
                document.documentElement.classList.remove('dark');
            }

            // Update active state of theme buttons
            const buttons = document.querySelectorAll('[data-set-theme]');
            for (const btn of buttons) {
                const actClass = btn.getAttribute('data-act-class');
                if (!actClass) continue;
                const classes = actClass.split(/\s+/).filter(Boolean);
                if (btn.getAttribute('data-set-theme') === theme) {
                    btn.classList.add(...classes);
                } else {
                    btn.classList.remove(...classes);
                }
            }
        } catch (e) {
            console.error('Error applying theme:', e);
        }
    }

    function setTheme(theme) {
        try {
            localStorage.setItem('theme', theme);
        } catch (e) {
            console.error('Error setting theme to localStorage:', e);
        }
        applyTheme(theme);
    }

    function initTheme() {
        try {
            const localTheme = localStorage.getItem('theme');
            const fallback = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
            const theme = localTheme || fallback;
            applyTheme(theme);
        } catch (e) {
            console.error('Error initializing theme:', e);
        }
    }

    // Event Listeners Initialization
    function initEventListeners() {
        document.addEventListener('click', function(e) {
            const target = e.target.closest('[data-set-theme]');
            if (!target) return;
            e.preventDefault();
            setTheme(target.getAttribute('data-set-theme'));
        });

        document.addEventListener('DOMContentLoaded', initTheme);
    }

    // Export for Node.js/Jest or Browser
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = { isDarkTheme, applyTheme, setTheme, initTheme, initEventListeners, DARK_THEMES };
    } else {
        global.ThemeManager = { isDarkTheme, applyTheme, setTheme, initTheme, initEventListeners };
        // Auto-init in browser
        initEventListeners();
        // Expose legacy global for compatibility if needed
        global.__setTheme = setTheme;
    }

})(typeof window !== 'undefined' ? window : this);
