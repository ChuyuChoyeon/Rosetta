"""
URL configuration for Rosetta project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from django.conf.urls.static import static
from django.conf import settings
from wagtail.admin import urls as wagtailadmin_urls
from wagtail import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls
from django.contrib.sitemaps.views import sitemap
from .sitemaps import BlogSitemap, VideoSitemap, StaticSitemap

sitemaps = {
    'blog': BlogSitemap,
    'videos': VideoSitemap,
    'static': StaticSitemap,
}

urlpatterns = [
    path('cms/', include(wagtailadmin_urls)),
    path('documents/', include(wagtaildocs_urls)),
    path('pages/', include(wagtail_urls)),
    path('admin/', admin.site.urls),
    path('',  include("home.urls")),
    path('vl/',  include("videolist.urls")),
    path('blog/',  include("blog.urls")),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
