"""
Rosetta 项目的 URL 配置。
urlpatterns "列表将 URL 路由到视图。更多信息请参阅
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
示例：
功能视图
    1.添加导入：from my_app import views
    2.在 urlpatterns 中添加 URL： path('', views.home, name='home')
基于类的视图
    1.添加导入：from other_app.views import Home
    2.在 urlpatterns 中添加 URL： path('', Home.as_view(), name='home')
包含另一个 URLconf
    1.导入 include() 函数： from django.urls import include, path
    2.在 urlpatterns 中添加 URL： path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django.urls import re_path
from django.contrib.sitemaps.views import sitemap
from django.views.i18n import JavaScriptCatalog
from .sitemaps import VideoSitemap, StaticSitemap

# 创建应用的站点地图
sitemaps = {
    'video_sites': VideoSitemap,
    'static': StaticSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home.urls', namespace='home')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('vl/', include('videolist.urls')),
    path('rosetta/', include('rosetta.urls')),
    
    # 多语言支持
    path('i18n/', include('django.conf.urls.i18n')),
    path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),
    
    # 站点地图
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
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
