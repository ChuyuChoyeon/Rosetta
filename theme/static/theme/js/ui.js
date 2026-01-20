(function(global) {
    /**
     * 初始化表单提交 loading 状态
     * 
     * 监听所有表单提交事件，将提交按钮设为 loading 状态。
     * 避免用户重复点击提交。
     */
    function initSubmitLoading() {
        document.addEventListener('submit', function(e) {
            const form = e.target;
            const submitBtn = form.querySelector('button[type="submit"]');
            
            // 如果表单有 'no-loading' 类或找不到提交按钮，则跳过
            if (!submitBtn || form.classList.contains('no-loading')) {
                return;
            }

            const originalText = submitBtn.innerHTML;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="loading loading-spinner loading-sm"></span> 处理中...';
            
            // 10秒后自动恢复按钮状态 (防止因网络问题导致的永久 loading)
            setTimeout(() => {
                if (submitBtn.disabled) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalText;
                }
            }, 10000);
        });
    }

    /**
     * 初始化按钮点击波纹效果 (Ripple Effect)
     * 
     * 为 .btn 类添加点击时的激活样式模拟。
     */
    function initRippleEffect() {
        document.addEventListener('mousedown', function(e) {
            const btn = e.target.closest('.btn');
            if (btn) {
                btn.classList.add('btn-active');
                setTimeout(() => btn.classList.remove('btn-active'), 200);
            }
        });
    }

    // --- 批量操作逻辑 (Bulk Actions) ---
    
    /**
     * 全选/取消全选
     * @param {HTMLElement} source - 全选复选框元素
     */
    global.toggleAll = function(source) {
        const checkboxes = document.querySelectorAll('.row-checkbox');
        checkboxes.forEach(cb => {
            cb.checked = source.checked;
        });
        updateBulkToolbar();
    };

    /**
     * 更新批量操作工具栏状态
     * 
     * 根据选中项的数量显示或隐藏工具栏。
     */
    global.updateBulkToolbar = function() {
        const checkboxes = document.querySelectorAll('.row-checkbox:checked');
        const count = checkboxes.length;
        const toolbar = document.getElementById('bulk-actions');
        const selectedCount = document.getElementById('selected-count');
        
        if (selectedCount) selectedCount.innerText = count;
        
        if (toolbar) {
            if (count > 0) {
                toolbar.classList.remove('hidden');
            } else {
                toolbar.classList.add('hidden');
            }
        }
    };

    /**
     * 提交批量操作
     * 
     * 将操作类型 (action) 注入表单并提交。
     * @param {string} action - 操作名称 (如 'delete', 'published')
     */
    global.submitBulkAction = function(action) {
        if (!confirm('确定要执行此操作吗？')) return;
        
        const form = document.getElementById('bulk-form');
        if (!form) return;

        let actionInput = form.querySelector('input[name="action"]');
        if (!actionInput) {
            actionInput = document.createElement('input');
            actionInput.type = 'hidden';
            actionInput.name = 'action';
            form.appendChild(actionInput);
        }
        actionInput.value = action;
        
        form.submit();
    };

    function initUI() {
        initSubmitLoading();
        initRippleEffect();
    }

    // --- 模块导出 ---
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = { initSubmitLoading, initRippleEffect, initUI };
    } else {
        global.UIManager = { initSubmitLoading, initRippleEffect, initUI };
        // 浏览器环境下自动初始化
        initUI();
    }

})(typeof window !== 'undefined' ? window : this);
