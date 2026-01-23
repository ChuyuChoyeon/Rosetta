// Global initializer for HTMX navigations and initial page load
// Ensures page-specific modules initialize after content swaps
(function () {
  function run(fn) {
    try {
      fn();
    } catch (e) {
      console.error('[htmx-init] initialization error:', e);
    }
  }

  function initEditor(root) {
    var editorContainer = (root || document).querySelector('#editor');
    var contentInput = (root || document).querySelector('#id_content');
    if (!editorContainer || !contentInput) return;
    if (editorContainer.dataset.initialized === '1') return;
    if (typeof window.initByteMD !== 'function') return;
    var initialValue = contentInput.value || '';
    window.initByteMD('editor', 'id_content', initialValue);
    editorContainer.dataset.initialized = '1';
  }

  function initDashboard(root) {
    if (typeof window.initCharts === 'function') {
      window.initCharts();
      return;
    }
    var trendEl = (root || document).querySelector('#trendChart');
    var donutEl = (root || document).querySelector('#commentDonut');
    if (!trendEl && !donutEl) return;
    console.warn('[htmx-init] dashboard initializer not found; ensure window.initCharts is defined on dashboard page.');
  }

  function initAll(root) {
    run(function () {
      initEditor(root);
    });
    run(function () {
      initDashboard(root);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      initAll(document);
    });
  } else {
    initAll(document);
  }

  if (window.htmx && typeof window.htmx.on === 'function') {
    window.htmx.on('htmx:afterSettle', function (evt) {
      initAll(evt.target || document);
    });
  } else {
    document.addEventListener('htmx:afterSettle', function (evt) {
      initAll(evt.target || document);
    });
  }
})();
