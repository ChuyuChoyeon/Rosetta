from django.urls import path
from django.views.generic import TemplateView
from .views import (
    PageView,
    debug_api_migrations,
    debug_api_stats,
    debug_api_system,
    debug_execute_command,
    health_check,
    robots_txt,
    translate_text,
    upload_image,
)

urlpatterns = [
    # SEO & Utils
    path("robots.txt", robots_txt, name="robots_txt"),
    path("upload/image/", upload_image, name="upload_image"),
    # Translation API
    path("api/translate/", translate_text, name="translate_text"),
    # 健康检查
    path("health/", health_check, name="health_check"),
    # 调试 API
    path("debug/api/stats/", debug_api_stats, name="debug_api_stats"),
    path("debug/api/system/", debug_api_system, name="debug_api_system"),
    path("debug/api/migrations/", debug_api_migrations, name="debug_api_migrations"),
    path("debug/api/execute/", debug_execute_command, name="debug_execute_command"),
    # 静态页面
    path("about/", PageView.as_view(), {"slug": "about"}, name="about"),
    path("contact/", PageView.as_view(), {"slug": "contact"}, name="contact"),
    # 通用单页面路由 (放在最后)
    path("p/<slug:slug>/", PageView.as_view(), name="page_detail"),
]
