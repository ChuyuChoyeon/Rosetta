from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# ==============================================================================
# 全局 URL 路由配置
# ==============================================================================

urlpatterns = [
    # --- 管理后台 ---
    path("admin/", include("administration.urls")), # 自定义管理后台
    
    # --- 用户认证 ---
    path("users/", include("users.urls")),          # 用户登录、注册、个人中心
    
    # --- 功能组件 ---
    path("captcha/", include("captcha.urls")),      # 验证码
    
    # --- 核心与博客应用 ---
    path("", include("core.urls")),                 # 首页、关于页等核心页面
    path("", include("blog.urls")),                 # 博客文章、分类、标签
    
    # --- 站点地图 (SEO) ---
    path("sitemap.xml", include("core.sitemaps")),  # sitemap.xml
]

# ==============================================================================
# 开发环境辅助配置
# ==============================================================================

if settings.DEBUG:
    from django.shortcuts import render

    urlpatterns += [
        # 浏览器自动刷新
        path("__reload__/", include("django_browser_reload.urls")),
        
        # --- 错误页面测试 ---
        path("test/404/", lambda request: render(request, "404.html")),
        path("test/403/", lambda request: render(request, "403.html")),
        path("test/500/", lambda request: render(request, "500.html")),
        path("test/502/", lambda request: render(request, "502.html")),
        path("test/400/", lambda request: render(request, "400.html")),
        path("test/403_csrf/", lambda request: render(request, "403_csrf.html")),
    ]
    
    # 静态文件与媒体文件服务 (仅开发环境)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
