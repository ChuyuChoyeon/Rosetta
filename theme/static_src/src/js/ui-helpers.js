import Cropper from "cropperjs";
import PinyinMatch from "pinyin-match";

// Expose PinyinMatch globally if needed, or just use it in this module
window.PinyinMatch = PinyinMatch;

/**
 * 全局 UI 辅助函数 (Global UI Helper Functions)
 * 标准化前端和管理后台的模态框、通知 (Toast) 和 HTMX 确认操作
 */

console.log("[UI Helpers] Loading v5.0.0...");

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
window.getCookie = getCookie;

// 1. 确保全局模态框存在于 DOM 中
window.ensureGlobalModals = function () {
  console.log("[UI Helpers] Ensuring global modals exist...");
  const hasConfirm = document.getElementById("global_confirm_modal");
  const hasAlert = document.getElementById("global_alert_modal");

  if (!hasConfirm || !hasAlert) {
    console.log("[UI Helpers] Injecting modals into DOM");
    const wrapper = document.createElement("div");
    wrapper.innerHTML = `
        <dialog id="global_confirm_modal" class="modal" style="z-index: 9999;">
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
        <dialog id="global_alert_modal" class="modal" style="z-index: 9999;">
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

// HTMX 内容替换后重新注入模态框
document.addEventListener("htmx:afterSwap", () => {
  if (window.ensureGlobalModals) window.ensureGlobalModals();
});

// 2. 显示确认模态框
window.showConfirmModal = function (title, message, onConfirm) {
  console.log("[UI Helpers] showConfirmModal called", { title, message });
  ensureGlobalModals();
  const modal = document.getElementById("global_confirm_modal");
  const titleEl = document.getElementById("global_confirm_title");
  const msgEl = document.getElementById("global_confirm_message");
  const btn = document.getElementById("global_confirm_btn");

  if (!modal || !titleEl || !msgEl || !btn) {
    console.error("[UI Helpers] Modal elements missing!");
    return;
  }

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
    console.log("[UI Helpers] Confirm button clicked");
    if (typeof onConfirm === "function") {
      onConfirm();
    } else if (typeof onConfirm === "string") {
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
  console.log("[UI Helpers] showToast", { message, type });
  window.dispatchEvent(
    new CustomEvent("show-toast", {
      detail: { message, type },
    })
  );
};

// 5. HTMX 确认助手
window.confirmHtmx = function (element, message) {
  console.log("[UI Helpers] confirmHtmx called");
  if (window.event) {
    window.event.preventDefault();
    window.event.stopPropagation();
  }
  
  // 兼容直接传入事件对象
  let targetElement = element;
  if (element instanceof Event) {
      targetElement = element.target.closest('[hx-trigger*="confirmed"]');
  }

  showConfirmModal("确认操作", message || "确定要执行此操作吗？", () => {
    if (window.htmx) {
      console.log("[UI Helpers] Triggering HTMX 'confirmed' event");
      htmx.trigger(targetElement, "confirmed");
    } else {
      console.error("[UI Helpers] HTMX not found!");
    }
  });
};

// 6. 传统删除助手
window.confirmDelete = function (url, message) {
  console.log("[UI Helpers] confirmDelete called", { url });
  window.showConfirmModal(
    "确认删除",
    message || "确定要删除此项目吗？此操作无法撤销。",
    () => {
      if (url.startsWith("javascript:")) {
        const code = url.substring(11);
        if (code.includes("history.back()")) {
            history.back();
        } else {
            try { new Function(code)(); } catch(e) { console.error("Script execution failed:", e); }
        }
      } else {
        console.log("[UI Helpers] Submitting form to", url);
        const form = document.createElement("form");
        form.method = "POST";
        form.action = url;
        form.style.display = "none";
        
        // 禁用 HTMX 处理
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

// 7. 通用操作确认助手
window.confirmAction = function (url, message, title) {
    window.confirmDelete(url, message); // 复用逻辑
};

// 8. 批量操作提交助手
window.submitBulkAction = function(action) {
  console.log("[UI Helpers] submitBulkAction called", { action });
  const form = document.getElementById('bulk-form');
  if (!form) {
      console.error("[UI Helpers] Bulk form #bulk-form not found!");
      if (window.showToast) window.showToast("页面错误：找不到批量操作表单", "error");
      return;
  }

  // 获取选中的 ID
  let checkboxes = form.querySelectorAll('input[name="selected_ids"]:checked');
  if (checkboxes.length === 0) {
      checkboxes = form.querySelectorAll('input[name="ids"]:checked');
  }

  console.log("[UI Helpers] Selected items:", checkboxes.length);

  if (checkboxes.length === 0) {
    if (window.showToast) window.showToast("请先选择要操作的项目", "warning");
    else alert("请先选择要操作的项目");
    return;
  }

  let message = "确定要执行此批量操作吗？";
  if (action === 'delete') {
    message = `确定要删除选中的 ${checkboxes.length} 个项目吗？此操作无法撤销。`;
  } else if (action === 'active' || action === 'published') {
    message = `确定要启用/发布选中的 ${checkboxes.length} 个项目吗？`;
  } else if (action === 'inactive' || action === 'draft') {
    message = `确定要禁用/撤稿选中的 ${checkboxes.length} 个项目吗？`;
  }

  window.showConfirmModal("批量操作确认", message, () => {
    console.log("[UI Helpers] Confirmed bulk action, submitting...");
    let actionInput = form.querySelector('input[name="action"]');
    if (!actionInput) {
      actionInput = document.createElement('input');
      actionInput.type = 'hidden';
      actionInput.name = 'action';
      form.appendChild(actionInput);
    }
    actionInput.value = action;
    
    // 禁用 HTMX 防止干扰
    form.setAttribute('hx-disable', 'true');
    form.submit();
  });
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
      const preview = document.getElementById('avatar-preview');
      if (preview) preview.src = e.target.result;
    };
    reader.readAsDataURL(file);
  }
};

// 页面加载时初始化
document.addEventListener("DOMContentLoaded", () => {
  console.log("[UI Helpers] DOMContentLoaded");
  ensureGlobalModals();
});


// ==========================================================================
// Alpine.js 组件定义
// ==========================================================================

document.addEventListener("alpine:init", () => {
  console.log("[UI Helpers] alpine:init");

  // 翻译表单组件
  Alpine.data("translationForm", () => ({
    activeTab: 'zh-hans', 
    loadingCount: 0,
    get isLoading() { return this.loadingCount > 0; },

    async translate(sourceId, mapping) {
      console.log("[Alpine] translate called", sourceId);
      const sourceEl = document.getElementById(sourceId);
      if (!sourceEl || !sourceEl.value.trim()) {
        if (window.showToast) window.showToast("请先输入中文内容", "warning");
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
        console.error("[Alpine] Translation error:", error);
        if (window.showToast) window.showToast("网络错误: " + error.message, "error");
      } finally {
        this.loadingCount--;
      }
    }
  }));

  // 分类快速创建模态框
  Alpine.data("categoryModal", () => ({
    activeTab: 'zh-hans',
    isTranslating: false,
    form: {
        name_zh_hans: '', name_en: '', name_ja: '', name_zh_hant: '',
        description_zh_hans: '', description_en: '', description_ja: '', description_zh_hant: '',
        parent: '', slug: '', icon: '', color: ''
    },

    async translateAll() {
        console.log("[Alpine] categoryModal.translateAll");
        if (!this.form.name_zh_hans) {
             if (window.showToast) window.showToast("请先输入中文名称", "warning");
             return;
        }
        this.isTranslating = true;
        
        try {
            const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]")?.value || getCookie("csrftoken");
            
            // 1. 翻译名称
            const nameRes = await fetch("/api/translate/", {
                method: "POST",
                headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
                body: JSON.stringify({
                    text: this.form.name_zh_hans,
                    target_langs: ['en', 'ja', 'zh-hant']
                })
            });
            const nameData = await nameRes.json();
            if (nameData.translations) {
                this.form.name_en = nameData.translations['en'] || '';
                this.form.name_ja = nameData.translations['ja'] || '';
                this.form.name_zh_hant = nameData.translations['zh-hant'] || '';
            }

            // 2. 翻译描述 (如果有)
            if (this.form.description_zh_hans) {
                const descRes = await fetch("/api/translate/", {
                    method: "POST",
                    headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
                    body: JSON.stringify({
                        text: this.form.description_zh_hans,
                        target_langs: ['en', 'ja', 'zh-hant']
                    })
                });
                const descData = await descRes.json();
                if (descData.translations) {
                    this.form.description_en = descData.translations['en'] || '';
                    this.form.description_ja = descData.translations['ja'] || '';
                    this.form.description_zh_hant = descData.translations['zh-hant'] || '';
                }
            }
            
            if (window.showToast) window.showToast("翻译完成", "success");
            
        } catch (e) {
            console.error(e);
            if (window.showToast) window.showToast("翻译出错: " + e.message, "error");
        } finally {
            this.isTranslating = false;
        }
    },

    async submitForm() {
        console.log("[Alpine] categoryModal.submitForm");
        const formEl = document.getElementById('category_quick_form');
        const formData = new FormData(formEl);
        
        try {
            const response = await fetch("/administration/categories/create/ajax/", {
                method: "POST",
                body: formData,
                headers: {
                    "X-CSRFToken": getCookie("csrftoken"),
                    "X-Requested-With": "XMLHttpRequest"
                }
            });
            
            const data = await response.json();
            
            if (response.ok && data.status === 'success') {
                if (window.showToast) window.showToast("分类创建成功", "success");
                document.getElementById('category_modal').close();
                setTimeout(() => window.location.reload(), 500);
            } else {
                let errorMsg = "创建失败";
                if (data.errors) {
                    errorMsg += ": " + Object.values(data.errors).flat().join(", ");
                }
                if (window.showToast) window.showToast(errorMsg, "error");
            }
        } catch (e) {
            console.error(e);
            if (window.showToast) window.showToast("网络错误", "error");
        }
    }
  }));

  // 标签输入组件
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

  // 导航搜索组件
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

  // 图片裁剪组件
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
      console.log("[Alpine] imageCropper.handleFile");
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

      // Re-bind buttons
      const ids = ['cropper_close_btn', 'cropper_cancel', 'cropper_backdrop', 'cropper_save', 
                   'cropper_rotate_left', 'cropper_rotate_right', 'cropper_reset'];
      const els = {};
      ids.forEach(id => els[id] = document.getElementById(id));
      
      const replaceEl = (id) => {
          const el = els[id];
          if(el) {
              const newEl = el.cloneNode(true);
              el.parentNode.replaceChild(newEl, el);
              return newEl;
          }
          return null;
      };
      
      const closeBtn = replaceEl('cropper_close_btn');
      const cancelBtn = replaceEl('cropper_cancel');
      const backdrop = replaceEl('cropper_backdrop');
      const saveBtn = replaceEl('cropper_save');
      
      if(closeBtn) closeBtn.onclick = closeHandler;
      if(cancelBtn) cancelBtn.onclick = closeHandler;
      if(backdrop) backdrop.onclick = closeHandler;
      if(saveBtn) saveBtn.onclick = saveHandler;
      
      const rotateLeft = replaceEl('cropper_rotate_left');
      const rotateRight = replaceEl('cropper_rotate_right');
      const resetBtn = replaceEl('cropper_reset');
      
      if(rotateLeft) rotateLeft.onclick = () => window.globalCropperInstance?.rotate(-90);
      if(rotateRight) rotateRight.onclick = () => window.globalCropperInstance?.rotate(90);
      if(resetBtn) resetBtn.onclick = () => window.globalCropperInstance?.reset();
    }
  }));

  // 媒体详情组件
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
    }
  }));

  // 多语言同步组件
  Alpine.data("translationSync", () => ({
    languages: ['zh_hans', 'en', 'ja', 'zh_hant'],
    loadingCount: 0,
    get isLoading() { return this.loadingCount > 0; },

    init() {
      this.setupSync('id_title', 'title');
      this.setupSync('id_subtitle', 'subtitle');
      this.setupSync('id_excerpt', 'excerpt');
      
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
          input.addEventListener('input', function() {
            if (this.value) {
              baseInput.value = this.value;
            } else {
              let foundValue = '';
              const languages = ['zh_hans', 'en', 'ja', 'zh_hant'];
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
      // Reuse the global translation logic if possible, or duplicate here
      // For simplicity in this refactor, we'll use the same logic as translationForm
      const sourceEl = document.getElementById(sourceId);
      if (!sourceEl || !sourceEl.value.trim()) {
        if (window.showToast) window.showToast("请先输入中文内容", "warning");
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
          if (window.showToast && successCount > 0) window.showToast("翻译成功", "success");
        }
      } catch (error) {
        if (window.showToast) window.showToast("翻译错误", "error");
      } finally {
        this.loadingCount--;
      }
    }
  }));

  // 颜色选择器组件 (保留原有逻辑)
  Alpine.data("colorPicker", ({ initialColor, name }) => ({
    name: name,
    hue: 0, sat: 0, val: 100, alpha: 1,
    isDraggingSat: false, isDraggingHue: false, isDraggingAlpha: false,
    hexColor: "#000000", hexInput: "#000000", rgb: { r: 0, g: 0, b: 0 },
    swatches: [
      "#000000", "#ffffff", "#ef4444", "#f97316",
      "#f59e0b", "#84cc16", "#22c55e", "#10b981",
      "#06b6d4", "#0ea5e9", "#3b82f6", "#6366f1",
      "#8b5cf6", "#d946ef", "#ec4899", "#f43f5e",
    ],

    init() {
      this.setColor(initialColor);
      window.addEventListener("mousemove", (e) => this.handleDrag(e));
      window.addEventListener("mouseup", () => this.stopDrag());
      window.addEventListener("touchmove", (e) => this.handleDrag(e));
      window.addEventListener("touchend", () => this.stopDrag());
    },

    get huePercentage() { return (this.hue / 360) * 100; },
    get satX() { return this.sat; },
    get satY() { return 100 - this.val; },

    setColor(color) {
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

    startDragSat(e) { this.isDraggingSat = true; this.handleSatDrag(e); },
    startDragHue(e) { this.isDraggingHue = true; this.handleHueDrag(e); },
    startDragAlpha(e) { this.isDraggingAlpha = true; this.handleAlphaDrag(e); },
    stopDrag() { this.isDraggingSat = false; this.isDraggingHue = false; this.isDraggingAlpha = false; },
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
});
