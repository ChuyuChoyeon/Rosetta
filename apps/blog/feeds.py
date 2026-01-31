from django.contrib.syndication.views import Feed
from django.urls import reverse
from django.utils.feedgenerator import Rss201rev2Feed
from .models import Post


class LatestPostsFeed(Feed):
    """
    最新文章 RSS Feed
    
    生成网站的 RSS 订阅源，返回最新的 20 篇已发布文章。
    遵循 RSS 2.01 规范。
    """
    title = "Rosetta Blog"
    link = "/"
    description = "Latest updates from Rosetta Blog."
    feed_type = Rss201rev2Feed

    def items(self):
        """
        获取 Feed 条目
        
        返回最近发布的 20 篇文章。
        """
        return (
            Post.objects.filter(status="published")
            .order_by("-published_at", "-created_at")[:20]
        )

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        """
        条目描述
        
        优先使用文章摘要，如果未设置则截取正文前 200 字。
        """
        return item.excerpt or item.content[:200]

    def item_link(self, item):
        return reverse("post_detail", args=[item.slug])

    def item_pubdate(self, item):
        return item.published_at or item.created_at
