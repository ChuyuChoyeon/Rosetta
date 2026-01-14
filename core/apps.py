from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "核心设置"

    def ready(self):
        from django.contrib import admin
        from django.utils.functional import SimpleLazyObject
        from constance import config

        # Use SimpleLazyObject to dynamically fetch titles from Constance
        # This prevents database access during startup while allowing dynamic changes
        # Update Django Admin properties
        # admin.site.site_title = SimpleLazyObject(lambda: config.UNFOLD_SITE_TITLE)
        # admin.site.site_header = SimpleLazyObject(lambda: config.UNFOLD_SITE_HEADER)
        # admin.site.index_title = SimpleLazyObject(lambda: config.UNFOLD_SITE_INDEX_TITLE)
        pass
