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
            const hue1 = Math.floor(rand() * 360);
            const hue2 = (hue1 + 60 + rand() * 120) % 360;
            const hue3 = (hue2 + 40 + rand() * 80) % 360;
            const bg1 = `hsl(${hue1} 70% 18%)`;
            const bg2 = `hsl(${hue2} 70% 12%)`;
            const glow1 = `hsl(${hue3} 90% 55%)`;
            const glow2 = `hsl(${(hue3 + 40) % 360} 95% 65%)`;
            const gridColor = `hsla(${hue1} 60% 60% / 0.18)`;
            const circuitColor = `hsla(${hue2} 80% 70% / 0.55)`;
            const highlight = `hsla(${hue3} 100% 70% / 0.5)`;
            const shardFill = `hsla(${(hue2 + 30) % 360} 80% 60% / 0.18)`;
            const shardStroke = `hsla(${(hue3 + 20) % 360} 90% 70% / 0.45)`;
            const meshStroke = `hsla(${(hue1 + 140) % 360} 80% 70% / 0.35)`;
            const meshFill = `hsla(${(hue2 + 200) % 360} 70% 55% / 0.12)`;
            const scanline = `hsla(${(hue3 + 80) % 360} 90% 70% / 0.08)`;

            const gridSize = 24 + Math.floor(rand() * 22);
            const blur = 110 + Math.floor(rand() * 90);
            const glowX = Math.floor(width * (0.2 + rand() * 0.6));
            const glowY = Math.floor(height * (0.2 + rand() * 0.6));
            const glowR = Math.floor(Math.max(width, height) * (0.35 + rand() * 0.2));
            const styleMode = Math.floor(rand() * 3);

            const buildCircuit = () => {
                const points = [];
                const startX = Math.floor(width * (0.05 + rand() * 0.2));
                const startY = Math.floor(height * (0.2 + rand() * 0.6));
                points.push([startX, startY]);
                const segments = 4 + Math.floor(rand() * 4);
                for (let i = 0; i < segments; i++) {
                    const dir = rand() > 0.5 ? 1 : -1;
                    const len = Math.floor(width * (0.12 + rand() * 0.18));
                    const last = points[points.length - 1];
                    const nextX = Math.max(0, Math.min(width, last[0] + len * dir));
                    const nextY = Math.max(0, Math.min(height, last[1] + (rand() - 0.5) * height * 0.25));
                    points.push([nextX, nextY]);
                }
                const path = points.map((p, index) => `${index === 0 ? 'M' : 'L'}${p[0]},${p[1]}`).join(' ');
                return { path, points };
            };

            const accents = Array.from({ length: 6 }).map(() => {
                const x = Math.floor(rand() * width);
                const y = Math.floor(rand() * height);
                const w = 14 + Math.floor(rand() * 32);
                const h = 6 + Math.floor(rand() * 18);
                const opacity = 0.2 + rand() * 0.4;
                return `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="2" fill="${highlight}" opacity="${opacity}"/>`;
            }).join('');

            const circuitA = buildCircuit();
            const circuitB = buildCircuit();
            const nodeMarkup = (points) => points.slice(1).map((p) => {
                const r = 2 + rand() * 3.2;
                return `<circle cx="${p[0]}" cy="${p[1]}" r="${r}" fill="${highlight}" opacity="0.85"/>`;
            }).join('');

            const shardCount = 6 + Math.floor(rand() * 6);
            const shards = Array.from({ length: shardCount }).map(() => {
                const centerX = width * (0.1 + rand() * 0.8);
                const centerY = height * (0.1 + rand() * 0.8);
                const radius = Math.min(width, height) * (0.12 + rand() * 0.18);
                const sides = 3 + Math.floor(rand() * 3);
                const rotation = rand() * Math.PI * 2;
                const points = Array.from({ length: sides }).map((_, idx) => {
                    const angle = rotation + (idx / sides) * Math.PI * 2;
                    const r = radius * (0.65 + rand() * 0.45);
                    const x = Math.max(0, Math.min(width, centerX + Math.cos(angle) * r));
                    const y = Math.max(0, Math.min(height, centerY + Math.sin(angle) * r));
                    return `${x},${y}`;
                }).join(' ');
                const opacity = 0.1 + rand() * 0.18;
                return `<polygon points="${points}" fill="${shardFill}" stroke="${shardStroke}" stroke-width="1" opacity="${opacity}"/>`;
            }).join('');

            const rings = Array.from({ length: 2 + Math.floor(rand() * 3) }).map(() => {
                const r = Math.min(width, height) * (0.18 + rand() * 0.22);
                const cx = width * (0.2 + rand() * 0.6);
                const cy = height * (0.2 + rand() * 0.6);
                return `<circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="${highlight}" stroke-width="1.4" opacity="0.35"/>`;
            }).join('');

            const meshGrid = () => {
                const cols = 6 + Math.floor(rand() * 4);
                const rows = 4 + Math.floor(rand() * 4);
                const stepX = width / cols;
                const stepY = height / rows;
                const points = [];
                for (let y = 0; y <= rows; y++) {
                    for (let x = 0; x <= cols; x++) {
                        const jitterX = (rand() - 0.5) * stepX * 0.35;
                        const jitterY = (rand() - 0.5) * stepY * 0.35;
                        points.push({
                            x: Math.max(0, Math.min(width, x * stepX + jitterX)),
                            y: Math.max(0, Math.min(height, y * stepY + jitterY))
                        });
                    }
                }
                const polygons = [];
                const lines = [];
                const idx = (x, y) => y * (cols + 1) + x;
                for (let y = 0; y < rows; y++) {
                    for (let x = 0; x < cols; x++) {
                        const p1 = points[idx(x, y)];
                        const p2 = points[idx(x + 1, y)];
                        const p3 = points[idx(x, y + 1)];
                        const p4 = points[idx(x + 1, y + 1)];
                        if (rand() > 0.5) {
                            polygons.push(`${p1.x},${p1.y} ${p2.x},${p2.y} ${p4.x},${p4.y}`);
                            polygons.push(`${p1.x},${p1.y} ${p4.x},${p4.y} ${p3.x},${p3.y}`);
                        } else {
                            polygons.push(`${p1.x},${p1.y} ${p2.x},${p2.y} ${p3.x},${p3.y}`);
                            polygons.push(`${p2.x},${p2.y} ${p4.x},${p4.y} ${p3.x},${p3.y}`);
                        }
                        lines.push(`M${p1.x},${p1.y} L${p2.x},${p2.y} L${p4.x},${p4.y} L${p3.x},${p3.y} Z`);
                    }
                }
                const polyMarkup = polygons.map((pts) => {
                    const opacity = 0.06 + rand() * 0.1;
                    return `<polygon points="${pts}" fill="${meshFill}" opacity="${opacity}"/>`;
                }).join('');
                const lineMarkup = lines.map((path) => `<path d="${path}" fill="none" stroke="${meshStroke}" stroke-width="1" opacity="0.35"/>`).join('');
                return { polyMarkup, lineMarkup };
            };

            const mesh = meshGrid();
            const scanlines = Array.from({ length: 8 + Math.floor(rand() * 6) }).map((_, index) => {
                const y = (index + 1) * (height / (10 + rand() * 6));
                return `<rect x="0" y="${y.toFixed(2)}" width="${width}" height="2" fill="${scanline}" opacity="0.4"/>`;
            }).join('');

            const svg = `
<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" preserveAspectRatio="xMidYMid slice">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="${bg1}"/>
      <stop offset="55%" stop-color="${bg2}"/>
      <stop offset="100%" stop-color="${bg1}"/>
    </linearGradient>
    <radialGradient id="glow" cx="${glowX}" cy="${glowY}" r="${glowR}" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="${glow2}" stop-opacity="0.55"/>
      <stop offset="60%" stop-color="${glow1}" stop-opacity="0.25"/>
      <stop offset="100%" stop-color="${glow1}" stop-opacity="0"/>
    </radialGradient>
    <pattern id="grid" width="${gridSize}" height="${gridSize}" patternUnits="userSpaceOnUse">
      <path d="M ${gridSize} 0 L 0 0 0 ${gridSize}" fill="none" stroke="${gridColor}" stroke-width="1"/>
    </pattern>
    <pattern id="diag" width="${gridSize}" height="${gridSize}" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
      <path d="M 0 ${gridSize / 2} L ${gridSize} ${gridSize / 2}" fill="none" stroke="${gridColor}" stroke-width="1"/>
    </pattern>
    <filter id="blur" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="${blur}"/>
    </filter>
  </defs>
  <rect width="${width}" height="${height}" fill="url(#bg)"/>
  <rect width="${width}" height="${height}" fill="url(#glow)"/>
  <rect width="${width}" height="${height}" fill="url(#grid)" opacity="0.65"/>
  <rect width="${width}" height="${height}" fill="url(#diag)" opacity="0.25"/>
  ${styleMode === 1 ? mesh.polyMarkup : shards}
  ${styleMode === 2 ? rings : mesh.lineMarkup}
  ${styleMode === 2 ? '' : `<path d="${circuitA.path}" fill="none" stroke="${circuitColor}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>`}
  ${styleMode === 2 ? '' : `<path d="${circuitB.path}" fill="none" stroke="${circuitColor}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" opacity="0.5"/>`}
  ${styleMode === 2 ? '' : nodeMarkup(circuitA.points)}
  ${styleMode === 2 ? '' : nodeMarkup(circuitB.points)}
  ${scanlines}
  ${accents}
  <rect width="${width}" height="${height}" fill="none" stroke="${highlight}" stroke-width="2" opacity="0.4"/>
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
