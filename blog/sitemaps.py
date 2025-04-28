from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import BlogPage, BlogCategory

class BlogPageSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return BlogPage.objects.live().order_by('-first_published_at')

    def lastmod(self, obj):
        return obj.last_published_at

    def location(self, obj):
        return obj.get_absolute_url()

class BlogCategorySitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.6

    def items(self):
        return BlogCategory.objects.all()

    def location(self, obj):
        return reverse('blog:category', kwargs={'slug': obj.slug})

class BlogStaticSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5

    def items(self):
        return ['blog:index', 'blog:search', 'blog:archive']

    def location(self, item):
        return reverse(item)
