from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.templatetags.static import static


class UserLabel(models.Model):
    """
    用户标签模型
    用于给用户打上自定义标签，如"VIP"、"作者"等。
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

    name = models.CharField("名称", max_length=50)
    color = models.CharField("颜色", max_length=20, choices=COLOR_CHOICES, default="neutral")
    description = models.CharField("描述", max_length=200, blank=True)

    class Meta:
        verbose_name = "用户标签"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class User(AbstractUser):
    """
    自定义用户模型
    扩展了Django默认的AbstractUser，添加了头像、封面图、昵称等个人资料字段。
    """

    avatar = models.ImageField("头像", upload_to="avatars/", blank=True, null=True)
    cover_image = models.ImageField(
        "封面图",
        upload_to="covers/",
        blank=True,
        null=True,
        help_text="建议尺寸 800x200 像素",
    )
    nickname = models.CharField("昵称", max_length=50, blank=True)
    bio = models.TextField("个人简介", blank=True, max_length=500)
    website = models.URLField("个人网站", blank=True)
    github = models.URLField("GitHub", blank=True)
    
    labels = models.ManyToManyField(
        UserLabel, blank=True, related_name="users", verbose_name="标签"
    )

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.nickname or self.username

    @property
    def get_avatar_url(self):
        """获取用户头像URL，如果未设置则返回默认头像"""
        if self.avatar and hasattr(self.avatar, "url"):
            return self.avatar.url
        return static("core/img/avatar-default.svg")

    @property
    def unread_notification_count(self):
        """获取用户未读通知的数量"""
        return self.user_notifications.filter(is_read=False).count()


class UserPreference(models.Model):
    """
    用户偏好设置模型
    存储用户特定的设置，如界面主题、隐私选项等。
    与User模型通过OneToOneField关联。
    """

    THEME_CHOICES = (
        ("light", "明亮"),
        ("dark", "暗黑"),
        ("cupcake", "杯子蛋糕"),
        ("bumblebee", "大黄蜂"),
        ("emerald", "翡翠"),
        ("corporate", "企业"),
        ("synthwave", "合成波"),
        ("retro", "复古"),
        ("cyberpunk", "赛博朋克"),
        ("valentine", "情人节"),
        ("halloween", "万圣节"),
        ("garden", "花园"),
        ("forest", "森林"),
        ("aqua", "水色"),
        ("lofi", "低保真"),
        ("pastel", "柔和"),
        ("fantasy", "幻想"),
        ("wireframe", "线框"),
        ("black", "黑色"),
        ("luxury", "奢华"),
        ("dracula", "德古拉"),
        ("cmyk", "CMYK"),
        ("autumn", "秋天"),
        ("business", "商务"),
        ("acid", "酸性"),
        ("lemonade", "柠檬水"),
        ("night", "夜间"),
        ("coffee", "咖啡"),
        ("winter", "冬天"),
        ("dim", "暗淡"),
        ("nord", "诺德"),
        ("sunset", "日落"),
    )

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="preference", verbose_name="用户"
    )
    public_profile = models.BooleanField(
        "公开资料", default=True, help_text="允许其他人查看您的个人资料和浏览历史"
    )
    theme = models.CharField(
        "主题偏好", max_length=20, choices=THEME_CHOICES, default="light"
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
    使用GenericForeignKey来支持关联任意类型的目标对象（如文章、评论等）。
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
