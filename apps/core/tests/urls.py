from django.urls import path, include
from django.shortcuts import render

try:
    from Rosetta.urls import urlpatterns as base_urlpatterns
except ImportError:
    from rosetta.urls import urlpatterns as base_urlpatterns

urlpatterns = base_urlpatterns + [
    path("test/404/", lambda request: render(request, "404.html")),
    path("test/403/", lambda request: render(request, "403.html")),
    path("test/500/", lambda request: render(request, "500.html")),
    path("test/502/", lambda request: render(request, "502.html")),
    path("test/400/", lambda request: render(request, "400.html")),
    path("test/403_csrf/", lambda request: render(request, "403_csrf.html")),
]
