"""
Rosetta 项目的 URL 配置。
urlpatterns "列表将 URL 路由到视图。更多信息请参阅
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django.views.i18n import JavaScriptCatalog

# 创建应用的站点地图

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('videolist.urls')),
    path('rosetta/', include('rosetta.urls')),
    
    # 多语言支持
    path('i18n/', include('django.conf.urls.i18n')),
    path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),
    
    # 站点地图
    path("__reload__/", include("django_browser_reload.urls")),

]

# 静态文件和媒体文件只在开发环境中由Django处理
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # 添加 Django Debug Toolbar 支持
    try:
        import debug_toolbar
        urlpatterns += [
            path('__debug__/', include(debug_toolbar.urls)),
        ]
    except ImportError:
        pass
