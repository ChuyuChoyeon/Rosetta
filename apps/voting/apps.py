from django.apps import AppConfig


class VotingConfig(AppConfig):
    """
    投票应用配置

    Voting 应用负责处理投票、问卷调查及其选项和结果统计。
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "voting"
    verbose_name = "投票管理"
