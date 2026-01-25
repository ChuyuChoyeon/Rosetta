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

    global.initGeoPattern = function(el, title) {
        if (!el) return;

        const createSeededRandom = (seedText) => {
            let hash = 2166136261;
            for (let i = 0; i < seedText.length; i++) {
                hash ^= seedText.charCodeAt(i);
                hash += (hash << 1) + (hash << 4) + (hash << 7) + (hash << 8) + (hash << 24);
            }
            let state = hash >>> 0;
            return () => {
                state ^= state << 13;
                state ^= state >>> 17;
                state ^= state << 5;
                return (state >>> 0) / 4294967296;
            };
        };

        const createTechSvg = (seedText, width, height) => {
            const rand = createSeededRandom(seedText);
            const palettes = [
                {
                    bg: '#0b1120',
                    colors: ['#0f172a', '#1e293b', '#334155', '#3b82f6', '#22d3ee'],
                    line: 'rgba(148, 163, 184, 0.2)',
                    accent: '#f59e0b'
                },
                {
                    bg: '#0f172a',
                    colors: ['#111827', '#1f2937', '#312e81', '#7c3aed', '#f472b6'],
                    line: 'rgba(199, 210, 254, 0.18)',
                    accent: '#38bdf8'
                },
                {
                    bg: '#0c101b',
                    colors: ['#0f172a', '#172554', '#1e3a8a', '#0ea5e9', '#38bdf8'],
                    line: 'rgba(125, 211, 252, 0.2)',
                    accent: '#f97316'
                },
                {
                    bg: '#10131f',
                    colors: ['#111827', '#1f2937', '#4b5563', '#06b6d4', '#2dd4bf'],
                    line: 'rgba(148, 163, 184, 0.18)',
                    accent: '#f472b6'
                },
                {
                    bg: '#0c111f',
                    colors: ['#111827', '#1e293b', '#3f3f46', '#6366f1', '#c084fc'],
                    line: 'rgba(165, 180, 252, 0.18)',
                    accent: '#34d399'
                }
            ];
            const palette = palettes[Math.floor(rand() * palettes.length)];
            const cell = Math.max(70, Math.min(width, height) * (0.16 + rand() * 0.12));
            const cols = Math.ceil(width / cell) + 1;
            const rows = Math.ceil(height / cell) + 1;
            const points = [];
            for (let y = 0; y <= rows; y++) {
                for (let x = 0; x <= cols; x++) {
                    const jitterX = (rand() - 0.5) * cell * 0.7;
                    const jitterY = (rand() - 0.5) * cell * 0.7;
                    points.push({
                        x: Math.max(0, Math.min(width, x * cell + jitterX)),
                        y: Math.max(0, Math.min(height, y * cell + jitterY))
                    });
                }
            }

            const idx = (x, y) => y * (cols + 1) + x;
            const triangles = [];
            for (let y = 0; y < rows; y++) {
                for (let x = 0; x < cols; x++) {
                    const p1 = points[idx(x, y)];
                    const p2 = points[idx(x + 1, y)];
                    const p3 = points[idx(x, y + 1)];
                    const p4 = points[idx(x + 1, y + 1)];
                    if (rand() > 0.5) {
                        triangles.push([p1, p2, p4]);
                        triangles.push([p1, p4, p3]);
                    } else {
                        triangles.push([p1, p2, p3]);
                        triangles.push([p2, p4, p3]);
                    }
                }
            }

            const clamp = (v, min, max) => Math.max(min, Math.min(max, v));
            const triangleMarkup = triangles.map((tri) => {
                const cx = (tri[0].x + tri[1].x + tri[2].x) / 3;
                const cy = (tri[0].y + tri[1].y + tri[2].y) / 3;
                const t = clamp((cx / width) * 0.5 + (cy / height) * 0.5 + (rand() - 0.5) * 0.12, 0, 0.999);
                const baseIndex = Math.floor(t * palette.colors.length);
                const shift = rand() > 0.84 ? 1 : 0;
                const fill = palette.colors[(baseIndex + shift) % palette.colors.length];
                const opacity = 0.78 + rand() * 0.18;
                const pointsAttr = `${tri[0].x},${tri[0].y} ${tri[1].x},${tri[1].y} ${tri[2].x},${tri[2].y}`;
                return `<polygon points="${pointsAttr}" fill="${fill}" opacity="${opacity}" stroke="${palette.line}" stroke-width="0.9"/>`;
            }).join('');

            const bandCount = 3 + Math.floor(rand() * 3);
            const bands = Array.from({ length: bandCount }).map((_, i) => {
                const bandHeight = height * (0.18 + rand() * 0.12);
                const y = (i / bandCount) * height + (rand() - 0.5) * bandHeight * 0.4;
                const skew = width * (0.08 + rand() * 0.08);
                const fill = rand() > 0.6 ? palette.accent : palette.colors[palette.colors.length - 1];
                const opacity = 0.14 + rand() * 0.12;
                const pointsAttr = `${-skew},${y} ${width - skew},${y} ${width + skew},${y + bandHeight} ${skew},${y + bandHeight}`;
                return `<polygon points="${pointsAttr}" fill="${fill}" opacity="${opacity}"/>`;
            }).join('');

            const shardCount = 4 + Math.floor(rand() * 4);
            const shards = Array.from({ length: shardCount }).map(() => {
                const centerX = width * (0.1 + rand() * 0.8);
                const centerY = height * (0.1 + rand() * 0.8);
                const radius = Math.min(width, height) * (0.08 + rand() * 0.12);
                const sides = 4 + Math.floor(rand() * 3);
                const rotation = rand() * Math.PI * 2;
                const pointsAttr = Array.from({ length: sides }).map((_, idx2) => {
                    const angle = rotation + (idx2 / sides) * Math.PI * 2;
                    const r = radius * (0.7 + rand() * 0.4);
                    const x = Math.max(0, Math.min(width, centerX + Math.cos(angle) * r));
                    const y = Math.max(0, Math.min(height, centerY + Math.sin(angle) * r));
                    return `${x},${y}`;
                }).join(' ');
                const opacity = 0.12 + rand() * 0.16;
                return `<polygon points="${pointsAttr}" fill="none" stroke="${palette.accent}" stroke-width="1.2" opacity="${opacity}"/>`;
            }).join('');

            const lineCount = 2 + Math.floor(rand() * 3);
            const polylines = Array.from({ length: lineCount }).map(() => {
                const pointsAttr = Array.from({ length: 4 + Math.floor(rand() * 3) }).map((_, idx2) => {
                    const x = (idx2 / 4) * width + (rand() - 0.5) * width * 0.08;
                    const y = rand() * height;
                    return `${x.toFixed(2)},${y.toFixed(2)}`;
                }).join(' ');
                return `<polyline points="${pointsAttr}" fill="none" stroke="${palette.line}" stroke-width="1.1" opacity="0.45"/>`;
            }).join('');

            const nodeCount = 6 + Math.floor(rand() * 6);
            const nodes = Array.from({ length: nodeCount }).map(() => {
                const x = Math.floor(rand() * width);
                const y = Math.floor(rand() * height);
                const r = 2 + rand() * 3.5;
                return `<circle cx="${x}" cy="${y}" r="${r}" fill="${palette.accent}" opacity="0.7"/>`;
            }).join('');

            const svg = `
<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" preserveAspectRatio="xMidYMid slice">
  <rect width="${width}" height="${height}" fill="${palette.bg}"/>
  ${triangleMarkup}
  ${bands}
  ${shards}
  ${polylines}
  ${nodes}
  <rect width="${width}" height="${height}" fill="none" stroke="${palette.line}" stroke-width="1" opacity="0.22"/>
</svg>`;
            return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`;
        };

        const resolveSeed = () => {
            let seed = title;
            if (!seed) {
                seed = el.dataset.seed || 'Rosetta';
            }
            return seed;
        };

        const rect = el.getBoundingClientRect();
        const width = Math.max(320, Math.round(rect.width || 800));
        const height = Math.max(200, Math.round(rect.height || 500));
        const seed = resolveSeed();

        try {
            const dataUrl = createTechSvg(seed, width, height);
            el.style.backgroundImage = `url("${dataUrl}")`;
            el.style.backgroundSize = 'cover';
            el.style.backgroundPosition = 'center';
        } catch (e) {
            if (window.GeoPattern) {
                try {
                    const pattern = GeoPattern.generate(seed);
                    el.style.backgroundImage = pattern.toDataUrl();
                } catch (err) {
                    console.error('GeoPattern generation failed:', err);
                }
            } else {
                console.error('Tech placeholder generation failed:', e);
            }
        }
    };

    /**
     * 批量初始化页面上的 Pattern Placeholders
     * 用于非 Alpine.js 环境或 HTMX 动态加载的内容
     */
    global.initPatterns = function() {
        document.querySelectorAll('.pattern-placeholder').forEach(function(el) {
            if (el.style.backgroundImage) return;
            global.initGeoPattern(el);
        });
    };

    function initUI() {
        initSubmitLoading();
        initRippleEffect();
        
        // Auto-init patterns on load
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', global.initPatterns);
        } else {
            global.initPatterns();
        }
        // Auto-init on HTMX swap
        document.addEventListener('htmx:afterSwap', global.initPatterns);
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
