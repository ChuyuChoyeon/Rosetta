from django.contrib import sitemaps
from django.urls import reverse
from blog.models import Post, Category, Tag


class PostSitemap(sitemaps.Sitemap):
    changefreq = "weekly"
    priority = 0.8
    i18n = True

    def items(self):
        return Post.objects.filter(status="published")

    def lastmod(self, obj):
        return obj.updated_at


class CategorySitemap(sitemaps.Sitemap):
    changefreq = "weekly"
    priority = 0.6
    i18n = True

    def items(self):
        return Category.objects.all()

    def location(self, obj):
        return reverse("post_by_category", kwargs={"slug": obj.slug})


class TagSitemap(sitemaps.Sitemap):
    changefreq = "weekly"
    priority = 0.6
    i18n = True

    def items(self):
        return Tag.objects.filter(is_active=True)

    def location(self, obj):
        return reverse("post_by_tag", kwargs={"slug": obj.slug})


class StaticViewSitemap(sitemaps.Sitemap):
    priority = 0.5
    changefreq = "daily"
    i18n = True

    def items(self):
        return [
            "home",
            "about",
            "contact",
            "users:login",
            "users:register",
            "category_list",
            "tag_list",
            "archive",
        ]

    def location(self, item):
        return reverse(item)


# URL patterns for sitemap
from django.contrib.sitemaps.views import sitemap
from django.urls import path

sitemaps = {
    "posts": PostSitemap,
    "categories": CategorySitemap,
    "tags": TagSitemap,
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
