from typing import Any, Dict
from django.views import View
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, Http404, FileResponse
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
import os

from ..mixins import StaffRequiredMixin, SuperuserRequiredMixin, DebugToolRequiredMixin

# --- System Views ---
class SettingsView(LoginRequiredMixin, StaffRequiredMixin, TemplateView):
    template_name = "administration/settings.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add settings context here
        # For now, just placeholder
        return context

class SystemToolsView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = "administration/system_tools.html"

class SystemMonitorView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = "administration/partials/system_monitor.html"
    
    def get_context_data(self, **kwargs):
        # This is usually HTMX polled, similar to dashboard logic
        from ..services.dashboard import DashboardService
        context = super().get_context_data(**kwargs)
        dashboard_data = DashboardService.get_dashboard_context()
        context.update(dashboard_data)
        return context

class BackupDownloadView(LoginRequiredMixin, SuperuserRequiredMixin, View):
    def get(self, request, filename):
        # Assuming backups are in a specific directory
        backup_dir = settings.BASE_DIR / "backups"
        file_path = backup_dir / filename
        
        if not file_path.exists():
            raise Http404("Backup file not found")
            
        response = FileResponse(open(file_path, "rb"))
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

# --- Debug Views ---
class DebugDashboardView(LoginRequiredMixin, SuperuserRequiredMixin, DebugToolRequiredMixin, TemplateView):
    template_name = "administration/debug.html"

class DebugUITestView(LoginRequiredMixin, SuperuserRequiredMixin, DebugToolRequiredMixin, TemplateView):
    template_name = "administration/debug/ui_test.html"

class DebugPermissionView(LoginRequiredMixin, SuperuserRequiredMixin, DebugToolRequiredMixin, TemplateView):
    template_name = "administration/debug/permission.html"

class DebugMockView(LoginRequiredMixin, SuperuserRequiredMixin, DebugToolRequiredMixin, TemplateView):
    template_name = "administration/debug/mock.html"

class DebugCacheView(LoginRequiredMixin, SuperuserRequiredMixin, DebugToolRequiredMixin, TemplateView):
    template_name = "administration/debug/cache.html"

class DebugEmailView(LoginRequiredMixin, SuperuserRequiredMixin, DebugToolRequiredMixin, TemplateView):
    template_name = "administration/debug/email.html"
