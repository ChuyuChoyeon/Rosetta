"""
Rosetta 项目核心配置文件。

包含项目的所有全局配置，如数据库连接、应用注册、中间件、静态资源管理等。
生产环境配置请优先使用环境变量覆盖默认值。
"""

import os
from pathlib import Path
from datetime import timedelta
import dj_database_url

# ------------------------------------------------------------------------------
# 基础路径配置
# ------------------------------------------------------------------------------
# 项目根目录，用于定位数据库、静态文件和模板等资源
BASE_DIR = Path(__file__).resolve().parent.parent


# ------------------------------------------------------------------------------
# 核心安全与调试配置
# ------------------------------------------------------------------------------

# 密钥配置
# 警告：生产环境必须保持密钥私密，泄露可能导致安全漏洞（如 Session 劫持）。
# 优先从环境变量 DJANGO_SECRET_KEY 获取，开发环境使用默认值。
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-598u(^sv4vtl1)@)uxmsz%&oeoxtgau09)5en^0#n!uz63$o@(",
)

# 调试模式
# 警告：生产环境必须设置为 False。
# 开启调试模式会暴露详细的错误堆栈信息，可能包含敏感数据。
DEBUG = os.environ.get("DEBUG", "True") == "True"

# 允许访问的主机域名
# 生产环境请填入具体的域名或 IP 地址，避免 HTTP Host 头攻击。
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")


# ------------------------------------------------------------------------------
# 安全加固配置 (生产环境建议开启)
# ------------------------------------------------------------------------------
# 浏览器 XSS 过滤保护
SECURE_BROWSER_XSS_FILTER = True
# 防止浏览器嗅探 Content-Type
SECURE_CONTENT_TYPE_NOSNIFF = True
# 仅通过 HTTPS 传输 Session Cookie（非调试模式下生效）
SESSION_COOKIE_SECURE = not DEBUG
# 仅通过 HTTPS 传输 CSRF Cookie（非调试模式下生效）
CSRF_COOKIE_SECURE = not DEBUG
# 禁止 JavaScript 访问 Session Cookie，防止 XSS 窃取 Session
SESSION_COOKIE_HTTPONLY = True
# 默认字符集
DEFAULT_CHARSET = 'utf-8'
# 禁止页面被嵌入 iframe，防止点击劫持
X_FRAME_OPTIONS = 'DENY'
# Referrer 策略：同源请求发送 Referrer，跨域仅发送源站信息
REFERRER_POLICY = 'same-origin'

if not DEBUG:
    # HSTS (HTTP Strict Transport Security) 配置
    # 强制浏览器在指定时间内仅使用 HTTPS 访问，防止降级攻击
    SECURE_HSTS_SECONDS = 31536000  # 1年
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    # 强制将所有 HTTP 请求重定向到 HTTPS
    SECURE_SSL_REDIRECT = True
    # 代理设置 (如果部署在 Nginx/LB 后)
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# ------------------------------------------------------------------------------
# 应用注册 (Installed Apps)
# ------------------------------------------------------------------------------
INSTALLED_APPS = [
    # --- 本地业务应用 ---
    "administration",         # 自定义管理后台
    
    # --- Django 内置组件 ---
    "django.contrib.admin",       # 默认管理后台
    "django.contrib.auth",        # 认证系统
    "django.contrib.contenttypes",# 内容类型框架
    "django.contrib.sessions",    # 会话管理
    "django.contrib.messages",    # 消息框架
    "django.contrib.staticfiles", # 静态文件管理
    "django.contrib.sites",       # 多站点框架 (评论、站点地图依赖)
    "django.contrib.sitemaps",    # 站点地图生成
    
    # --- 第三方扩展 ---
    "guardian",               # 对象级权限控制
    "tailwind",               # Tailwind CSS 集成
    "theme",                  # 前端主题 (DaisyUI)
    "django_browser_reload",  # 开发环境浏览器自动刷新
    "django_htmx",            # HTMX 前后端交互支持
    "django_filters",         # 高级查询过滤器
    "import_export",          # 数据导入导出工具
    "captcha",                # 图形验证码
    "simple_history",         # 模型变更审计与回滚
    "rest_framework",         # RESTful API 框架
    "rest_framework_simplejwt", # JWT 认证支持
    "imagekit",               # 图片处理 (缩略图、调整大小)
    "watson",                 # 数据库全文搜索
    "compressor",             # 静态资源压缩与合并
    "meta",                   # SEO Meta 标签生成
    "constance",              # 动态配置系统 (支持数据库或 Redis)
    "constance.backends.database",
    "chartjs",                # Chart.js 图表渲染辅助
    
    # --- 核心业务模块 ---
    "blog.apps.BlogConfig",   # 博客内容管理
    "users.apps.UsersConfig", # 用户账户与权限
    "core.apps.CoreConfig",   # 通用基础设施
]


# ------------------------------------------------------------------------------
# 中间件配置 (Middleware)
# ------------------------------------------------------------------------------
# 注意：中间件的顺序至关重要，请求从上往下处理，响应从下往上返回。
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",        # 静态文件服务 (生产环境)
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    
    # --- 扩展中间件 ---
    "django_htmx.middleware.HtmxMiddleware",             # 解析 HTMX 请求头
    "simple_history.middleware.HistoryRequestMiddleware", # 自动记录操作用户
    "watson.middleware.SearchContextMiddleware",         # 自动更新搜索索引
]

# 开发环境下启用浏览器自动刷新
if DEBUG:
    MIDDLEWARE += [
        "django_browser_reload.middleware.BrowserReloadMiddleware",
    ]

# 根 URL 路由配置
ROOT_URLCONF = "Rosetta.urls"

# WSGI 应用入口
WSGI_APPLICATION = "Rosetta.wsgi.application"


# ------------------------------------------------------------------------------
# 模板系统配置 (Templates)
# ------------------------------------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # 模板搜索路径：优先查找项目根目录下的 templates 文件夹
        "DIRS": [BASE_DIR / "templates"],
        # 启用应用内模板查找 (templates/ 目录)
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # 自定义上下文处理器
                "core.context_processors.site_settings", # 注入全局站点设置
                "constance.context_processors.config",   # 注入动态配置变量
            ],
        },
    },
]


# ------------------------------------------------------------------------------
# 数据库配置 (Database)
# ------------------------------------------------------------------------------
# 默认使用 SQLite3，适合开发环境。
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# 生产环境数据库适配
# 如果存在 DATABASE_URL 环境变量 (例如在 PaaS 平台)，则自动配置数据库连接。
# 格式示例: postgres://user:password@host:port/dbname
if os.environ.get("DATABASE_URL"):
    DATABASES["default"] = dj_database_url.config(
        conn_max_age=600,        # 保持数据库连接 10 分钟，减少连接开销
        conn_health_checks=True, # 定期检查连接健康状态
    )


# ------------------------------------------------------------------------------
# 认证与用户系统
# ------------------------------------------------------------------------------
# 指定自定义用户模型
AUTH_USER_MODEL = "users.User"

# 认证后端
AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",   # 标准用户名/密码认证
    "guardian.backends.ObjectPermissionBackend",   # 对象级权限认证
)

# 密码强度验证
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"}, # 避免与用户信息太相似
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},           # 最小长度限制
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},          # 禁止常见弱密码
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},         # 禁止纯数字密码
]

# 登录跳转配置
LOGIN_REDIRECT_URL = "/"      # 登录成功后跳转地址
LOGOUT_REDIRECT_URL = "/"     # 登出成功后跳转地址
LOGIN_URL = "users:login"     # 登录页面 URL 名称


# ------------------------------------------------------------------------------
# 国际化与时区 (I18N & L10N)
# ------------------------------------------------------------------------------
LANGUAGE_CODE = "zh-hans"     # 语言代码：简体中文
TIME_ZONE = "Asia/Shanghai"   # 时区：亚洲/上海
USE_I18N = True               # 启用翻译系统
USE_TZ = True                 # 启用时区支持 (数据库存储 UTC，显示时转换为本地时间)


# ------------------------------------------------------------------------------
# 静态文件与媒体资源
# ------------------------------------------------------------------------------
# 静态文件 URL 前缀
STATIC_URL = "static/"
# 收集静态文件的目录 (执行 python manage.py collectstatic 后生成)
STATIC_ROOT = BASE_DIR / "staticfiles"

# 静态文件查找策略
STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder", # 查找 STATICFILES_DIRS
    "django.contrib.staticfiles.finders.AppDirectoriesFinder", # 查找各 App 下的 static 目录
    "compressor.finders.CompressorFinder", # 查找压缩后的缓存文件
)

# 静态文件存储引擎 (集成 WhiteNoise)
# 支持静态文件压缩和长期缓存 (Cache Busting)
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# 用户上传文件 URL 前缀
MEDIA_URL = "/media/"
# 用户上传文件存储路径
MEDIA_ROOT = BASE_DIR / "media"


# ------------------------------------------------------------------------------
# 第三方组件配置
# ------------------------------------------------------------------------------

# --- Tailwind CSS ---
TAILWIND_APP_NAME = "theme"
# NPM 路径 (Windows 环境下通常指向 npm.cmd)
# 请确保此路径与本地开发环境一致，或通过环境变量配置
NPM_BIN_PATH = "C:\\Program Files\\nodejs\\npm.cmd"

# --- Django Sites Framework ---
# 当前站点 ID，多站点部署时需修改
SITE_ID = 1

# --- REST Framework (API) ---
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication", # API 优先使用 JWT
        "rest_framework.authentication.SessionAuthentication",       # 浏览器调试使用 Session
    )
}

# --- Simple JWT (Token 配置) ---
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60), # Access Token 有效期
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),    # Refresh Token 有效期
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    "UPDATE_LAST_LOGIN": True,
}

# --- Django Compressor (静态资源压缩) ---
# 开发环境关闭压缩，避免频繁修改导致的缓存问题；生产环境开启。
COMPRESS_ENABLED = not DEBUG
COMPRESS_OFFLINE = False

# --- Django Meta (SEO 配置) ---
META_SITE_PROTOCOL = "http"
META_SITE_DOMAIN = "localhost:8000"
META_USE_OG_PROPERTIES = True      # Open Graph 协议支持 (Facebook/微信等)
META_USE_TWITTER_PROPERTIES = True # Twitter 卡片支持


# ------------------------------------------------------------------------------
# 动态配置与缓存系统 (Constance & Cache)
# ------------------------------------------------------------------------------
# 默认使用数据库作为动态配置存储
CONSTANCE_BACKEND = "constance.backends.database.DatabaseBackend"

# Redis 集成 (生产环境推荐)
# 如果检测到 REDIS_URL 环境变量，自动切换缓存、Session 和动态配置后端为 Redis
if os.environ.get("REDIS_URL"):
    # 1. 缓存配置
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": os.environ.get("REDIS_URL"),
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "IGNORE_EXCEPTIONS": True,  # Redis 连接失败时不中断服务
                "CONNECTION_POOL_KWARGS": {"max_connections": 100},
            },
            "KEY_PREFIX": "rosetta",
        }
    }
    
    # 2. Session 存储 (使用缓存)
    SESSION_ENGINE = "django.contrib.sessions.backends.cache"
    SESSION_CACHE_ALIAS = "default"
    
    # 3. 动态配置存储 (切换到 Redis)
    CONSTANCE_BACKEND = "constance.backends.redis.RedisBackend"
    CONSTANCE_REDIS_CONNECTION = os.environ.get("REDIS_URL")
    CONSTANCE_REDIS_PREFIX = "rosetta_config:"

# Constance 配置项定义
# 格式: "KEY": (默认值, "描述文本", 类型[可选])
CONSTANCE_CONFIG = {
    # 站点基础信息
    "SITE_NAME": ("Rosetta Blog", "站点名称"),
    "SITE_DESCRIPTION": ("A modern Django blog.", "站点描述"),
    "SITE_KEYWORDS": ("blog, django, python", "SEO 关键词"),
    "SHOW_SITE_LOGO": (True, "是否显示站点 Logo"),
    "SITE_LOGO": ("/static/core/img/logo.png", "站点 Logo URL"),
    "SITE_FAVICON": ("/static/core/img/favicon.ico", "站点 Favicon URL"),
    
    # 后台界面定制
    "SITE_HEADER": ("Rosetta Dashboard", "后台头部标题"),
    "SITE_ADMIN_SUFFIX": (" - Rosetta Dashboard", "后台页面标题后缀"),
    "ADMIN_NAVBAR_TITLE": ("Rosetta 管理后台", "后台导航栏标题"),
    "DASHBOARD_WELCOME_TEXT": ("这里是您的站点概览，祝您有美好的一天。", "仪表盘欢迎语"),
    "DASHBOARD_WELCOME_WORDS": ("['Creator', 'Admin', 'Master', 'Manager']", "仪表盘动态欢迎词 (Flip Words)"),
    
    # 页脚信息
    "FOOTER_TEXT": ("© 2026 Rosetta Blog", "页脚版权文本"),
    "FOOTER_SLOGAN": ("分享代码，记录生活。<br/>构建属于你的知识花园。", "页脚标语/简介"),
    "BEIAN_CODE": ("", "ICP 备案号"),
    
    # 社交媒体链接
    "GITHUB_URL": ("", "GitHub 链接"),
    "X_URL": ("", "X (Twitter) 链接"),
    "BILIBILI_URL": ("", "Bilibili 链接"),
    "CONTACT_EMAIL": ("", "联系邮箱"),
    
    # 邮件服务配置
    "SMTP_HOST": ("smtp.qq.com", "SMTP 服务器地址"),
    "SMTP_PORT": (465, "SMTP 端口"),
    "SMTP_USER": ("", "SMTP 用户名"),
    "SMTP_PASSWORD": ("", "SMTP 密码/授权码"),
    "SMTP_USE_TLS": (True, "启用 SSL/TLS 加密"),
    "SMTP_FROM_EMAIL": ("", "默认发件人邮箱"),
    
    # 功能特性开关
    "MAINTENANCE_MODE": (False, "开启维护模式"),
    "ENABLE_COMMENTS": (True, "开启评论功能"),
    "ENABLE_REGISTRATION": (True, "开启用户注册"),
    "ENABLE_EMAIL_NOTIFICATIONS": (False, "开启邮件通知"),
    
    # 自定义代码注入
    "EXTRA_HEAD_CODE": ("", "自定义 Head 代码 (CSS/JS)"),
    "EXTRA_FOOTER_CODE": ("", "自定义 Footer 代码 (JS)"),
    
    # 外观设置
    "CODE_HIGHLIGHT_STYLE": ("default", "代码高亮风格 (Pygments)"),
}

# Constance 配置分组显示
CONSTANCE_CONFIG_FIELDSETS = {
    "基本设置": (
        "SITE_NAME", "SITE_DESCRIPTION", "SITE_KEYWORDS",
        "SHOW_SITE_LOGO", "SITE_LOGO", "SITE_FAVICON",
        "FOOTER_SLOGAN", "FOOTER_TEXT", "BEIAN_CODE",
        "BEIAN_CODE", "FOOTER_TEXT",
    ),
    "外观设置": (
        "CODE_HIGHLIGHT_STYLE",
    ),
    "后台界面": (
        "SITE_HEADER", "SITE_ADMIN_SUFFIX", "ADMIN_NAVBAR_TITLE",
        "DASHBOARD_WELCOME_TEXT", "DASHBOARD_WELCOME_WORDS",
    ),
    "社交与联系": (
        "GITHUB_URL", "X_URL", "BILIBILI_URL", "CONTACT_EMAIL",
    ),
    "邮件服务": (
        "SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD",
        "SMTP_USE_TLS", "SMTP_FROM_EMAIL", "ENABLE_EMAIL_NOTIFICATIONS",
    ),
    "功能开关": (
        "MAINTENANCE_MODE", "ENABLE_COMMENTS", "ENABLE_REGISTRATION",
    ),
    "自定义代码": (
        "EXTRA_HEAD_CODE", "EXTRA_FOOTER_CODE",
    ),
}


# ------------------------------------------------------------------------------
# 日志系统 (Loguru Integration)
# ------------------------------------------------------------------------------
# 拦截 Django 默认日志并转发给 Loguru
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "intercept": {
            "level": "INFO",
            "class": "core.logging.InterceptHandler", # 使用自定义拦截器
        },
    },
    "loggers": {
        "django": {
            "handlers": ["intercept"],
            "level": "INFO",
            "propagate": True,
        },
        "django.db.backends": {
            "handlers": ["intercept"],
            "level": "WARNING",  # 仅记录警告级以上的 SQL 问题，避免日志爆炸
            "propagate": False,
        },
    },
}

# Loguru 文件日志配置
LOG_DIR = BASE_DIR / "logs"
# 自动创建日志目录
if not LOG_DIR.exists():
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

if not DEBUG:
    # 生产环境：记录 INFO 及以上级别，按大小轮转，压缩归档
    from loguru import logger
    logger.add(
        LOG_DIR / "rosetta.log",
        rotation="10 MB",     # 文件超过 10MB 时轮转
        retention="30 days",  # 保留最近 30 天的日志
        level="WARNING",      # 仅记录警告及以上
        compression="zip",    # 历史日志压缩存储
        enqueue=True,         # 异步写入，不阻塞主线程
    )
else:
    # 开发环境：记录 DEBUG 级别，方便调试
    from loguru import logger
    logger.add(
        LOG_DIR / "debug.log",
        level="DEBUG",
    )

# 邮件后端配置 (使用支持 Constance 动态配置的自定义后端)
EMAIL_BACKEND = "core.backends.ConstanceEmailBackend"
