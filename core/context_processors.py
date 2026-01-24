from .models import FriendLink, Navigation, SearchPlaceholder
from users.models import UserPreference
from constance import config


def site_settings(request):
    """
    全局上下文处理器 (Context Processor)
    """
    # 将元组形式的选项转换为字典列表，方便模板遍历使用
    themes = [
        {"id": code, "name": label} for code, label in UserPreference.THEME_CHOICES
    ]

    # 获取启用的搜索占位符
    placeholders = list(
        SearchPlaceholder.objects.filter(is_active=True).values_list("text", flat=True)
    )
    if not placeholders:
        # 提供默认值，防止数据库为空时前端效果失效
        placeholders = ["搜索文章...", "搜索标签..."]

    return {
        "friend_links": FriendLink.objects.filter(is_active=True),
        "navigations": Navigation.objects.filter(is_active=True),
        "themes": themes,
        "search_placeholders": placeholders,
        "config": config,
    }
