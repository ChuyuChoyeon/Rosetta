from django.db import models
from django.conf import settings
from django.utils.text import slugify
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill


class Category(models.Model):
    """
    文章分类模型
    用于组织和归档文章，支持slug作为URL友好的标识符。
    """

    name = models.CharField("名称", max_length=100)
    slug = models.SlugField("别名", unique=True, blank=True)
    description = models.TextField("描述", blank=True)

    class Meta:
        verbose_name = "分类"
        verbose_name_plural = verbose_name

    def save(self, *args, **kwargs):
        """保存时自动生成slug（如果未提供）"""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Tag(models.Model):
    """
    文章标签模型
    用于对文章进行灵活标记和分类。
    """
    COLOR_CHOICES = (
        ("primary", "Primary (Indigo)"),
        ("secondary", "Secondary (Pink)"),
        ("accent", "Accent (Cyan)"),
        ("neutral", "Neutral (Grey)"),
        ("info", "Info (Blue)"),
        ("success", "Success (Green)"),
        ("warning", "Warning (Yellow)"),
        ("error", "Error (Red)"),
    )

    name = models.CharField("名称", max_length=100)
    slug = models.SlugField("别名", unique=True, blank=True)
    color = models.CharField("颜色", max_length=20, choices=COLOR_CHOICES, default="neutral")
    is_active = models.BooleanField("是否可见", default=True)

    class Meta:
        verbose_name = "标签"
        verbose_name_plural = verbose_name

    def save(self, *args, **kwargs):
        """保存时自动生成slug（如果未提供）"""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Post(models.Model):
    """
    博客文章核心模型
    包含文章的所有元数据：标题、内容、作者、分类、标签等。
    支持草稿/发布状态控制和密码保护功能。
    """

    STATUS_CHOICES = (
        ("draft", "草稿"),
        ("published", "已发布"),
    )

    title = models.CharField("标题", max_length=200)
    slug = models.SlugField("别名", unique=True, blank=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name="作者",
    )
    content = models.TextField("内容")
    excerpt = models.TextField("摘要", blank=True, max_length=500)
    cover_image = models.ImageField("封面图", upload_to="posts/", blank=True, null=True)

    # ImageKit Thumbnails
    cover_thumbnail = ImageSpecField(
        source="cover_image",
        processors=[ResizeToFill(400, 250)],
        format="JPEG",
        options={"quality": 80},
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name="posts",
        verbose_name="分类",
    )
    tags = models.ManyToManyField(
        Tag, blank=True, related_name="posts", verbose_name="标签"
    )
    status = models.CharField(
        "状态", max_length=10, choices=STATUS_CHOICES, default="draft", db_index=True
    )
    password = models.CharField(
        "访问密码",
        max_length=50,
        blank=True,
        help_text="设置此密码后，访问文章需要输入密码",
    )
    views = models.PositiveIntegerField("阅读量", default=0)
    created_at = models.DateTimeField("创建时间", auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)
    notification_sent = models.BooleanField("已发送通知", default=False, editable=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "文章"
        verbose_name_plural = verbose_name

    def save(self, *args, **kwargs):
        """保存时自动生成slug（如果未提供）"""
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse("post_detail", kwargs={"slug": self.slug})


class Comment(models.Model):
    """
    文章评论模型
    支持多级回复（通过parent字段）。
    """

    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="comments", verbose_name="文章"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="用户"
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
        verbose_name="父评论",
    )
    content = models.TextField("内容")
    created_at = models.DateTimeField("创建时间", auto_now_add=True, db_index=True)
    active = models.BooleanField("是否可见", default=True, db_index=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "评论"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.user.username} 对 {self.post} 的评论"

    @property
    def active_replies(self):
        """获取当前评论下所有可见的回复"""
        return self.replies.filter(active=True)


class PostViewHistory(models.Model):
    """
    用户阅读历史记录模型
    记录用户最近浏览过的文章。
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="view_history",
        verbose_name="用户",
    )
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="view_history", verbose_name="文章"
    )
    viewed_at = models.DateTimeField("浏览时间", auto_now=True)

    class Meta:
        ordering = ["-viewed_at"]
        verbose_name = "浏览历史"
        verbose_name_plural = verbose_name
        unique_together = ("user", "post")

    def __str__(self):
        return f"{self.user.username} 浏览了 {self.post.title}"


import uuid


class Subscriber(models.Model):
    """
    邮件订阅者模型
    用于管理博客的邮件订阅列表。
    """

    email = models.EmailField("邮箱地址", unique=True)
    is_active = models.BooleanField("是否订阅", default=True)
    created_at = models.DateTimeField("订阅时间", auto_now_add=True)
    token = models.UUIDField(default=uuid.uuid4, editable=False)

    class Meta:
        verbose_name = "订阅者"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]

    def __str__(self):
        return self.email
