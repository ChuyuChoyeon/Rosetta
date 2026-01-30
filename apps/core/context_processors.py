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

    placeholders = load_cached(
        "site:search_placeholders",
        lambda: list(SearchPlaceholder.objects.filter(is_active=True)),
    )
    if not placeholders:
        placeholders = [_("搜索文章..."), _("搜索标签...")]
    else:
        # Extract text property to trigger modeltranslation fallback/current language logic
        placeholders = [p.text for p in placeholders]

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
