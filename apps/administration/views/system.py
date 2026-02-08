from typing import Any, Dict
from django.views import View
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, Http404, FileResponse
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
import os
from pathlib import Path
from django.apps import apps
from django.db import models
from django.core.cache import cache
from django.utils import timezone
from django.utils.translation import gettext as _
import platform
import django
from django.db import connection

from ..mixins import StaffRequiredMixin, SuperuserRequiredMixin, DebugToolRequiredMixin

import shutil
import time
from datetime import datetime
from django.core.management import call_command
from django.db.models import Sum
from core.models import Page
from blog.models import Post, Comment
from users.models import User

# --- System Views ---
class SettingsView(LoginRequiredMixin, StaffRequiredMixin, TemplateView):
    template_name = "administration/settings.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from constance import config
        from django.conf import settings as django_settings
        from django.contrib.sites.models import Site

        # Get Current Site
        try:
            context["current_site"] = Site.objects.get_current()
        except Site.DoesNotExist:
            context["current_site"] = None

        # Define Fieldsets (Grouped Settings)
        # We manually structure this to match the UI expectations
        fieldsets_metadata = [
            {
                "slug": "general",
                "title": _("常规设置"),
                "icon": "settings",
            },
            {
                "slug": "seo",
                "title": _("SEO 优化"),
                "icon": "search",
            },
            {
                "slug": "social",
                "title": _("社交媒体"),
                "icon": "share",
            },
            {
                "slug": "email",
                "title": _("邮件服务"),
                "icon": "mail",
            },
            {
                "slug": "feature",
                "title": _("功能开关"),
                "icon": "toggle_on",
            },
            {
                "slug": "admin",
                "title": _("后台界面"),
                "icon": "dashboard",
            },
            {
                "slug": "analytics",
                "title": _("统计分析"),
                "icon": "analytics",
            },
             {
                "slug": "custom",
                "title": _("自定义代码"),
                "icon": "code",
            }
        ]
        
        # Prepare fieldsets list
        fieldsets = []
        
        # Helper to get config item
        constance_conf = getattr(django_settings, 'CONSTANCE_CONFIG', {})
        constance_fieldsets = getattr(django_settings, 'CONSTANCE_CONFIG_FIELDSETS', {})

        def get_config_item(key):
            if key not in constance_conf:
                return None
            
            options = constance_conf[key]
            if len(options) == 3:
                default_val, help_text, type_data = options
            elif len(options) == 2:
                default_val, help_text = options
                type_data = type(default_val)
            else:
                return None

            # Determine type
            field_type = 'text'
            choices = None
            
            if isinstance(type_data, bool) or type_data is bool:
                field_type = 'bool'
            elif isinstance(type_data, int) or type_data is int:
                field_type = 'number'
            elif isinstance(type_data, (list, tuple)):
                # If it's a tuple of tuples, it's choices
                if len(type_data) > 0:
                    if isinstance(type_data[0], (list, tuple)):
                        field_type = 'select'
                        choices = type_data
                    else:
                        # Simple list of values -> convert to choices
                        field_type = 'select'
                        choices = [(str(x), str(x)) for x in type_data]
                else:
                    field_type = 'text'
            elif key.endswith('_IMAGE') or key.endswith('_LOGO') or key.endswith('_ICON'):
                 field_type = 'image'
            elif 'COLOR' in key:
                 field_type = 'color'
            
            # Get current value
            value = getattr(config, key)
            
            return {
                "key": key,
                "value": value,
                "default": default_val,
                "help_text": help_text,
                "type": field_type,
                "choices": choices
            }

        # Populate items based on CONSTANCE_CONFIG_FIELDSETS from settings
        for meta in fieldsets_metadata:
            slug = meta["slug"]
            # Look up keys in settings.CONSTANCE_CONFIG_FIELDSETS
            # If slug matches key in settings fieldsets, use those keys
            keys = constance_fieldsets.get(slug, [])
            
            items = []
            for key in keys:
                item = get_config_item(key)
                if item:
                    items.append(item)
            
            # Add to fieldsets if we have metadata (even if empty items, user might want to see tab)
            # But user complained about "Empty content", so we better have items.
            # With new settings.py, all groups should have items.
            group = meta.copy()
            group["items"] = items
            fieldsets.append(group)

        # Fallback for keys NOT in any fieldset?
        # Ideally we should capture them.
        all_handled_keys = set()
        for keys in constance_fieldsets.values():
            all_handled_keys.update(keys)
            
        unhandled_keys = set(constance_conf.keys()) - all_handled_keys
        if unhandled_keys:
             # Find or create 'general' or 'other' group
             general_group = next((g for g in fieldsets if g["slug"] == "general"), None)
             if not general_group:
                 general_group = {"slug": "general", "title": _("常规设置"), "icon": "settings", "items": []}
                 fieldsets.append(general_group)
             
             for key in unhandled_keys:
                 item = get_config_item(key)
                 if item:
                     general_group["items"].append(item)

        context["fieldsets"] = fieldsets
        return context

    def post(self, request):
        from constance import config
        from django.contrib.sites.models import Site
        
        # 1. Update Site Info
        if 'site_domain' in request.POST and 'site_name' in request.POST:
            try:
                site = Site.objects.get_current()
                site.domain = request.POST['site_domain']
                site.name = request.POST['site_name']
                site.save()
            except Exception as e:
                messages.error(request, _("站点信息更新失败: {error}").format(error=str(e)))

        # 2. Update Constance Settings
        # Iterate over all keys in config to check for POST data
        # Note: Checkboxes for booleans might not send value if unchecked
        from django.conf import settings as django_settings
        constance_conf = getattr(django_settings, 'CONSTANCE_CONFIG', {})
        
        updated_count = 0
        
        for key, options in constance_conf.items():
            if len(options) == 3:
                default_val, help_text, type_data = options
            elif len(options) == 2:
                default_val, help_text = options
                # Infer type from default value
                type_data = type(default_val)
            else:
                continue # Skip invalid config
            
            # Boolean handling
            is_bool = isinstance(type_data, bool) or type_data is bool
            
            if is_bool:
                # Checkbox logic: presence means True, absence means False (if we know it's a bool field form submission)
                # But to be safe against partial forms, we usually only update if we know we are submitting this form.
                # Assuming this form submits ALL settings.
                new_value = request.POST.get(key) == 'on'
                setattr(config, key, new_value)
                updated_count += 1
            elif key in request.POST:
                new_value = request.POST.get(key)
                
                # Type conversion
                if isinstance(type_data, int) or type_data is int:
                    try:
                        new_value = int(new_value)
                    except ValueError:
                        continue # Skip invalid
                        
                setattr(config, key, new_value)
                updated_count += 1
                
        messages.success(request, _("设置已更新"))
        return redirect("administration:settings")

class SystemToolsView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = "administration/system_tools.html"
    
    def _get_async_task_status(self, latest_key_pointer):
        task_key = cache.get(latest_key_pointer)
        if not task_key:
            return {"status": "idle"}
        return cache.get(task_key) or {"status": "unknown"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 1. Media Scan Stats
        # media_scan_stats uses direct key "media_scan_stats" in current utils.py logic? 
        # Wait, utils.py trigger_media_scan_async sets "media:scan:latest" -> task_key -> result
        # The OLD view code read "media_scan_stats". I should update this too.
        
        scan_task = self._get_async_task_status("media:scan:latest")
        context.update({
            "media_scan_status": scan_task.get("status", "idle"),
            "media_scan_updated_at": scan_task.get("updated_at"),
            "media_scan_orphaned_count": scan_task.get("orphaned_count", 0),
            "media_scan_orphaned_size": scan_task.get("orphaned_size", 0),
        })
        
        clean_task = self._get_async_task_status("media:clean:latest")
        context.update({
            "media_clean_status": clean_task.get("status", "idle"),
            "media_clean_cleaned_count": clean_task.get("cleaned_count", 0),
            "media_clean_cleaned_size": clean_task.get("cleaned_size", 0),
            "media_clean_error": clean_task.get("detail"), # utils.py uses 'detail' for error
        })

        # 2. Watson Rebuild Stats
        watson_task = self._get_async_task_status("watson:rebuild:latest")
        context.update({
            "watson_rebuild_status": watson_task.get("status", "idle"),
            "watson_rebuild_updated_at": watson_task.get("updated_at"),
        })

        # 3. Image Queue Stats
        img_task = self._get_async_task_status("image:queue:latest")
        context.update({
            "image_queue_status": img_task.get("status", "idle"),
            "image_queue_updated_at": img_task.get("updated_at"),
            "image_queue_queued": img_task.get("queued", 0),
            "image_queue_processed": img_task.get("processed", 0),
        })

        # 4. Privacy Policy Status
        context["privacy_policy_exists"] = Page.objects.filter(slug="privacy-policy").exists()

        # 5. Backups
        backup_dir = settings.BASE_DIR / "backups"
        backups = []
        if backup_dir.exists():
            for f in backup_dir.glob("*"):
                if f.is_file() and not f.name.startswith("."):
                    stat = f.stat()
                    backups.append({
                        "name": f.name,
                        "size": stat.st_size,
                        "mtime": datetime.fromtimestamp(stat.st_mtime),
                        "path": str(f),
                    })
        backups.sort(key=lambda x: x["mtime"], reverse=True)
        context["backups"] = backups

        return context

    def post(self, request):
        action = request.POST.get("action")
        
        handlers = {
            "scan_media": self.handle_scan_media,
            "clean_media": self.handle_clean_media,
            "rebuild_watson": self.handle_rebuild_watson,
            "init_privacy_policy": self.handle_init_privacy_policy,
            "queue_images": self.handle_queue_images,
            "create_backup": self.handle_create_backup,
            "restore_backup": self.handle_restore_backup,
            "delete_backup": self.handle_delete_backup,
        }

        handler = handlers.get(action)
        if handler:
            return handler(request)
        
        messages.warning(request, _("未知的操作"))
        return redirect("administration:system_tools")

    # ... Media Handlers ...
    def handle_scan_media(self, request):
        if cache.get("media_scan_status") == "running":
            messages.warning(request, _("媒体扫描任务正在进行中"))
            return redirect("administration:system_tools")

        from core.utils import trigger_media_scan_async
        result = trigger_media_scan_async()
        
        if result["accepted"]:
            messages.success(request, _("已启动媒体扫描任务"))
        else:
            messages.warning(request, _("无法启动扫描任务（可能已有任务在运行）"))
            
        return redirect("administration:system_tools")

    def handle_clean_media(self, request):
        if cache.get("media_clean_status") == "running":
            messages.warning(request, _("媒体清理任务正在进行中"))
            return redirect("administration:system_tools")

        from core.utils import trigger_media_clean_async
        result = trigger_media_clean_async()
        
        if result["accepted"]:
             messages.success(request, _("已启动媒体清理任务"))
        elif result.get("error"):
             messages.error(request, _("无法启动清理任务: {error}").format(error=result["error"]))
        else:
             messages.warning(request, _("无法启动清理任务"))
             
        return redirect("administration:system_tools") 

    def handle_rebuild_watson(self, request):
        from core.utils import trigger_watson_rebuild_async
        result = trigger_watson_rebuild_async()
        
        if result["accepted"]:
            messages.success(request, _("已启动索引重建任务"))
        else:
            messages.warning(request, _("索引重建任务正在进行中"))
            
        return redirect("administration:system_tools")

    def handle_init_privacy_policy(self, request):
        if Page.objects.filter(slug="privacy-policy").exists():
            messages.warning(request, _("隐私政策页面已存在"))
            return redirect("administration:system_tools")

        try:
            # 1. Prepare Content for all supported languages
            content_map = {
                "zh_hans": {
                    "title": "隐私政策",
                    "content": """## 隐私政策

**生效日期：** 2024年1月1日

感谢您访问我们的网站。我们非常重视您的隐私保护。本隐私政策旨在向您说明我们如何收集、使用、存储和保护您的个人信息。

### 1. 我们收集的信息

我们可能会收集以下类型的个人信息：
- **账户信息：** 当您注册账户时，我们会收集您的用户名、电子邮件地址等。
- **使用数据：** 我们会自动收集您访问我们网站时的 IP 地址、浏览器类型、访问时间等日志信息。
- **用户内容：** 您在评论区或个人资料中主动发布的内容。

### 2. 信息的使用

我们收集的信息主要用于：
- 提供、维护和改进我们的服务。
- 向您发送通知、更新和营销信息（您可以随时退订）。
- 防止欺诈和滥用，确保系统安全。

### 3. 信息共享

除法律法规规定或为了保护我们的合法权益外，我们不会未经您的同意向第三方出售或出租您的个人信息。

### 4. 数据安全

我们采取合理的技术和管理措施来保护您的信息安全，防止未经授权的访问、披露或丢失。

### 5. 您的权利

您有权访问、更正或删除您的个人信息。如需行使这些权利，请通过联系方式与我们联系。

### 6. 联系我们

如果您对本隐私政策有任何疑问，请联系我们。
"""
                },
                "en": {
                    "title": "Privacy Policy",
                    "content": """## Privacy Policy

**Effective Date:** January 1, 2024

Thank you for visiting our website. We take your privacy very seriously. This Privacy Policy explains how we collect, use, store, and protect your personal information.

### 1. Information We Collect

We may collect the following types of personal information:
- **Account Information:** When you register, we collect your username, email address, etc.
- **Usage Data:** We automatically collect log information such as your IP address, browser type, and access times.
- **User Content:** Content you voluntarily post in comments or your profile.

### 2. How We Use Information

The information we collect is primarily used to:
- Provide, maintain, and improve our services.
- Send you notifications, updates, and marketing communications (you can opt-out at any time).
- Prevent fraud and abuse, ensuring system security.

### 3. Information Sharing

We do not sell or rent your personal information to third parties without your consent, except as required by law or to protect our legal rights.

### 4. Data Security

We implement reasonable technical and administrative measures to protect your information from unauthorized access, disclosure, or loss.

### 5. Your Rights

You have the right to access, correct, or delete your personal information. To exercise these rights, please contact us.

### 6. Contact Us

If you have any questions about this Privacy Policy, please contact us.
"""
                },
                "ja": {
                    "title": "プライバシーポリシー",
                    "content": """## プライバシーポリシー

**発効日：** 2024年1月1日

当ウェブサイトをご覧いただきありがとうございます。私たちは、お客様のプライバシー保護を非常に重視しています。本プライバシーポリシーは、私たちがどのようにお客様の個人情報を収集、使用、保存、保護するかについて説明するものです。

### 1. 収集する情報

私たちは、以下の種類の個人情報を収集する場合があります：
- **アカウント情報：** 登録時に、ユーザー名、メールアドレスなどを収集します。
- **利用データ：** お客様が当サイトにアクセスした際のIPアドレス、ブラウザの種類、アクセス日時などのログ情報を自動的に収集します。
- **ユーザーコンテンツ：** コメント欄やプロフィールで自主的に公開されたコンテンツ。

### 2.情報の利用目的

収集した情報は、主に以下の目的で使用されます：
- サービスの提供、維持、改善のため。
- 通知、更新情報、マーケティング情報の送信（いつでも配信停止可能です）。
- 不正行為や乱用の防止、システムセキュリティの確保。

### 3. 情報の共有

法律で定められている場合や、私たちの法的権利を保護する場合を除き、お客様の同意なしに個人情報を第三者に販売または貸与することはありません。

### 4. データセキュリティ

私たちは、不正アクセス、開示、紛失からお客様の情報を保護するために、合理的な技術的および管理的措置を講じています。

### 5. お客様の権利

お客様には、ご自身の個人情報にアクセスし、訂正または削除する権利があります。これらの権利を行使される場合は、お問い合わせください。

### 6. お問い合わせ

本プライバシーポリシーについてご質問がある場合は、お問い合わせください。
"""
                },
                "zh_hant": {
                    "title": "隱私政策",
                    "content": """## 隱私政策

**生效日期：** 2024年1月1日

感謝您訪問我們的網站。我們非常重視您的隱私保護。本隱私政策旨在向您說明我們如何收集、使用、存儲和保護您的個人信息。

### 1. 我們收集的信息

我們可能會收集以下類型的個人信息：
- **賬戶信息：** 當您註冊賬戶時，我們會收集您的用戶名、電子郵件地址等。
- **使用數據：** 我們會自動收集您訪問我們網站時的 IP 地址、瀏覽器類型、訪問時間等日誌信息。
- **用戶內容：** 您在評論區或個人資料中主動發佈的內容。

### 2. 信息的使用

我們收集的信息主要用於：
- 提供、維護和改進我們的服務。
- 向您發送通知、更新和營銷信息（您可以隨時退訂）。
- 防止欺詐和濫用，確保系統安全。

### 3. 信息共享

除法律法規規定或為了保護我們的合法權益外，我們不會未經您的同意向第三方出售或出租您的個人信息。

### 4. 數據安全

我們採取合理的技術和管理措施來保護您的信息安全，防止未經授權的訪問、披露或丟失。

### 5. 您的權利

您有權訪問、更正或刪除您的個人信息。如需行使這些權利，請通過聯繫方式與我們聯繫。

### 6. 聯繫我們

如果您對本隱私政策有任何疑問，請聯繫我們。
"""
                },
            }
            
            # 2. Create Page object
            # Use zh_hans as default content
            page = Page(
                title=content_map["zh_hans"]["title"],
                slug="privacy-policy",
                status="published",
                content=content_map["zh_hans"]["content"],
            )
            
            # 3. Set translated fields dynamically
            for lang, data in content_map.items():
                # Assuming django-modeltranslation uses fields like title_en, content_en
                # Note: lang code in modeltranslation might differ (e.g. zh_hans vs zh-hans).
                # Usually underscores are used in field names.
                setattr(page, f"title_{lang}", data["title"])
                setattr(page, f"content_{lang}", data["content"])
            
            page.save()
            messages.success(request, _("隐私政策页面已初始化（包含中、英、日、繁体中文）"))
        except Exception as e:
            messages.error(request, _("初始化失败: {error}").format(error=str(e)))
            
        return redirect("administration:system_tools")

    def handle_queue_images(self, request):
        from core.utils import queue_post_images_async
        
        try:
            limit = int(request.POST.get("limit", 20))
        except ValueError:
            limit = 20

        result = queue_post_images_async(limit=limit)
        
        if result["accepted"]:
            messages.success(request, _("已启动图片处理任务"))
        else:
            messages.warning(request, _("图片处理任务正在进行中"))
            
        return redirect("administration:system_tools")

    def handle_create_backup(self, request):
        from core.tasks import backup_database_task
        
        # 启动后台备份任务
        backup_database_task.delay()
        messages.success(request, _("已启动数据库备份任务，请稍后刷新查看"))
        return redirect("administration:system_tools")

    def handle_restore_backup(self, request):
        filename = request.POST.get("filename")
        if not filename:
            messages.error(request, _("未指定文件名"))
            return redirect("administration:system_tools")
            
        try:
            from core.utils import restore_backup
            restore_backup(filename)
            messages.success(request, _("数据库已成功恢复"))
        except Exception as e:
             messages.error(request, _("恢复失败: {error}").format(error=str(e)))
             
        return redirect("administration:system_tools")

    def handle_delete_backup(self, request):
        filename = request.POST.get("filename")
        if not filename:
            messages.error(request, _("未指定文件名"))
            return redirect("administration:system_tools")
            
        try:
            from core.utils import delete_backup
            delete_backup(filename)
            messages.success(request, _("备份文件已删除"))
        except Exception as e:
            messages.error(request, _("删除失败: {error}").format(error=str(e)))
        
        return redirect("administration:system_tools")

# --- Debug Views ---
# (Previous views remain, just updating their implementation if needed)

class SystemMonitorView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = "administration/partials/system_monitor.html"
    
    def get_context_data(self, **kwargs):
        # This is usually HTMX polled, similar to dashboard logic
        from ..services.dashboard import DashboardService
        context = super().get_context_data(**kwargs)
        dashboard_data = DashboardService.get_dashboard_context()
        
        # Flatten system_info for template accessibility
        if "system_info" in dashboard_data:
            context.update(dashboard_data["system_info"])
            
        context.update(dashboard_data)
        return context

class BackupDownloadView(LoginRequiredMixin, SuperuserRequiredMixin, View):
    def get(self, request, filename):
        # Assuming backups are in a specific directory
        backup_dir = settings.BASE_DIR / "backups"
        file_path = backup_dir / filename
        
        if not file_path.exists():
            raise Http404("Backup file not found")
            
        response = FileResponse(open(file_path, "rb"))
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

# --- Debug Views ---
class DebugDashboardView(LoginRequiredMixin, SuperuserRequiredMixin, DebugToolRequiredMixin, TemplateView):
    template_name = "administration/debug.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 1. Database Status
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                row = cursor.fetchone()
                context["db_ok"] = (row and row[0] == 1)
        except Exception:
            context["db_ok"] = False
            
        # 2. System Info
        context["system_info"] = {
            "python_version": platform.python_version(),
            "django_version": django.get_version(),
            "platform": platform.platform(),
        }
        
        # 3. Data Counts
        context["counts"] = {
            "users": User.objects.count(),
            "posts": Post.objects.count(),
            "comments": Comment.objects.count(),
        }

        # 4. URL Patterns
        from django.urls import get_resolver
        from django.urls.resolvers import URLPattern, URLResolver

        url_patterns = []
        resolver = get_resolver()

        def extract_patterns(patterns, prefix=""):
            for pattern in patterns:
                if isinstance(pattern, URLPattern):
                    # Skip internal/admin patterns if desired, or keep all
                    # Attempt to resolve name
                    name = pattern.name or ""
                    
                    # Clean up pattern string for display
                    pattern_str = str(pattern.pattern)
                    display_pattern = prefix + pattern_str.lstrip('^').rstrip('$')
                    
                    # Generate sample URL only for parameter-less routes
                    sample_url = None
                    has_params = '<' in pattern_str or '(?P' in pattern_str
                    
                    if not has_params:
                        try:
                            # Try to reverse it if it has a name
                            if name:
                                from django.urls import reverse
                                # If namespaced (which we don't have easily here recursively without passing namespace), 
                                # reverse might fail if we don't know the full 'namespace:name'.
                                # So simplistic approach: if it looks static, just append to prefix.
                                # But prefix logic is tricky with includes.
                                # Better approach: just check regex.
                                pass
                            
                            # Construct a simple path representation
                            # This is approximate for display
                            sample_url = "/" + display_pattern
                        except Exception:
                            pass

                    url_patterns.append({
                        "name": name,
                        "pattern": pattern_str,
                        "display_pattern": display_pattern,
                        "description": pattern.callback.__doc__.strip().split('\n')[0] if pattern.callback and pattern.callback.__doc__ else "",
                        "sample_url": sample_url if not has_params else None
                    })
                elif isinstance(pattern, URLResolver):
                    # Recursive extraction for includes
                    # pattern.pattern is the prefix
                    new_prefix = prefix + str(pattern.pattern).lstrip('^').rstrip('$')
                    extract_patterns(pattern.url_patterns, new_prefix)

        # Start extraction
        try:
            extract_patterns(resolver.url_patterns)
            # Filter out some noise if needed, e.g., admin/ or static/
            # url_patterns = [p for p in url_patterns if not p['display_pattern'].startswith('admin/')]
            context["url_patterns"] = sorted(url_patterns, key=lambda x: x['display_pattern'])
        except Exception as e:
            context["url_patterns"] = []
            # Optionally log error
        
        return context

class DebugUITestView(LoginRequiredMixin, SuperuserRequiredMixin, DebugToolRequiredMixin, TemplateView):
    template_name = "administration/debug/ui_test.html"

class DebugPermissionView(LoginRequiredMixin, SuperuserRequiredMixin, DebugToolRequiredMixin, TemplateView):
    template_name = "administration/debug/permission.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add permission check logic here if needed
        # For now, we can list all permissions for the current user
        from django.contrib.auth.models import Permission
        
        user = self.request.user
        if user.is_superuser:
            context["user_permissions"] = "Superuser (All Permissions)"
        else:
            perms = user.get_all_permissions()
            context["user_permissions"] = sorted(list(perms))
            
        return context

class DebugCacheView(LoginRequiredMixin, SuperuserRequiredMixin, DebugToolRequiredMixin, TemplateView):
    template_name = "administration/debug/cache.html"
    
    def post(self, request):
        action = request.POST.get("action")
        if action == "clear_all":
            cache.clear()
            messages.success(request, _("所有缓存已清理"))
        elif action == "clear_templates":
            # Clearing specific keys if possible, but default cache.clear() is safer for simple setups
            # If using specific template cache backend, we would clear that.
            # For now, standard clear is fine or we can try to delete specific patterns if using Redis
            cache.clear() 
            messages.success(request, _("模板缓存已清理"))
        else:
            messages.warning(request, _("未知操作"))
            
        return redirect("administration:debug_cache")

class DebugEmailView(LoginRequiredMixin, SuperuserRequiredMixin, DebugToolRequiredMixin, TemplateView):
    template_name = "administration/debug/email.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["email_host"] = getattr(settings, "EMAIL_HOST", "")
        context["email_port"] = getattr(settings, "EMAIL_PORT", "")
        context["email_host_user"] = getattr(settings, "EMAIL_HOST_USER", "")
        context["email_use_tls"] = getattr(settings, "EMAIL_USE_TLS", "")
        return context
        
    def post(self, request):
        recipient = request.POST.get("recipient")
        subject = request.POST.get("subject")
        message = request.POST.get("message")
        
        if not recipient or not subject or not message:
            messages.error(request, _("请填写完整信息"))
            return redirect("administration:debug_email")
            
        try:
            from django.core.mail import send_mail
            send_mail(
                subject,
                message,
                None, # Use default FROM
                [recipient],
                fail_silently=False,
            )
            messages.success(request, _("邮件发送成功"))
        except Exception as e:
            messages.error(request, _("发送失败: {error}").format(error=str(e)))
            
        return redirect("administration:debug_email")
