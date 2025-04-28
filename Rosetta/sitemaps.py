from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from videolist.models import VideoSite


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
        return ['home:index', 'videolist:index', 'videolist:sitemap']

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
