from django.apps import AppConfig


class UsersConfig(AppConfig):
    """
    用户应用配置

    Users 应用负责处理用户认证、注册、登录、个人资料管理以及通知系统。
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "users"
    verbose_name = "用户管理"

    def ready(self):
        """
        App 初始化
        1. 确保必要的媒体目录存在，防止 FileNotFoundError。
        2. 注册信号接收器 (已通过 import models 自动完成，如果 models.py 中有 @receiver)。
        """
        import os
        from django.conf import settings

        # 需要自动创建的目录列表
        media_dirs = [
            "avatars",
            "covers",
            "posts",  # 虽然这是 blog app 用的，但统一在这里检查也没问题，或者在 blog app 里做
        ]

        if settings.MEDIA_ROOT:
            for d in media_dirs:
                path = os.path.join(settings.MEDIA_ROOT, d)
                if not os.path.exists(path):
                    try:
                        os.makedirs(path, exist_ok=True)
                    except OSError:
                        pass
