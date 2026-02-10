import Cropper from "cropperjs";
import PinyinMatch from "pinyin-match";

// Expose PinyinMatch globally if needed, or just use it in this module
window.PinyinMatch = PinyinMatch;

/**
 * 全局 UI 辅助函数 (Global UI Helper Functions)
 * 标准化前端和管理后台的模态框、通知 (Toast) 和 HTMX 确认操作
 */

// 1. 确保全局模态框存在于 DOM 中
window.ensureGlobalModals = function () {
  const hasConfirm = document.getElementById("global_confirm_modal");
  const hasAlert = document.getElementById("global_alert_modal");

  if (!hasConfirm || !hasAlert) {
    // 仅当不存在时注入 (例如未通过 include 引入的情况)
    const wrapper = document.createElement("div");
    wrapper.innerHTML = `
        <dialog id="global_confirm_modal" class="modal">
            <div class="modal-box">
                <h3 class="font-bold text-lg flex items-center gap-2 text-warning" id="global_confirm_title">
                    <span class="material-symbols-outlined">warning</span>
                    确认操作
                </h3>
                <p class="py-4 text-base-content/80" id="global_confirm_message">确定要执行此操作吗？</p>
                <div class="modal-action">
                    <button type="button" class="btn btn-ghost" data-modal-close="global_confirm_modal">取消</button>
                    <button type="button" id="global_confirm_btn" class="btn btn-error text-white shadow-lg shadow-error/20">确定</button>
                </div>
            </div>
            <form method="dialog" class="modal-backdrop">
                <button>close</button>
            </form>
        </dialog>
        <dialog id="global_alert_modal" class="modal">
            <div class="modal-box">
                <h3 class="font-bold text-lg flex items-center gap-2 text-info">
                    <span class="material-symbols-outlined">info</span>
                    提示
                </h3>
                <p class="py-4 text-base-content/80" id="global_alert_message"></p>
                <div class="modal-action">
                    <button type="button" class="btn btn-primary" data-modal-close="global_alert_modal">确定</button>
                </div>
            </div>
            <form method="dialog" class="modal-backdrop">
                <button>close</button>
            </form>
        </dialog>
        `;
    document.body.appendChild(wrapper);
  }

  // 绑定关闭按钮事件 (使用事件委托处理动态创建的元素)
  if (!window.globalModalCloseListenerBound) {
    document.body.addEventListener("click", (evt) => {
      const btn = evt.target.closest("[data-modal-close]");
      if (btn) {
        evt.preventDefault();
        const modalId = btn.getAttribute("data-modal-close");
        const modal = document.getElementById(modalId);
        if (modal) modal.close();
      }
    });
    window.globalModalCloseListenerBound = true;
  }
};

// HTMX 内容替换后重新注入模态框 (防止全页替换导致模态框丢失)
document.addEventListener("htmx:afterSwap", () => {
  ensureGlobalModals();
});

// 2. 显示确认模态框
window.showConfirmModal = function (title, message, onConfirm) {
  ensureGlobalModals();
  const modal = document.getElementById("global_confirm_modal");
  const titleEl = document.getElementById("global_confirm_title");
  const msgEl = document.getElementById("global_confirm_message");
  const btn = document.getElementById("global_confirm_btn");

  if (!modal || !titleEl || !msgEl || !btn) return;

  // 更新内容
  // 标题支持 HTML (如图标)，消息仅支持文本 (安全考虑)
  if (title.includes("<")) {
    titleEl.innerHTML = title;
  } else {
    titleEl.innerHTML = `<span class="material-symbols-outlined">warning</span> ${title}`;
  }
  msgEl.textContent = message;

  // 克隆按钮以移除旧的事件监听器
  const newBtn = btn.cloneNode(true);
  btn.parentNode.replaceChild(newBtn, btn);

  newBtn.onclick = () => {
    if (typeof onConfirm === "function") {
      onConfirm();
    } else if (typeof onConfirm === "string") {
      // 处理 URL 跳转
      window.location.href = onConfirm;
    }
    modal.close();
  };

  modal.showModal();
};

// 3. 显示提示模态框
window.showGlobalAlert = function (message) {
  ensureGlobalModals();
  const modal = document.getElementById("global_alert_modal");
  const msgEl = document.getElementById("global_alert_message");

  if (!modal || !msgEl) return;

  msgEl.textContent = message;
  modal.showModal();
};

// 4. 显示 Toast 通知
window.showToast = function (message, type = "success") {
  window.dispatchEvent(
    new CustomEvent("show-toast", {
      detail: { message, type },
    }),
  );
};

// 5. HTMX 确认助手
// 用法: <button hx-post="..." hx-trigger="confirmed" onclick="confirmHtmx(this, 'Msg')">
window.confirmHtmx = function (element, message) {
  // 立即阻止默认 HTMX 触发
  if (window.event) {
    window.event.preventDefault();
    window.event.stopPropagation();
  }

  showConfirmModal("确认操作", message || "确定要执行此操作吗？", () => {
    // 触发实际的 HTMX 请求
    if (window.htmx) {
      htmx.trigger(element, "confirmed");
    }
  });
};

// 6. 传统删除助手 (用于非 HTMX 表单)
// 替代 eval(url) 的安全实现
window.confirmDelete = function (url, message) {
  window.showConfirmModal(
    "确认删除",
    message || "确定要删除此项目吗？此操作无法撤销。",
    () => {
      if (url.startsWith("javascript:")) {
        const code = url.substring(11);
        if (code.includes("history.back()")) {
            history.back();
        } else {
            // 尝试执行其他简单 JS，但建议后端改为返回 URL
            try { new Function(code)(); } catch(e) { console.error("Script execution failed:", e); }
        }
      } else {
        // 创建并提交 POST 表单
        const form = document.createElement("form");
        form.method = "POST";
        form.action = url;
        form.style.display = "none";

        // 禁用 HTMX 处理
        form.setAttribute("hx-boost", "false");
        form.setAttribute("hx-disable", "true");

        // 添加 CSRF Token
        const csrfToken =
          document.querySelector('input[name="csrfmiddlewaretoken"]')?.value ||
          getCookie("csrftoken");

        if (csrfToken) {
          const csrfInput = document.createElement("input");
          csrfInput.type = "hidden";
          csrfInput.name = "csrfmiddlewaretoken";
          csrfInput.value = csrfToken;
          form.appendChild(csrfInput);
        }

        document.body.appendChild(form);
        form.submit();
      }
    },
  );
};

// 7. 通用操作确认助手 (用于 post_detail.html 等)
window.confirmAction = function (url, message, title) {
  window.showConfirmModal(
    title || "确认操作",
    message || "确定要执行此操作吗？",
    () => {
      if (url.startsWith("javascript:")) {
        const code = url.substring(11);
        if (code.includes("history.back()")) {
            history.back();
        } else {
            try { new Function(code)(); } catch(e) { console.error("Script execution failed:", e); }
        }
      } else {
        // 创建并提交 POST 表单
        const form = document.createElement("form");
        form.method = "POST";
        form.action = url;
        form.style.display = "none";
        form.setAttribute("hx-boost", "false");
        form.setAttribute("hx-disable", "true");

        const csrfToken =
          document.querySelector('input[name="csrfmiddlewaretoken"]')?.value ||
          getCookie("csrftoken");
        if (csrfToken) {
          const csrfInput = document.createElement("input");
          csrfInput.type = "hidden";
          csrfInput.name = "csrfmiddlewaretoken";
          csrfInput.value = csrfToken;
          form.appendChild(csrfInput);
        }

        document.body.appendChild(form);
        form.submit();
      }
    },
  );
};

// 9. 头像预览助手
window.previewImage = function(input) {
  if (input.files && input.files[0]) {
    const file = input.files[0];
    if (!file.type.startsWith('image/')) {
      if (window.showToast) window.showToast("请上传图片文件", "error");
      return;
    }

    const reader = new FileReader();
    reader.onload = function(e) {
      // Update simple preview if exists
      const preview = document.getElementById('avatar-preview');
      if (preview) preview.src = e.target.result;

      // Trigger global cropper if requested
      // This allows compatibility with register.html logic which might expect manual cropper handling
      // or just simple preview.
      // If register.html is refactored to use imageCropper Alpine component, this function isn't needed there,
      // but kept for compatibility.
    };
    reader.readAsDataURL(file);
  }
};

// 获取 Cookie 助手函数
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// 页面加载时初始化
document.addEventListener("DOMContentLoaded", () => {
  ensureGlobalModals();
  // initReadingProgress() 由 Rosetta.onLoad 统一调用，此处不再重复调用以避免冲突
});

// 阅读进度条逻辑
window.initReadingProgress = function() {
  const progressBar = document.getElementById("readingProgress");
  if (!progressBar) return; // 当前页面没有进度条

  // 移除旧的监听器 (如果存在) - 简单处理: 重新替换节点或检查标记
  // 由于 scroll 事件是全局的，我们需要确保不会重复绑定过多的 heavy listeners
  // 这里使用一个简单的防抖或标记位
  
  if (window._readingProgressHandler) {
      window.removeEventListener('scroll', window._readingProgressHandler);
  }

  let scrollTimeout;
  window._readingProgressHandler = function() {
    if (!scrollTimeout) {
      scrollTimeout = requestAnimationFrame(function() {
        // 重新获取，因为 DOM 可能已变
        const bar = document.getElementById("readingProgress"); 
        if (bar) {
          let winScroll = document.body.scrollTop || document.documentElement.scrollTop;
          let height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
          let scrolled = (height > 0) ? (winScroll / height) * 100 : 0;
          bar.style.width = scrolled + "%";
        }
        scrollTimeout = null;
      });
    }
  };

  window.addEventListener('scroll', window._readingProgressHandler);
  // 立即触发一次以设置初始状态
  window._readingProgressHandler();
};

// ==========================================================================
// Alpine.js 组件定义
// ==========================================================================

document.addEventListener("alpine:init", () => {
  // 颜色选择器组件
  Alpine.data("colorPicker", ({ initialColor, name }) => ({
    name: name,
    // HSV 状态
    hue: 0, // 0-360
    sat: 0, // 0-100
    val: 100, // 0-100
    alpha: 1, // 0-1

    // 拖拽状态
    isDraggingSat: false,
    isDraggingHue: false,
    isDraggingAlpha: false,

    // 计算属性/衍生值
    hexColor: "#000000",
    hexInput: "#000000",
    rgb: { r: 0, g: 0, b: 0 },

    // 预设色板
    swatches: [
      "#000000", "#ffffff", "#ef4444", "#f97316",
      "#f59e0b", "#84cc16", "#22c55e", "#10b981",
      "#06b6d4", "#0ea5e9", "#3b82f6", "#6366f1",
      "#8b5cf6", "#d946ef", "#ec4899", "#f43f5e",
    ],

    init() {
      this.setColor(initialColor);

      // 全局鼠标事件
      window.addEventListener("mousemove", (e) => this.handleDrag(e));
      window.addEventListener("mouseup", () => this.stopDrag());
      window.addEventListener("touchmove", (e) => this.handleDrag(e));
      window.addEventListener("touchend", () => this.stopDrag());
    },

    get huePercentage() { return (this.hue / 360) * 100; },
    get satX() { return this.sat; },
    get satY() { return 100 - this.val; },

    setColor(color) {
      // 兼容旧版 Tailwind 颜色名称
      const legacyColors = {
        primary: "#4f46e5", secondary: "#ec4899", accent: "#06b6d4",
        neutral: "#3b82f6", info: "#6366f1", success: "#22c55e",
        warning: "#f59e0b", error: "#ef4444",
      };

      if (!color) color = "#000000";
      if (legacyColors[color]) color = legacyColors[color];

      if (color.startsWith("rgb")) {
        const parts = color.match(/[\d.]+/g);
        if (parts && parts.length >= 3) {
          const r = parseInt(parts[0]);
          const g = parseInt(parts[1]);
          const b = parseInt(parts[2]);
          const a = parts.length > 3 ? parseFloat(parts[3]) : 1;
          color = this.rgbaToHex(r, g, b, a);
        }
      }

      if (!color.startsWith("#")) {
        const ctx = document.createElement("canvas").getContext("2d");
        ctx.fillStyle = color;
        if (ctx.fillStyle !== "#000000" || color === "black") {
          color = ctx.fillStyle;
        }
      }

      this.hexInput = color;
      this.updateFromHexInput();
    },

    updateFromHexInput() {
      let hex = this.hexInput;
      if (!hex.startsWith("#")) hex = "#" + hex;

      // 验证 Hex6 或 Hex8
      if (/^#[0-9A-F]{6}([0-9A-F]{2})?$/i.test(hex)) {
        if (hex.length === 9) {
          this.alpha = parseInt(hex.slice(7, 9), 16) / 255;
          this.hexColor = hex.slice(0, 7);
        } else {
          this.alpha = 1;
          this.hexColor = hex;
        }

        this.rgb = this.hexToRgb(this.hexColor);
        const hsv = this.rgbToHsv(this.rgb.r, this.rgb.g, this.rgb.b);
        this.hue = hsv.h;
        this.sat = hsv.s;
        this.val = hsv.v;

        this.updateFinalHex();
      }
    },

    updateColorFromHsv() {
      const rgb = this.hsvToRgb(this.hue, this.sat, this.val);
      this.rgb = rgb;
      this.hexColor = this.rgbToHex(rgb.r, rgb.g, rgb.b);
      this.updateFinalHex();
    },

    updateFinalHex() {
      if (this.alpha < 1) {
        const alphaHex = Math.round(this.alpha * 255).toString(16).padStart(2, "0").toUpperCase();
        this.hexInput = this.hexColor + alphaHex;
      } else {
        this.hexInput = this.hexColor;
      }
    },

    // 拖拽处理
    startDragSat(e) { this.isDraggingSat = true; this.handleSatDrag(e); },
    startDragHue(e) { this.isDraggingHue = true; this.handleHueDrag(e); },
    startDragAlpha(e) { this.isDraggingAlpha = true; this.handleAlphaDrag(e); },
    stopDrag() {
      this.isDraggingSat = false;
      this.isDraggingHue = false;
      this.isDraggingAlpha = false;
    },
    handleDrag(e) {
      if (this.isDraggingSat) this.handleSatDrag(e);
      if (this.isDraggingHue) this.handleHueDrag(e);
      if (this.isDraggingAlpha) this.handleAlphaDrag(e);
    },

    handleSatDrag(e) {
      const rect = this.$refs.satArea.getBoundingClientRect();
      const clientX = e.touches ? e.touches[0].clientX : e.clientX;
      const clientY = e.touches ? e.touches[0].clientY : e.clientY;

      let x = (clientX - rect.left) / rect.width;
      let y = (clientY - rect.top) / rect.height;
      x = Math.max(0, Math.min(1, x));
      y = Math.max(0, Math.min(1, y));

      this.sat = x * 100;
      this.val = 100 - y * 100;
      this.updateColorFromHsv();
    },

    handleHueDrag(e) {
      const rect = this.$refs.hueSlider.getBoundingClientRect();
      const clientX = e.touches ? e.touches[0].clientX : e.clientX;
      let x = (clientX - rect.left) / rect.width;
      x = Math.max(0, Math.min(1, x));
      this.hue = x * 360;
      this.updateColorFromHsv();
    },

    handleAlphaDrag(e) {
      const rect = this.$refs.alphaSlider.getBoundingClientRect();
      const clientX = e.touches ? e.touches[0].clientX : e.clientX;
      let x = (clientX - rect.left) / rect.width;
      x = Math.max(0, Math.min(1, x));
      this.alpha = x;
      this.updateFinalHex();
    },

    // 颜色转换工具
    hexToRgb(hex) {
      const bigint = parseInt(hex.slice(1), 16);
      return { r: (bigint >> 16) & 255, g: (bigint >> 8) & 255, b: bigint & 255 };
    },
    rgbToHex(r, g, b) {
      return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1).toUpperCase();
    },
    rgbaToHex(r, g, b, a) {
      const hex = this.rgbToHex(r, g, b);
      if (a < 1) {
        const alpha = Math.round(a * 255).toString(16).padStart(2, "0").toUpperCase();
        return hex + alpha;
      }
      return hex;
    },
    hsvToRgb(h, s, v) {
      s /= 100; v /= 100;
      const k = (n) => (n + h / 60) % 6;
      const f = (n) => v * (1 - s * Math.max(0, Math.min(k(n), 4 - k(n), 1)));
      return { r: Math.round(f(5) * 255), g: Math.round(f(3) * 255), b: Math.round(f(1) * 255) };
    },
    rgbToHsv(r, g, b) {
      r /= 255; g /= 255; b /= 255;
      const v = Math.max(r, g, b), c = v - Math.min(r, g, b);
      const h = c && (v === r ? (g - b) / c : v === g ? 2 + (b - r) / c : 4 + (r - g) / c);
      return { h: 60 * (h < 0 ? h + 6 : h), s: v && (c / v) * 100, v: v * 100 };
    },
  }));

  // 媒体详情组件 (Media Detail)
  Alpine.data("mediaDetail", (config) => ({
    id: null,
    url: "",
    filename: "",
    title: "",
    altText: "",
    description: "",
    size: "",
    createdAt: "",
    uploader: "",
    isSaving: false,

    init() {
      // 注册全局打开函数
      window.openMediaDetail = (id, url, filename, title, alt, desc, size, created, uploader) => {
        this.id = id;
        this.url = url;
        this.filename = filename;
        this.title = title || "";
        this.altText = alt || "";
        this.description = desc || "";
        this.size = size;
        this.createdAt = created;
        this.uploader = uploader;
        document.getElementById("detail_modal").showModal();
      };
    },

    isImage(name) { return /\.(jpg|jpeg|png|gif|webp|svg|bmp)$/i.test(name); },

    copyUrl() {
      navigator.clipboard.writeText(this.url).then(() => {
        if (window.showToast) window.showToast(config.messages.copySuccess || "链接已复制", "success");
      });
    },

    async saveMetadata() {
      this.isSaving = true;
      try {
        const url = config.updateUrl.replace("0", this.id);
        const response = await fetch(url, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": config.csrfToken,
            "X-Requested-With": "XMLHttpRequest",
          },
          body: JSON.stringify({
            title: this.title,
            alt_text: this.altText,
            description: this.description,
          }),
        });

        if (response.ok) {
          if (window.showToast) window.showToast(config.messages.saveSuccess || "保存成功", "success");
        } else {
          throw new Error("Failed to update");
        }
      } catch (e) {
        if (window.showToast) window.showToast(config.messages.saveError || "保存失败", "error");
        console.error(e);
      } finally {
        this.isSaving = false;
      }
    },

    async deleteMedia() {
      if (!confirm(config.messages.deleteConfirm || "确定要删除吗？")) return;

      try {
        const url = config.deleteUrl.replace("0", this.id);
        const response = await fetch(url, {
          method: "POST",
          headers: {
            "X-CSRFToken": config.csrfToken,
            "X-Requested-With": "XMLHttpRequest",
          },
        });

        if (response.ok) {
          if (window.showToast) window.showToast(config.messages.deleteSuccess || "删除成功", "success");
          document.getElementById("detail_modal").close();
          window.location.reload();
        } else {
          throw new Error("Failed to delete");
        }
      } catch (e) {
        if (window.showToast) window.showToast(config.messages.deleteError || "删除失败", "error");
        console.error(e);
      }
    },
  }));

  // 图片预览组件 (Image Preview)
  Alpine.data("imagePreview", () => ({
    avatarPreview: null,
    coverPreview: null,

    handleFileSelect(event, type) {
      const file = event.target.files[0];
      if (!file) return;

      if (!file.type.startsWith('image/')) {
        // alert('{% trans "请上传图片文件" %}');
        if (window.showToast) window.showToast("请上传图片文件", "error");
        return;
      }

      const reader = new FileReader();
      reader.onload = (e) => {
        if (type === 'avatar') {
          this.avatarPreview = e.target.result;
        } else if (type === 'cover') {
          this.coverPreview = e.target.result;
        }
      };
      reader.readAsDataURL(file);
    }
  }));

  // 多语言同步组件 (Translation Sync)
  Alpine.data("translationSync", () => ({
    languages: ['zh_hans', 'en', 'ja', 'zh_hant'],
    loadingCount: 0,
    get isLoading() { return this.loadingCount > 0; },

    init() {
      this.setupSync('id_title', 'title');
      this.setupSync('id_subtitle', 'subtitle');
      this.setupSync('id_excerpt', 'excerpt');
      
      // 表单提交前的检查
      this.$el.closest('form').addEventListener('submit', () => {
         this.ensureValue('id_title', 'title');
         this.ensureValue('id_content', 'content');
         this.ensureValue('id_subtitle', 'subtitle');
         this.ensureValue('id_excerpt', 'excerpt');
      });
    },

    setupSync(baseId, fieldName) {
      const baseInput = document.getElementById(baseId);
      if (!baseInput) return;

      this.languages.forEach(lang => {
        const inputId = `id_${fieldName}_${lang}`;
        const input = document.getElementById(inputId);
        if (input) {
          // Sync on input
          input.addEventListener('input', function() {
            if (this.value) {
              baseInput.value = this.value;
            } else {
              let foundValue = '';
              const languages = ['zh_hans', 'en', 'ja', 'zh_hant']; // Re-declare to be safe inside listener
              for (const otherLang of languages) {
                const otherInput = document.getElementById(`id_${fieldName}_${otherLang}`);
                if (otherInput && otherInput.value) {
                  foundValue = otherInput.value;
                  break;
                }
              }
              baseInput.value = foundValue;
            }
          });
          
          // Initial sync
          if (input.value && !baseInput.value) {
            baseInput.value = input.value;
          }
        }
      });
    },

    ensureValue(baseId, fieldName) {
        const baseInput = document.getElementById(baseId);
        if (baseInput && !baseInput.value) {
            for (const lang of this.languages) {
                const input = document.getElementById(`id_${fieldName}_${lang}`);
                if (input && input.value) {
                    baseInput.value = input.value;
                    break;
                }
            }
        }
    },

    async translate(sourceId, mapping) {
      // mapping: { 'en': 'target_id_en', 'ja': 'target_id_ja', 'zh-hant': 'target_id_zh_hant' }
      const sourceEl = document.getElementById(sourceId);
      if (!sourceEl || !sourceEl.value.trim()) {
        if (sourceId.includes("title") && (!sourceEl || !sourceEl.value.trim())) {
          if (window.showToast) window.showToast("请先输入中文内容", "warning");
        }
        return;
      }

      this.loadingCount++;
      const text = sourceEl.value;
      const targetLangs = Object.keys(mapping);

      try {
        const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]")?.value || getCookie("csrftoken");
        const response = await fetch("/api/translate/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken,
          },
          body: JSON.stringify({
            text: text,
            target_langs: targetLangs,
          }),
        });

        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

        const data = await response.json();

        if (data.translations) {
          let successCount = 0;
          Object.entries(data.translations).forEach(([lang, translatedText]) => {
              const targetId = mapping[lang];
              const targetEl = document.getElementById(targetId);
              if (targetEl) {
                targetEl.value = translatedText;
                targetEl.dispatchEvent(new Event("input"));
                targetEl.dispatchEvent(new Event("change"));
                successCount++;
              }
          });

          if (window.showToast && successCount > 0)
            window.showToast(`成功翻译 ${successCount} 个语言字段`, "success");
        } else if (data.error) {
          if (window.showToast) window.showToast("翻译失败: " + data.error, "error");
        }
      } catch (error) {
        if (window.showToast) window.showToast("网络错误: " + error.message, "error");
      } finally {
        this.loadingCount--;
      }
    }
  }));

  // 标签输入组件 (Tag Input)
  Alpine.data("tagInput", (config) => ({
    tags: [],
    newTag: '',
    inputId: config.inputId,
    
    init() {
      this.$nextTick(() => {
        const initial = document.getElementById(this.inputId).value;
        if (initial) {
          this.tags = initial.split(',').map(t => t.trim()).filter(t => t);
        }
      });
    },
    
    addTag() {
      const tag = this.newTag.trim();
      if (tag && !this.tags.includes(tag)) {
        this.tags.push(tag);
        this.newTag = '';
        this.updateHiddenInput();
      } else if (this.tags.includes(tag)) {
        this.newTag = '';
        if (window.showToast) window.showToast(config.messages?.exists || '标签已存在', 'warning');
      }
    },
    
    removeTag(index) {
      this.tags.splice(index, 1);
      this.updateHiddenInput();
    },
    
    removeLastTag() {
      if (this.newTag === '' && this.tags.length > 0) {
        this.tags.pop();
        this.updateHiddenInput();
      }
    },
    
    updateHiddenInput() {
      document.getElementById(this.inputId).value = this.tags.join(',');
    }
  }));

  // 导航搜索组件 (Nav Search)
  Alpine.data("navSearchComponent", (config) => ({
    query: '',
    suggestions: [],
    loading: false,
    placeholders: [],
    currentPlaceholderIndex: 0,
    searchUrl: config.searchUrl,
    
    init() {
        this.placeholders = config.placeholders || ["搜索文章...", "搜索标签...", "输入关键词..."];
        setInterval(() => {
            this.currentPlaceholderIndex = (this.currentPlaceholderIndex + 1) % this.placeholders.length;
        }, 3000);
    },

    fetchSuggestions() {
        if (this.query.length < 1) {
            this.suggestions = [];
            return;
        }
        
        this.loading = true;
        // Use URL constructor to safely append params
        const url = new URL(this.searchUrl, window.location.origin);
        url.searchParams.set('type', 'suggest');
        url.searchParams.set('q', this.query);

        fetch(url)
            .then(response => response.json())
            .then(data => {
                this.suggestions = data.results || [];
                this.loading = false;
            })
            .catch(() => {
                this.loading = false;
            });
    },

    search() {
        if (this.query.trim()) {
            const url = new URL(this.searchUrl, window.location.origin);
            url.searchParams.set('q', this.query);
            window.location.href = url.toString();
            return;
        }
        window.location.href = this.searchUrl;
    },

    getIcon(type) {
        const icons = { 'post': 'article', 'tag': 'tag', 'category': 'category', 'user': 'person' };
        return icons[type] || 'search';
    },

    highlightMatch(text) {
        if (!this.query) return text;
        try {
            const regex = new RegExp(`(${this.query})`, 'gi');
            return text.replace(regex, '<span class="text-primary font-bold">$1</span>');
        } catch (e) {
            return text;
        }
    }
  }));

  // 图片裁剪组件 (Image Cropper)
  // 依赖: Cropper.js (需确保已加载)
  Alpine.data("imageCropper", (config = {}) => ({
    previewUrl: config.previewUrl || null,
    cropper: null,
    aspectRatio: config.aspectRatio || 16 / 9,
    originalFile: null,

    init() {
      if (typeof window.injectCropperModal === "function") {
        window.injectCropperModal();
      }
    },

    handleFile(event) {
      const file = event.target.files[0];
      if (!file) return;

      if (!file.type.startsWith("image/")) {
        if (window.showToast) window.showToast("请上传图片文件", "error");
        return;
      }

      this.originalFile = file;
      const reader = new FileReader();
      reader.onload = (e) => {
        this.openCropper(e.target.result, event.target);
      };
      reader.readAsDataURL(file);
      event.target.value = "";
    },

    openCropper(imageUrl, inputElement) {
      if (typeof window.injectCropperModal === "function") {
        window.injectCropperModal();
      }

      const modal = document.getElementById("global_cropper_modal");
      const image = document.getElementById("global_cropper_image");
      
      if (!modal || !image) {
        console.error("Cropper modal elements not found!");
        return;
      }

      image.src = imageUrl;
      image.style.opacity = "0";
      modal.showModal();

      if (window.globalCropperInstance) {
        window.globalCropperInstance.destroy();
      }
      
      // Dynamic import or check global
      // Cropper is now imported at the top, so we can use it directly if bundled, 
      // or check window if loaded via CDN (fallback)
      const CropperClass = Cropper || window.Cropper;
      if (!CropperClass) {
         console.error("Cropper.js library not loaded");
         if(window.showToast) window.showToast("Cropper library missing", "error");
         return;
      }

      window.globalCropperInstance = new CropperClass(image, {
        aspectRatio: this.aspectRatio,
        viewMode: 1,
        dragMode: "move",
        autoCropArea: 0.8,
        restore: false,
        guides: true,
        center: true,
        highlight: false,
        cropBoxMovable: true,
        cropBoxResizable: true,
        toggleDragModeOnDblclick: false,
        ready() {
          image.style.opacity = "1";
        },
      });

      const closeHandler = () => {
        modal.close();
        if (window.globalCropperInstance) {
          window.globalCropperInstance.destroy();
          window.globalCropperInstance = null;
        }
      };

      const saveHandler = () => {
        if (!window.globalCropperInstance) return;
        const canvas = window.globalCropperInstance.getCroppedCanvas({
          maxWidth: 4096, maxHeight: 4096, fillColor: "#fff",
        });

        canvas.toBlob((blob) => {
          if (!blob) return;
          const newFile = new File([blob], this.originalFile.name, {
            type: this.originalFile.type,
            lastModified: new Date().getTime(),
          });

          const dataTransfer = new DataTransfer();
          dataTransfer.items.add(newFile);
          inputElement.files = dataTransfer.files;

          this.previewUrl = URL.createObjectURL(blob);
          closeHandler();
        }, this.originalFile.type);
      };

      // Re-bind buttons (using IDs from modal)
      // Note: Since modal is global, we must be careful not to add duplicate listeners if we don't clone
      // The implementation in image-cropper.js cloned buttons. We should do the same.
      const ids = ['cropper_close_btn', 'cropper_cancel', 'cropper_backdrop', 'cropper_save', 
                   'cropper_rotate_left', 'cropper_rotate_right', 'cropper_reset'];
      const els = {};
      ids.forEach(id => els[id] = document.getElementById(id));
      
      // Clone to remove old listeners
      const replaceEl = (id) => {
          const el = els[id];
          if(el) {
              const newEl = el.cloneNode(true);
              el.parentNode.replaceChild(newEl, el);
              return newEl;
          }
          return null;
      };

      const newClose = replaceEl('cropper_close_btn');
      const newCancel = replaceEl('cropper_cancel');
      const newBackdrop = replaceEl('cropper_backdrop');
      const newSave = replaceEl('cropper_save');
      
      if(newClose) newClose.addEventListener("click", closeHandler);
      if(newCancel) newCancel.addEventListener("click", closeHandler);
      if(newBackdrop) newBackdrop.addEventListener("click", closeHandler);
      if(newSave) newSave.addEventListener("click", saveHandler);

      const rLeft = document.getElementById('cropper_rotate_left');
      if(rLeft) rLeft.onclick = () => window.globalCropperInstance?.rotate(-90);
      
      const rRight = document.getElementById('cropper_rotate_right');
      if(rRight) rRight.onclick = () => window.globalCropperInstance?.rotate(90);
      
      const rReset = document.getElementById('cropper_reset');
      if(rReset) rReset.onclick = () => window.globalCropperInstance?.reset();
    },
  }));
  // 密码显示切换组件
  Alpine.data("passwordToggle", () => ({
    showPassword: false,
    toggle() { this.showPassword = !this.showPassword; }
  }));
});

// Inject Cropper Modal
window.injectCropperModal = function () {
  if (document.getElementById("global_cropper_modal")) return;
  if (!document.body) return;

  const modalHtml = `
    <dialog id="global_cropper_modal" class="modal" style="z-index: 99999;">
        <div class="modal-box w-11/12 max-w-5xl h-[80vh] flex flex-col p-0 bg-base-100 rounded-xl overflow-hidden shadow-2xl">
            <div class="flex justify-between items-center p-4 border-b border-base-200 bg-base-100 z-10">
                <h3 class="font-bold text-lg flex items-center gap-2">
                    <span class="material-symbols-outlined text-primary">crop</span>
                    裁剪图片
                </h3>
                <button type="button" class="btn btn-sm btn-circle btn-ghost" id="cropper_close_btn">✕</button>
            </div>
            <div class="flex-1 bg-neutral/90 relative overflow-hidden flex items-center justify-center p-4">
                    <img id="global_cropper_image" class="max-w-full max-h-full block opacity-0 transition-opacity duration-300" src="">
            </div>
            <div class="p-4 border-t border-base-200 flex justify-between items-center bg-base-100 z-10">
                <div class="flex gap-2">
                    <button type="button" class="btn btn-sm btn-square btn-ghost tooltip tooltip-right" data-tip="向左旋转" id="cropper_rotate_left">
                        <span class="material-symbols-outlined">rotate_left</span>
                    </button>
                    <button type="button" class="btn btn-sm btn-square btn-ghost tooltip tooltip-right" data-tip="向右旋转" id="cropper_rotate_right">
                        <span class="material-symbols-outlined">rotate_right</span>
                    </button>
                    <button type="button" class="btn btn-sm btn-square btn-ghost tooltip tooltip-right" data-tip="重置" id="cropper_reset">
                        <span class="material-symbols-outlined">restart_alt</span>
                    </button>
                </div>
                <div class="flex gap-3">
                    <button type="button" class="btn btn-ghost" id="cropper_cancel">取消</button>
                    <button type="button" class="btn btn-primary px-6 gap-2" id="cropper_save">
                        <span class="material-symbols-outlined text-lg">check</span>
                        确定
                    </button>
                </div>
            </div>
        </div>
        <form method="dialog" class="modal-backdrop">
            <button type="button" id="cropper_backdrop">close</button>
        </form>
    </dialog>
    `;
  document.body.insertAdjacentHTML("beforeend", modalHtml);
};

// 10. 全局命令面板 (Command Palette)
window.injectCommandPalette = function() {
    if (document.getElementById("global_command_palette")) return;
    
    const modalHtml = `
    <dialog id="global_command_palette" class="modal">
        <div class="modal-box w-full max-w-2xl p-0 bg-base-100 rounded-xl overflow-hidden shadow-2xl" 
             x-data="commandPalette">
            <div class="relative border-b border-base-200 bg-base-100">
                <span class="material-symbols-outlined absolute left-4 top-3.5 text-base-content/40">search</span>
                <input type="text" 
                       x-model="query"
                       @input.debounce.300ms="performSearch"
                       @keydown.down.prevent="selectNext"
                       @keydown.up.prevent="selectPrev"
                       @keydown.enter.prevent="executeSelected"
                       class="w-full bg-transparent border-none focus:ring-0 h-14 pl-12 pr-4 text-lg text-base-content placeholder:text-base-content/40 focus:outline-none"
                       placeholder="搜索命令、文章或页面..."
                       autofocus>
                <div class="absolute right-3 top-3 flex gap-1">
                    <kbd class="kbd kbd-sm font-mono text-xs">ESC</kbd>
                </div>
            </div>
            <div class="max-h-[60vh] overflow-y-auto p-2 bg-base-100" x-show="groups.length > 0">
                <template x-for="(group, gIndex) in groups" :key="group.name">
                    <div class="mb-2">
                        <div class="px-2 py-1 text-xs font-bold text-base-content/40 uppercase tracking-wider" x-text="group.name"></div>
                        <template x-for="(item, iIndex) in group.items" :key="item.id">
                            <button type="button"
                                    class="w-full text-left px-3 py-2 rounded-lg flex items-center gap-3 transition-colors"
                                    :class="{ 'bg-primary/10 text-primary': isSelected(gIndex, iIndex), 'hover:bg-base-200': !isSelected(gIndex, iIndex) }"
                                    @click="execute(item)"
                                    @mouseenter="selectedIndex = { g: gIndex, i: iIndex }">
                                <span class="material-symbols-outlined text-[20px]" :class="isSelected(gIndex, iIndex) ? 'text-primary' : 'text-base-content/50'" x-text="item.icon"></span>
                                <div class="flex-1">
                                    <div class="font-medium text-sm" x-text="item.title"></div>
                                    <div class="text-xs opacity-60" x-text="item.desc" x-show="item.desc"></div>
                                </div>
                                <span class="text-xs opacity-40" x-text="item.shortcut" x-show="item.shortcut"></span>
                            </button>
                        </template>
                    </div>
                </template>
            </div>
            <div class="p-8 text-center text-base-content/40" x-show="query && groups.length === 0 && !loading">
                <span class="material-symbols-outlined text-4xl mb-2">search_off</span>
                <p>未找到相关结果</p>
            </div>
        </div>
        <form method="dialog" class="modal-backdrop">
            <button>close</button>
        </form>
    </dialog>
    `;
    document.body.insertAdjacentHTML("beforeend", modalHtml);
};

window.openCommandPalette = function(event) {
    if (event) event.preventDefault();
    window.injectCommandPalette();
    const modal = document.getElementById("global_command_palette");
    if (modal) {
        modal.showModal();
        setTimeout(() => {
            const input = modal.querySelector('input');
            if (input) input.focus();
        }, 100);
    }
};

// Global Shortcut for Command Palette (Ctrl+K or Cmd+K)
document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        window.openCommandPalette();
    }
});

// Auto-inject on load
if (typeof window.Rosetta !== 'undefined') {
    window.Rosetta.onLoad(window.injectCropperModal);
    window.Rosetta.onLoad(window.injectCommandPalette);
} else {
    document.addEventListener("DOMContentLoaded", () => {
        window.injectCropperModal();
        window.injectCommandPalette();
    });
    document.addEventListener("htmx:afterSwap", () => {
        window.injectCropperModal();
        window.injectCommandPalette();
    });
}

document.addEventListener("alpine:init", () => {
    Alpine.data("commandPalette", (initialItems) => ({
        query: '',
        loading: false,
        
        // Frontend State
        selectedIndex: { g: 0, i: 0 },
        groups: [],
        defaultGroups: [],
        
        // Admin State
        items: Array.isArray(initialItems) ? initialItems : [],
        activeIndex: 0,
        
        init() {
            // Check for global items if none provided (e.g. from Admin backend)
            if (this.items.length === 0 && window.ROSETTA_COMMANDS && Array.isArray(window.ROSETTA_COMMANDS)) {
                this.items = window.ROSETTA_COMMANDS;
            }

            if (this.items.length > 0) {
                // Admin Mode
                this.setupAdminGroups();
                this.$watch('query', () => this.filterAdminGroups());
            } else {
                // Frontend Mode
                this.setupFrontendGroups();
                this.$watch('query', () => this.selectedIndex = { g: 0, i: 0 });
            }
        },

        setupFrontendGroups() {
            this.defaultGroups = [
                {
                    name: '快速导航',
                    items: [
                        { id: 'home', title: '首页', desc: '返回网站首页', icon: 'home', action: () => window.location.href = '/' },
                        { id: 'dashboard', title: '控制台', desc: '管理后台首页', icon: 'dashboard', action: () => window.location.href = '/administration/' },
                        { id: 'profile', title: '个人资料', desc: '查看我的资料', icon: 'person', action: () => window.location.href = '/users/profile/' },
                    ]
                },
                {
                    name: '操作',
                    items: [
                        { id: 'theme', title: '切换主题', desc: '切换深色/浅色模式', icon: 'dark_mode', action: () => window.toggleTheme && window.toggleTheme() },
                        { id: 'logout', title: '退出登录', desc: '注销当前账号', icon: 'logout', action: () => window.location.href = '/users/logout/' },
                    ]
                }
            ];
            this.groups = this.defaultGroups;
        },

        setupAdminGroups() {
            // Group by 'group' property
            const groups = {};
            this.items.forEach(item => {
                const gName = item.group || '通用';
                if (!groups[gName]) groups[gName] = [];
                groups[gName].push(item);
            });
            
            this.defaultGroups = Object.keys(groups).map(name => ({
                name: name,
                items: groups[name]
            }));
            
            this.groups = this.defaultGroups;
        },

        filterAdminGroups() {
             if (!this.query.trim()) {
                this.groups = this.defaultGroups;
                return;
            }
            
            const q = this.query.toLowerCase();
            const isPinyin = typeof window.PinyinMatch !== 'undefined';
            
            this.groups = this.defaultGroups.map(g => ({
                name: g.name,
                items: g.items.filter(i => {
                    const text = `${i.title} ${i.keywords || ""} ${i.group || ""}`;
                    if (isPinyin) return window.PinyinMatch.match(text, this.query);
                    return text.toLowerCase().includes(q);
                })
            })).filter(g => g.items.length > 0);
            
            this.selectedIndex = { g: 0, i: 0 };
        },

        performSearch() {
            if (this.items.length > 0) {
                this.filterAdminGroups();
                return;
            }

            if (!this.query.trim()) {
                this.groups = this.defaultGroups;
                return;
            }
            
            // Pinyin Support for Frontend
            if (window.PinyinMatch) {
                 this.groups = this.defaultGroups.map(g => ({
                    name: g.name,
                    items: g.items.filter(i => {
                        const text = `${i.title} ${i.desc || ""}`;
                        return window.PinyinMatch.match(text, this.query);
                    })
                })).filter(g => g.items.length > 0);
                return;
            }

            const q = this.query.toLowerCase();
            this.groups = this.defaultGroups.map(g => ({
                name: g.name,
                items: g.items.filter(i => i.title.toLowerCase().includes(q) || i.desc.toLowerCase().includes(q))
            })).filter(g => g.items.length > 0);
            
            // Call backend search if needed (optional extension)
            // if (this.query.length > 2) this.fetchRemoteResults(q);
        },

        // Admin Computed Property
        get filteredItems() {
            if (!this.items.length) return [];
            if (!this.query) return this.items;

            // PinyinMatch Support
            if (window.PinyinMatch) {
                return this.items.filter((item) => {
                    const text = `${item.title} ${item.group || ""} ${item.keywords || ""}`;
                    return window.PinyinMatch.match(text, this.query);
                });
            }

            const q = this.query.toLowerCase();
            return this.items.filter(item => 
                item.title.toLowerCase().includes(q) || 
                (item.keywords && item.keywords.toLowerCase().includes(q)) ||
                (item.group && item.group.toLowerCase().includes(q))
            );
        },

        // Admin Methods
        selectItem(index) {
            const item = this.filteredItems[index];
            if (item) window.location.href = item.url;
        },

        // Frontend Methods
        isSelected(gIndex, iIndex) {
            return this.selectedIndex.g === gIndex && this.selectedIndex.i === iIndex;
        },

        execute(item) {
            if (item.action) item.action();
            else if (item.url) window.location.href = item.url;
            
            // Close modal
            const modal = document.getElementById("global_command_palette");
            if (modal) modal.close();
        },

        executeSelected() {
            const group = this.groups[this.selectedIndex.g];
            if (group && group.items[this.selectedIndex.i]) {
                this.execute(group.items[this.selectedIndex.i]);
            }
        },

        selectNext() {
            const group = this.groups[this.selectedIndex.g];
            if (!group) return;
            
            if (this.selectedIndex.i < group.items.length - 1) {
                this.selectedIndex.i++;
            } else if (this.selectedIndex.g < this.groups.length - 1) {
                this.selectedIndex.g++;
                this.selectedIndex.i = 0;
            }
        },

        selectPrev() {
            if (this.selectedIndex.i > 0) {
                this.selectedIndex.i--;
            } else if (this.selectedIndex.g > 0) {
                this.selectedIndex.g--;
                this.selectedIndex.i = this.groups[this.selectedIndex.g].items.length - 1;
            }
        }
    }));
});
