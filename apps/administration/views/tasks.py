from django.urls import reverse_lazy
from django_celery_beat.models import PeriodicTask
from ..forms import PeriodicTaskForm
from ..generics import BaseListView, BaseCreateView, BaseUpdateView, BaseDeleteView
from ..services.tasks import get_task_info_map
from django.views import View
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.utils.translation import gettext as _
from celery import current_app
from django.http import HttpResponse
import json

class PeriodicTaskListView(BaseListView):
    """
    定时任务列表视图
    """
    model = PeriodicTask
    context_object_name = "tasks"
    template_name = "administration/periodic_task_list.html"
    paginate_by = 20
    ordering = ["-enabled", "name"]

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.select_related("interval", "crontab")
        
        query = self.request.GET.get("q")
        if query:
            qs = qs.filter(name__icontains=query)
            
        return qs

class PeriodicTaskCreateView(BaseCreateView):
    """
    定时任务创建视图
    """
    model = PeriodicTask
    form_class = PeriodicTaskForm
    template_name = "administration/periodic_task_form.html"
    success_url = reverse_lazy("administration:periodic_task_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["task_info_map"] = json.dumps(get_task_info_map())
        return context

class PeriodicTaskUpdateView(BaseUpdateView):
    """
    定时任务更新视图
    """
    model = PeriodicTask
    form_class = PeriodicTaskForm
    template_name = "administration/periodic_task_form.html"
    success_url = reverse_lazy("administration:periodic_task_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["task_info_map"] = json.dumps(get_task_info_map())
        return context

class PeriodicTaskDeleteView(BaseDeleteView):
    """
    定时任务删除视图
    """
    model = PeriodicTask
    success_url = reverse_lazy("administration:periodic_task_list")

class PeriodicTaskRunView(View):
    """
    手动运行定时任务视图
    """
    def post(self, request, pk):
        task = get_object_or_404(PeriodicTask, pk=pk)
        try:
            task_name = task.task
            args = json.loads(task.args or "[]")
            kwargs = json.loads(task.kwargs or "{}")
            
            # 发送任务到 Celery
            current_app.send_task(task_name, args=args, kwargs=kwargs)
            
            msg = _("任务 '{name}' 已手动触发").format(name=task.name)
            messages.success(request, msg)
            
            if request.htmx:
                return HttpResponse(headers={
                    "HX-Trigger": json.dumps({
                        "showMessage": {"level": "success", "message": msg}
                    })
                })
                
        except Exception as e:
            error_msg = _("触发任务失败: {error}").format(error=str(e))
            messages.error(request, error_msg)
            
            if request.htmx:
                 return HttpResponse(headers={
                    "HX-Trigger": json.dumps({
                        "showMessage": {"level": "error", "message": error_msg}
                    })
                })
            
        return redirect("administration:periodic_task_list")

class PeriodicTaskToggleView(View):
    """
    切换定时任务启用状态视图
    """
    def post(self, request, pk):
        task = get_object_or_404(PeriodicTask, pk=pk)
        task.enabled = not task.enabled
        task.save()
        
        msg = _("任务 '{name}' 已{status}").format(
            name=task.name, 
            status=_("启用") if task.enabled else _("禁用")
        )
        messages.success(request, msg)
        
        if request.htmx:
            # 我们将返回更新后的切换按钮
            # 但目前，我们只触发一个 toast，并可能刷新行（如果有行模板）
            # 理想情况下我们返回切换开关的 partial
            context = {'task': task}
            return render(request, "administration/partials/task_toggle.html", context)

        return redirect("administration:periodic_task_list")
