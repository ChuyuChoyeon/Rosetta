/**
 * @jest-environment jsdom
 */

const { initSubmitLoading, initRippleEffect } = require('../../static/theme/js/ui');

describe('UI Manager', () => {
    beforeEach(() => {
        document.body.innerHTML = '';
        jest.useFakeTimers();
    });

    afterEach(() => {
        jest.useRealTimers();
    });

    test('Submit button shows loading state on form submit', () => {
        document.body.innerHTML = `
            <form id="test-form">
                <button type="submit">Submit</button>
            </form>
        `;

        initSubmitLoading();

        const form = document.getElementById('test-form');
        const btn = form.querySelector('button');

        // Trigger submit event
        const event = new Event('submit', { bubbles: true, cancelable: true });
        // Prevent default to avoid navigation errors in jsdom
        event.preventDefault(); 
        form.dispatchEvent(event);

        expect(btn.disabled).toBe(true);
        expect(btn.innerHTML).toContain('loading');
    });

    test('Submit button restores state after timeout', () => {
        document.body.innerHTML = `
            <form id="test-form">
                <button type="submit">Original</button>
            </form>
        `;

        initSubmitLoading();
        const form = document.getElementById('test-form');
        const btn = form.querySelector('button');
        
        // Trigger submit
        form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));

        expect(btn.disabled).toBe(true);

        // Fast-forward time by 10 seconds
        jest.advanceTimersByTime(10000);

        expect(btn.disabled).toBe(false);
        expect(btn.innerHTML).toBe('Original');
    });

    test('Forms with no-loading class are ignored', () => {
        document.body.innerHTML = `
            <form id="test-form" class="no-loading">
                <button type="submit">Submit</button>
            </form>
        `;

        initSubmitLoading();
        const form = document.getElementById('test-form');
        const btn = form.querySelector('button');
        
        form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));

        expect(btn.disabled).toBe(false);
        expect(btn.innerHTML).toBe('Submit');
    });

    test('Ripple effect is added on mousedown', () => {
        document.body.innerHTML = `
            <button class="btn">Click Me</button>
        `;

        initRippleEffect();
        const btn = document.querySelector('.btn');

        btn.dispatchEvent(new Event('mousedown', { bubbles: true }));

        expect(btn.classList.contains('btn-active')).toBe(true);

        // Fast-forward time by 200ms
        jest.advanceTimersByTime(200);

        expect(btn.classList.contains('btn-active')).toBe(false);
    });
});
