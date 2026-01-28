# Rosetta 项目索引文档

本索引文档旨在为 Rosetta 项目的全面结构化上下文，以便高效理解、分析和生成代码。

## 1. 项目概览

- **项目名称**: Rosetta
- **描述**: 一个生产就绪、针对 1Panel 部署环境优化的 Django 内容管理系统 (CMS) / 博客平台。
- **设计哲学**: 遵循 12-Factor App 原则，严格区分开发与生产环境配置。
- **核心功能**:
    - 博客文章管理 (发布、草稿、置顶、加密)
    - 用户与权限系统 (自定义用户、称号、RBAC)
    - 互动系统 (评论、点赞、投票)
    - 管理后台 (基于 Django Admin 的深度定制 Dashboard)
    - 现代化前端 (Tailwind CSS + DaisyUI + HTMX + Alpine.js)
    - 生产级特性 (Redis 缓存、Celery 异步任务、Docker/1Panel 适配)

## 2. 技术栈与依赖

### 后端 (Python)
- **核心框架**: Django >= 6.0
- **API 框架**: Django REST Framework (DRF), SimpleJWT
- **异步任务**: Celery + Redis
- **数据库**:
    - 开发: SQLite
    - 生产: PostgreSQL / MySQL (`dj-database-url`)
- **搜索**: `django-watson` (全文搜索)
- **工具库**:
    - `django-tailwind`: Tailwind CSS 集成
    - `django-htmx`: HTMX 集成
    - `django-imagekit`: 图片处理
    - `django-constance`: 动态配置 (Redis/DB backend)
    - `django-environ`: 环境变量管理
- **测试**: `pytest`, `factory_boy`, `faker`

### 前端 (Node.js / Assets)
- **构建工具**: Tailwind CSS CLI (via `django-tailwind`)
- **CSS 框架**: Tailwind CSS v4, DaisyUI v5
- **JS 库**:
    - HTMX (交互)
    - Alpine.js (轻量级响应式)
    - Bytemd (Markdown 编辑器)
    - Esbuild (JS 打包)

### 基础设施
- **容器化**: 适配 Docker / 1Panel
- **Web Server**: Gunicorn / Uvicorn (ASGI)
- **反向代理**: Nginx (推荐生产环境配置)

## 3. 目录结构解析

```
d:\PythonProjects\rosetta\
├── apps/                   # [Container] 业务应用容器
│   ├── administration/     # [App] 自定义管理后台
│   │   └── views.py        # 后台视图逻辑 (CRUD)
│   ├── blog/               # [App] 博客核心业务
│   │   ├── models.py       # Post, Category, Tag, Comment
│   │   ├── views.py        # 文章展示、列表、详情
│   │   └── feeds.py        # RSS/Atom Feeds
│   ├── core/               # [App] 系统核心组件
│   │   ├── models.py       # Page, Navigation, Notification
│   │   ├── middleware.py   # 访问频率限制, 维护模式等
│   │   ├── utils.py        # 通用工具函数
│   │   └── management/     # 自定义管理命令 (createdb, mock data)
│   ├── guestbook/          # [App] 留言板
│   ├── users/              # [App] 用户认证系统
│   │   ├── models.py       # Custom User, UserTitle, UserPreference
│   │   └── views.py        # 登录、注册、个人中心
│   └── voting/             # [App] 投票系统
│       ├── models.py       # Poll, Choice, Vote
│       └── views.py        # 投票交互逻辑
├── Rosetta/                # 项目配置根目录
│   ├── settings.py         # 核心配置文件 (环境驱动)
│   ├── urls.py             # 全局路由入口
│   ├── wsgi.py/asgi.py     # WSGI/ASGI 入口
│   └── celery.py           # Celery 任务配置
├── theme/                  # [App] 前端主题构建 (Tailwind/Node.js)
│   └── static_src/         # Tailwind/JS 源码 (Node.js 项目根目录)
├── templates/              # [Global] 全局模板目录 (按 App 分组)
│   ├── administration/     # 后台模板
│   ├── blog/               # 博客模板
│   ├── core/               # 核心组件模板
│   ├── guestbook/          # 留言板模板
│   ├── voting/             # 投票模板
│   ├── components/         # UI 组件
│   └── base.html           # 基础布局
├── static/                 # 收集后的静态文件 (生产环境)
├── media/                  # 用户上传文件存储
├── pyproject.toml          # Python 依赖与工具配置
├── manage.py               # Django 管理脚本
└── requirements.txt        # 生产环境依赖列表
```

## 4. 核心模块与组件

### 4.1 数据模型 (Models)
*   **User (users)**: 扩展 AbstractUser，包含头像、封面、简介、称号关联。
*   **Post (blog)**: 核心内容模型，支持 Markdown，包含分类、标签、状态流转、加密、SEO 字段。
*   **Category/Tag (blog)**: 内容组织维度，Tag 支持颜色配置。
*   **Comment (blog)**: 多级评论系统，关联 User 和 Post。
*   **Poll (voting)**: 投票系统，支持单选/多选，可关联 Post。
*   **Notification (core)**: 站内通知，使用 GenericForeignKey 关联任意目标对象。
*   **Navigation (core)**: 动态菜单配置 (Header/Footer/Sidebar)。

### 4.2 视图与交互 (Views & UI)
*   **Frontend**: 采用 Django Template 渲染首屏，结合 HTMX 实现局部刷新 (如评论提交、点赞、无限滚动)。
*   **Admin Dashboard**: `administration` 应用提供了一套独立于 Django Admin 的现代化后台，使用 Class-Based Views (CBV) 实现资源的 CRUD。
*   **Authentication**: 基于 Django Auth，自定义了登录/注册页面和流程。

### 4.3 关键服务 (Services)
*   **RateLimitMiddleware (core)**: 基于 Redis/Cache 的请求频率限制。
*   **Constance (Config)**: 允许在后台动态修改系统配置 (如站点标题、维护模式) 而无需重启。
*   **Celery Tasks**: 用于异步处理耗时任务 (如图片处理、邮件发送)。

## 5. 配置与环境

项目完全通过环境变量驱动 (`.env`)，遵循 `Rosetta/settings.py` 中的逻辑：

| 环境变量 | 必填 (Prod) | 默认值 (Dev) | 说明 |
| :--- | :---: | :--- | :--- |
| `DEBUG` | 是 | `True` | **核心开关**，生产环境必须设为 `False` |
| `DJANGO_SECRET_KEY` | 是 | (Hardcoded) | Django 加密密钥 |
| `DATABASE_URL` | 是 | `sqlite:///db.sqlite3` | 数据库连接串 (Postgres/MySQL) |
| `REDIS_URL` | 是 | `None` | 缓存与 Celery Broker 地址 |
| `ALLOWED_HOSTS` | 是 | `*` | 允许访问的域名列表 |

## 6. 数据流与 API

虽然项目主要通过服务端渲染 HTML，但也暴露了部分 API 供特定场景使用：

*   **API 风格**: RESTful (DRF)
*   **认证**: JWT (JSON Web Token)
*   **主要端点**:
    *   `/users/api/...` (待定): 用户相关接口
    *   `htmx` 请求: 大量交互通过特定的 HTMX 视图处理 (如 `comment_create`, `vote`)，这些视图通常返回 HTML 片段而非 JSON。

## 7. 构建与运行指南

### 开发环境
1.  **环境准备**: Python 3.14+, Node.js 20+, Redis (可选)
2.  **安装 uv**:
    ```bash
    pip install uv  # 如果已安装 uv 可跳过
    ```
3.  **安装依赖**:
    ```bash
    uv sync
    cd theme/static_src && npm install
    ```
4.  **构建前端**:
    ```bash
    uv run python manage.py tailwind start  # 开启 Tailwind 监听
    ```
5.  **运行服务**:
    ```bash
    uv run python manage.py migrate
    uv run python manage.py runserver
    ```

### 生产环境
1.  **环境变量**: 确保 `.env` 配置正确 (`DEBUG=False`).
2.  **静态资源**:
    ```bash
    python manage.py tailwind build
    python manage.py collectstatic --noinput
    ```
3.  **服务启动**: 使用 Gunicorn 或 Uvicorn 启动 WSGI/ASGI 应用。
4.  **后台任务**: 启动 Celery Worker 和 Beat。

## 8. 已知问题与注意事项

*   **Tailwind 依赖**: 必须安装 Node.js 环境才能编译 CSS。开发时需保持 `tailwind start` 运行。
*   **缓存依赖**: 生产环境强依赖 Redis，缺少 Redis 会导致缓存、Celery 和 Constance 功能异常。
*   **HTMX 竞态**: 在处理 Alpine.js 与 HTMX 结合的复杂交互时，需注意 DOM 更新时机 (使用 `htmx-init.js` 中的钩子)。
*   **1Panel 部署**: 需注意 Nginx 反向代理的 Header 设置 (`HTTP_X_FORWARDED_PROTO`) 以防止无限重定向循环。

---