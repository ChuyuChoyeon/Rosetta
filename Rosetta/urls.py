"""
Rosetta 全局 URL 路由配置。

负责将 URL 请求分发到各个应用和视图函数。
包含管理后台、用户认证、核心业务逻辑及开发环境辅助工具的路由定义。
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# ------------------------------------------------------------------------------
# 核心业务路由
# ------------------------------------------------------------------------------
urlpatterns = [
    # --- 管理后台 ---
    path(
        "admin/", include("administration.urls")
    ),  # 自定义管理后台，提供增强的仪表盘和功能
    # --- 用户系统 ---
    path("users/", include("users.urls")),  # 登录、注册、个人资料管理
    # --- 功能组件 ---
    path("captcha/", include("captcha.urls")),  # 图形验证码生成与校验
    path("voting/", include("voting.urls")),  # 投票系统
    path("guestbook/", include("guestbook.urls")),  # 留言板
    # --- 核心业务 ---
    # 注意：core 和 blog 的路由包含空路径 ""，应放在特定前缀路由之后
    path("", include("core.urls")),  # 首页、静态页、通用功能
    path("", include("blog.urls")),  # 博客文章、分类、标签检索
    # --- SEO 支持 ---
    path("sitemap.xml", include("core.sitemaps")),  # 站点地图索引
]


# ------------------------------------------------------------------------------
# 开发环境辅助路由 (仅在 DEBUG=True 时生效)
# ------------------------------------------------------------------------------
if settings.DEBUG:
    from django.shortcuts import render

    urlpatterns += [
        # 浏览器自动刷新工具 (django-browser-reload)
        path("__reload__/", include("django_browser_reload.urls")),
        # --- 错误页面预览 ---
        # 方便在开发环境下直接查看错误页面的样式
        path("test/404/", lambda request: render(request, "404.html")),
        path("test/403/", lambda request: render(request, "403.html")),
        path("test/500/", lambda request: render(request, "500.html")),
        path("test/502/", lambda request: render(request, "502.html")),
        path("test/400/", lambda request: render(request, "400.html")),
        path("test/403_csrf/", lambda request: render(request, "403_csrf.html")),
    ]

    # 本地静态文件与媒体文件服务
    # 生产环境通常由 Nginx 或 WhiteNoise 处理
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
