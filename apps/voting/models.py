from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Poll(models.Model):
    """
    投票/问卷模型

    定义投票活动的基本信息，如标题、描述、是否允许多选、截止时间等。
    """

    title = models.CharField(_("标题"), max_length=200)
    description = models.TextField(_("描述"), blank=True)
    is_active = models.BooleanField(_("是否开启"), default=True)
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    allow_multiple_choices = models.BooleanField(_("允许多选"), default=False)
    end_date = models.DateTimeField(_("结束时间"), null=True, blank=True)

    # 可选关联文章
    related_post = models.ForeignKey(
        "blog.Post",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="polls",
        verbose_name=_("关联文章"),
    )

    class Meta:
        verbose_name = _("投票")
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def total_votes(self):
        """计算总票数"""
        return self.choices.aggregate(total=models.Sum("votes_count"))["total"] or 0


class Choice(models.Model):
    """
    投票选项模型

    定义投票的可选答案。
    """

    poll = models.ForeignKey(
        Poll,
        related_name="choices",
        on_delete=models.CASCADE,
        verbose_name=_("所属投票"),
    )
    text = models.CharField(_("选项文本"), max_length=200)
    votes_count = models.PositiveIntegerField(_("票数"), default=0)

    class Meta:
        verbose_name = _("选项")
        verbose_name_plural = verbose_name
        ordering = ["id"]

    def __str__(self):
        return self.text


class Vote(models.Model):
    """
    用户投票记录模型

    记录用户对某个选项的投票，用于防止重复投票。
    """

    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, verbose_name=_("投票"))
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_("用户")
    )
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE, verbose_name=_("选择"))
    created_at = models.DateTimeField(_("投票时间"), auto_now_add=True)

    class Meta:
        verbose_name = _("投票记录")
        verbose_name_plural = verbose_name
        unique_together = ["user", "choice"]

    def __str__(self):
        return f"{self.user} voted on {self.poll}"
