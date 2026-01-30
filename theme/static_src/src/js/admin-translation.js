document.addEventListener('alpine:init', () => {
    Alpine.data('translationForm', () => ({
        loadingCount: 0,
        get isLoading() { return this.loadingCount > 0; },
        activeTab: 'zh-hans',
        
        async translate(sourceId, mapping) {
            // mapping: { 'en': 'target_id_en', 'ja': 'target_id_ja', 'zh-hant': 'target_id_zh_hant' }
            const sourceEl = document.getElementById(sourceId);
            if (!sourceEl || !sourceEl.value.trim()) {
                // Only warn if it's the title field (main field), for others just skip silently or log?
                // But for "One Click Translate All", we probably don't want 4 warnings if only title is filled.
                // However, the current UI has separate translate buttons? No, it's one big button calling translate 3 times.
                // If subtitle is empty, it returns.
                // Let's suppress warning if source is empty but return silently.
                // But wait, the original code showed warning.
                // If I click the big button and subtitle is empty, I don't want a warning.
                // Let's just return if empty.
                if (sourceId.includes('title') && (!sourceEl || !sourceEl.value.trim())) {
                     if (window.showToast) window.showToast('请先输入中文内容', 'warning');
                }
                return;
            }
            
            this.loadingCount++;
            const text = sourceEl.value;
            const targetLangs = Object.keys(mapping);
            
            try {
                // Get CSRF token
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
                
                const response = await fetch('/api/translate/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({
                        text: text,
                        target_langs: targetLangs
                    })
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const data = await response.json();
                
                if (data.translations) {
                    let successCount = 0;
                    Object.entries(data.translations).forEach(([lang, translatedText]) => {
                        const targetId = mapping[lang];
                        const targetEl = document.getElementById(targetId);
                        if (targetEl) {
                            // Only update if empty or if user wants to overwrite (current logic: overwrite)
                            targetEl.value = translatedText;
                            targetEl.dispatchEvent(new Event('input'));
                            targetEl.dispatchEvent(new Event('change'));
                            successCount++;
                        }
                    });
                    
                    if (window.showToast && successCount > 0) window.showToast(`成功翻译 ${successCount} 个语言字段`, 'success');
                } else if (data.error) {
                    console.error('Translation error:', data.error);
                    if (window.showToast) window.showToast('翻译失败: ' + data.error, 'error');
                }
            } catch (error) {
                console.error('Network error:', error);
                if (window.showToast) window.showToast('网络错误: ' + error.message, 'error');
            } finally {
                this.loadingCount--;
            }
        }
    }));
});
