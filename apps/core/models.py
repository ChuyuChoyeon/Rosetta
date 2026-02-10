from django.db import models
from django.conf import settings
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from core.utils import generate_unique_slug


"""
核心数据模型 (Core Models)

本模块定义了网站运行所需的基础数据模型，包括：
- Page: 单页面（关于、联系我们等）
- Navigation: 导航菜单配置
- FriendLink: 友情链接
- SearchPlaceholder: 搜索框动态占位符
- Notification: 用户站内通知
"""


class Page(models.Model):
    """
    单页面模型 (Page)

    用于创建那些不属于博客文章流的独立页面，例如“关于我”、“联系页面”、“隐私政策”等。
    支持自定义 URL 别名 (slug) 和 Markdown 内容。
    """

    STATUS_CHOICES = (
        ("draft", _("草稿")),
        ("published", _("已发布")),
    )

    title = models.CharField(_("标题"), max_length=200)
    slug = models.SlugField(
        _("别名"),
        unique=True,
        help_text=_("URL 路径的一部分，例如 about 或 contact，留空将自动根据标题生成"),
    )
    content = models.TextField(_("内容"), help_text=_("支持 Markdown 格式"))
    status = models.CharField(
        _("状态"),
        max_length=10,
        choices=STATUS_CHOICES,
        default="published",
        help_text=_("控制页面是否对外可见"),
    )
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)

    class Meta:
        verbose_name = _("页面")
        verbose_name_plural = verbose_name

    def save(self, *args, **kwargs):
        """
        重写 save 方法以自动处理 Slug。
        如果用户未填写 Slug，则根据标题自动生成唯一的 Slug。
        """
        if not self.slug:
            self.slug = generate_unique_slug(Page, self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class SearchPlaceholder(models.Model):
    """
    搜索框占位符模型 (Search Placeholder)

    用于在前端搜索框中展示动态的提示文字（如“搜索 Django 教程...”）。
    可以在后台配置多条记录，系统会随机或按权重显示，引导用户搜索。
    """

    text = models.CharField(
        _("占位符文本"), max_length=100, help_text=_("例如：搜索 Django...")
    )
    is_active = models.BooleanField(_("是否启用"), default=True)
    order = models.IntegerField(_("排序"), default=0, help_text=_("数字越小越靠前"))
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)

    class Meta:
        verbose_name = _("搜索占位符")
        verbose_name_plural = verbose_name
        ordering = ["order", "-created_at"]

    def __str__(self):
        return self.text


class FriendLink(models.Model):
    """
    友情链接模型 (Friend Link)

    用于管理与其他网站的互换链接。通常显示在页脚或侧边栏。
    """

    name = models.CharField(_("网站名称"), max_length=100)
    url = models.URLField(_("网站链接"))
    description = models.CharField(_("描述"), max_length=200, blank=True)
    logo = models.ImageField(
        _("标志"), upload_to="friend_links/", blank=True, null=True
    )
    order = models.IntegerField(_("排序"), default=0, help_text=_("数字越小越靠前"))
    is_active = models.BooleanField(_("是否显示"), default=True)
    target_blank = models.BooleanField(
        _("新窗口打开"), default=False, help_text=_("是否在新标签页中打开链接")
    )

    class Meta:
        verbose_name = _("友情链接")
        verbose_name_plural = verbose_name
        ordering = ["order", "id"]

    def __str__(self):
        return self.name


class Navigation(models.Model):
    """
    导航菜单模型 (Navigation)

    用于动态管理全站的菜单链接，无需修改代码即可调整菜单结构。
    支持配置显示位置（顶部、底部、侧边栏）。
    """

    LOCATION_CHOICES = (
        ("header", _("顶部导航")),
        ("footer", _("底部链接")),
        ("sidebar", _("侧边栏")),
    )

    title = models.CharField(_("标题"), max_length=100)
    url = models.CharField(
        "URL", max_length=200, help_text=_("可以是绝对路径或相对路径")
    )
    location = models.CharField(
        _("位置"), max_length=20, choices=LOCATION_CHOICES, default="header"
    )
    order = models.IntegerField(_("排序"), default=0, help_text=_("数字越小越靠前"))
    is_active = models.BooleanField(_("是否显示"), default=True)
    target_blank = models.BooleanField(
        _("新窗口打开"), default=False, help_text=_("是否在新标签页中打开链接")
    )

    class Meta:
        ordering = ["order"]
        verbose_name = _("导航菜单")
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.title


class Notification(models.Model):
    """
    系统通知模型 (Notification)

    用于向用户发送各类消息提醒，如评论回复、系统公告等。
    """

    LEVEL_CHOICES = (
        ("info", _("信息")),
        ("success", _("成功")),
        ("warning", _("警告")),
        ("error", _("错误")),
    )

    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        verbose_name=_("用户"),
        related_name="notifications",
        help_text=_("接收通知的用户"),
    )
    title = models.CharField(_("标题"), max_length=255)
    message = models.TextField(_("内容"))
    level = models.CharField(
        _("级别"), max_length=20, choices=LEVEL_CHOICES, default="info"
    )
    is_read = models.BooleanField(_("已读"), default=False)
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    link = models.CharField(
        _("链接"),
        max_length=255,
        blank=True,
        null=True,
        help_text=_("可选，点击通知跳转的 URL，例如评论所在的文章地址"),
    )

    class Meta:
        verbose_name = _("通知")
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Media(models.Model):
    """
    媒体资源模型 (Media)

    集中管理全站上传的图片、视频、文档等资源。
    支持元数据管理 (Alt, Title) 以优化 SEO。
    """

    FILE_TYPE_CHOICES = (
        ("image", _("图片")),
        ("video", _("视频")),
        ("audio", _("音频")),
        ("document", _("文档")),
        ("other", _("其他")),
    )

    file = models.FileField(_("文件"), upload_to="uploads/%Y/%m/")
    filename = models.CharField(_("文件名"), max_length=255, blank=True)
    file_type = models.CharField(
        _("类型"), max_length=20, choices=FILE_TYPE_CHOICES, default="other"
    )
    file_size = models.PositiveIntegerField(_("大小(字节)"), default=0)

    # Metadata for SEO
    title = models.CharField(
        _("标题"), max_length=255, blank=True, help_text=_("用于图片的 title 属性")
    )
    alt_text = models.CharField(
        _("替代文本"),
        max_length=255,
        blank=True,
        help_text=_("用于图片的 alt 属性，对 SEO 至关重要"),
    )
    description = models.TextField(_("描述"), blank=True)

    uploaded_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("上传者"),
        related_name="media_uploads",
    )
    created_at = models.DateTimeField(_("上传时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)

    class Meta:
        verbose_name = _("媒体资源")
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]

    def __str__(self):
        return self.filename or self.file.name

    def save(self, *args, **kwargs):
        """
        自动填充文件元数据
        """
        if self.file:
            if not self.filename:
                self.filename = self.file.name.split("/")[-1]
            if not self.file_size and self.file.storage.exists(self.file.name):
                try:
                    self.file_size = self.file.size
                except Exception:
                    pass

            # Simple MIME type detection based on extension
            if not self.file_type or self.file_type == "other":
                ext = self.filename.split(".")[-1].lower()
                if ext in ["jpg", "jpeg", "png", "gif", "webp", "svg", "bmp"]:
                    self.file_type = "image"
                elif ext in ["mp4", "webm", "ogg", "mov"]:
                    self.file_type = "video"
                elif ext in ["mp3", "wav", "flac"]:
                    self.file_type = "audio"
                elif ext in [
                    "pdf",
                    "doc",
                    "docx",
                    "xls",
                    "xlsx",
                    "ppt",
                    "pptx",
                    "txt",
                    "md",
                ]:
                    self.file_type = "document"

        super().save(*args, **kwargs)

    @property
    def url(self):
        return self.file.url


def _clear_site_cache():
    """
    辅助函数：清除全站相关的缓存。

    当导航、友链等基础数据发生变更时调用，确保前台显示最新数据。
    """
    # 清除字典型缓存
    cache.delete("site:friend_links")
    cache.delete("site:navigations")
    cache.delete("site:search_placeholders")

    # 清除模板片段缓存 (Template Fragment Cache)
    # 因为侧边栏等位置可能使用了 {% cache %} 标签，需要手动清除
    languages = [l[0] for l in settings.LANGUAGES]
    for lang in languages:
        cache.delete(make_template_fragment_key("sidebar_friend_links", [lang]))
        cache.delete(make_template_fragment_key("sidebar_search", [lang]))


@receiver([post_save, post_delete], sender=FriendLink)
def _invalidate_friendlink_cache(sender, instance, **kwargs):
    """
    信号接收器：FriendLink 变动时清除缓存。
    """
    _clear_site_cache()


@receiver([post_save, post_delete], sender=Navigation)
def _invalidate_navigation_cache(sender, instance, **kwargs):
    """
    信号接收器：Navigation 变动时清除缓存。
    """
    _clear_site_cache()


@receiver([post_save, post_delete], sender=SearchPlaceholder)
def _invalidate_searchplaceholder_cache(sender, instance, **kwargs):
    """
    信号接收器：SearchPlaceholder 变动时清除缓存。
    """
    _clear_site_cache()
