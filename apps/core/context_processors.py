from django.conf import settings
from django.core.cache import cache
from .models import FriendLink, Navigation, SearchPlaceholder
from users.models import UserPreference
from constance import config
from django.utils.translation import gettext_lazy as _

"""
全局上下文处理器 (Context Processors)

该模块定义了在所有 Django 模板中全局可用的变量。
主要用于注入全站通用的配置、导航菜单、友情链接以及个性化设置（如主题）。
"""


def site_settings(request):
    """
    注入全站通用的上下文变量。

    该函数会被 Django 的模板引擎自动调用（需在 settings.TEMPLATES 中配置）。
    它负责加载并缓存导航菜单、友情链接、搜索框占位符等高频访问的数据，
    以减少数据库查询次数，提升页面渲染性能。

    返回:
        dict: 包含全站配置信息的字典，可在任何模板中直接使用。
    """
    # 将用户偏好设置中的主题选项元组转换为字典列表
    # 这样在前端模板中遍历生成下拉菜单时会更加方便
    themes = [
        {"id": code, "name": label} for code, label in UserPreference.THEME_CHOICES
    ]

    # 从设置中获取缓存过期时间，默认为 300 秒（5分钟）
    # 对于这些不经常变动的数据，使用缓存可以显著降低数据库压力
    ttl = getattr(settings, "SITE_SETTINGS_CACHE_TTL", 300)

    def load_cached(key, builder):
        """
        辅助函数：尝试从缓存读取数据，如果未命中则执行构建函数并写入缓存。
        """
        data = cache.get(key)
        if data is None:
            data = builder()
            cache.set(key, data, ttl)
        return data

    def get_search_placeholders():
        """
        获取搜索框的动态占位符文本。
        策略：
        1. 优先使用后台手动配置的 SearchPlaceholder。
        2. 如果没有手动配置，则随机选取 5 个活跃的标签作为候补。
        3. 如果连标签都没有，返回空列表。
        """
        # 1. 尝试查询后台配置的固定占位符
        phs = list(SearchPlaceholder.objects.filter(is_active=True))
        if phs:
            return phs

        # 2. 回退方案：使用热门或随机标签
        try:
            from blog.models import Tag

            # 使用 order_by('?') 随机打乱，取前 5 个
            # 注意：数据量极大时 order_by('?') 可能会有性能问题，但对于标签表通常可以接受
            tags = list(Tag.objects.filter(is_active=True).order_by("?")[:5])
            if tags:
                return tags
        except ImportError:
            # 避免循环导入或应用未安装的情况
            pass
        return []

    # 缓存搜索占位符数据，避免每次请求都去查数据库
    cached_data = load_cached("site:search_placeholders_v2", get_search_placeholders)

    placeholders = []
    if cached_data:
        # 这里的 cached_data 可能是 SearchPlaceholder 对象列表，也可能是 Tag 对象列表
        # 我们需要统一提取出展示用的文本
        first_item = cached_data[0]
        if hasattr(first_item, "text"):  # 如果是 SearchPlaceholder 模型
            placeholders = [p.text for p in cached_data]
        elif hasattr(first_item, "name"):  # 如果是 Tag 模型
            # 格式化为提示语，例如 "搜索 Python..."
            prefix = _("搜索 {}...")
            placeholders = [str(prefix).format(tag.name) for tag in cached_data]

    # 3. 兜底方案：如果上述两者都为空，使用硬编码的默认提示
    if not placeholders:
        placeholders = [_("搜索文章..."), _("搜索标签...")]

    def build_navigations():
        """
        构建导航菜单字典。
        将所有启用的导航项按位置（顶部、底部、侧边栏）分类。
        """
        navs = Navigation.objects.filter(is_active=True).order_by("order")
        return {
            "header": [n for n in navs if n.location == "header"],
            "footer": [n for n in navs if n.location == "footer"],
            "sidebar": [n for n in navs if n.location == "sidebar"],
        }

    # 缓存导航菜单数据
    navigations = load_cached("site:navigations_dict", build_navigations)

    # 返回最终的上下文数据
    return {
        # 友情链接：同样使用缓存机制
        "friend_links": load_cached(
            "site:friend_links",
            lambda: list(FriendLink.objects.filter(is_active=True)),
        ),
        "nav_header": navigations["header"],
        "nav_footer": navigations["footer"],
        "nav_sidebar": navigations["sidebar"],
        "themes": themes,
        "search_placeholders": placeholders,
        "config": config,  # 注入 Constance 动态配置对象
    }
