from django.db import models
from django.conf import settings

class GuestbookEntry(models.Model):
    """
    留言板模型
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="用户"
    )
    nickname = models.CharField("昵称", max_length=50, blank=True)
    email = models.EmailField("邮箱", blank=True)
    website = models.URLField("网站", blank=True)
    show_email = models.BooleanField("显示邮箱", default=False)
    content = models.TextField("内容")
    is_public = models.BooleanField("公开", default=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    
    # 管理员回复
    reply_content = models.TextField("回复内容", blank=True)
    reply_at = models.DateTimeField("回复时间", null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "留言"
        verbose_name_plural = verbose_name

    def __str__(self):
        name = self.nickname or (self.user.nickname if self.user else "匿名")
        return f"{name}: {self.content[:20]}"
