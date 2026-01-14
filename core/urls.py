from django.urls import path
from django.views.generic import TemplateView
from .views import (
    PageView,
    debug_api_migrations,
    debug_api_stats,
    debug_api_system,
    debug_execute_command,
    health_check,
)

urlpatterns = [
    path("health/", health_check, name="health_check"),
    path("debug/api/stats/", debug_api_stats, name="debug_api_stats"),
    path("debug/api/system/", debug_api_system, name="debug_api_system"),
    path("debug/api/migrations/", debug_api_migrations, name="debug_api_migrations"),
    path("debug/api/execute/", debug_execute_command, name="debug_execute_command"),
    path("about/", PageView.as_view(), {"slug": "about"}, name="about"),
    path("contact/", PageView.as_view(), {"slug": "contact"}, name="contact"),
    path(
        "rosetta/",
        TemplateView.as_view(template_name="rosetta_intro.html"),
        name="rosetta_intro",
    ),
    path("p/<slug:slug>/", PageView.as_view(), name="page_detail"),
]
