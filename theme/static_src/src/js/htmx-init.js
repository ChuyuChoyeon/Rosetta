/**
 * Rosetta HTMX Initialization & Global State Management
 * v5.0 - Fully Optimized & Chinese Annotated
 *
 * 核心职责:
 * 1. 管理 HTMX 生命周期事件 (Load, Swap, Error)
 * 2. 初始化全局 UI 组件 (Theme, Charts, etc.)
 * 3. 提供插件注册机制，供各页面功能模块使用
 * 4. 解决 SPA 模式下的内存泄漏和状态同步问题
 */

// 确保 Rosetta 命名空间存在
window.Rosetta = window.Rosetta || {};

(function (R) {
  "use strict";

  // ==========================================================================
  // 1. 核心工具与生命周期管理 (Core Utilities)
  // ==========================================================================

  /**
   * 注册初始化函数 - 页面加载和 HTMX 内容替换时都会触发
   * @param {Function} callback - (targetElement) => void
   */
  R.onLoad = function (callback) {
    if (window.htmx) {
      htmx.onLoad(callback);
    } else {
      document.addEventListener("DOMContentLoaded", () =>
        callback(document.body),
      );
    }
  };

  /**
   * 获取当前主题模式 (Dark/Light)
   * 优先级: data-theme > class > localStorage > System
   * @returns {'dark'|'light'}
   */
  R.getThemeMode = function () {
    const el = document.documentElement;
    const attr = el.getAttribute("data-theme");
    if (attr === "dark" || attr === "light") return attr;
    if (el.classList.contains("dark")) return "dark";
    const stored = localStorage.getItem("theme");
    if (stored === "dark" || stored === "light") return stored;
    if (
      window.matchMedia &&
      window.matchMedia("(prefers-color-scheme: dark)").matches
    )
      return "dark";
    return "light";
  };

  // ==========================================================================
  // 2. 图表管理模块 (Chart Manager)
  // ==========================================================================

  R.Charts = {
    instances: new Map(), // 存储图表实例: id -> chartInstance

    /**
     * 初始化所有仪表盘图表
     * @param {HTMLElement} content - 扫描范围
     */
    init(content) {
      if (typeof ApexCharts === "undefined") return;

      // 1. 同步主题状态 (防止图表颜色与当前主题不一致)
      this.syncTheme();

      // 2. 初始化各个图表
      this.initTrendChart(content);
      this.initCommentDonut(content);
      this.initCategoryChart(content);
      this.initTagChart(content);
    },

    /**
     * 强制同步 ThemeManager 状态与 DOM
     */
    syncTheme() {
      if (window.ThemeManager) {
        const currentMode = R.getThemeMode();
        if (window.ThemeManager.currentTheme !== currentMode) {
          // console.log(`[Rosetta] Syncing ThemeManager to ${currentMode}`);
          window.ThemeManager.currentTheme = currentMode;
        }
        window.ThemeManager.syncToggles();
      }
    },

    /**
     * 趋势图 (Area Chart)
     */
    initTrendChart(content) {
      const el = content.querySelector("#trendChart");
      if (!el || el.chart) return;

      // 防止回退导航时的重复渲染
      if (el.querySelector(".apexcharts-canvas")) el.innerHTML = "";

      try {
        const dates = JSON.parse(el.dataset.trendDates);
        const counts = JSON.parse(el.dataset.trendCounts);
        const userCounts = JSON.parse(el.dataset.userTrendCounts);
        const initialMode = R.getThemeMode();

        const options = {
          series: [
            { name: "评论", data: counts },
            { name: "新用户", data: userCounts },
          ],
          chart: {
            type: "area",
            height: 320,
            toolbar: { show: false },
            fontFamily: "inherit",
            background: "transparent",
            animations: { enabled: true },
            events: {
              mounted: (chart) => this.attachThemeObserver(chart, "trendChart"),
            },
          },
          colors: ["#4f46e5", "#9333ea"],
          dataLabels: { enabled: false },
          stroke: { curve: "smooth", width: 2 },
          fill: {
            type: "gradient",
            gradient: {
              shadeIntensity: 1,
              opacityFrom: 0.4,
              opacityTo: 0.05,
              stops: [0, 90, 100],
            },
          },
          xaxis: {
            categories: dates,
            axisBorder: { show: false },
            axisTicks: { show: false },
            labels: {
              style: {
                colors:
                  initialMode === "dark"
                    ? "#A6ADBB"
                    : "var(--fallback-bc,oklch(var(--bc)/0.6))",
              },
            },
          },
          yaxis: { show: false },
          grid: {
            borderColor: "var(--fallback-bc,oklch(var(--bc)/0.05))",
            strokeDashArray: 4,
            yaxis: { lines: { show: true } },
          },
          theme: {
            mode: initialMode,
            palette: initialMode === "dark" ? "palette1" : undefined,
          },
        };

        const chart = new ApexCharts(el, options);
        chart.render();
        el.chart = chart;
        this.instances.set("trendChart", chart);
      } catch (e) {
        console.error("[Rosetta] Error initializing trend chart:", e);
      }
    },

    /**
     * 评论分布图 (Donut Chart)
     */
    initCommentDonut(content) {
      const el = content.querySelector("#commentDonut");
      if (!el || el.chart) return;

      if (el.querySelector(".apexcharts-canvas")) el.innerHTML = "";

      try {
        const data = JSON.parse(el.dataset.commentStatus);
        const initialMode = R.getThemeMode();
        const options = {
          series: data,
          labels: ["已发布", "待审核"],
          chart: {
            type: "donut",
            height: 240,
            fontFamily: "inherit",
            background: "transparent",
            events: {
              mounted: (chart) =>
                this.attachThemeObserver(chart, "commentDonut"),
            },
          },
          plotOptions: {
            pie: {
              donut: {
                size: "75%",
                labels: {
                  show: true,
                  name: {
                    show: true,
                    offsetY: -10,
                    color:
                      initialMode === "dark"
                        ? "#A6ADBB"
                        : "var(--fallback-bc,oklch(var(--bc)/0.6))",
                  },
                  value: {
                    show: true,
                    fontSize: "24px",
                    fontWeight: 600,
                    offsetY: 5,
                    color: initialMode === "dark" ? "#A6ADBB" : "#1f2937",
                  },
                  total: {
                    show: true,
                    label: "总评论",
                    color:
                      initialMode === "dark"
                        ? "#A6ADBB"
                        : "var(--fallback-bc,oklch(var(--bc)/0.6))",
                    formatter: function (w) {
                      return w.globals.seriesTotals.reduce((a, b) => a + b, 0);
                    },
                  },
                },
              },
            },
          },
          colors: ["#22c55e", "#eab308"],
          dataLabels: { enabled: false },
          legend: { show: false },
          stroke: { show: false },
          theme: {
            mode: initialMode,
            palette: initialMode === "dark" ? "palette1" : undefined,
          },
        };

        const chart = new ApexCharts(el, options);
        chart.render();
        el.chart = chart;
        this.instances.set("commentDonut", chart);
      } catch (e) {
        console.error("[Rosetta] Error initializing comment donut:", e);
      }
    },

    /**
     * 分类分布图 (Polar Area)
     */
    initCategoryChart(content) {
      const el = content.querySelector("#categoryChart");
      if (!el || el.chart) return;

      if (el.querySelector(".apexcharts-canvas")) el.innerHTML = "";

      try {
        const labels = JSON.parse(el.dataset.categoryLabels);
        const data = JSON.parse(el.dataset.categoryData);
        const initialMode = R.getThemeMode();

        const options = {
          series: data,
          labels: labels,
          chart: {
            type: "polarArea",
            height: 300,
            fontFamily: "inherit",
            background: "transparent",
            toolbar: { show: false },
            events: {
              mounted: (chart) =>
                this.attachThemeObserver(chart, "categoryChart"),
            },
          },
          stroke: { colors: ["var(--fallback-b1,oklch(var(--b1)/1))"] },
          fill: { opacity: 0.8 },
          legend: {
            position: "bottom",
            labels: {
              colors:
                initialMode === "dark"
                  ? "#A6ADBB"
                  : "var(--fallback-bc,oklch(var(--bc)/1))",
            },
          },
          theme: {
            mode: initialMode,
            monochrome: {
              enabled: true,
              color: "#4f46e5",
              shadeTo: "light",
              shadeIntensity: 0.65,
            },
          },
        };

        const chart = new ApexCharts(el, options);
        chart.render();
        el.chart = chart;
        this.instances.set("categoryChart", chart);
      } catch (e) {
        console.error("[Rosetta] Error initializing category chart:", e);
      }
    },

    /**
     * 标签图 (Bar Chart)
     */
    initTagChart(content) {
      const el = content.querySelector("#tagChart");
      if (!el || el.chart) return;

      if (el.querySelector(".apexcharts-canvas")) el.innerHTML = "";

      try {
        const labels = JSON.parse(el.dataset.tagLabels);
        const data = JSON.parse(el.dataset.tagData);
        const initialMode = R.getThemeMode();

        const options = {
          series: [{ name: "文章数", data: data }],
          chart: {
            type: "bar",
            height: 300,
            toolbar: { show: false },
            fontFamily: "inherit",
            background: "transparent",
            events: {
              mounted: (chart) => this.attachThemeObserver(chart, "tagChart"),
            },
          },
          plotOptions: {
            bar: { borderRadius: 4, horizontal: true, distributed: true },
          },
          colors: [
            "#4f46e5",
            "#ec4899",
            "#06b6d4",
            "#8b5cf6",
            "#10b981",
            "#f59e0b",
          ],
          dataLabels: { enabled: false },
          xaxis: {
            categories: labels,
            labels: {
              style: {
                colors:
                  initialMode === "dark"
                    ? "#A6ADBB"
                    : "var(--fallback-bc,oklch(var(--bc)/0.6))",
              },
            },
          },
          yaxis: {
            labels: {
              style: { colors: initialMode === "dark" ? "#A6ADBB" : "#1f2937" },
            },
          },
          grid: {
            borderColor: "var(--fallback-bc,oklch(var(--bc)/0.05))",
          },
          legend: { show: false },
          theme: { mode: initialMode },
        };

        const chart = new ApexCharts(el, options);
        chart.render();
        el.chart = chart;
        this.instances.set("tagChart", chart);
      } catch (e) {
        console.error("[Rosetta] Error initializing tag chart:", e);
      }
    },

    /**
     * 监听主题变化并自动更新图表
     */
    attachThemeObserver(chart, chartId) {
      const observer = new MutationObserver((mutations) => {
        const el = document.getElementById(chartId);
        if (!el || !el.chart) {
          observer.disconnect();
          return;
        }

        mutations.forEach((mutation) => {
          if (
            mutation.attributeName === "data-theme" ||
            mutation.attributeName === "class"
          ) {
            const mode = R.getThemeMode();
            try {
              // 简单的通用更新逻辑
              const textColor = mode === "dark" ? "#A6ADBB" : "#1f2937";
              chart.updateOptions({
                theme: { mode: mode },
                xaxis: { labels: { style: { colors: textColor } } },
                legend: { labels: { colors: textColor } },
              });
            } catch (e) {
              // 图表可能已被销毁
              observer.disconnect();
            }
          }
        });
      });

      observer.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ["data-theme", "class"],
      });
      chart.themeObserver = observer;
    },

    /**
     * 销毁所有图表实例 (用于 HTMX 页面切换前清理)
     */
    destroyAll() {
      this.instances.forEach((chart, id) => {
        if (chart) {
          if (chart.themeObserver) chart.themeObserver.disconnect();
          chart.destroy();
        }
      });
      this.instances.clear();
      // 清除 DOM 元素上的引用
      document.querySelectorAll('[id$="Chart"], [id$="Donut"]').forEach(el => {
        el.chart = null;
      });
    },
  };

  // ==========================================================================
  // 3. 全局 Alpine 组件注册 (Global Alpine Components)
  // ==========================================================================

  R.registerComponents = function () {
    if (typeof Alpine === "undefined") return;

    // 3. 全局命令面板 (Moved to ui-helpers.js to support both Frontend and Admin)
    // Alpine.data("commandPalette", ...) removed to avoid conflict.


    // 1. 图标选择器组件
    Alpine.data("iconPicker", (config) => {
      config = config || {};
      return {
        searchQuery: "",
        selected: config.initialValue || "star",
        icons: config.icons || [],
        isOpen: false,

      get filteredIcons() {
        if (!this.searchQuery) return this.icons;
        const lower = this.searchQuery.toLowerCase();
        return this.icons.filter((icon) => icon.toLowerCase().includes(lower));
      },

      selectIcon(name) {
        this.selected = name;
        this.$dispatch("icon-selected", name);
        // 如果绑定了 input，更新 input 值
        const input = document.getElementById(config.inputId);
        if (input) {
          input.value = name;
          input.dispatchEvent(new Event("change"));
        }
        document.getElementById(config.modalId).close();
      },

      isSelected(name) {
        return this.selected === name;
      },
    };
  });

    // 2. 创建分类组件 (带自动翻译)
    Alpine.data("createCategory", () => ({
      isTranslating: false,
      coverPreview: null,
      form: {
        name_zh_hans: "",
        name_en: "",
        name_ja: "",
        name_zh_hant: "",
        color: "Blue",
      },
      colors: [
        { name: "Slate", value: "#64748b", class: "bg-slate-500" },
        { name: "Red", value: "#ef4444", class: "bg-red-500" },
        { name: "Orange", value: "#f97316", class: "bg-orange-500" },
        { name: "Amber", value: "#f59e0b", class: "bg-amber-500" },
        { name: "Yellow", value: "#eab308", class: "bg-yellow-500" },
        { name: "Lime", value: "#84cc16", class: "bg-lime-500" },
        { name: "Green", value: "#22c55e", class: "bg-green-500" },
        { name: "Emerald", value: "#10b981", class: "bg-emerald-500" },
        { name: "Teal", value: "#14b8a6", class: "bg-teal-500" },
        { name: "Cyan", value: "#06b6d4", class: "bg-cyan-500" },
        { name: "Sky", value: "#0ea5e9", class: "bg-sky-500" },
        { name: "Blue", value: "#3b82f6", class: "bg-blue-500" },
        { name: "Indigo", value: "#6366f1", class: "bg-indigo-500" },
        { name: "Violet", value: "#8b5cf6", class: "bg-violet-500" },
        { name: "Purple", value: "#a855f7", class: "bg-purple-500" },
        { name: "Fuchsia", value: "#d946ef", class: "bg-fuchsia-500" },
        { name: "Pink", value: "#ec4899", class: "bg-pink-500" },
        { name: "Rose", value: "#f43f5e", class: "bg-rose-500" },
      ],

      handleFile(event) {
        const file = event.target.files[0];
        if (file) {
          const reader = new FileReader();
          reader.onload = (e) => {
            this.coverPreview = e.target.result;
          };
          reader.readAsDataURL(file);
        }
      },

      async translateAll() {
        if (!this.form.name_zh_hans) {
          if (window.showToast) window.showToast("请先输入中文名称", "warning");
          return;
        }
        this.isTranslating = true;
        try {
          const csrfToken = document.querySelector(
            "[name=csrfmiddlewaretoken]",
          ).value;
          const response = await fetch("/api/translate/", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": csrfToken,
            },
            body: JSON.stringify({
              text: this.form.name_zh_hans,
              target_langs: ["en", "ja", "zh-hant"],
            }),
          });
          const data = await response.json();
          if (data.translations) {
            if (data.translations.en) this.form.name_en = data.translations.en;
            if (data.translations.ja) this.form.name_ja = data.translations.ja;
            if (data.translations["zh-hant"])
              this.form.name_zh_hant = data.translations["zh-hant"];
            if (window.showToast) window.showToast("翻译完成", "success");
          }
        } catch (e) {
          console.error(e);
          if (window.showToast) window.showToast("翻译失败", "error");
        } finally {
          this.isTranslating = false;
        }
      },
    }));
  };

  // ==========================================================================
  // 4. 事件监听与初始化 (Event Listeners & Init)
  // ==========================================================================

  // A. 注册 Alpine 组件
  document.addEventListener("alpine:init", R.registerComponents);
  if (window.Alpine) R.registerComponents(); // 如果 Alpine 已经加载

  // B. 使用 HTMX onLoad 钩子初始化页面逻辑
  R.onLoad((target) => {
    // 1. 初始化图表
    R.Charts.init(target);
    
    // 2. 初始化阅读进度条
    if (window.initReadingProgress) {
      window.initReadingProgress();
    }
    
    // 3. 自动检测表单错误并显示 Toast
    // 扫描 target 内的错误提示 (兼容 Django Form errors 和 alert-error)
    const errorAlerts = target.querySelectorAll('.alert.alert-error, .alert.text-error, .errorlist li, .invalid-feedback');
    if (errorAlerts.length > 0) {
      // 收集错误信息 (去重)
      let messages = new Set();
      errorAlerts.forEach(alert => {
        // 忽略隐藏元素
        if (alert.offsetParent === null) return;
        
        const text = alert.innerText.replace(/\s+/g, ' ').trim();
        if (text && text.length < 100) {
          messages.add(text);
        }
      });
      
      if (messages.size > 0) {
        const msgArray = Array.from(messages);
        let toastMsg = "表单提交有误，请检查填写内容";
        
        if (msgArray.length === 1) {
          toastMsg = msgArray[0];
        } else if (msgArray.length <= 3) {
          toastMsg = msgArray.join('\n');
        } else {
          toastMsg = `表单提交有误，共有 ${messages.size} 处错误，请检查填写内容`;
        }
        
        if (window.showToast) {
          // 延迟一点显示，确保 Toast 组件已挂载
          setTimeout(() => window.showToast(toastMsg, 'error'), 100);
        }
      }
    }
  });

  // C. HTMX 生命周期管理
  
  // 在保存历史记录前销毁图表，防止恢复时出现僵尸图表
  document.addEventListener("htmx:beforeHistorySave", () => {
    R.Charts.destroyAll();
  });

  // 在内容交换前销毁图表 (防止内存泄漏)
  document.addEventListener("htmx:beforeSwap", () => {
    R.Charts.destroyAll();
  });

  // 全局 HTMX 错误处理
  document.addEventListener("htmx:responseError", function (evt) {
    const xhr = evt.detail.xhr;
    let errorMessage = "系统错误";

    try {
      if (xhr.response) {
        const data = JSON.parse(xhr.response);
        if (data.error || data.message) {
          errorMessage = data.error || data.message;
        } else {
          // 尝试从 HTML 中提取标题
          const parser = new DOMParser();
          const doc = parser.parseFromString(xhr.response, "text/html");
          const title = doc.querySelector("title");
          if (title) errorMessage = title.innerText;
        }
      }
    } catch (e) {
      if (xhr.statusText) errorMessage = `${xhr.status} ${xhr.statusText}`;
    }

    if (window.showToast) {
      window.showToast(errorMessage, "error");
    } else {
      console.error("[HTMX Error]", errorMessage);
    }
  });

})(window.Rosetta);
