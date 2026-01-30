from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from core.utils import generate_unique_slug


class Page(models.Model):
    """
    单页面模型
    用于创建关于页、联系页等独立页面，不属于博客文章流。
    """

    STATUS_CHOICES = (
        ("draft", _("草稿")),
        ("published", _("已发布")),
    )
    title = models.CharField(_("标题"), max_length=200)
    slug = models.SlugField(
        _("别名"), unique=True, help_text=_("URL 路径的一部分，例如 about 或 contact")
    )
    content = models.TextField(_("内容"))
    status = models.CharField(
        _("状态"), max_length=10, choices=STATUS_CHOICES, default="published"
    )
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)

    class Meta:
        verbose_name = _("页面")
        verbose_name_plural = verbose_name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(Page, self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class SearchPlaceholder(models.Model):
    """
    搜索框占位符模型
    用于管理前台搜索框的动态占位符文字。
    """

    text = models.CharField(
        _("占位符文本"), max_length=100, help_text=_("例如：搜索 Django...")
    )
    is_active = models.BooleanField(_("是否启用"), default=True)
    order = models.IntegerField(_("排序"), default=0)
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)

    class Meta:
        verbose_name = _("搜索占位符")
        verbose_name_plural = verbose_name
        ordering = ["order", "-created_at"]

    def __str__(self):
        return self.text


class FriendLink(models.Model):
    """
    友情链接模型
    用于在页脚或侧边栏显示合作伙伴链接。
    """

    name = models.CharField(_("网站名称"), max_length=100)
    url = models.URLField(_("网站链接"))
    description = models.CharField(_("描述"), max_length=200, blank=True)
    logo = models.ImageField(_("标志"), upload_to="friend_links/", blank=True, null=True)
    order = models.IntegerField(_("排序"), default=0)
    is_active = models.BooleanField(_("是否显示"), default=True)
    target_blank = models.BooleanField(_("新窗口打开"), default=False)

    class Meta:
        verbose_name = _("友情链接")
        verbose_name_plural = verbose_name
        ordering = ["order", "id"]

    def __str__(self):
        return self.name


class Navigation(models.Model):
    """
    导航菜单模型
    用于动态管理网站头部导航栏、底部链接等。
    """

    LOCATION_CHOICES = (
        ("header", _("顶部导航")),
        ("footer", _("底部链接")),
        ("sidebar", _("侧边栏")),
    )
    title = models.CharField(_("标题"), max_length=100)
    url = models.CharField("URL", max_length=200)
    location = models.CharField(
        _("位置"), max_length=20, choices=LOCATION_CHOICES, default="header"
    )
    order = models.IntegerField(_("排序"), default=0)
    is_active = models.BooleanField(_("是否显示"), default=True)
    target_blank = models.BooleanField(_("新窗口打开"), default=False)

    class Meta:
        ordering = ["order"]
        verbose_name = _("导航菜单")
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.title


class Notification(models.Model):
    """
    系统通知模型
    用于向用户发送站内消息（评论回复、提及、系统通知等）。
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
        help_text=_("可选，点击通知跳转的 URL"),
    )

    class Meta:
        verbose_name = _("通知")
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


def _clear_site_cache():
    cache.delete("site:friend_links")
    cache.delete("site:navigations")
    cache.delete("site:search_placeholders")
    
    languages = [l[0] for l in settings.LANGUAGES]
    for lang in languages:
        cache.delete(make_template_fragment_key("sidebar_friend_links", [lang]))
        cache.delete(make_template_fragment_key("sidebar_search", [lang]))


@receiver([post_save, post_delete], sender=FriendLink)
def _invalidate_friendlink_cache(sender, instance, **kwargs):
    _clear_site_cache()


@receiver([post_save, post_delete], sender=Navigation)
def _invalidate_navigation_cache(sender, instance, **kwargs):
    _clear_site_cache()


@receiver([post_save, post_delete], sender=SearchPlaceholder)
def _invalidate_searchplaceholder_cache(sender, instance, **kwargs):
    _clear_site_cache()
