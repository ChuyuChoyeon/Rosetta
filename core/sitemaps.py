from django.contrib import sitemaps
from django.urls import reverse
from blog.models import Post


class PostSitemap(sitemaps.Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Post.objects.filter(status="published")

    def lastmod(self, obj):
        return obj.updated_at


class StaticViewSitemap(sitemaps.Sitemap):
    priority = 0.5
    changefreq = "daily"

    def items(self):
        return ["home", "about", "contact", "users:login", "users:register"]

    def location(self, item):
        return reverse(item)


# URL patterns for sitemap
from django.contrib.sitemaps.views import sitemap
from django.urls import path

sitemaps = {
    "posts": PostSitemap,
    "static": StaticViewSitemap,
}

urlpatterns = [
    path(
        "",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    )
]
