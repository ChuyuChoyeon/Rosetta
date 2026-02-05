/**
 * Global Page Loader (NProgress)
 * Integrated with HTMX and standard navigation.
 * 
 * Best Practices:
 * 1. Does not use 'beforeunload' to avoid stuck bars on cancelled navigation.
 * 2. Hooks into HTMX events for SPA-like transitions.
 * 3. Handles history restore events.
 */

(function() {
    // 1. Configure NProgress
    if (window.NProgress) {
        NProgress.configure({ 
            showSpinner: false,
            minimum: 0.1,
            speed: 500,
            easing: 'ease',
            trickleSpeed: 200
        });
    }

    // 2. HTMX Integration
    document.addEventListener("htmx:configRequest", function() {
        if (window.NProgress) NProgress.start();
        document.body.classList.add('loading-state');
    });

    document.addEventListener("htmx:afterOnLoad", function() {
        if (window.NProgress) NProgress.done();
        document.body.classList.remove('loading-state');
    });

    document.addEventListener("htmx:historyRestore", function() {
        // Force cleanup on restore just in case
        if (window.NProgress) NProgress.remove();
        document.body.classList.remove('loading-state');
    });

    document.addEventListener("htmx:loadError", function() {
        if (window.NProgress) NProgress.done();
        document.body.classList.remove('loading-state');
    });

    // CRITICAL: Prevent NProgress from being saved in HTMX history snapshot
    // If we don't do this, the progress bar (at 20% or whatever) gets saved in the DOM HTML.
    // When the user clicks "Back", HTMX restores that HTML, showing a stuck progress bar.
    document.addEventListener("htmx:beforeHistorySave", function() {
        if (window.NProgress) {
            // Remove the DOM element completely before snapshot
            NProgress.remove(); 
        }
        document.body.classList.remove('loading-state');
    });

    // 3. Fallback / Standard Navigation Safety
    // Ensure bar is done when the new page is fully loaded
    window.addEventListener('load', function() {
        if (window.NProgress) NProgress.done();
        document.body.classList.remove('loading-state');
    });

    // 4. Handle bfcache (Back/Forward Cache)
    window.addEventListener('pageshow', function(event) {
        if (event.persisted) {
            if (window.NProgress) NProgress.done();
            document.body.classList.remove('loading-state');
        }
    });

})();
