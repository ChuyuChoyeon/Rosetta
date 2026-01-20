from .models import FriendLink, Navigation, SearchPlaceholder
from users.models import UserPreference


def site_settings(request):
    """
    全局上下文处理器 (Context Processor)
    
    向所有模板注入全站通用的配置和数据，避免在每个视图中重复获取。
    
    注入数据:
    - friend_links: 友情链接 (FriendLink)
    - navigations: 导航菜单 (Navigation)
    - themes: 可选的主题列表 (用于主题切换器)
    - search_placeholders: 搜索框占位符文本列表 (用于前端打字机效果)
    """
    # 将元组形式的选项转换为字典列表，方便模板遍历使用
    themes = [
        {"id": code, "name": label} for code, label in UserPreference.THEME_CHOICES
    ]
    
    # 获取启用的搜索占位符
    placeholders = list(SearchPlaceholder.objects.filter(is_active=True).values_list('text', flat=True))
    if not placeholders:
        # 提供默认值，防止数据库为空时前端效果失效
        placeholders = ["搜索文章...", "搜索标签..."]

    return {
        "friend_links": FriendLink.objects.filter(is_active=True),
        "navigations": Navigation.objects.filter(is_active=True),
        "themes": themes,
        "search_placeholders": placeholders,
    }
