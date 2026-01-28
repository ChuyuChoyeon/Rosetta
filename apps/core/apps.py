from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "核心设置"

    def ready(self):
        from django.contrib import admin
        from django.utils.functional import SimpleLazyObject
        from constance import config

        admin.site.site_title = SimpleLazyObject(
            lambda: f"{config.SITE_NAME}{config.SITE_ADMIN_SUFFIX}"
        )
        admin.site.site_header = SimpleLazyObject(lambda: config.SITE_HEADER)
        admin.site.index_title = SimpleLazyObject(lambda: config.ADMIN_NAVBAR_TITLE)
