# Rosetta Blog Project

![Django](docs/badges/django.svg)&nbsp;&nbsp;![TailwindCSS](docs/badges/tailwindcss.svg)&nbsp;&nbsp;![Alpine.js](docs/badges/alpinejs.svg)&nbsp;&nbsp;![License](docs/badges/license.svg)

Rosetta 是基于 **Django 6.0**、**Tailwind CSS** 和 **Alpine.js** 开发的个人博客系统。项目集成了文章管理、用户认证、评论互动、动态配置及 SEO 优化等核心功能。

## 功能特性

### 前端体验
*   **响应式布局**: 基于 Tailwind CSS 和 DaisyUI，适配多端设备。
*   **深色模式**: 支持系统跟随及手动切换。
*   **阅读体验**: Markdown 渲染、代码高亮、TOC 目录生成。
*   **交互设计**: 集成 Alpine.js 和 HTMX，提供无刷新页面交互；支持 GeoPattern 自动封面生成。

### 用户系统
*   **认证**: 注册、登录、邮件找回密码。
*   **个人中心**: 资料编辑、头像/封面裁剪 (Cropper.js)、站内信通知。
*   **互动**: 多级评论、文章点赞。

### 后台管理
*   **仪表盘**: 基于 ApexCharts 的数据可视化统计。
*   **内容管理**: Markdown 编辑器 (Toast UI)、文章/分类/标签管理、单页管理。
*   **系统配置**:
    *   **动态设置**: 在线修改站点信息、Logo、SEO 等 (Constance)。
    *   **运维**: Loguru 日志集成、缓存管理。

### 技术架构
*   **后端**: Django 6.0 (Python 3.10+)
*   **前端**: Tailwind CSS CLI (无需 Webpack)
*   **数据库**: SQLite (默认) / PostgreSQL
*   **API**: Django REST Framework (DRF)
*   **异步**: Celery (可选)

## 快速开始

### 1. 环境准备
需安装 Python 3.10+ 和 Node.js。

### 2. 克隆项目
```bash
git clone https://github.com/chuyuchoyeon/rosetta.git
cd rosetta
```

### 3. 安装依赖
```bash
# 创建虚拟环境
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate

# 安装 Python 依赖
pip install -r requirements.txt

# 安装前端依赖
python manage.py tailwind install
```

### 4. 初始化
```bash
# 数据库迁移
python manage.py makemigrations
python manage.py migrate

# 创建管理员
python manage.py createsuperuser

# 生成模拟数据 (可选)
python manage.py generate_mock_data
```

### 5. 启动
需开启两个终端：

**终端 1 (Django):**
```bash
python manage.py runserver
```

**终端 2 (Tailwind):**
```bash
python manage.py tailwind start
```

访问: `http://127.0.0.1:8000/`

## 部署指南

### 生产环境
1.  **配置**: 复制 `.env.example` 为 `.env`，设置 `DEBUG=False` 及 `SECRET_KEY`。
2.  **静态资源**: `python manage.py collectstatic`。
3.  **服务**: 使用 Gunicorn/Daphne 配合 Nginx 反向代理。

### Docker
```bash
docker-compose up -d --build
```

## 测试

```bash
# 运行全部测试
python -m pytest

# 生成覆盖率报告
python -m pytest --cov=.
```

## 许可证
MIT License
