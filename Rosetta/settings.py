"""
Rosetta 项目核心配置文件 (Production Ready / 1Panel Optimized).

遵循 12-Factor App 原则，严格区分开发与生产环境。
核心逻辑：DEBUG 模式决定一切配置策略。
"""

import os
import sys
from pathlib import Path
from datetime import timedelta
import environ  # requires: django-environ

# ------------------------------------------------------------------------------
# 环境与路径配置
# ------------------------------------------------------------------------------
# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 将 apps 目录添加到 sys.path，使 Django 能直接导入其中的应用
sys.path.insert(0, str(BASE_DIR / "apps"))

# 初始化环境变量
env = environ.Env()

# 读取 .env 文件
# 为了兼容本地开发和容器部署，我们尝试读取但忽略错误。
env.read_env(BASE_DIR / ".env")

# ------------------------------------------------------------------------------
# 核心模式控制 (The Cornerstone)
# ------------------------------------------------------------------------------
# 警告：DEBUG 必须由环境变量控制。
# 默认开启 (Safe for Dev)，但生产环境必须显式设置为 False。
DEBUG = env.bool("DEBUG", default=True)
DEBUG_TOOL_ENABLED = env.bool("DEBUG_TOOL_ENABLED", default=DEBUG)

# ------------------------------------------------------------------------------
# 安全配置 (Security)
# ------------------------------------------------------------------------------
# 密钥配置
if DEBUG:
    # 开发环境使用硬编码密钥，方便且无风险
    SECRET_KEY = env(
        "DJANGO_SECRET_KEY", default="django-insecure-dev-key-rosetta-local-dev-only"
    )
else:
    # 生产环境必须从环境变量获取，否则拒绝启动
    # 1Panel 设置：在应用配置 -> 环境变量中添加 DJANGO_SECRET_KEY
    SECRET_KEY = env("DJANGO_SECRET_KEY")

# 主机与源信任
if DEBUG:
    ALLOWED_HOSTS = ["*"]
    CSRF_TRUSTED_ORIGINS = ["http://localhost:8000", "http://127.0.0.1:8000"]
else:
    # 生产环境必须严格限制 Host
    # 示例: ALLOWED_HOSTS=rosetta.com,www.rosetta.com
    ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")
    # 解决反向代理后的 CSRF 问题
    CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# ------------------------------------------------------------------------------
# 数据库配置 (Database)
# ------------------------------------------------------------------------------
# 严格分离：开发用 SQLite，生产用 Database URL
if DEBUG:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    # 生产环境：强制使用 DATABASE_URL
    # 格式: postgres://user:password@host:port/dbname
    # 1Panel: 确保数据库容器与应用在同一网络，host 使用容器名或内部 IP
    DATABASES = {"default": env.db("DATABASE_URL")}

    # 数据库连接优化 (针对 PostgreSQL/MySQL)
    DATABASES["default"]["CONN_MAX_AGE"] = env.int(
        "CONN_MAX_AGE", default=600
    )  # 保持连接 10 分钟
    DATABASES["default"]["CONN_HEALTH_CHECKS"] = True  # 定期检查连接健康

# ------------------------------------------------------------------------------
# 缓存与动态配置 (Cache & Constance)
# ------------------------------------------------------------------------------
if DEBUG:
    # 开发环境：本地内存缓存
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }
    # 动态配置存储在数据库中 (方便调试)
    CONSTANCE_BACKEND = "constance.backends.database.DatabaseBackend"
else:
    # 生产环境：强制使用 Redis
    # 格式: redis://:password@host:port/db
    if not env("REDIS_URL", default=None):
        raise RuntimeError("REDIS_URL 未配置，生产环境必须启用 Redis")

    CACHES = {"default": env.cache("REDIS_URL")}

    # Session 使用缓存 (高性能)
    SESSION_ENGINE = "django.contrib.sessions.backends.cache"
    SESSION_CACHE_ALIAS = "default"

    # Constance 使用 Redis (高性能)
    CONSTANCE_BACKEND = "constance.backends.redisd.RedisBackend"
    CONSTANCE_REDIS_CONNECTION = env("REDIS_URL")
    CONSTANCE_REDIS_PREFIX = "rosetta_config:"
    # Redis 连接池配置
    CONSTANCE_REDIS_CONNECTION_CLASS = "core.utils.ConstanceRedisConnection"

SIDEBAR_CACHE_TTL = env.int("SIDEBAR_CACHE_TTL", default=300)
SITE_SETTINGS_CACHE_TTL = env.int("SITE_SETTINGS_CACHE_TTL", default=300)
IMAGE_PROCESSING_DELAY = env.int("IMAGE_PROCESSING_DELAY", default=120)
IMAGE_QUEUE_STATUS_TTL = env.int("IMAGE_QUEUE_STATUS_TTL", default=86400)
IMAGE_QUEUE_LOCK_TTL = env.int("IMAGE_QUEUE_LOCK_TTL", default=3600)
WATSON_REBUILD_STATUS_TTL = env.int("WATSON_REBUILD_STATUS_TTL", default=86400)
WATSON_REBUILD_LOCK_TTL = env.int("WATSON_REBUILD_LOCK_TTL", default=3600)

CELERY_BROKER_URL = env("REDIS_URL", default="memory://")
CELERY_RESULT_BACKEND = env("REDIS_URL", default="cache+memory://")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Asia/Shanghai"
# 开发环境如果没有 Redis，使用立即执行模式
if DEBUG and "memory://" in CELERY_BROKER_URL:
    CELERY_TASK_ALWAYS_EAGER = True

# ------------------------------------------------------------------------------
# 应用注册 (Installed Apps)
# ------------------------------------------------------------------------------
INSTALLED_APPS = [
    # --- 本地业务应用 ---
    "administration",  # 自定义管理后台
    # --- Django 内置组件 ---
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.sitemaps",
    # --- 第三方扩展 ---
    "guardian",  # 对象级权限控制
    "tailwind",  # Tailwind CSS
    "theme",  # DaisyUI Theme
    "django_browser_reload",  # 浏览器自动刷新 (Middleware handle logic)
    "django_htmx",  # HTMX
    "captcha",  # 验证码
    "rest_framework",  # DRF
    "rest_framework_simplejwt",  # JWT
    "imagekit",  # 图片处理
    "watson",  # 全文搜索
    "meta",  # SEO
    "constance",  # 动态配置
    "constance.backends.database",  # 注册 Database Backend App (即使在 Redis 模式下保留也不影响，除非 strict)
    "widget_tweaks",  # 表单渲染增强
    # --- 核心业务模块 ---
    "blog.apps.BlogConfig",
    "users.apps.UsersConfig",
    "core.apps.CoreConfig",
    "voting.apps.VotingConfig",
    "guestbook.apps.GuestbookConfig",
]

# ------------------------------------------------------------------------------
# 中间件配置 (Middleware)
# ------------------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "core.middleware.RateLimitMiddleware",
    "core.logging.RequestIDMiddleware",  # 请求 ID
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "core.middleware.MaintenanceMiddleware",
    "watson.middleware.SearchContextMiddleware",
]

# 开发环境专用中间件
if DEBUG:
    MIDDLEWARE += [
        "django_browser_reload.middleware.BrowserReloadMiddleware",
    ]

# ------------------------------------------------------------------------------
# 模板与入口 (Templates & WSGI)
# ------------------------------------------------------------------------------
ROOT_URLCONF = "Rosetta.urls"
WSGI_APPLICATION = "Rosetta.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.site_settings",
                "constance.context_processors.config",
            ],
        },
    },
]
if not DEBUG:
    TEMPLATES[0]["APP_DIRS"] = False
    TEMPLATES[0]["OPTIONS"]["loaders"] = [
        (
            "django.template.loaders.cached.Loader",
            [
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
        )
    ]

# ------------------------------------------------------------------------------
# 认证与用户 (Auth)
# ------------------------------------------------------------------------------
AUTH_USER_MODEL = "users.User"
AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "guardian.backends.ObjectPermissionBackend",
)
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
LOGIN_URL = "users:login"

# ------------------------------------------------------------------------------
# 国际化 (I18N)
# ------------------------------------------------------------------------------
LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

# ------------------------------------------------------------------------------
# 静态资源与媒体 (Static & Media)
# ------------------------------------------------------------------------------
# 1Panel/Nginx 部署关键点：
# 1. Nginx 需配置 location /static/ { alias /path/to/rosetta/static/; }
# 2. Nginx 需配置 location /media/ { alias /path/to/rosetta/media/; }
# 3. 确保容器挂载卷权限正确 (www-data 或 1000:1000)

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)

# 生产环境使用 WhiteNoise (可选，如果不想完全依赖 Nginx 处理静态文件)
# 但通常 1Panel + Nginx 组合直接由 Nginx 处理效率更高。
# 这里保持默认 Storage，假设 Nginx 接管。
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"


# ------------------------------------------------------------------------------
# 安全加固 (Production Security)
# ------------------------------------------------------------------------------
# 默认安全设置
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = "DENY"
REFERRER_POLICY = "same-origin"

if not DEBUG:
    # 生产环境强制 HTTPS
    # 前提：Nginx 配置了 SSL 并且正确转发了 Proto 头
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True

    # Cookie 安全
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # HSTS
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

RATE_LIMIT_ENABLED = env.bool("RATE_LIMIT_ENABLED", default=True)
RATE_LIMIT_RULES = [
    {
        "name": "login",
        "path_prefix": "/users/login/",
        "methods": ["POST"],
        "limit": 5,
        "window": 300,
    },
    {
        "name": "comment",
        "path_prefix": "/post/",
        "methods": ["POST"],
        "limit": 10,
        "window": 300,
    },
]

# ------------------------------------------------------------------------------
# 第三方组件 (Third Party)
# ------------------------------------------------------------------------------
# Tailwind
TAILWIND_APP_NAME = "theme"
NPM_BIN_PATH = env(
    "NPM_BIN_PATH",
    default=r"C:\Program Files\nodejs\npm.cmd" if os.name == "nt" else "npm",
)

# Sites
SITE_ID = 1

# DRF & JWT
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    )
}
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    "UPDATE_LAST_LOGIN": True,
}

# Meta
META_SITE_PROTOCOL = "https" if not DEBUG else "http"
META_SITE_DOMAIN = env("SITE_DOMAIN", default="localhost:8000")
META_USE_OG_PROPERTIES = True
META_USE_TWITTER_PROPERTIES = True

# ------------------------------------------------------------------------------
# Constance 配置定义 (保持不变)
# ------------------------------------------------------------------------------
CONSTANCE_CONFIG = {
    "SITE_NAME": ("Rosetta Blog", "站点名称"),
    "SITE_DESCRIPTION": ("A modern Django blog.", "站点描述"),
    "SITE_KEYWORDS": ("blog, django, python", "SEO 关键词"),
    "SITE_AUTHOR": ("Rosetta", "站点作者"),
    "SITE_EMAIL": ("admin@example.com", "站点联系邮箱"),
    "SHOW_SITE_LOGO": (True, "是否显示站点 Logo"),
    "SITE_LOGO": ("/static/core/img/logo.svg", "站点 Logo URL"),
    "SITE_FAVICON": ("/static/core/img/favicon.ico", "站点 Favicon URL"),
    "SITE_HEADER": ("Rosetta Dashboard", "后台头部标题"),
    "SITE_ADMIN_SUFFIX": (" - Rosetta Dashboard", "后台页面标题后缀"),
    "ADMIN_NAVBAR_TITLE": ("Rosetta 管理后台", "后台导航栏标题"),
    "DASHBOARD_WELCOME_TEXT": (
        "这里是您的站点概览，祝您有美好的一天。",
        "仪表盘欢迎语",
    ),
    "DASHBOARD_WELCOME_WORDS": (
        "['Creator', 'Admin', 'Master', 'Manager']",
        "仪表盘动态欢迎词 (Flip Words)",
    ),
    "FOOTER_TEXT": ("© 2026 Rosetta Blog", "页脚版权文本"),
    "FOOTER_SLOGAN": (
        "分享代码，记录生活。<br/>构建属于你的知识花园。",
        "页脚标语/简介",
    ),
    "BEIAN_CODE": ("", "ICP 备案号"),
    "GITHUB_URL": ("", "GitHub 链接"),
    "X_URL": ("", "X 链接"),
    "BILIBILI_URL": ("", "Bilibili 链接"),
    "CONTACT_EMAIL": ("", "联系邮箱"),
    "SMTP_HOST": ("smtp.qq.com", "SMTP 服务器地址"),
    "SMTP_PORT": (465, "SMTP 端口"),
    "SMTP_USER": ("", "SMTP 用户名"),
    "SMTP_PASSWORD": ("", "SMTP 密码/授权码"),
    "SMTP_USE_TLS": (True, "启用 SSL/TLS 加密"),
    "SMTP_FROM_EMAIL": ("", "默认发件人邮箱"),
    "MAINTENANCE_MODE": (False, "开启维护模式"),
    "ENABLE_COMMENTS": (True, "开启评论功能"),
    "ENABLE_REGISTRATION": (True, "开启用户注册"),
    "ENABLE_EMAIL_NOTIFICATIONS": (False, "开启邮件通知"),
    "EXTRA_HEAD_CODE": ("", "自定义 Head 代码 (CSS/JS)"),
    "EXTRA_FOOTER_CODE": ("", "自定义 Footer 代码 (JS)"),
    "CODE_HIGHLIGHT_STYLE": ("default", "代码高亮风格 (Pygments)"),
    "BLOG_DEFAULT_VIEW_MODE": ("list", "博客文章列表默认视图 (list/grid)"),
}

CONSTANCE_CONFIG_FIELDSETS = {
    "基本设置": (
        "SITE_NAME",
        "SITE_DESCRIPTION",
        "SITE_KEYWORDS",
        "SITE_AUTHOR",
        "SITE_EMAIL",
        "SHOW_SITE_LOGO",
        "SITE_LOGO",
        "SITE_FAVICON",
        "FOOTER_SLOGAN",
        "FOOTER_TEXT",
        "BEIAN_CODE",
    ),
    "外观设置": ("CODE_HIGHLIGHT_STYLE", "BLOG_DEFAULT_VIEW_MODE"),
    "后台界面": (
        "SITE_HEADER",
        "SITE_ADMIN_SUFFIX",
        "ADMIN_NAVBAR_TITLE",
        "DASHBOARD_WELCOME_TEXT",
        "DASHBOARD_WELCOME_WORDS",
    ),
    "社交与联系": ("GITHUB_URL", "X_URL", "BILIBILI_URL", "CONTACT_EMAIL"),
    "邮件服务": (
        "SMTP_HOST",
        "SMTP_PORT",
        "SMTP_USER",
        "SMTP_PASSWORD",
        "SMTP_USE_TLS",
        "SMTP_FROM_EMAIL",
        "ENABLE_EMAIL_NOTIFICATIONS",
    ),
    "功能开关": ("MAINTENANCE_MODE", "ENABLE_COMMENTS", "ENABLE_REGISTRATION"),
    "自定义代码": ("EXTRA_HEAD_CODE", "EXTRA_FOOTER_CODE"),
}

# ------------------------------------------------------------------------------
# 日志系统 (Loguru Integration)
# ------------------------------------------------------------------------------
LOG_DIR = BASE_DIR / "logs"
if not LOG_DIR.exists():
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

# Django Logging 拦截器
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "intercept": {
            "level": "INFO",
            "class": "core.logging.InterceptHandler",
        },
    },
    "loggers": {
        "django": {"handlers": ["intercept"], "level": "INFO", "propagate": True},
        "uvicorn": {"handlers": ["intercept"], "level": "INFO", "propagate": True},
        "uvicorn.access": {
            "handlers": ["intercept"],
            "level": "INFO",
            "propagate": True,
        },
        "django.db.backends": {
            "handlers": ["intercept"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}

# Loguru 配置
from loguru import logger

logger.remove()  # 移除默认
logger.configure(extra={"request_id": "-"})  # 默认 Context

LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level.icon} {level: <8}</level> | "
    "<cyan>{extra[request_id]}</cyan> | "
    "<blue>{name}:{function}:{line}</blue> - "
    "<level>{message}</level>"
)

logger.level("TRACE", icon="🔍")
logger.level("DEBUG", icon="🐛")
logger.level("INFO", icon="ℹ️")
logger.level("SUCCESS", icon="✅")
logger.level("WARNING", icon="⚠️")
logger.level("ERROR", icon="❌")
logger.level("CRITICAL", icon="🚨")

if DEBUG:
    # 开发环境：全彩、详细堆栈
    logger.add(
        sys.stderr,
        level="DEBUG",
        format=LOG_FORMAT,
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )
    logger.add(
        LOG_DIR / "debug.log",
        level="DEBUG",
        format=LOG_FORMAT,
        rotation="50 MB",
        retention="7 days",
    )
else:
    # 生产环境：标准错误输出 (供 Docker 采集)、JSON 文件日志
    logger.add(
        sys.stderr,
        level="INFO",
        format=LOG_FORMAT,
        enqueue=True,
        backtrace=True,
        diagnose=False,
    )
    logger.add(
        LOG_DIR / "rosetta.log",
        rotation="10 MB",
        retention="30 days",
        level="WARNING",
        compression="zip",
        enqueue=True,
        serialize=True,  # JSON 格式，方便 ELK/1Panel 分析
        backtrace=True,
        diagnose=False,
    )

# 邮件后端
EMAIL_BACKEND = "core.backends.ConstanceEmailBackend"
