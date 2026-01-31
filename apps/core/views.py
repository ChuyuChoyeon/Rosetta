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


"""
核心视图模块 (Core Views)

本模块包含网站的基础视图和通用 API 接口，包括：
- 健康检查、robots.txt
- 图片上传 API
- 文本翻译 API
- 单页面展示 (PageView)
- 超级管理员专用的调试 API (Debug APIs)
"""


@require_GET
def health_check(request):
    """
    健康检查 API。
    
    用于负载均衡器或监控系统检查应用是否存活。
    返回当前的服务器时间戳。
    """
    return JsonResponse({"status": "ok", "timestamp": timezone.now().isoformat()})


@require_GET
def robots_txt(request):
    """
    动态生成 robots.txt 文件。
    
    指导搜索引擎爬虫的行为，禁止访问后台和用户中心，并指定 Sitemap 地址。
    """
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
    """
    通用图片上传 API。
    
    接收一个名为 'image' 的文件，将其保存到默认存储后端，并返回访问 URL。
    通常用于 Markdown 编辑器或富文本编辑器的图片上传功能。
    
    权限：
        仅限已登录用户。
    
    返回:
        JSON: {"url": "..."} 或错误信息
    """
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=403)
    if "image" not in request.FILES:
        return JsonResponse({"error": "No image provided"}, status=400)

    image = request.FILES["image"]
    content_type = image.content_type or ""
    # 简单的文件类型校验，防止上传非图片文件
    if not content_type.startswith("image/"):
        return JsonResponse({"error": "Invalid image type"}, status=400)
    
    # 生成唯一文件名，防止重名覆盖
    ext = os.path.splitext(image.name)[1]
    filename = f"uploads/{uuid.uuid4().hex}{ext}"

    file_path = default_storage.save(filename, image)
    file_url = default_storage.url(file_path)

    return JsonResponse({"url": file_url})


@require_POST
@user_passes_test(lambda u: u.is_staff, login_url="users:login")
def translate_text(request):
    """
    文本翻译 API。
    
    使用 deep_translator 调用 Google 翻译接口，将文本翻译为指定语言。
    主要用于后台自动填充多语言字段。
    
    权限：
        仅限管理员 (Staff) 用户。
        
    参数 (JSON):
        text: 待翻译的文本
        target_langs: 目标语言代码列表 (例如 ['en', 'zh-hant'])
    """
    try:
        data = json.loads(request.body)
        text = data.get("text", "")
        target_langs = data.get("target_langs", [])
        
        if not text or not target_langs:
            return JsonResponse({"error": "Missing text or target languages"}, status=400)
        
        translations = {}
        
        for lang in target_langs:
            try:
                # 映射 Django 语言代码到 Google 翻译支持的代码
                dest_lang = lang
                if lang == 'zh-hant':
                    dest_lang = 'zh-TW'
                elif lang == 'zh-hans':
                    dest_lang = 'zh-CN'
                
                # 强制源语言为中文 (zh-CN)，因为目前需求主要是从中文翻译到其他语言
                translated_text = GoogleTranslator(source='zh-CN', target=dest_lang).translate(text)
                translations[lang] = translated_text
            except Exception as e:
                translations[lang] = f"Translation error: {str(e)}"
        
        return JsonResponse({"translations": translations})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


class PageView(DetailView):
    """
    单页面展示视图 (Page View)

    用于渲染数据库中存储的静态页面内容（如关于、联系我们）。
    支持在内容中使用简单的模板语法（如 {{ config.SITE_NAME }}）。
    """

    model = Page
    template_name = "core/page.html"
    context_object_name = "page"

    def get_queryset(self):
        # 仅展示已发布且按创建时间倒序排列的页面
        return Page.objects.filter(status="published").order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 获取全站 SEO 配置信息
        site_name = getattr(config, "SITE_NAME", "Rosetta Blog")
        site_desc = getattr(config, "SITE_DESCRIPTION", "")
        site_keywords = getattr(config, "SITE_KEYWORDS", "")
        keywords = [
            item.strip() for item in str(site_keywords).split(",") if item.strip()
        ]
        page = self.object
        
        # 尝试将页面内容作为模板进行渲染
        # 这样管理员在后台编辑页面内容时，可以插入 {{ config.SITE_NAME }} 等变量
        if page and page.content:
            from django.template import Template, Context
            try:
                # 创建一个包含 config 的简单上下文
                # 注意：这里不会包含 request 等其他上下文变量，仅用于简单的变量替换
                t = Template(page.content)
                c = Context({'config': config})
                context['rendered_content'] = t.render(c)
            except Exception:
                # 如果渲染出错（例如语法错误），则回退到原始内容
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
    调试 API：查看待应用的数据库迁移。
    
    仅超级用户可用。用于在前端面板快速查看数据库状态。
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
        
        # 计算迁移计划
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
    调试 API：获取系统核心统计数据。
    
    仅超级用户可用。返回用户、分类、文章、评论的总数，以及数据库连接状态。
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
    调试 API：获取服务器系统环境信息。
    
    仅超级用户可用。返回 Python/Django 版本、已安装的第三方应用列表、
    以及服务器的 CPU、内存、磁盘使用情况（依赖 psutil 库）。
    """
    if not getattr(settings, "DEBUG_TOOL_ENABLED", False):
        return JsonResponse({"error": "Not found"}, status=404)

    installed_apps = list(getattr(settings, "INSTALLED_APPS", []))
    # 筛选出第三方应用（排除 Django 内置应用和本项目应用）
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

    # 获取系统资源使用情况
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
    
    仅超级用户可用。出于安全考虑，仅支持白名单内的无害或只读命令。
    用于在前端面板快速执行一些维护操作（如检查配置、清除 Session）。
    """
    if not getattr(settings, "DEBUG_TOOL_ENABLED", False):
        return JsonResponse({"error": "Not found"}, status=404)

    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    command = request.POST.get("command")

    # 安全白名单：仅允许执行以下命令
    ALLOWED_COMMANDS = {
        "check": ["--deploy", "--fail-level", "WARNING"],
        "showmigrations": ["--list"],
        # "diffsettings": ["--all"],  # 出于安全原因已禁用
        "clearsessions": [],
        "help": [],
    }

    if command not in ALLOWED_COMMANDS:
        return JsonResponse({"error": "Command not allowed"}, status=403)

    # 强制使用白名单中预定义的参数，忽略用户传递的任何参数
    # 这是防止命令注入的关键措施
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
