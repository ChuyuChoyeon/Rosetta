from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class NavigationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'navigation'
    verbose_name = _('导航管理')
