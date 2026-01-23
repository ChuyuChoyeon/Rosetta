from django.contrib.syndication.views import Feed
from django.urls import reverse
from django.utils.feedgenerator import Rss201rev2Feed
from .models import Post

class LatestPostsFeed(Feed):
    title = "Rosetta Blog"
    link = "/"
    description = "Latest updates from Rosetta Blog."
    feed_type = Rss201rev2Feed

    def items(self):
        return Post.objects.filter(status='published').order_by('-created_at')[:20]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.excerpt or item.content[:200]

    def item_link(self, item):
        return reverse('post_detail', args=[item.slug])

    def item_pubdate(self, item):
        return item.created_at
