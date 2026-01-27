from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.templatetags.static import static
from core.validators import validate_image_file


class UserTitle(models.Model):
    """
    用户称号模型

    用于给用户设置专属称号，如"VIP"、"贡献者"、"管理员"等。
    包含名称、颜色样式、图标和描述。
    """

    name = models.CharField("称号名称", max_length=50)
    color = models.CharField(
        "颜色风格",
        max_length=20,
        default="#3B82F6",
    )
    icon = models.TextField("图标SVG", blank=True, help_text="SVG图标代码")
    description = models.CharField("称号说明", max_length=200, blank=True)

    class Meta:
        verbose_name = "用户称号"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class User(AbstractUser):
    """
    自定义用户模型

    扩展了Django默认的AbstractUser，添加了以下增强字段：
    - 头像 (avatar)
    - 封面图 (cover_image)
    - 昵称 (nickname)
    - 个人简介 (bio)
    - 社交链接 (website, github)
    - 用户称号 (title)
    """

    avatar = models.ImageField(
        "头像",
        upload_to="avatars/",
        blank=True,
        null=True,
        validators=[validate_image_file],
    )
    cover_image = models.ImageField(
        "封面图",
        upload_to="covers/",
        blank=True,
        null=True,
        help_text="建议尺寸 800x200 像素",
        validators=[validate_image_file],
    )
    nickname = models.CharField("昵称", max_length=50, blank=True)
    bio = models.TextField("个人简介", blank=True, max_length=500)
    website = models.URLField("个人网站", blank=True)
    github = models.URLField("GitHub", blank=True)

    title = models.ForeignKey(
        UserTitle,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="users",
        verbose_name="称号",
    )

    is_banned = models.BooleanField(
        "是否封禁",
        default=False,
        help_text="封禁用户将禁止其登录系统",
    )

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.nickname or self.username

    @property
    def get_avatar_url(self):
        """
        获取用户头像URL

        如果用户未上传头像，则返回默认的 SVG 头像。
        """
        if self.avatar and hasattr(self.avatar, "url"):
            return self.avatar.url
        return static("core/img/avatar-default.svg")

    @property
    def unread_notification_count(self):
        """
        获取用户未读通知的数量

        用于在导航栏或其他位置显示未读消息红点。
        """
        return self.user_notifications.filter(is_read=False).count()

    @property
    def total_views(self):
        """
        获取用户所有文章的总阅读量
        
        优化: 优先使用注解字段 total_views_annotated (避免 N+1 查询)
        """
        if hasattr(self, "total_views_annotated"):
            return self.total_views_annotated or 0
            
        from django.db.models import Sum
        return self.posts.aggregate(total=Sum("views"))["total"] or 0


class UserPreference(models.Model):
    """
    用户偏好设置模型

    存储用户特定的界面和隐私设置，与 User 模型一对一关联。
    包含：
    - 公开资料设置
    - 界面主题选择 (支持 DaisyUI 的多种主题)
    """

    THEME_CHOICES = (
        ("light", "明亮"),
        ("dark", "暗黑"),
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="preference",
        verbose_name="用户",
    )
    public_profile = models.BooleanField(
        "公开资料",
        default=True,
        help_text="允许其他人查看您的个人资料和浏览历史",
    )
    theme = models.CharField(
        "主题偏好",
        max_length=20,
        choices=THEME_CHOICES,
        default="light",
    )

    class Meta:
        verbose_name = "用户偏好"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.user.username} 的偏好设置"


class Notification(models.Model):
    """
    系统通知模型

    用于存储用户收到的各种通知消息。
    使用 GenericForeignKey 实现多态关联，可以关联到任意模型对象（如文章、评论、点赞等）。

    字段说明:
    - recipient: 接收通知的用户
    - actor: 触发通知的用户
    - verb: 动作描述 (如 "评论了", "点赞了")
    - target: 动作的目标对象 (通过 content_type 和 object_id 关联)
    """

    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="user_notifications",
        verbose_name="接收者",
    )
    actor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="triggered_notifications",
        verbose_name="触发者",
    )
    verb = models.CharField("动作", max_length=255)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    target = GenericForeignKey("content_type", "object_id")

    timestamp = models.DateTimeField("时间", auto_now_add=True)
    is_read = models.BooleanField("已读", default=False)

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "通知"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.actor} {self.verb} {self.recipient}"


@receiver(post_save, sender=User)
def create_user_preference(sender, instance, created, **kwargs):
    """
    信号接收器：在创建新用户时自动创建默认的 UserPreference 对象。
    """
    if created:
        UserPreference.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_preference(sender, instance, **kwargs):
    """
    信号接收器：在保存用户对象时确保 UserPreference 对象存在并保存。
    """
    if not hasattr(instance, "preference"):
        UserPreference.objects.create(user=instance)
    instance.preference.save()
