(function(global) {
    function initSubmitLoading() {
        document.addEventListener('submit', function(e) {
            const form = e.target;
            const submitBtn = form.querySelector('button[type="submit"]');
            
            // Skip if form has 'no-loading' class or button not found
            if (!submitBtn || form.classList.contains('no-loading')) {
                return;
            }

            const originalText = submitBtn.innerHTML;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="loading loading-spinner loading-sm"></span> 处理中...';
            
            // Restore button after 10s (safety timeout)
            setTimeout(() => {
                if (submitBtn.disabled) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalText;
                }
            }, 10000);
        });
    }

    function initRippleEffect() {
        document.addEventListener('mousedown', function(e) {
            const btn = e.target.closest('.btn');
            if (btn) {
                btn.classList.add('btn-active');
                setTimeout(() => btn.classList.remove('btn-active'), 200);
            }
        });
    }

    // Bulk Actions
    global.toggleAll = function(source) {
        const checkboxes = document.querySelectorAll('.row-checkbox');
        checkboxes.forEach(cb => {
            cb.checked = source.checked;
        });
        updateBulkToolbar();
    };

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

    // Export for Node.js/Jest or Browser
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = { initSubmitLoading, initRippleEffect, initUI };
    } else {
        global.UIManager = { initSubmitLoading, initRippleEffect, initUI };
        // Auto-init in browser
        initUI();
    }

})(typeof window !== 'undefined' ? window : this);
