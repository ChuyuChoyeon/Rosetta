(function(global) {
    // --- 常量定义 ---
    // 被视为 "暗色" 的主题列表，用于配合 Tailwind 的 dark 模式
    const DARK_THEMES = [
        'dark', 'synthwave', 'halloween', 'forest', 'aqua', 'black', 'luxury',
        'dracula', 'business', 'night', 'coffee', 'dim', 'sunset'
    ];

    /**
     * 判断是否为暗色主题
     * @param {string} theme - 主题名称
     * @returns {boolean}
     */
    function isDarkTheme(theme) {
        return DARK_THEMES.includes(theme);
    }

    /**
     * 应用主题到 DOM
     * 
     * 1. 设置 html[data-theme] 属性 (daisyUI)
     * 2. 切换 html.dark 类 (Tailwind)
     * 3. 更新主题切换按钮的激活状态
     * 
     * @param {string} theme - 主题名称
     */
    function applyTheme(theme) {
        try {
            document.documentElement.setAttribute('data-theme', theme);
            if (isDarkTheme(theme)) {
                document.documentElement.classList.add('dark');
            } else {
                document.documentElement.classList.remove('dark');
            }

            // 更新所有主题切换按钮的激活样式 (data-act-class)
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

    /**
     * 设置并持久化主题
     * 
     * 保存到 localStorage 并立即应用
     * @param {string} theme - 主题名称
     */
    function setTheme(theme) {
        try {
            localStorage.setItem('theme', theme);
        } catch (e) {
            console.error('Error setting theme to localStorage:', e);
        }
        applyTheme(theme);
    }

    /**
     * 初始化主题
     * 
     * 优先级: localStorage > 系统偏好 (prefers-color-scheme)
     */
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

    // --- 事件监听初始化 ---
    function initEventListeners() {
        // 使用事件委托处理主题切换点击
        document.addEventListener('click', function(e) {
            const target = e.target.closest('[data-set-theme]');
            if (!target) return;
            e.preventDefault();
            setTheme(target.getAttribute('data-set-theme'));
        });

        document.addEventListener('DOMContentLoaded', initTheme);
    }

    // --- 模块导出 ---
    // 支持 Node.js/Jest 测试环境和浏览器环境
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = { isDarkTheme, applyTheme, setTheme, initTheme, initEventListeners, DARK_THEMES };
    } else {
        global.ThemeManager = { isDarkTheme, applyTheme, setTheme, initTheme, initEventListeners };
        // 浏览器环境下自动初始化监听
        initEventListeners();
        // 暴露旧版全局函数以兼容旧代码
        global.__setTheme = setTheme;
    }

})(typeof window !== 'undefined' ? window : this);
