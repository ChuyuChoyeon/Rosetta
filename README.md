# Rosetta Blog Project

![Rosetta](https://img.shields.io/badge/Django-6.0-green.svg) ![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4-blue.svg) ![AlpineJS](https://img.shields.io/badge/AlpineJS-3.x-yellow.svg)

Rosetta 是一个基于 Django 6.0、Tailwind CSS 和 Alpine.js 构建的现代个人博客系统。它集成了丰富的功能，包括文章管理、用户系统、评论系统、动态设置、SEO 优化等，旨在提供极致的写作和阅读体验。

## 🌟 主要功能 (Features)

### 🎨 前台功能 (Frontend)
*   **响应式设计**: 基于 Tailwind CSS 和 DaisyUI，完美适配移动端和桌面端。
*   **深色模式**: 支持明亮/暗黑模式切换，并跟随系统偏好。
*   **文章阅读**: 沉浸式阅读体验，支持 Markdown 渲染、代码高亮、目录生成。
*   **用户系统**:
    *   注册、登录、密码重置。
    *   **个人中心**: 个人资料管理、头像/封面图裁剪上传 (Cropper.js)。
    *   **消息通知**: 站内信通知系统。
*   **互动系统**:
    *   评论功能 (支持嵌套回复)。
    *   阅读量统计。
*   **搜索功能**: 全文搜索支持。

### 🛠 后台管理 (Administration)
*   **仪表盘**: 可视化数据统计 (Chart.js)，展示文章、用户、评论、流量趋势。
*   **内容管理**:
    *   文章发布与编辑 (集成 Markdown 编辑器)。
    *   分类与标签管理。
    *   页面 (Page) 管理 (如关于页面)。
*   **用户管理**: 用户列表、权限管理、封禁/解封。
*   **评论审核**: 评论审批流程。
*   **系统设置**:
    *   **动态配置 (Constance)**: 在后台直接修改站点名称、SEO设置、页脚文案等，无需重启服务器。
    *   **日志查看**: 集成 Loguru 日志系统。
    *   **批量操作**: 支持数据导出/导入。

### 🚀 技术栈 (Tech Stack)
*   **后端**: Django 6.0, Python 3.10+
*   **前端**: Tailwind CSS, Alpine.js, HTMX
*   **数据库**: SQLite (默认) / PostgreSQL (生产环境推荐)
*   **其他**:
    *   `django-compressor`: 静态资源压缩。
    *   `django-constance`: 动态配置。
    *   `django-simple-history`: 数据变更历史。
    *   `rest_framework`: API 支持。

## 📂 项目结构 (Structure)

```
rosetta/
├── administration/      # 后台管理应用 (Dashboard, CRUD)
├── blog/                # 博客核心应用 (文章, 评论, 标签)
├── core/                # 核心通用功能 (基类, 工具, 全局模板)
├── theme/               # 前端主题应用 (Tailwind 配置, 静态资源)
├── users/               # 用户认证与个人中心应用
├── media/               # 用户上传文件 (头像, 封面图)
├── templates/           # 全局模板覆盖
├── Rosetta/             # 项目配置 (Settings, WSGI)
└── manage.py            # Django 管理脚本
```

## 🚀 快速开始 (Quick Start)

### 1. 环境准备
确保已安装 Python 3.10+ 和 Node.js (用于 Tailwind CSS 构建)。

### 2. 安装依赖
```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装 Python 依赖
pip install -r requirements.txt

# 安装前端依赖 (Tailwind CSS)
python manage.py tailwind install
```

### 3. 数据库迁移
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. 创建超级管理员
```bash
python manage.py createsuperuser
```

### 5. 启动开发服务器
需要开启两个终端窗口：

**终端 1 (Django Server):**
```bash
python manage.py runserver
```

**终端 2 (Tailwind Watcher):**
```bash
python manage.py tailwind start
```

访问地址: `http://127.0.0.1:8000/`

## 📝 开发指南

*   **样式修改**: 修改 `theme/static_src/src/styles.css` 或模板中的 Tailwind 类名。
*   **配置修改**: 大部分站点配置可在后台 "系统设置" -> "动态配置" 中修改。
*   **添加新功能**: 建议新建 Django App 并注册到 `INSTALLED_APPS`。

## 📄 许可证
MIT License
