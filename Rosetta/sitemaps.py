from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from blog.models import BlogPage
from videolist.models import VideoSite

class BlogSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return BlogPage.objects.live()

    def lastmod(self, obj):
        return obj.last_published_at

    def location(self, obj):
        return f"/blog/post/{obj.slug}/"

class VideoSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return VideoSite.objects.filter(is_invalid=False)

    def lastmod(self, obj):
        return obj.update_time

    def location(self, obj):
        return f"/vl/site/{obj.id}/"

class StaticSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5

    def items(self):
        return ['home:index', 'blog:index', 'videolist:index', 'videolist:sitemap']

    def location(self, item):
        if item == 'home:index':
            return reverse(item)
        elif item == 'blog:index':
            return '/blog/'
        elif item == 'videolist:index':
            return '/vl/'
        elif item == 'videolist:sitemap':
            return '/vl/sitemap/'
        return reverse(item)
