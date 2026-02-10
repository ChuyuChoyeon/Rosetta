from typing import Any, Dict
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from ..mixins import StaffRequiredMixin
from ..services.dashboard import DashboardService


class IndexView(LoginRequiredMixin, StaffRequiredMixin, TemplateView):
    """
    管理后台首页视图。

    展示系统概览、统计数据和最近活动。
    数据通过 DashboardService 获取。
    """

    template_name = "administration/index.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """
        获取仪表盘上下文数据。

        Returns:
            Dict[str, Any]: 包含统计信息、图表数据等的字典。
        """
        context = super().get_context_data(**kwargs)
        # 使用服务层获取数据，保持控制器轻量
        context.update(DashboardService.get_dashboard_context())
        return context
