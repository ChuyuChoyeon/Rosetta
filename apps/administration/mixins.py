from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_str
from django.conf import settings
from django.http import Http404
import logging

logger = logging.getLogger(__name__)

class AuditLogMixin:
    """
    操作日志混入类

    自动记录用户的操作日志 (Create, Update, Delete)。
    """

    def log_action(self, action_flag, object_repr=None, change_message=""):
        if not self.request.user.is_authenticated:
            return

        obj = getattr(self, "object", None)
        if not obj and hasattr(self, "get_object"):
            try:
                obj = self.get_object()
            except Exception:
                pass

        if not obj:
            return

        try:
            content_type = ContentType.objects.get_for_model(obj)
            object_repr = object_repr or force_str(obj)

            # Use create() directly to avoid manager issues and ensure compatibility
            LogEntry.objects.create(
                user_id=self.request.user.pk,
                content_type_id=content_type.pk,
                object_id=str(obj.pk),
                object_repr=object_repr[:200],
                action_flag=action_flag,
                change_message=change_message,
            )
        except Exception as e:
            # In development, print errors to help debugging
            if settings.DEBUG:
                logger.error(f"Failed to create audit log: {e}")
            pass


class StaffRequiredMixin(UserPassesTestMixin):
    """
    权限混入类：仅允许管理员（is_staff=True）访问。

    用于保护管理后台的所有视图，确保只有具备管理员权限的用户才能访问。
    """

    def test_func(self) -> bool:
        return self.request.user.is_staff


class SuperuserRequiredMixin(UserPassesTestMixin):
    """
    权限混入类：仅允许超级管理员（is_superuser=True）访问。
    """

    def test_func(self) -> bool:
        return self.request.user.is_superuser


class DebugToolRequiredMixin:
    """
    调试工具权限混入类

    仅在 settings.DEBUG_TOOL_ENABLED 为 True 时允许访问。
    用于保护调试相关的视图，防止在生产环境中意外暴露。
    """

    def dispatch(self, request, *args, **kwargs):
        if not getattr(settings, "DEBUG_TOOL_ENABLED", False):
            raise Http404("Not found")
        return super().dispatch(request, *args, **kwargs)
