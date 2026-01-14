from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", include("administration.urls")),
    path("users/", include("users.urls")),
    path("captcha/", include("captcha.urls")),
    path("", include("core.urls")),
    path("", include("blog.urls")),
    path("sitemap.xml", include("core.sitemaps")),
]

if settings.DEBUG:
    from django.shortcuts import render

    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
        path("test/404/", lambda request: render(request, "404.html")),
        path("test/403/", lambda request: render(request, "403.html")),
        path("test/500/", lambda request: render(request, "500.html")),
        path("test/502/", lambda request: render(request, "502.html")),
        path("test/400/", lambda request: render(request, "400.html")),
        path("test/403_csrf/", lambda request: render(request, "403_csrf.html")),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
