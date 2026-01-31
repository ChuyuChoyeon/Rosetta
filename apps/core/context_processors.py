from django.conf import settings
from django.core.cache import cache
from .models import FriendLink, Navigation, SearchPlaceholder
from users.models import UserPreference
from constance import config
from django.utils.translation import gettext_lazy as _


def site_settings(request):
    """
    全局上下文处理器 (Context Processor)
    """
    # 将元组形式的选项转换为字典列表，方便模板遍历使用
    themes = [
        {"id": code, "name": label} for code, label in UserPreference.THEME_CHOICES
    ]

    ttl = getattr(settings, "SITE_SETTINGS_CACHE_TTL", 300)

    def load_cached(key, builder):
        data = cache.get(key)
        if data is None:
            data = builder()
            cache.set(key, data, ttl)
        return data

    def get_search_placeholders():
        # 1. 优先使用 SearchPlaceholder
        phs = list(SearchPlaceholder.objects.filter(is_active=True))
        if phs:
            return phs

        # 2. 回退到热门/随机标签 (Tags)
        try:
            from blog.models import Tag
            # 随机获取 5 个标签作为占位符
            tags = list(Tag.objects.filter(is_active=True).order_by('?')[:5])
            if tags:
                return tags
        except ImportError:
            pass
        return []

    cached_data = load_cached("site:search_placeholders_v2", get_search_placeholders)

    placeholders = []
    if cached_data:
        # 判断数据类型并提取文本
        first_item = cached_data[0]
        if hasattr(first_item, "text"):  # SearchPlaceholder
            placeholders = [p.text for p in cached_data]
        elif hasattr(first_item, "name"):  # Tag
            # 格式化: "搜索 <标签名>..."
            prefix = _("搜索 {}...")
            placeholders = [str(prefix).format(tag.name) for tag in cached_data]

    if not placeholders:
        placeholders = [_("搜索文章..."), _("搜索标签...")]

    def build_navigations():
        navs = Navigation.objects.filter(is_active=True).order_by("order")
        return {
            "header": [n for n in navs if n.location == "header"],
            "footer": [n for n in navs if n.location == "footer"],
            "sidebar": [n for n in navs if n.location == "sidebar"],
        }

    navigations = load_cached("site:navigations_dict", build_navigations)

    return {
        "friend_links": load_cached(
            "site:friend_links",
            lambda: list(FriendLink.objects.filter(is_active=True)),
        ),
        "nav_header": navigations["header"],
        "nav_footer": navigations["footer"],
        "nav_sidebar": navigations["sidebar"],
        "themes": themes,
        "search_placeholders": placeholders,
        "config": config,
    }
