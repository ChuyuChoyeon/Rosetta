from django.shortcuts import render
from django.conf import settings
from django.urls import reverse
from constance import config

class MaintenanceMiddleware:
    """
    维护模式中间件
    
    当 Constance 中的 MAINTENANCE_MODE 为 True 时，
    拦截所有非管理员请求，显示维护页面。
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. 检查是否开启维护模式
        if not getattr(config, 'MAINTENANCE_MODE', False):
            return self.get_response(request)

        # 2. 允许访问的路径 (白名单)
        # 静态文件、媒体文件、管理后台、用户登录/退出
        path = request.path
        if (
            path.startswith(settings.STATIC_URL) or
            path.startswith(settings.MEDIA_URL) or
            path.startswith('/admin/') or
            path.startswith('/users/login/') or
            path.startswith('/users/logout/') or
            path.startswith('/__reload__/') # 开发工具
        ):
            return self.get_response(request)

        # 3. 允许管理员/职员访问
        if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
            return self.get_response(request)

        # 4. 其他请求拦截并显示维护页面
        return render(request, 'maintenance.html', status=503)
