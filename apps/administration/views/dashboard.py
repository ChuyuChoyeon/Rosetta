from typing import Any, Dict
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from ..mixins import StaffRequiredMixin
from ..services.dashboard import DashboardService

class IndexView(LoginRequiredMixin, StaffRequiredMixin, TemplateView):
    """
    管理后台首页视图
    """
    template_name = "administration/index.html"
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        # Use service to get data
        context.update(DashboardService.get_dashboard_context())
        return context
