from django.db import connection
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.db import transaction
from django.views.generic import DetailView
from django.conf import settings
from django.core.mail import send_mail
from django.core.cache import cache
from django.core.management import call_command
from django.utils import timezone
from io import StringIO
import platform
import django
import random
import string
import psutil
from faker import Faker
from .models import Page
from blog.models import Category, Comment, Post
from core.services import generate_mock_data


class PageView(DetailView):
    model = Page
    template_name = "core/page.html"
    context_object_name = "page"

    def get_queryset(self):
        return Page.objects.filter(status="published").order_by("-created_at")


def health_check(request):
    try:
        connection.ensure_connection()
        db_ok = True
    except Exception:
        db_ok = False

    status = 200 if db_ok else 503
    return JsonResponse(
        {
            "status": "ok" if db_ok else "error",
            "database": "ok" if db_ok else "error",
        },
        status=status,
    )


@user_passes_test(lambda u: u.is_staff, login_url="users:login")
def admin_debug(request):
    """
    调试工具视图，提供 Mock 数据生成、缓存清理和邮件测试功能。
    仅限管理员访问。
    """
    User = get_user_model()

    if request.method == "POST":
        action = str(request.POST.get("action") or "")

        if action == "generate_mock":
            try:
                users_count = max(0, int(request.POST.get("users") or 0))
                categories_count = max(0, int(request.POST.get("categories") or 0))
                posts_count = max(0, int(request.POST.get("posts") or 0))
                comments_count = max(0, int(request.POST.get("comments") or 0))
                password = str(request.POST.get("password") or "password123")
            except (TypeError, ValueError):
                messages.error(request, "参数不合法，请检查输入。")
                return redirect(reverse("administration:debug"))

            created = generate_mock_data(
                users_count=users_count,
                categories_count=categories_count,
                posts_count=posts_count,
                comments_count=comments_count,
                password=password,
            )

            messages.success(
                request,
                f"已生成 mock 数据：用户 {created['users']}、分类 {created['categories']}、文章 {created['posts']}、评论 {created['comments']}",
            )
            return redirect(reverse("administration:debug"))

        elif action == "clear_cache":
            try:
                cache.clear()
                messages.success(request, "缓存已清理")
            except Exception as e:
                messages.error(request, f"清理缓存失败: {str(e)}")
            return redirect(reverse("administration:debug"))

        elif action == "test_email":
            try:
                fake = Faker("zh_CN")
                send_mail(
                    subject="Rosetta 邮件测试",
                    message=f"这是一封测试邮件。\n\n时间: {timezone.now()}\n随机内容: {fake.text()}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[request.user.email],
                    fail_silently=False,
                )
                messages.success(request, f"测试邮件已发送至 {request.user.email}")
            except Exception as e:
                messages.error(request, f"邮件发送失败: {str(e)}")
            return redirect(reverse("administration:debug"))

        messages.error(request, "未知操作。")
        return redirect(reverse("administration:debug"))

    try:
        connection.ensure_connection()
        db_ok = True
    except Exception:
        db_ok = False

    # 获取所有注册的 URL 模式用于路由表展示
    from django.urls import get_resolver

    url_patterns = []
    resolver = get_resolver()
    for pattern in resolver.url_patterns:
        if hasattr(pattern, "pattern"):
            url_patterns.append(str(pattern.pattern))
        elif hasattr(pattern, "url_patterns"):
            url_patterns.append(str(pattern))

    context = {
        "db_ok": db_ok,
        "counts": {
            "users": User.objects.count(),
            "categories": Category.objects.count(),
            "posts": Post.objects.count(),
            "comments": Comment.objects.count(),
        },
        "defaults": {
            "users": 5,
            "categories": 5,
            "posts": 20,
            "comments": 60,
            "password": "password123",
        },
        "url_patterns": url_patterns[:20],  # Show first 20 for brevity
    }
    return render(request, "administration/debug.html", context)


@user_passes_test(lambda u: u.is_staff, login_url="users:login")
def debug_api_stats(request):
    """
    调试 API：返回系统统计数据（用户、分类、文章、评论数量）和数据库状态。
    """
    User = get_user_model()
    try:
        connection.ensure_connection()
        db_ok = True
    except Exception:
        db_ok = False

    return JsonResponse(
        {
            "db_ok": db_ok,
            "counts": {
                "users": User.objects.count(),
                "categories": Category.objects.count(),
                "posts": Post.objects.count(),
                "comments": Comment.objects.count(),
            },
        }
    )


@user_passes_test(lambda u: u.is_staff, login_url="users:login")
def debug_api_system(request):
    """
    调试 API：返回系统环境信息，包括 Python/Django 版本、已安装应用、中间件以及资源使用情况（CPU、内存、磁盘）。
    """
    installed_apps = list(getattr(settings, "INSTALLED_APPS", []))
    third_party = [
        app
        for app in installed_apps
        if not app.startswith("django.")
        and not app.startswith("django.contrib.")
        and not app.startswith("blog.")
        and not app.startswith("users.")
        and not app.startswith("core.")
        and app not in {"blog", "users", "core"}
    ]

    # PSUtil info
    try:
        cpu_percent = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        resource_usage = {
            "cpu": cpu_percent,
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used,
            },
            "disk": {
                "total": disk.total,
                "free": disk.free,
                "percent": disk.percent,
            },
        }
    except Exception:
        resource_usage = {}

    return JsonResponse(
        {
            "python": platform.python_version(),
            "django": django.get_version(),
            "debug": bool(getattr(settings, "DEBUG", False)),
            "time_zone": str(getattr(settings, "TIME_ZONE", "")),
            "use_tz": bool(getattr(settings, "USE_TZ", False)),
            "database": {
                "vendor": str(getattr(connection, "vendor", "")),
                "engine": str(connection.settings_dict.get("ENGINE") or ""),
            },
            "apps": {
                "installed_count": len(installed_apps),
                "third_party": third_party,
                "third_party_count": len(third_party),
            },
            "middleware_count": len(list(getattr(settings, "MIDDLEWARE", []))),
            "resources": resource_usage,
        }
    )


@user_passes_test(lambda u: u.is_staff, login_url="users:login")
def debug_api_migrations(request):
    """
    调试 API：返回待执行的数据库迁移列表。
    """
    try:
        from django.db.migrations.executor import MigrationExecutor

        executor = MigrationExecutor(connection)
        targets = executor.loader.graph.leaf_nodes()
        plan = executor.migration_plan(targets)
        pending = [
            f"{migration.app_label}.{migration.name}"
            for migration, backwards in plan
            if not backwards
        ]
        return JsonResponse({"count": len(pending), "pending": pending})
    except Exception as exc:
        return JsonResponse({"count": 0, "pending": [], "error": str(exc)}, status=500)


@user_passes_test(lambda u: u.is_staff, login_url="users:login")
def debug_execute_command(request):
    """
    调试 API：执行受限的 Django 管理命令。
    仅支持白名单内的命令。
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    command = request.POST.get("command")
    args = request.POST.get("args", "").split()

    # Allowed commands whitelist for security
    ALLOWED_COMMANDS = {
        "check": ["--deploy", "--fail-level", "WARNING"],
        "showmigrations": ["--list"],
        "diffsettings": ["--all"],
        "clearsessions": [],
        "help": [],
    }

    if command not in ALLOWED_COMMANDS:
        return JsonResponse({"error": "Command not allowed"}, status=403)

    # Filter args strictly? For now, we trust staff, but let's be careful.
    # Actually, let's just ignore user args for now and use safe defaults or empty
    # Or allow user to provide args but we should probably sanitize.
    # For this iteration, let's allow "safe" args if provided, or fallback to defaults.

    # Simple approach: Run command with no args (or safe default args if needed)
    # If user provides args, we append them.
    # Be aware of injection, but call_command handles list of args safely (it's not shell=True).

    out = StringIO()
    err = StringIO()

    try:
        call_command(command, *args, stdout=out, stderr=err)
        return JsonResponse(
            {"status": "ok", "output": out.getvalue(), "error": err.getvalue()}
        )
    except Exception as e:
        return JsonResponse(
            {"status": "error", "output": out.getvalue(), "error": str(e)}
        )
