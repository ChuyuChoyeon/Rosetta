from typing import Any, Dict, List
import os
from django.conf import settings
from django.views import View
from django.views.generic import TemplateView
from django.contrib.admin.models import LogEntry
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, Http404, FileResponse
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.contrib import messages
from django.shortcuts import redirect

from ..mixins import StaffRequiredMixin, SuperuserRequiredMixin
from ..generics import (
    BaseListView,
    BaseDeleteView,
    BaseExportView,
)

# --- LogEntry Views ---
class LogEntryListView(BaseListView):
    model = LogEntry
    context_object_name = "logentries"
    ordering = ["-action_time"]
    paginate_by = 50

    def get_queryset(self):
        qs = super().get_queryset().select_related("user", "content_type")
        query = self.request.GET.get("q")
        user_id = self.request.GET.get("user")

        if query:
            qs = qs.filter(object_repr__icontains=query)
        
        if user_id:
            qs = qs.filter(user_id=user_id)
            
        return qs

class LogEntryDeleteView(BaseDeleteView):
    model = LogEntry
    success_url = reverse_lazy("administration:logentry_list")

class LogEntryExportView(BaseExportView):
    model = LogEntry


# --- LogFile Views ---
class LogFileListView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    """
    系统日志文件列表
    """
    template_name = "administration/logfile_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        log_dir = settings.BASE_DIR / "logs"
        logs = []
        
        if log_dir.exists():
            for f in log_dir.glob("*.log"):
                stat = f.stat()
                logs.append({
                    "name": f.name,
                    "size": stat.st_size,
                    "mtime": stat.st_mtime,
                    "path": str(f),
                })
        
        # Sort by modification time desc
        logs.sort(key=lambda x: x["mtime"], reverse=True)
        context["logs"] = logs
        return context

class LogFileView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    """
    查看日志文件内容
    """
    template_name = "administration/logfile_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filename = kwargs.get("filename")
        file_path = settings.BASE_DIR / "logs" / filename
        
        if not file_path.exists() or not file_path.is_file():
            raise Http404("Log file not found")
            
        # Read last 2000 lines
        lines = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                # Efficiently read last N lines would be better, but for now simple read
                # For large files this might be slow, in production use `tail` or optimized reader
                all_lines = f.readlines()
                lines = all_lines[-2000:]
        except Exception as e:
            messages.error(self.request, f"Error reading log: {e}")
            
        context["filename"] = filename
        context["content"] = "".join(lines)
        return context

class LogFileDownloadView(LoginRequiredMixin, SuperuserRequiredMixin, View):
    def get(self, request, filename):
        file_path = settings.BASE_DIR / "logs" / filename
        if not file_path.exists():
            raise Http404("Log file not found")
            
        response = FileResponse(open(file_path, "rb"))
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

class LogFileDeleteView(LoginRequiredMixin, SuperuserRequiredMixin, View):
    def post(self, request, filename):
        file_path = settings.BASE_DIR / "logs" / filename
        if file_path.exists():
            try:
                os.remove(file_path)
                messages.success(request, _("日志文件已删除"))
            except Exception as e:
                messages.error(request, _("删除失败: {error}").format(error=str(e)))
        
        return redirect("administration:logfile_list")
