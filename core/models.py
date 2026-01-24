from django.db import models
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from core.utils import generate_unique_slug


class Page(models.Model):
    """
    单页面模型
    用于创建关于页、联系页等独立页面，不属于博客文章流。
    """

    STATUS_CHOICES = (
        ("draft", "草稿"),
        ("published", "已发布"),
    )
    title = models.CharField("标题", max_length=200)
    slug = models.SlugField(
        "别名", unique=True, help_text="URL 路径的一部分，例如 about 或 contact"
    )
    content = models.TextField("内容")
    status = models.CharField(
        "状态", max_length=10, choices=STATUS_CHOICES, default="published"
    )
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "页面"
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
        "占位符文本", max_length=100, help_text="例如：搜索 Django..."
    )
    is_active = models.BooleanField("是否启用", default=True)
    order = models.IntegerField("排序", default=0)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "搜索占位符"
        verbose_name_plural = verbose_name
        ordering = ["order", "-created_at"]

    def __str__(self):
        return self.text


class FriendLink(models.Model):
    """
    友情链接模型
    用于在页脚或侧边栏显示合作伙伴链接。
    """

    name = models.CharField("网站名称", max_length=100)
    url = models.URLField("网站链接")
    description = models.CharField("描述", max_length=200, blank=True)
    logo = models.ImageField("标志", upload_to="friend_links/", blank=True, null=True)
    order = models.IntegerField("排序", default=0)
    is_active = models.BooleanField("是否显示", default=True)

    class Meta:
        verbose_name = "友情链接"
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
        ("header", "顶部导航"),
        ("footer", "底部链接"),
        ("sidebar", "侧边栏"),
    )
    title = models.CharField("标题", max_length=100)
    url = models.CharField("URL", max_length=200)
    location = models.CharField(
        "位置", max_length=20, choices=LOCATION_CHOICES, default="header"
    )
    order = models.IntegerField("排序", default=0)
    is_active = models.BooleanField("是否显示", default=True)

    class Meta:
        ordering = ["order"]
        verbose_name = "导航菜单"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.title


class Notification(models.Model):
    """
    系统通知模型
    用于向用户发送站内消息（评论回复、提及、系统通知等）。
    """

    LEVEL_CHOICES = (
        ("info", "信息"),
        ("success", "成功"),
        ("warning", "警告"),
        ("error", "错误"),
    )
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        verbose_name="用户",
        related_name="notifications",
    )
    title = models.CharField("标题", max_length=255)
    message = models.TextField("内容")
    level = models.CharField(
        "级别", max_length=20, choices=LEVEL_CHOICES, default="info"
    )
    is_read = models.BooleanField("已读", default=False)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    link = models.CharField(
        "链接",
        max_length=255,
        blank=True,
        null=True,
        help_text="可选，点击通知跳转的 URL",
    )

    class Meta:
        verbose_name = "通知"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
