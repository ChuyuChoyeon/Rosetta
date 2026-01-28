from django.shortcuts import render
from django.conf import settings
from django.urls import reverse
from constance import config
from django.core.cache import cache
import time


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
        if not getattr(config, "MAINTENANCE_MODE", False):
            return self.get_response(request)

        # 2. 允许访问的路径 (白名单)
        # 静态文件、媒体文件、管理后台、用户登录/退出
        path = request.path
        if (
            path.startswith(settings.STATIC_URL)
            or path.startswith(settings.MEDIA_URL)
            or path.startswith("/admin/")
            or path.startswith("/users/login/")
            or path.startswith("/users/logout/")
            or path.startswith("/__reload__/")  # 开发工具
        ):
            return self.get_response(request)

        # 3. 允许管理员/职员访问
        if request.user.is_authenticated and (
            request.user.is_staff or request.user.is_superuser
        ):
            return self.get_response(request)

        # 4. 其他请求拦截并显示维护页面
        return render(request, "maintenance.html", status=503)


class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not getattr(settings, "RATE_LIMIT_ENABLED", False):
            return self.get_response(request)

        rules = getattr(settings, "RATE_LIMIT_RULES", [])
        if not rules:
            return self.get_response(request)

        method = request.method.upper()
        path = request.path
        ip = self._get_client_ip(request)
        now = int(time.time())

        for rule in rules:
            if method not in rule.get("methods", []):
                continue
            prefix = rule.get("path_prefix")
            if prefix and not path.startswith(prefix):
                continue
            window = int(rule.get("window", 60))
            limit = int(rule.get("limit", 10))
            bucket = now // window
            key = f"ratelimit:{rule.get('name','default')}:{ip}:{bucket}"
            if cache.add(key, 0, window):
                count = 1
                cache.incr(key)
            else:
                count = cache.incr(key)
            if count > limit:
                return self._rate_limited_response(request, window)

        return self.get_response(request)

    def _rate_limited_response(self, request, window):
        if "application/json" in (request.headers.get("Accept") or ""):
            from django.http import JsonResponse

            return JsonResponse(
                {"error": "rate_limited", "retry_after": window}, status=429
            )
        from django.http import HttpResponse

        return HttpResponse("请求过于频繁，请稍后再试。", status=429)

    def _get_client_ip(self, request):
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR") or "unknown"
