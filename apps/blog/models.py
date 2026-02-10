from django.db import models
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from core.utils import generate_unique_slug, schedule_post_image_processing
from core.validators import validate_image_file
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill, ResizeToFit
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import re
import math


class Category(models.Model):
    """
    文章分类模型
    用于组织和归档文章，支持 slug 作为 URL 友好的标识符。
    """

    name = models.CharField(_("名称"), max_length=100)
    slug = models.SlugField(_("别名"), unique=True, blank=True)
    description = models.TextField(_("描述"), blank=True)
    icon = models.CharField(
        _("图标"),
        max_length=50,
        blank=True,
        default="",
        help_text=_("Material Symbols 图标代码"),
    )
    color = models.CharField(
        _("颜色"),
        max_length=20,
        default="primary",
        help_text=_("Tailwind 颜色类名 (如 primary, secondary)"),
    )
    cover_image = models.ImageField(
        _("封面图"),
        upload_to="categories/",
        blank=True,
        null=True,
        validators=[validate_image_file],
    )

    # ImageKit 缩略图
    cover_thumbnail = ImageSpecField(
        source="cover_image",
        processors=[ResizeToFill(200, 50)],
        format="WEBP",
        options={"quality": 80},
    )

    cover_optimized = ImageSpecField(
        source="cover_image",
        processors=[ResizeToFill(800, 200)],
        format="WEBP",
        options={"quality": 85},
    )

    class Meta:
        verbose_name = _("分类")
        verbose_name_plural = verbose_name

    def save(self, *args, **kwargs):
        """保存时自动生成 slug（如果未提供）"""
        if not self.slug:
            self.slug = generate_unique_slug(Category, self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Tag(models.Model):
    """
    文章标签模型
    用于对文章进行灵活标记和分类。
    包含颜色配置，用于前端展示。
    """

    name = models.CharField(_("名称"), max_length=100)
    slug = models.SlugField(_("别名"), unique=True, blank=True)
    color = models.CharField(_("颜色"), max_length=20, default="#64748B")
    is_active = models.BooleanField(_("是否可见"), default=True)
    icon = models.CharField(
        _("图标"),
        max_length=50,
        blank=True,
        default="",
        help_text=_("Material Symbols 图标代码"),
    )

    class Meta:
        verbose_name = _("标签")
        verbose_name_plural = verbose_name

    def save(self, *args, **kwargs):
        """保存时自动生成 slug（如果未提供）"""
        if not self.slug:
            self.slug = generate_unique_slug(Tag, self.name)
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
        ("draft", _("草稿")),
        ("published", _("已发布")),
    )

    title = models.CharField(_("标题"), max_length=200)
    subtitle = models.CharField(_("副标题"), max_length=200, blank=True)
    source = models.CharField(_("来源"), max_length=50, blank=True, default="原创")
    source_url = models.URLField(_("来源链接"), blank=True)
    audio = models.FileField(_("音频"), upload_to="posts/audio/", blank=True, null=True)
    video = models.FileField(_("视频"), upload_to="posts/video/", blank=True, null=True)
    video_url = models.URLField(
        _("视频链接"), blank=True, help_text=_("外部视频链接 (YouTube, Bilibili)")
    )
    slug = models.SlugField(_("别名"), unique=True, blank=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name=_("作者"),
    )
    content = models.TextField(_("内容"))
    excerpt = models.TextField(_("摘要"), blank=True, max_length=500)
    cover_image = models.ImageField(
        _("封面图"),
        upload_to="posts/",
        blank=True,
        null=True,
        validators=[validate_image_file],
    )

    # ImageKit Thumbnails (自动生成缩略图)
    cover_thumbnail = ImageSpecField(
        source="cover_image",
        processors=[ResizeToFill(400, 250)],
        format="WEBP",
        options={"quality": 80},
    )

    cover_optimized = ImageSpecField(
        source="cover_image",
        processors=[ResizeToFit(1200, 1200)],
        format="WEBP",
        options={"quality": 85},
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name="posts",
        verbose_name=_("分类"),
    )
    tags = models.ManyToManyField(
        Tag, blank=True, related_name="posts", verbose_name=_("标签")
    )
    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="liked_posts",
        blank=True,
        verbose_name=_("点赞"),
    )
    status = models.CharField(
        _("状态"), max_length=10, choices=STATUS_CHOICES, default="draft", db_index=True
    )
    password = models.CharField(
        _("访问密码"),
        max_length=128,  # 增加长度以容纳哈希
        blank=True,
        help_text=_("设置此密码后，访问文章需要输入密码"),
    )
    views = models.PositiveIntegerField(_("阅读量"), default=0)
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True, db_index=True)
    published_at = models.DateTimeField(
        _("发布时间"), null=True, blank=True, db_index=True
    )
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)
    is_pinned = models.BooleanField(_("置顶"), default=False)
    allow_comments = models.BooleanField(_("允许评论"), default=True)

    # SEO Fields
    meta_title = models.CharField(
        _("Meta 标题"),
        max_length=200,
        blank=True,
        help_text=_("覆盖默认的标题，用于搜索引擎显示"),
    )
    meta_description = models.CharField(
        _("Meta 描述"),
        max_length=200,
        blank=True,
        help_text=_("覆盖默认的描述，建议 160 字以内"),
    )
    meta_keywords = models.CharField(
        _("Meta 关键词"), max_length=200, blank=True, help_text=_("逗号分隔的关键词")
    )

    @property
    def reading_time(self):
        """
        估算文章的阅读时长（分钟）。

        计算规则：
        1. 假设内容为 Markdown 格式或纯文本。
        2. 中文阅读速度按 300 字/分钟计算。
        3. 英文阅读速度按 150 词/分钟计算。
        4. 结果向上取整，最少显示 1 分钟。
        """
        # 移除 HTML 标签 (如果 content 已经是 Markdown 还没渲染 HTML，则直接计算)
        # 这里假设 content 是 Markdown 源码
        text = self.content

        # 简单统计：中文算 1 个字，英文单词算 1 个字
        # 1. 匹配中文字符
        chinese_char_count = len(re.findall(r"[\u4e00-\u9fa5]", text))

        # 2. 匹配英文单词 (简单的空格分割，移除标点)
        english_words = re.findall(r"[a-zA-Z0-9]+", text)
        english_word_count = len(english_words)

        # 计算总分钟数
        minutes = (chinese_char_count / 300) + (english_word_count / 150)

        return math.ceil(minutes) if minutes > 0 else 1

    class Meta:
        ordering = ["-is_pinned", "-published_at", "-created_at"]
        verbose_name = "文章"
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["status", "published_at"]),
        ]

    def set_password(self, raw_password):
        """设置加密后的密码"""
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        """验证密码是否正确"""
        return check_password(raw_password, self.password)

    def save(self, *args, **kwargs):
        """保存时自动生成 slug（如果未提供）"""
        if not self.slug:
            self.slug = generate_unique_slug(Post, self.title)
        if self.status == "published" and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        """获取文章详情页的绝对 URL"""
        from django.urls import reverse

        return reverse("post_detail", kwargs={"slug": self.slug})


class Comment(models.Model):
    """
    文章评论模型
    支持多级回复（通过 parent 字段）。
    """

    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="comments", verbose_name=_("文章")
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_("用户")
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
        verbose_name=_("父评论"),
    )
    content = models.TextField(_("内容"))
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True, db_index=True)
    active = models.BooleanField(_("是否可见"), default=True, db_index=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = _("评论")
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.user.username} 对 {self.post} 的评论"

    @property
    def active_replies(self):
        """获取当前评论下所有可见的回复"""
        if hasattr(self, "active_replies_list"):
            return self.active_replies_list
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
        verbose_name=_("用户"),
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="view_history",
        verbose_name=_("文章"),
    )
    viewed_at = models.DateTimeField(_("浏览时间"), auto_now=True)

    class Meta:
        ordering = ["-viewed_at"]
        verbose_name = _("浏览历史")
        verbose_name_plural = verbose_name
        unique_together = ("user", "post")

    def __str__(self):
        return f"{self.user.username} 浏览了 {self.post.title}"


def _delete_pattern(pattern):
    delete_pattern = getattr(cache, "delete_pattern", None)
    if callable(delete_pattern):
        delete_pattern(pattern)
    else:
        # 如果缓存后端不支持 delete_pattern，我们选择不执行全站缓存清理
        # 因为这在生产环境中风险过大。接受数据短暂不一致（等待 TTL 过期）。
        # 或者可以记录一条日志提醒
        pass


def _clear_sidebar_cache():
    cache.delete("sidebar:tags")
    cache.delete("sidebar:comments")
    cache.delete("sidebar:popular_posts")
    cache.delete("sidebar:categories")
    cache.delete(make_template_fragment_key("sidebar_tags"))
    cache.delete(make_template_fragment_key("sidebar_comments"))
    cache.delete(make_template_fragment_key("sidebar_popular_posts"))


@receiver([post_save, post_delete], sender=Comment)
def _invalidate_comment_sidebar_cache(sender, instance, **kwargs):
    cache.delete("sidebar:comments")
    cache.delete(make_template_fragment_key("sidebar_comments"))


@receiver([post_save, post_delete], sender=Tag)
def _invalidate_tag_sidebar_cache(sender, instance, **kwargs):
    cache.delete("sidebar:tags")
    cache.delete(make_template_fragment_key("sidebar_tags"))
    _delete_pattern("post:*:related")
    _delete_pattern("post:*:meta_desc")


@receiver([post_save, post_delete], sender=Category)
def _invalidate_category_sidebar_cache(sender, instance, **kwargs):
    cache.delete("sidebar:categories")


@receiver([post_save, post_delete], sender=Post)
def _invalidate_post_cache(sender, instance, **kwargs):
    _clear_sidebar_cache()
    cache.delete(f"post:{instance.id}:related")
    cache.delete(f"post:{instance.id}:previous")
    cache.delete(f"post:{instance.id}:next")
    cache.delete(f"post:{instance.id}:meta_desc")
    _delete_pattern("post:*:previous")
    _delete_pattern("post:*:next")
    _delete_pattern("post:*:related")
    if kwargs.get("signal") == post_save and instance.cover_image:
        schedule_post_image_processing(instance.id)


@receiver(m2m_changed, sender=Post.tags.through)
def _invalidate_post_tags_cache(sender, instance, action, **kwargs):
    if action in {"post_add", "post_remove", "post_clear"}:
        cache.delete(f"post:{instance.id}:related")
        cache.delete(f"post:{instance.id}:meta_desc")
        cache.delete("sidebar:tags")

        languages = [l[0] for l in settings.LANGUAGES]
        for lang in languages:
            cache.delete(make_template_fragment_key("sidebar_tags", [lang]))

        _delete_pattern("post:*:related")
