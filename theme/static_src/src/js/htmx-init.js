// Global constants
window.ICONS_LIST = [
    'folder', 'article', 'tag', 'star', 'person', 'home', 'settings', 'search', 'favorite', 'share',
    'lock', 'visibility', 'edit', 'delete', 'add', 'check', 'close', 'menu', 'more_vert', 'arrow_forward',
    'image', 'movie', 'music_note', 'book', 'bookmark', 'label', 'flag', 'notifications', 'chat', 'mail',
    'code', 'terminal', 'bug_report', 'developer_mode', 'lightbulb', 'bolt', 'rocket', 'science', 'school',
    'work', 'business', 'shopping_cart', 'credit_card', 'account_balance', 'schedule', 'today', 'event', 'history',
    'dashboard', 'grid_view', 'list', 'sort', 'filter_list', 'tune', 'language', 'translate', 'public',
    'description', 'folder_open', 'link', 'cloud', 'download', 'upload', 'error', 'warning', 'info', 'help',
    'add_circle', 'remove_circle', 'check_circle', 'cancel', 'arrow_back', 'arrow_upward', 'arrow_downward',
    'chevron_left', 'chevron_right', 'expand_more', 'expand_less', 'refresh', 'sync', 'loop', 'undo', 'redo',
    'content_copy', 'content_paste', 'content_cut', 'save', 'print', 'send', 'archive', 'unarchive', 'reply',
    'reply_all', 'forward', 'report', 'thumb_up', 'thumb_down', 'comment', 'forum', 'question_answer',
    'group', 'groups', 'person_add', 'person_remove', 'manage_accounts', 'account_circle', 'face', 'mood',
    'mood_bad', 'sentiment_satisfied', 'sentiment_dissatisfied', 'star_border', 'star_half', 'toggle_on',
    'toggle_off', 'check_box', 'check_box_outline_blank', 'radio_button_checked', 'radio_button_unchecked'
];

// Global initializer for HTMX navigations and initial page load
function initDashboardCharts() {
    if (typeof ApexCharts === 'undefined') return;

    // Trend Chart
    const trendChartEl = document.getElementById('trendChart');
    if (trendChartEl && !trendChartEl.chart) {
        try {
            const dates = JSON.parse(trendChartEl.dataset.trendDates);
            const counts = JSON.parse(trendChartEl.dataset.trendCounts);
            const userCounts = JSON.parse(trendChartEl.dataset.userTrendCounts);

            const options = {
                series: [{
                    name: '评论',
                    data: counts
                }, {
                    name: '新用户',
                    data: userCounts
                }],
                chart: {
                    type: 'area',
                    height: 320,
                    toolbar: { show: false },
                    fontFamily: 'inherit',
                    background: 'transparent',
                    animations: { enabled: true }
                },
                colors: ['#4f46e5', '#9333ea'],
                dataLabels: { enabled: false },
                stroke: { curve: 'smooth', width: 2 },
                fill: {
                    type: 'gradient',
                    gradient: {
                        shadeIntensity: 1,
                        opacityFrom: 0.4,
                        opacityTo: 0.05,
                        stops: [0, 90, 100]
                    }
                },
                xaxis: {
                    categories: dates,
                    axisBorder: { show: false },
                    axisTicks: { show: false },
                    labels: { style: { colors: 'var(--fallback-bc,oklch(var(--bc)/0.6))' } }
                },
                yaxis: { show: false },
                grid: {
                    borderColor: 'var(--fallback-bc,oklch(var(--bc)/0.05))',
                    strokeDashArray: 4,
                    yaxis: { lines: { show: true } }
                },
                theme: { mode: document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light' }
            };

            const chart = new ApexCharts(trendChartEl, options);
            chart.render();
            trendChartEl.chart = chart;
        } catch (e) {
            console.error('Error initializing trend chart:', e);
        }
    }

    // Comment Donut
    const commentDonutEl = document.getElementById('commentDonut');
    if (commentDonutEl && !commentDonutEl.chart) {
        try {
            const data = JSON.parse(commentDonutEl.dataset.commentStatus);
            const options = {
                series: data,
                labels: ['已发布', '待审核'],
                chart: {
                    type: 'donut',
                    height: 240,
                    fontFamily: 'inherit',
                    background: 'transparent'
                },
                colors: ['#22c55e', '#eab308'],
                plotOptions: {
                    pie: {
                        donut: {
                            size: '70%',
                            labels: {
                                show: true,
                                total: {
                                    show: true,
                                    label: '总计',
                                    color: 'var(--fallback-bc,oklch(var(--bc)/1))',
                                    formatter: function (w) {
                                        return w.globals.seriesTotals.reduce((a, b) => a + b, 0)
                                    }
                                }
                            }
                        }
                    }
                },
                dataLabels: { enabled: false },
                legend: { show: false },
                stroke: { show: false },
                theme: { mode: document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light' }
            };

            const chart = new ApexCharts(commentDonutEl, options);
            chart.render();
            commentDonutEl.chart = chart;
        } catch (e) {
            console.error('Error initializing comment donut:', e);
        }
    }
    
    // Category Chart
    const categoryChartEl = document.getElementById('categoryChart');
    if (categoryChartEl && !categoryChartEl.chart) {
        try {
            const labels = JSON.parse(categoryChartEl.dataset.categoryLabels);
            const data = JSON.parse(categoryChartEl.dataset.categoryData);
            
            const options = {
                series: data,
                labels: labels,
                chart: {
                    type: 'polarArea',
                    height: 300,
                    fontFamily: 'inherit',
                    background: 'transparent',
                    toolbar: { show: false }
                },
                stroke: { colors: ['var(--fallback-b1,oklch(var(--b1)/1))'] },
                fill: { opacity: 0.8 },
                legend: { 
                    position: 'bottom',
                    labels: { colors: 'var(--fallback-bc,oklch(var(--bc)/1))' }
                },
                theme: { 
                    mode: document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light',
                    monochrome: {
                        enabled: true,
                        color: '#4f46e5',
                        shadeTo: 'light',
                        shadeIntensity: 0.65
                    }
                }
            };
            
            const chart = new ApexCharts(categoryChartEl, options);
            chart.render();
            categoryChartEl.chart = chart;
        } catch(e) {
            console.error('Error initializing category chart:', e);
        }
    }

    // Tag Chart
    const tagChartEl = document.getElementById('tagChart');
    if (tagChartEl && !tagChartEl.chart) {
        try {
            const labels = JSON.parse(tagChartEl.dataset.tagLabels);
            const data = JSON.parse(tagChartEl.dataset.tagData);
            
            const options = {
                series: [{
                    name: '文章数',
                    data: data
                }],
                chart: {
                    type: 'bar',
                    height: 300,
                    toolbar: { show: false },
                    fontFamily: 'inherit',
                    background: 'transparent'
                },
                plotOptions: {
                    bar: {
                        borderRadius: 4,
                        horizontal: true,
                        distributed: true
                    }
                },
                colors: ['#9333ea', '#7e22ce', '#6b21a8', '#581c87', '#3b0764'],
                dataLabels: { enabled: false },
                xaxis: {
                    categories: labels,
                    axisBorder: { show: false },
                    axisTicks: { show: false },
                    labels: { style: { colors: 'var(--fallback-bc,oklch(var(--bc)/0.6))' } }
                },
                yaxis: {
                    labels: { style: { colors: 'var(--fallback-bc,oklch(var(--bc)/0.6))' } }
                },
                theme: { mode: document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light' },
                legend: { show: false }
            };
            
            const chart = new ApexCharts(tagChartEl, options);
            chart.render();
            tagChartEl.chart = chart;
        } catch(e) {
            console.error('Error initializing tag chart:', e);
        }
    }
}

// Initialize on load and HTMX swap
document.addEventListener('DOMContentLoaded', initDashboardCharts);
document.addEventListener('htmx:afterSwap', initDashboardCharts);
document.addEventListener('htmx:historyRestore', initDashboardCharts);

// Global component registry for HTMX-loaded content
window.registerGlobalComponents = function() {
    if (typeof Alpine === 'undefined') return;

    // Register categoryModal if not exists
    if (!Alpine.data('categoryModal')) {
        Alpine.data('categoryModal', () => ({
            isSubmitting: false,
            isTranslating: false,
            activeTab: 'zh-hans',
            coverPreview: null,
            form: {
                name_zh_hans: '',
                name_en: '',
                name_ja: '',
                name_zh_hant: '',
                description_zh_hans: '',
                description_en: '',
                description_ja: '',
                description_zh_hant: '',
                icon: 'folder',
                color: 'primary',
            },
            colors: [
                { name: 'Primary', value: 'primary', class: 'bg-primary' },
                { name: 'Secondary', value: 'secondary', class: 'bg-secondary' },
                { name: 'Accent', value: 'accent', class: 'bg-accent' },
                { name: 'Neutral', value: 'neutral', class: 'bg-neutral' },
                { name: 'Info', value: 'info', class: 'bg-info' },
                { name: 'Success', value: 'success', class: 'bg-success' },
                { name: 'Warning', value: 'warning', class: 'bg-warning' },
                { name: 'Error', value: 'error', class: 'bg-error' },
                { name: 'Red', value: '#ef4444', class: 'bg-red-500' },
                { name: 'Orange', value: '#f97316', class: 'bg-orange-500' },
                { name: 'Amber', value: '#f59e0b', class: 'bg-amber-500' },
                { name: 'Yellow', value: '#eab308', class: 'bg-yellow-500' },
                { name: 'Lime', value: '#84cc16', class: 'bg-lime-500' },
                { name: 'Green', value: '#22c55e', class: 'bg-green-500' },
                { name: 'Emerald', value: '#10b981', class: 'bg-emerald-500' },
                { name: 'Teal', value: '#14b8a6', class: 'bg-teal-500' },
                { name: 'Cyan', value: '#06b6d4', class: 'bg-cyan-500' },
                { name: 'Sky', value: '#0ea5e9', class: 'bg-sky-500' },
                { name: 'Blue', value: '#3b82f6', class: 'bg-blue-500' },
                { name: 'Indigo', value: '#6366f1', class: 'bg-indigo-500' },
                { name: 'Violet', value: '#8b5cf6', class: 'bg-violet-500' },
                { name: 'Purple', value: '#a855f7', class: 'bg-purple-500' },
                { name: 'Fuchsia', value: '#d946ef', class: 'bg-fuchsia-500' },
                { name: 'Pink', value: '#ec4899', class: 'bg-pink-500' },
                { name: 'Rose', value: '#f43f5e', class: 'bg-rose-500' },
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
                    if (window.showToast) window.showToast('请先输入中文名称', 'warning');
                    return;
                }
                this.isTranslating = true;
                try {
                    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
                    const response = await fetch('/api/translate/', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                        body: JSON.stringify({
                            text: this.form.name_zh_hans,
                            target_langs: ['en', 'ja', 'zh-hant']
                        })
                    });
                    const data = await response.json();
                    if (data.translations) {
                        if (data.translations.en) this.form.name_en = data.translations.en;
                        if (data.translations.ja) this.form.name_ja = data.translations.ja;
                        if (data.translations['zh-hant']) this.form.name_zh_hant = data.translations['zh-hant'];
                        if (window.showToast) window.showToast('翻译完成', 'success');
                    }
                } catch (e) {
                    console.error(e);
                    if (window.showToast) window.showToast('翻译失败', 'error');
                } finally {
                    this.isTranslating = false;
                }
            },

            async submitForm() {
                this.isSubmitting = true;
                try {
                    const formData = new FormData(document.getElementById('category_quick_form'));
                    // Ensure hidden fields are populated
                    formData.set('name', this.form.name_zh_hans);
                    formData.set('description', this.form.description_zh_hans);
                    formData.set('name_en', this.form.name_en);
                    formData.set('name_ja', this.form.name_ja);
                    formData.set('name_zh_hant', this.form.name_zh_hant);
                    formData.set('description_en', this.form.description_en);
                    formData.set('description_ja', this.form.description_ja);
                    formData.set('description_zh_hant', this.form.description_zh_hant);
                    
                    // Use relative URL to avoid hardcoded paths if possible, or ensure administration namespace
                    const response = await fetch('/admin/categories/create/quick/', {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                        },
                        body: formData
                    });
                    
                    const data = await response.json();
                    if (data.status === 'success') {
                        // Add to select box
                        const select = document.getElementById('id_category');
                        if (select) {
                            const option = new Option(data.name, data.id);
                            select.add(option, undefined);
                            select.value = data.id;
                        }
                        // Close modal and reset
                        document.getElementById('category_modal').close();
                        this.resetForm();
                        if (window.showToast) window.showToast('分类创建成功', 'success');
                    } else {
                        if (window.showToast) window.showToast('创建失败: ' + JSON.stringify(data.errors), 'error');
                    }
                } catch (e) {
                    console.error(e);
                    if (window.showToast) window.showToast('系统错误', 'error');
                } finally {
                    this.isSubmitting = false;
                }
            },
            
            resetForm() {
                this.form = {
                    name_zh_hans: '',
                    name_en: '',
                    name_ja: '',
                    name_zh_hant: '',
                    description_zh_hans: '',
                    description_en: '',
                    description_ja: '',
                    description_zh_hant: '',
                    icon: 'folder',
                    color: 'primary',
                };
                this.coverPreview = null;
                this.activeTab = 'zh-hans';
                const formEl = document.getElementById('category_quick_form');
                if (formEl) formEl.reset();
            }
        }));
    }

    // Register iconPicker if not exists
    if (!Alpine.data('iconPicker')) {
        Alpine.data('iconPicker', () => ({
            searchQuery: '',
            icons: [],
            
            init() {
                if (window.ICONS_LIST) {
                    this.icons = window.ICONS_LIST;
                } else {
                    setTimeout(() => {
                        if (window.ICONS_LIST) this.icons = window.ICONS_LIST;
                    }, 100);
                }
            },

            get filteredIcons() {
                if (!this.searchQuery) return this.icons;
                const query = this.searchQuery.toLowerCase();
                return this.icons.filter(i => i.toLowerCase().includes(query));
            },

            isSelected(iconName) {
                if (window.currentIconInput) {
                    return window.currentIconInput.value === iconName;
                }
                const input = document.querySelector('[name=icon]');
                return input && input.value === iconName;
            },

            selectIcon(iconName) {
                if (window.currentIconInput) {
                    window.currentIconInput.value = iconName;
                    window.currentIconInput.dispatchEvent(new Event('input'));
                } else {
                    const input = document.querySelector('[name=icon]');
                    if (input) {
                        input.value = iconName;
                        input.dispatchEvent(new Event('input'));
                    }
                }
                document.getElementById('icon_picker_modal').close();
            }
        }));
    }
};

// Initialize components immediately if Alpine is ready, otherwise wait
document.addEventListener('alpine:init', window.registerGlobalComponents);
if (typeof Alpine !== 'undefined') {
    window.registerGlobalComponents();
}
