from typing import List
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext as _
from django.http import HttpResponse, HttpResponseRedirect
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import redirect
from django.utils import timezone
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
import json

from .mixins import AuditLogMixin, StaffRequiredMixin


class BaseListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    """
    基础列表视图混入类

    提供通用的列表展示功能，集成了 HTMX 支持。

    特性：
    1. 默认分页大小为 20。
    2. 支持动态排序 (GET sort/order 参数)。
    3. 支持 HTMX 局部刷新：检测 HX-Request 头，返回局部模板或完整页面。
    """

    paginate_by = 20
    template_name_suffix = "_list"

    def get_ordering(self):
        sort_by = self.request.GET.get("sort")
        if sort_by:
            allowed_fields = {field.name for field in self.model._meta.fields}
            if sort_by in allowed_fields:
                order = self.request.GET.get("order", "asc")
                if order == "desc":
                    return f"-{sort_by}"
                return sort_by
        return self.ordering

    def get_template_names(self) -> List[str]:
        # HTMX 局部刷新支持
        # 如果是 HTMX 请求且非 Boosted 请求（全页导航），则仅返回局部模板
        if self.request.htmx and not self.request.htmx.boosted:
            return [
                f"administration/partials/{self.model._meta.model_name}_list_rows.html"
            ]

        # 优先使用显式定义的 template_name
        if self.template_name:
            return [self.template_name]

        return [f"administration/{self.model._meta.model_name}_list.html"]


class BaseCreateView(AuditLogMixin, LoginRequiredMixin, StaffRequiredMixin, CreateView):
    """
    基础创建视图混入类

    提供通用的对象创建功能。

    特性：
    1. 自动查找模板 ({model}_form.html 或 generic_form.html)。
    2. 处理保存后的跳转逻辑 (保存并继续编辑、保存并新增另一个)。
    3. 集成消息提示 (创建成功)。
    4. 自动记录操作日志 (AuditLogMixin)。
    """

    template_name_suffix = "_form"

    def get_template_names(self) -> List[str]:
        # 优先使用显式定义的 template_name
        if self.template_name:
            return [self.template_name]

        return [
            f"administration/{self.model._meta.model_name}_form.html",
            "administration/generic_form.html",
        ]

    def get_success_url(self):
        if "_continue" in self.request.POST:
            return reverse_lazy(
                f"administration:{self.model._meta.model_name}_edit",
                kwargs={"pk": self.object.pk},
            )
        if "_addanother" in self.request.POST:
            return reverse_lazy(f"administration:{self.model._meta.model_name}_create")
        return super().get_success_url()

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            _("{name} 创建成功").format(name=self.model._meta.verbose_name),
        )
        self.log_action(ADDITION, change_message=_("通过管理后台创建"))
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        verbose_name = self.model._meta.verbose_name
        context["title"] = _("新建{name}").format(name=verbose_name)
        return context


class BaseUpdateView(AuditLogMixin, LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    """
    基础更新视图混入类

    提供通用的对象更新功能。
    逻辑与 BaseCreateView 类似，但用于编辑现有对象。
    """

    template_name_suffix = "_form"

    def get_template_names(self) -> List[str]:
        return [
            f"administration/{self.model._meta.model_name}_form.html",
            "administration/generic_form.html",
        ]

    def get_success_url(self):
        if "_continue" in self.request.POST:
            return reverse_lazy(
                f"administration:{self.model._meta.model_name}_edit",
                kwargs={"pk": self.object.pk},
            )
        if "_addanother" in self.request.POST:
            return reverse_lazy(f"administration:{self.model._meta.model_name}_create")
        return super().get_success_url()

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            _("{name} 更新成功").format(name=self.model._meta.verbose_name),
        )

        # 尝试检测变更字段 (简单的实现)
        changed_data = form.changed_data
        msg = _("通过管理后台更新")
        if changed_data:
            msg = _("更新字段: {fields}").format(fields=", ".join(changed_data))

        self.log_action(CHANGE, change_message=msg)
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        verbose_name = self.model._meta.verbose_name
        context["title"] = _("编辑{name}").format(name=verbose_name)
        return context


class BaseExportView(LoginRequiredMixin, StaffRequiredMixin, View):
    """
    基础导出视图

    将模型数据导出为 JSON 文件。
    """

    model = None

    def get(self, request, *args, **kwargs):
        if not self.model:
            raise NotImplementedError("BaseExportView requires a model definition")

        queryset = self.model.objects.all()
        data = list(queryset.values())

        # 处理 datetime 和 UUID 等无法序列化的对象
        response = HttpResponse(
            json.dumps(data, cls=DjangoJSONEncoder, ensure_ascii=False, indent=2),
            content_type="application/json",
        )
        filename = f"{self.model._meta.model_name}_export_{timezone.now().strftime('%Y%m%d%H%M%S')}.json"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class BaseImportView(LoginRequiredMixin, StaffRequiredMixin, View):
    """
    基础导入视图

    从 JSON 文件导入数据。
    """

    model = None
    success_url = None

    def post(self, request, *args, **kwargs):
        if not self.model:
            raise NotImplementedError("BaseImportView requires a model definition")

        if "json_file" not in request.FILES:
            messages.error(request, _("请上传 JSON 文件"))
            if self.success_url:
                return redirect(self.success_url)
            return redirect("administration:index")  # Fallback

        json_file = request.FILES["json_file"]
        try:
            data = json.load(json_file)
            if not isinstance(data, list):
                raise ValueError(_("JSON 格式错误：根元素应为列表"))

            success_count = 0
            for item in data:
                # 移除 id 以避免冲突，或用于查找
                item_id = item.pop("id", None)

                # 尝试查找唯一键
                lookup_fields = {}
                if hasattr(self.model, "slug") and "slug" in item:
                    lookup_fields["slug"] = item["slug"]
                elif hasattr(self.model, "username") and "username" in item:
                    lookup_fields["username"] = item["username"]
                elif hasattr(self.model, "name") and "name" in item:
                    lookup_fields["name"] = item["name"]
                elif item_id:
                    lookup_fields["id"] = item_id

                if lookup_fields:
                    obj, created = self.model.objects.update_or_create(
                        defaults=item, **lookup_fields
                    )
                    success_count += 1
                else:
                    self.model.objects.create(**item)
                    success_count += 1

            messages.success(
                request, _("成功导入 {count} 条数据").format(count=success_count)
            )

        except Exception as e:
            messages.error(request, _("导入失败: {error}").format(error=str(e)))

        if self.success_url:
            return redirect(self.success_url)
        return redirect("administration:index")


class BaseDeleteView(AuditLogMixin, LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    """
    基础删除视图混入类

    提供通用的对象删除确认功能。
    支持标准 POST 删除和 HTMX 删除。
    """

    template_name = "administration/generic_confirm_delete.html"

    def form_valid(self, form):
        success_url = self.get_success_url()

        # 在删除前记录日志
        try:
            self.object = self.get_object()
            self.log_action(DELETION, change_message=_("通过管理后台删除"))
        except Exception:
            pass

        self.object.delete()

        # HTMX Support
        if self.request.htmx:
            # 返回空内容以移除行，并触发 Toast 消息
            response = HttpResponse("")
            response["HX-Trigger"] = json.dumps(
                {
                    "show-toast": {
                        "message": _("{name} 删除成功").format(
                            name=self.model._meta.verbose_name
                        ),
                        "type": "success",
                    }
                }
            )
            return response

        messages.success(
            self.request,
            _("{name} 删除成功").format(name=self.model._meta.verbose_name),
        )
        return HttpResponseRedirect(success_url)
