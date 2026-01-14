/**
 * @jest-environment jsdom
 */

const { isDarkTheme, applyTheme, setTheme, DARK_THEMES } = require('../../static/theme/js/theme');

describe('Theme Manager', () => {
    beforeEach(() => {
        // Clear localStorage and document attributes before each test
        localStorage.clear();
        document.documentElement.removeAttribute('data-theme');
        document.documentElement.classList.remove('dark');
        document.body.innerHTML = '';
    });

    test('isDarkTheme correctly identifies dark themes', () => {
        expect(isDarkTheme('dark')).toBe(true);
        expect(isDarkTheme('business')).toBe(true);
        expect(isDarkTheme('light')).toBe(false);
        expect(isDarkTheme('cupcake')).toBe(false);
    });

    test('applyTheme sets data-theme attribute', () => {
        applyTheme('cupcake');
        expect(document.documentElement.getAttribute('data-theme')).toBe('cupcake');
        expect(document.documentElement.classList.contains('dark')).toBe(false);
    });

    test('applyTheme adds dark class for dark themes', () => {
        applyTheme('business');
        expect(document.documentElement.getAttribute('data-theme')).toBe('business');
        expect(document.documentElement.classList.contains('dark')).toBe(true);
    });

    test('applyTheme updates button active states', () => {
        // Setup DOM with theme buttons
        document.body.innerHTML = `
            <button data-set-theme="light" data-act-class="active font-bold">Light</button>
            <button data-set-theme="dark" data-act-class="active font-bold">Dark</button>
        `;

        applyTheme('dark');

        const lightBtn = document.querySelector('[data-set-theme="light"]');
        const darkBtn = document.querySelector('[data-set-theme="dark"]');

        expect(lightBtn.classList.contains('active')).toBe(false);
        expect(darkBtn.classList.contains('active')).toBe(true);
        expect(darkBtn.classList.contains('font-bold')).toBe(true);
    });

    test('setTheme saves to localStorage', () => {
        setTheme('cyberpunk');
        expect(localStorage.getItem('theme')).toBe('cyberpunk');
        expect(document.documentElement.getAttribute('data-theme')).toBe('cyberpunk');
    });
});
