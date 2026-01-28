from django.db import models
from django.conf import settings

class Poll(models.Model):
    """
    投票/问卷模型
    """
    title = models.CharField("标题", max_length=200)
    description = models.TextField("描述", blank=True)
    is_active = models.BooleanField("是否开启", default=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    allow_multiple_choices = models.BooleanField("允许多选", default=False)
    end_date = models.DateTimeField("结束时间", null=True, blank=True)
    
    # 可选关联文章
    related_post = models.ForeignKey(
        'blog.Post', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='polls',
        verbose_name="关联文章"
    )

    class Meta:
        verbose_name = "投票"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def total_votes(self):
        return self.choices.aggregate(total=models.Sum('votes_count'))['total'] or 0

class Choice(models.Model):
    """
    投票选项
    """
    poll = models.ForeignKey(Poll, related_name='choices', on_delete=models.CASCADE, verbose_name="所属投票")
    text = models.CharField("选项文本", max_length=200)
    votes_count = models.PositiveIntegerField("票数", default=0)

    class Meta:
        verbose_name = "选项"
        verbose_name_plural = verbose_name
        ordering = ["id"]

    def __str__(self):
        return self.text

class Vote(models.Model):
    """
    用户投票记录
    """
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, verbose_name="投票")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="用户")
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE, verbose_name="选择")
    created_at = models.DateTimeField("投票时间", auto_now_add=True)

    class Meta:
        verbose_name = "投票记录"
        verbose_name_plural = verbose_name
        unique_together = ['user', 'choice'] 

    def __str__(self):
        return f"{self.user} voted on {self.poll}"
