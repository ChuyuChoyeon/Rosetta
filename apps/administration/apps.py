from django.apps import AppConfig


class AdministrationConfig(AppConfig):
    """
    管理后台应用配置

    Administration 应用提供了一个基于 Tailwind CSS (DaisyUI) 的自定义管理后台，
    替代 Django 默认的 Admin 界面，提供更现代的 UI 和更好的移动端支持。
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "administration"
