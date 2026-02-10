/**
 * 全局页面加载器 (NProgress)
 * 集成 HTMX 和标准导航
 *
 * 最佳实践:
 * 1. 不使用 'beforeunload' 以避免在取消导航时进度条卡住
 * 2. 挂钩 HTMX 事件以支持 SPA 风格的过渡
 * 3. 处理历史记录恢复
 */

(function () {
  // 1. 配置 NProgress
  if (window.NProgress) {
    NProgress.configure({
      showSpinner: false,
      minimum: 0.1,
      speed: 500,
      easing: "ease",
      trickleSpeed: 200,
    });
  }

  // 2. HTMX 集成
  document.addEventListener("htmx:configRequest", function () {
    if (window.NProgress) NProgress.start();
    document.body.classList.add("loading-state");
  });

  document.addEventListener("htmx:afterOnLoad", function () {
    if (window.NProgress) NProgress.done();
    document.body.classList.remove("loading-state");
  });

  document.addEventListener("htmx:historyRestore", function () {
    // 在恢复时强制清理，以防万一
    if (window.NProgress) NProgress.remove();
    document.body.classList.remove("loading-state");
  });

  document.addEventListener("htmx:loadError", function () {
    if (window.NProgress) NProgress.done();
    document.body.classList.remove("loading-state");
  });

  // 关键: 防止 NProgress 被保存到 HTMX 历史快照中
  // 如果不这样做，进度条 (例如 20%) 会被保存到 DOM HTML 中
  // 当用户点击"返回"时，HTMX 会恢复该 HTML，显示卡住的进度条
  document.addEventListener("htmx:beforeHistorySave", function () {
    if (window.NProgress) {
      // 在快照前完全移除 DOM 元素
      NProgress.remove();
    }
    document.body.classList.remove("loading-state");
  });

  // 3. 回退 / 标准导航安全
  // 确保新页面完全加载时进度条完成
  window.addEventListener("load", function () {
    if (window.NProgress) NProgress.done();
    document.body.classList.remove("loading-state");
  });

  // 4. 处理 bfcache (后退/前进缓存)
  window.addEventListener("pageshow", function (event) {
    if (event.persisted) {
      if (window.NProgress) NProgress.done();
      document.body.classList.remove("loading-state");
    }
  });
})();
