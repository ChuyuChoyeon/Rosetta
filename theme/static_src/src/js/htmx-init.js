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

  var registry = [];
  function register(fn) {
    if (typeof fn === 'function') {
      registry.push(fn);
    }
  }
  function runRegistry(root) {
    registry.forEach(function (fn) {
      run(function () {
        fn(root || document);
      });
    });
  }
  window.registerHtmxInit = register;
  window.runHtmxInit = runRegistry;

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
    var scope = root || document;
    var trendEl = scope.querySelector('#trendChart');
    var donutEl = scope.querySelector('#commentDonut');
    var categoryEl = scope.querySelector('#categoryChart');
    var tagEl = scope.querySelector('#tagChart');

    if (!trendEl && !donutEl && !categoryEl && !tagEl) return;
    if (typeof window.ApexCharts !== 'function') return;

    var parseJson = function (value, fallback) {
      if (!value) return fallback;
      try {
        return JSON.parse(value);
      } catch (e) {
        return fallback;
      }
    };
    var resolveColor = function (cssColor) {
      var el = document.createElement('span');
      el.style.color = cssColor;
      el.style.display = 'none';
      document.body.appendChild(el);
      var resolved = getComputedStyle(el).color;
      document.body.removeChild(el);
      return resolved || cssColor;
    };
    var getCssVar = function (varName) {
      return getComputedStyle(document.documentElement).getPropertyValue(varName).trim();
    };

    var currentTheme = document.documentElement.getAttribute('data-theme');
    var themeMode = currentTheme === 'light' ? 'light' : 'dark';
    var textColor = resolveColor('oklch(var(--bc))');
    var mutedTextColor = resolveColor('oklch(var(--bc) / 0.6)');
    var gridColor = resolveColor('oklch(var(--bc) / 0.1)');

    var applyChartTextColors = function (container) {
      if (!container) return;
      var textNodes = container.querySelectorAll('text.apexcharts-text');
      textNodes.forEach(function (node) {
        var isMuted = node.classList.contains('apexcharts-xaxis-label') || node.classList.contains('apexcharts-yaxis-label') || node.classList.contains('apexcharts-datalabel-label');
        var color = isMuted ? mutedTextColor : textColor;
        node.setAttribute('fill', color);
        node.style.fill = color;
      });
    };

    if (trendEl) {
      if (trendEl._chart) {
        try {
          trendEl._chart.destroy();
        } catch (e) {}
      }
      var trendCounts = parseJson(trendEl.dataset.trendCounts, []);
      var userTrendCounts = parseJson(trendEl.dataset.userTrendCounts, []);
      var trendDates = parseJson(trendEl.dataset.trendDates, []);
      var optionsTrend = {
        series: [
          { name: '评论数', data: trendCounts },
          { name: '新用户', data: userTrendCounts }
        ],
        chart: {
          type: 'area',
          height: 320,
          toolbar: { show: false },
          fontFamily: 'inherit',
          background: 'transparent',
          animations: { enabled: true },
          foreColor: textColor
        },
        stroke: { curve: 'smooth', width: 3 },
        fill: {
          type: 'gradient',
          gradient: {
            shadeIntensity: 1,
            opacityFrom: 0.45,
            opacityTo: 0.05,
            stops: [0, 100]
          }
        },
        dataLabels: { enabled: false },
        xaxis: {
          categories: trendDates,
          labels: {
            show: true,
            style: { colors: mutedTextColor, fontSize: '11px', fontFamily: 'inherit' }
          },
          axisBorder: { show: false },
          axisTicks: { show: false },
          tooltip: { enabled: false }
        },
        yaxis: {
          show: true,
          labels: {
            style: { colors: mutedTextColor, fontSize: '11px', fontFamily: 'inherit' }
          }
        },
        grid: {
          show: true,
          borderColor: gridColor,
          strokeDashArray: 4,
          padding: { top: 0, right: 0, bottom: 0, left: 10 }
        },
        theme: { mode: themeMode },
        colors: [getCssVar('--p') || '#3ABFF8', getCssVar('--s') || '#D926A9'],
        tooltip: {
          theme: themeMode,
          style: { fontSize: '12px', fontFamily: 'inherit' },
          x: { show: false },
          marker: { show: false },
          cssClass: 'apexcharts-tooltip-theme-layer'
        }
      };
      var chartTrend = new ApexCharts(trendEl, optionsTrend);
      chartTrend.render();
      trendEl._chart = chartTrend;
      setTimeout(function () {
        applyChartTextColors(trendEl);
      }, 0);
    }

    if (donutEl) {
      if (donutEl._chart) {
        try {
          donutEl._chart.destroy();
        } catch (e) {}
      }
      var commentStatusData = parseJson(donutEl.dataset.commentStatus, []);
      var optionsDonut = {
        series: commentStatusData,
        labels: ['已发布', '待审核'],
        chart: {
          type: 'donut',
          height: 160,
          fontFamily: 'inherit',
          background: 'transparent',
          foreColor: textColor
        },
        plotOptions: {
          pie: {
            donut: {
              size: '75%',
              labels: {
                show: true,
                name: { show: false },
                value: {
                  show: true,
                  fontSize: '20px',
                  fontWeight: 700,
                  color: textColor,
                  formatter: function (val) {
                    return val;
                  }
                },
                total: {
                  show: true,
                  showAlways: true,
                  label: '总计',
                  fontSize: '12px',
                  color: mutedTextColor,
                  formatter: function (w) {
                    return w.globals.seriesTotals.reduce(function (a, b) {
                      return a + b;
                    }, 0);
                  }
                }
              }
            }
          }
        },
        dataLabels: { enabled: false },
        legend: { show: false },
        stroke: { show: false },
        theme: { mode: themeMode },
        colors: [getCssVar('--su') || '#36D399', getCssVar('--wa') || '#FBBD23'],
        tooltip: { enabled: false }
      };
      var chartDonut = new ApexCharts(donutEl, optionsDonut);
      chartDonut.render();
      donutEl._chart = chartDonut;
      setTimeout(function () {
        applyChartTextColors(donutEl);
      }, 0);
    }

    if (categoryEl) {
      if (categoryEl._chart) {
        try {
          categoryEl._chart.destroy();
        } catch (e) {}
      }
      var categoryLabels = parseJson(categoryEl.dataset.categoryLabels, []);
      var categoryData = parseJson(categoryEl.dataset.categoryData, []);

      var optionsCategory = {
        series: categoryData,
        labels: categoryLabels,
        chart: {
          type: 'donut',
          height: 300,
          fontFamily: 'inherit',
          background: 'transparent',
          foreColor: textColor
        },
        plotOptions: {
          pie: {
            donut: {
              size: '65%',
              labels: {
                show: true,
                total: {
                  show: true,
                  label: '总计',
                  color: mutedTextColor,
                  formatter: function (w) {
                    return w.globals.seriesTotals.reduce(function (a, b) {
                      return a + b;
                    }, 0);
                  }
                }
              }
            }
          }
        },
        dataLabels: { enabled: false },
        legend: {
          position: 'bottom',
          labels: { colors: textColor }
        },
        stroke: { show: false },
        theme: { mode: themeMode },
        colors: [
          getCssVar('--p') || '#3ABFF8',
          getCssVar('--s') || '#D926A9',
          getCssVar('--a') || '#1FB2A6',
          getCssVar('--n') || '#2A323C'
        ],
        tooltip: { theme: themeMode }
      };

      var chartCategory = new ApexCharts(categoryEl, optionsCategory);
      chartCategory.render();
      categoryEl._chart = chartCategory;
    }

    if (tagEl) {
      if (tagEl._chart) {
        try {
          tagEl._chart.destroy();
        } catch (e) {}
      }
      var tagLabels = parseJson(tagEl.dataset.tagLabels, []);
      var tagData = parseJson(tagEl.dataset.tagData, []);

      var optionsTag = {
        series: [{
          name: '文章数',
          data: tagData
        }],
        chart: {
          type: 'bar',
          height: 300,
          toolbar: { show: false },
          fontFamily: 'inherit',
          background: 'transparent',
          foreColor: textColor
        },
        plotOptions: {
          bar: {
            borderRadius: 4,
            horizontal: true,
            barHeight: '60%',
            distributed: true
          }
        },
        dataLabels: { enabled: false },
        xaxis: {
          categories: tagLabels,
          labels: { style: { colors: mutedTextColor } },
          axisBorder: { show: false },
          axisTicks: { show: false }
        },
        yaxis: {
          labels: { style: { colors: textColor } }
        },
        grid: {
          borderColor: gridColor,
          strokeDashArray: 4
        },
        theme: { mode: themeMode },
        colors: [
          getCssVar('--p') || '#3ABFF8',
          getCssVar('--s') || '#D926A9',
          getCssVar('--a') || '#1FB2A6',
          getCssVar('--in') || '#3ABFF8',
          getCssVar('--su') || '#36D399',
          getCssVar('--wa') || '#FBBD23',
          getCssVar('--er') || '#F87272'
        ],
        legend: { show: false },
        tooltip: {
          theme: themeMode,
          x: { show: true }  // 确保 tooltip 显示标签名
        }
      };

      var chartTag = new ApexCharts(tagEl, optionsTag);
      chartTag.render();
      tagEl._chart = chartTag;
    }

    if (!document.documentElement.dataset.dashboardObserver) {
      var observer = new MutationObserver(function (mutations) {
        mutations.forEach(function (mutation) {
          if (mutation.type === 'attributes' && mutation.attributeName === 'data-theme') {
            setTimeout(function () {
              initDashboard(document);
            }, 100);
          }
        });
      });
      observer.observe(document.documentElement, { attributes: true });
      document.documentElement.dataset.dashboardObserver = '1';
    }

    if (!document.documentElement.dataset.dashboardCleanupBound) {
      document.addEventListener('htmx:beforeSwap', function () {
        var trendTarget = document.querySelector('#trendChart');
        if (trendTarget && trendTarget._chart) {
          try {
            trendTarget._chart.destroy();
          } catch (e) {}
          delete trendTarget._chart;
        }
        var donutTarget = document.querySelector('#commentDonut');
        if (donutTarget && donutTarget._chart) {
          try {
            donutTarget._chart.destroy();
          } catch (e) {}
          delete donutTarget._chart;
        }
        var categoryTarget = document.querySelector('#categoryChart');
        if (categoryTarget && categoryTarget._chart) {
          try {
            categoryTarget._chart.destroy();
          } catch (e) {}
          delete categoryTarget._chart;
        }
        var tagTarget = document.querySelector('#tagChart');
        if (tagTarget && tagTarget._chart) {
          try {
            tagTarget._chart.destroy();
          } catch (e) {}
          delete tagTarget._chart;
        }
      });
      document.documentElement.dataset.dashboardCleanupBound = '1';
    }
  }

  function initThemeToggle(root) {
    var toggle = (root || document).querySelector('#theme-toggle-admin');
    if (!toggle) return;
    var currentTheme = localStorage.getItem('theme') || document.documentElement.getAttribute('data-theme');
    toggle.checked = currentTheme === 'dark';
  }

  function initAll(root) {
    run(function () {
      initEditor(root);
    });
    run(function () {
      initDashboard(root);
    });
    run(function () {
      initThemeToggle(root);
    });
    run(function () {
      runRegistry(root);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      initAll(document);
    });
  } else {
    initAll(document);
  }

  var handleInitEvent = function (evt) {
    initAll((evt && evt.target) || document);
  };

  if (window.htmx && typeof window.htmx.on === 'function') {
    window.htmx.on('htmx:afterSettle', handleInitEvent);
    window.htmx.on('htmx:historyRestore', handleInitEvent);
  } else {
    document.addEventListener('htmx:afterSettle', handleInitEvent);
    document.addEventListener('htmx:historyRestore', handleInitEvent);
  }
})();
