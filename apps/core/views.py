import os
import platform
import uuid
import json
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
from deep_translator import GoogleTranslator

from blog.models import Category, Comment, Post
from core.services import generate_mock_data
from .models import Page
from constance import config
from meta.views import Meta


@require_GET
def health_check(request):
    """
    健康检查 API
    """
    return JsonResponse({"status": "ok", "timestamp": timezone.now().isoformat()})


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


@require_POST
@user_passes_test(lambda u: u.is_staff, login_url="users:login")
def translate_text(request):
    try:
        data = json.loads(request.body)
        text = data.get("text", "")
        target_langs = data.get("target_langs", [])
        
        if not text or not target_langs:
            return JsonResponse({"error": "Missing text or target languages"}, status=400)
        
        translations = {}
        
        for lang in target_langs:
            try:
                # Map Django language codes to Google Translate codes if necessary
                dest_lang = lang
                if lang == 'zh-hant':
                    dest_lang = 'zh-TW'
                elif lang == 'zh-hans':
                    dest_lang = 'zh-CN'
                
                # Using src='zh-CN' as per user requirement (input is Chinese)
                translated_text = GoogleTranslator(source='zh-CN', target=dest_lang).translate(text)
                translations[lang] = translated_text
            except Exception as e:
                translations[lang] = f"Translation error: {str(e)}"
        
        return JsonResponse({"translations": translations})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


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
                t = Template(page.content)
                # Create a minimal context with config
                c = Context({'config': config})
                context['rendered_content'] = t.render(c)
            except Exception:
                # Fallback to raw content if rendering fails
                context['rendered_content'] = page.content
        else:
             context['rendered_content'] = ""

        context.update(
            {
                "site_name": site_name,
                "site_desc": site_desc,
                "site_keywords": site_keywords,
                "meta_keywords": ",".join(keywords),
            }
        )
        return context


@user_passes_test(lambda u: u.is_superuser, login_url="users:login")
def debug_api_migrations(request):
    """
    调试 API：返回待应用的迁移
    """
    if not getattr(settings, "DEBUG_TOOL_ENABLED", False):
        return JsonResponse({"error": "Not found"}, status=404)

    from django.db.migrations.executor import MigrationExecutor
    from django.db import connections, DEFAULT_DB_ALIAS

    try:
        connection = connections[DEFAULT_DB_ALIAS]
        connection.prepare_database()
        executor = MigrationExecutor(connection)
        targets = executor.loader.graph.leaf_nodes()
        
        # Plan migrations
        plan = executor.migration_plan(targets)
        
        pending = [
            {"app": migration.app_label, "name": migration.name}
            for migration, backwards in plan
            if not backwards
        ]
        return JsonResponse({"count": len(pending), "pending": pending})
    except Exception as exc:
        return JsonResponse({"count": 0, "pending": [], "error": str(exc)}, status=500)


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
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent,
            },
        }
    except Exception:
        resource_usage = {"error": "psutil not available or failed"}

    return JsonResponse(
        {
            "python_version": platform.python_version(),
            "django_version": django.get_version(),
            "os": f"{platform.system()} {platform.release()}",
            "installed_apps": {
                "count": len(installed_apps),
                "third_party": third_party,
            },
            "resource_usage": resource_usage,
            "server_time": timezone.now().isoformat(),
        }
    )


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
