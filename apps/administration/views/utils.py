from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.apps import apps
from django.http import Http404
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import gettext as _

from ..mixins import StaffRequiredMixin
from ..generics import BaseExportView, BaseImportView


class BulkActionView(LoginRequiredMixin, StaffRequiredMixin, View):
    """
    通用批量操作视图
    """

    def post(self, request, model):
        action = request.POST.get("action")
        ids = request.POST.getlist("ids")

        if not ids:
            messages.warning(request, _("未选择任何项目"))
            return redirect(request.META.get("HTTP_REFERER", "/"))

        try:
            Model = (
                apps.get_model(model.split(".")[0], model.split(".")[1])
                if "." in model
                else None
            )
            # Fallback for simple model names usually in current app or blog/core
            if not Model:
                # Try common apps
                for app_label in ["blog", "core", "users", "auth", "administration"]:
                    try:
                        Model = apps.get_model(app_label, model)
                        break
                    except LookupError:
                        continue

            if not Model:
                raise Http404(f"Model {model} not found")

            queryset = Model.objects.filter(id__in=ids)
            count = queryset.count()

            if action == "delete":
                queryset.delete()
                messages.success(
                    request, _("已删除 {count} 个项目").format(count=count)
                )
            elif action == "published":
                if hasattr(Model, "status"):
                    queryset.update(status="published")
                    messages.success(
                        request, _("已发布 {count} 个项目").format(count=count)
                    )
            elif action == "draft":
                if hasattr(Model, "status"):
                    queryset.update(status="draft")
                    messages.success(
                        request, _("已设为草稿 {count} 个项目").format(count=count)
                    )
            # Add more bulk actions as needed

        except Exception as e:
            messages.error(request, _("操作失败: {error}").format(error=str(e)))

        return redirect(request.META.get("HTTP_REFERER", "/"))


class ExportAllView(BaseExportView):
    """
    通用导出视图 (通过 URL 参数指定模型)
    """

    def get(self, request, *args, **kwargs):
        model_name = kwargs.get("model")

        try:
            # Handle app.Model format
            if "." in model_name:
                app_label, model = model_name.split(".")
                self.model = apps.get_model(app_label, model)
            else:
                # Try finding model in common apps
                for app_label in ["blog", "core", "users", "auth", "administration"]:
                    try:
                        self.model = apps.get_model(app_label, model_name)
                        break
                    except LookupError:
                        continue

            if not self.model:
                raise Http404(f"Model {model_name} not found")

            return super().get(request, *args, **kwargs)
        except Exception:
            raise Http404(f"Invalid model {model_name}")


class ImportJsonView(BaseImportView):
    """
    通用导入视图
    """

    def post(self, request, *args, **kwargs):
        model_name = kwargs.get("model")
        try:
            # Handle app.Model format
            if "." in model_name:
                app_label, model = model_name.split(".")
                self.model = apps.get_model(app_label, model)
            else:
                # Try finding model in common apps
                for app_label in ["blog", "core", "users", "auth", "administration"]:
                    try:
                        self.model = apps.get_model(app_label, model_name)
                        break
                    except LookupError:
                        continue

            if not self.model:
                raise Http404(f"Model {model_name} not found")

            # Set success url to referrer
            self.success_url = request.META.get("HTTP_REFERER", "/")
            return super().post(request, *args, **kwargs)
        except Exception:
            raise Http404(f"Invalid model {model_name}")
