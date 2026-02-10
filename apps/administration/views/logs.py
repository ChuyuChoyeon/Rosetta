import os
from django.conf import settings
from django.views import View
from django.views.generic import TemplateView
from django.contrib.admin.models import LogEntry
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, FileResponse
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.contrib import messages
from django.shortcuts import redirect

from ..mixins import SuperuserRequiredMixin
from ..generics import (
    BaseListView,
    BaseDeleteView,
    BaseExportView,
)


# --- 日志条目视图 ---
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


# --- 日志文件视图 ---
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
                logs.append(
                    {
                        "name": f.name,
                        "size": stat.st_size,
                        "mtime": stat.st_mtime,
                        "path": str(f),
                    }
                )

        # 按修改时间降序排序
        logs.sort(key=lambda x: x["mtime"], reverse=True)
        context["log_files"] = logs

        # 处理分屏视图选中的文件
        current_file = self.request.GET.get("file")
        if current_file:
            # 验证文件名以防止目录遍历
            if "/" in current_file or "\\" in current_file or ".." in current_file:
                messages.error(self.request, _("非法的文件名"))
            else:
                file_path = log_dir / current_file
                if file_path.exists() and file_path.is_file():
                    context["current_file"] = current_file

                    # 查找文件信息
                    for log in logs:
                        if log["name"] == current_file:
                            context["current_file_info"] = log
                            break

                    # 读取内容
                    try:
                        try:
                            last_pos = int(self.request.GET.get("last_pos", 0))
                        except (ValueError, TypeError):
                            last_pos = 0

                        with open(
                            file_path, "r", encoding="utf-8", errors="ignore"
                        ) as f:
                            if last_pos > 0:
                                # Incremental update
                                f.seek(last_pos)
                                content = f.read()
                                context["log_content"] = content
                                self.current_log_pos = f.tell()
                            else:
                                # Initial load or full refresh
                                # Read all lines to get the last 2000
                                # Note: For huge files, this is inefficient.
                                # Production grade would use seek relative to end.
                                f.seek(0, 2)
                                file_size = f.tell()
                                self.current_log_pos = file_size

                                f.seek(0)
                                all_lines = f.readlines()
                                context["log_content"] = "".join(all_lines[-2000:])

                                # Pass initial pos to template
                                context["initial_log_pos"] = file_size
                    except Exception as e:
                        messages.error(self.request, f"Error reading log: {e}")
                        context["log_content"] = ""
                        self.current_log_pos = 0
                else:
                    messages.error(self.request, _("文件不存在"))

        if (
            self.request.htmx
            and self.request.GET.get("partial") == "content"
        ):
            pass

        return context

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)
        if hasattr(self, "current_log_pos"):
            response["X-Log-Pos"] = str(self.current_log_pos)
        return response


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
        action = request.POST.get("action")

        if file_path.exists():
            try:
                if action == "clear":
                    # Clear file content instead of deleting
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write("")
                    messages.success(request, _("日志已清空"))
                    # Redirect back to the same file view
                    return redirect(
                        f"{reverse_lazy('administration:logfile_list')}?file={filename}"
                    )
                else:
                    os.remove(file_path)
                    messages.success(request, _("日志文件已删除"))
            except Exception as e:
                messages.error(request, _("操作失败: {error}").format(error=str(e)))

        return redirect("administration:logfile_list")
