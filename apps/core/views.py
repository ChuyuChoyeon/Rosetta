import os
import platform
import uuid
from io import StringIO

import django
import psutil
from faker import Faker
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.cache import cache
from django.core.files.storage import default_storage
from django.core.mail import send_mail
from django.core.management import call_command
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import DetailView

from blog.models import Category, Comment, Post
from core.services import generate_mock_data
from .models import Page
from constance import config
from meta.views import Meta


@require_GET
def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /users/",
        "Allow: /",
        f"Sitemap: {request.scheme}://{request.get_host()}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


@require_POST
def upload_image(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=403)
    if "image" not in request.FILES:
        return JsonResponse({"error": "No image provided"}, status=400)

    image = request.FILES["image"]
    content_type = image.content_type or ""
    if not content_type.startswith("image/"):
        return JsonResponse({"error": "Invalid image type"}, status=400)
    ext = os.path.splitext(image.name)[1]
    filename = f"uploads/{uuid.uuid4().hex}{ext}"

    file_path = default_storage.save(filename, image)
    file_url = default_storage.url(file_path)

    return JsonResponse({"url": file_url})


class PageView(DetailView):
    """
    单页面视图

    用于展示关于页、联系页等静态内容页面。
    """

    model = Page
    template_name = "core/page.html"
    context_object_name = "page"

    def get_queryset(self):
        return Page.objects.filter(status="published").order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        site_name = getattr(config, "SITE_NAME", "Rosetta Blog")
        site_desc = getattr(config, "SITE_DESCRIPTION", "")
        site_keywords = getattr(config, "SITE_KEYWORDS", "")
        keywords = [
            item.strip() for item in str(site_keywords).split(",") if item.strip()
        ]
        page = self.object
        
        # Render page content as a template to support {{ config.SITE_NAME }} etc.
        if page and page.content:
            from django.template import Template, Context
            try:
                # Use current context to render the content
                # We need to ensure 'config' is available. 
                # Since we are in get_context_data, context processors haven't run yet for *this* dictionary,
                # but they will run when the final response is rendered.
                # However, to render the string *now*, we need the values.
                
                # A safer/simpler way for just config is to pass it explicitly if needed,
                # or use RequestContext if we were in a view function.
                # Here we just want to support 'config' and basic tags.
                
                # Let's create a temporary context with 'config' and 'request'
                render_ctx = Context({
                    'config': config,
                    'request': self.request,
                    'user': self.request.user,
                    'site_name': site_name, # helper
                })
                template = Template(page.content)
                rendered_content = template.render(render_ctx)
                context['rendered_content'] = rendered_content
            except Exception as e:
                # Fallback to raw content if rendering fails
                context['rendered_content'] = page.content
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to render page content template: {e}")
        else:
            context['rendered_content'] = ""

        description = site_desc
        if page and page.content:
            from django.utils.html import strip_tags
            import markdown

            # Use the rendered content for description to avoid {{ }} showing up
            text_source = context.get('rendered_content', page.content)
            text = strip_tags(markdown.markdown(text_source))
            if text:
                description = text[:150] + "..." if len(text) > 150 else text
        if page and page.title:
            keywords = keywords + [page.title]
        site_suffix = getattr(config, "SITE_TITLE_SUFFIX", " - Rosetta Blog")
        context["meta"] = Meta(
            title=f"{page.title}{site_suffix}",
            description=description or "",
            keywords=keywords,
            url=self.request.build_absolute_uri(),
            object_type="article",
        )
        return context


def health_check(request):
    """
    健康检查接口

    用于监控系统状态，检查数据库连接是否正常。
    通常由负载均衡器或监控服务调用。
    """
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


@user_passes_test(lambda u: u.is_superuser, login_url="users:login")
def admin_debug(request):
    """
    调试工具视图

    提供 Mock 数据生成、缓存清理和邮件测试功能。
    仅限超级管理员访问。
    """
    if not getattr(settings, "DEBUG_TOOL_ENABLED", False):
        return JsonResponse({"error": "Not found"}, status=404)

    User = get_user_model()

    if request.method == "POST":
        action = str(request.POST.get("action") or "")

        # --- Mock 数据生成 ---
        if action == "generate_mock":
            try:
                users_count = max(0, int(request.POST.get("users") or 0))
                categories_count = max(0, int(request.POST.get("categories") or 0))
                tags_count = max(0, int(request.POST.get("tags") or 0))
                posts_count = max(0, int(request.POST.get("posts") or 0))
                comments_count = max(0, int(request.POST.get("comments") or 0))
                password = str(request.POST.get("password") or "password123")
            except (TypeError, ValueError):
                messages.error(request, "参数不合法，请检查输入。")
                return redirect(reverse("administration:debug"))

            created = generate_mock_data(
                users_count=users_count,
                categories_count=categories_count,
                tags_count=tags_count,
                posts_count=posts_count,
                comments_count=comments_count,
                password=password,
            )

            messages.success(
                request,
                (
                    "已生成 mock 数据：用户 "
                    f"{created['users']}、分类 {created['categories']}、"
                    f"标签 {created['tags']}、文章 {created['posts']}、"
                    f"评论 {created['comments']}"
                ),
            )
            return redirect(reverse("administration:debug"))

        # --- 缓存清理 ---
        elif action == "clear_cache":
            try:
                cache.clear()
                messages.success(request, "缓存已清理")
            except Exception as e:
                messages.error(request, f"清理缓存失败: {str(e)}")
            return redirect(reverse("administration:debug"))

        # --- 邮件发送测试 ---
        elif action == "test_email":
            try:
                fake = Faker("zh_CN")
                message = (
                    "这是一封测试邮件。\n\n"
                    f"时间: {timezone.now()}\n"
                    f"随机内容: {fake.text()}"
                )
                send_mail(
                    subject="Rosetta 邮件测试",
                    message=message,
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

    # --- GET 请求处理 ---
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
        "url_patterns": url_patterns[:20],  # 仅展示前20条，避免页面过长
    }
    return render(request, "administration/debug.html", context)


@user_passes_test(lambda u: u.is_superuser, login_url="users:login")
def debug_api_stats(request):
    """
    调试 API：返回系统统计数据

    包括用户、分类、文章、评论数量和数据库连接状态。
    """
    if not getattr(settings, "DEBUG_TOOL_ENABLED", False):
        return JsonResponse({"error": "Not found"}, status=404)

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


@user_passes_test(lambda u: u.is_superuser, login_url="users:login")
def debug_api_system(request):
    """
    调试 API：返回系统环境信息

    包括 Python/Django 版本、已安装应用、中间件以及资源使用情况（CPU、内存、磁盘）。
    """
    if not getattr(settings, "DEBUG_TOOL_ENABLED", False):
        return JsonResponse({"error": "Not found"}, status=404)

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

    # 获取系统资源信息 (依赖 psutil)
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


@user_passes_test(lambda u: u.is_superuser, login_url="users:login")
def debug_api_migrations(request):
    """
    调试 API：返回待执行的数据库迁移列表。
    """
    if not getattr(settings, "DEBUG_TOOL_ENABLED", False):
        return JsonResponse({"error": "Not found"}, status=404)

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


@user_passes_test(lambda u: u.is_superuser, login_url="users:login")
def debug_execute_command(request):
    """
    调试 API：执行受限的 Django 管理命令。

    出于安全考虑，仅支持白名单内的命令。
    """
    if not getattr(settings, "DEBUG_TOOL_ENABLED", False):
        return JsonResponse({"error": "Not found"}, status=404)

    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    command = request.POST.get("command")

    # 安全白名单：仅允许执行以下无害或只读命令
    ALLOWED_COMMANDS = {
        "check": ["--deploy", "--fail-level", "WARNING"],
        "showmigrations": ["--list"],
        # "diffsettings": ["--all"],  # 已移除以防止敏感信息泄露
        "clearsessions": [],
        "help": [],
    }

    if command not in ALLOWED_COMMANDS:
        return JsonResponse({"error": "Command not allowed"}, status=403)

    # 目前忽略用户传递的参数，强制使用白名单中的安全参数
    # 避免命令注入风险
    safe_args = ALLOWED_COMMANDS[command]

    out = StringIO()
    err = StringIO()

    try:
        call_command(command, *safe_args, stdout=out, stderr=err)
        return JsonResponse(
            {
                "status": "success",
                "output": out.getvalue(),
                "error": err.getvalue(),
            }
        )
    except Exception as e:
        return JsonResponse(
            {
                "status": "error",
                "output": out.getvalue(),
                "error": str(e),
            },
            status=500,
        )
