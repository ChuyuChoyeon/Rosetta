from typing import Any, Dict, List
from django.db.models import QuerySet, Sum, Q
from django.http import HttpRequest, HttpResponseRedirect, JsonResponse
from django.views import View
from django.views.generic import (
    TemplateView,
    ListView,
    UpdateView,
    CreateView,
    DeleteView,
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from django.contrib import messages
from django.conf import settings
from blog.models import Post, Comment, Category, Tag, PostViewHistory
from core.models import Page, Navigation, FriendLink, SearchPlaceholder
from voting.models import Poll
from django import get_version
import platform
from .forms import (
    PostForm,
    CategoryForm,
    TagForm,
    PageForm,
    NavigationForm,
    FriendLinkForm,
    UserForm,
    GroupForm,
    SearchPlaceholderForm,
    UserTitleForm,
    PollForm,
    ChoiceFormSet,
)
from django.utils import timezone
import django
from django.db.models import Count
from django.db.models.functions import TruncDate
from datetime import timedelta
import psutil
import sys
from users.models import UserTitle
from django.contrib.auth.models import Group
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
import os
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse, Http404
from core.utils import (
    trigger_watson_rebuild_async,
    queue_post_images_async,
    trigger_media_scan_async,
    trigger_media_clean_async,
    list_backups,
    create_backup,
    delete_backup,
    restore_backup,
)
import uuid
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_str
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


class AuditLogMixin:
    """
    操作日志混入类

    自动记录用户的操作日志 (Create, Update, Delete)。
    """

    def log_action(self, action_flag, object_repr=None, change_message=""):
        if not self.request.user.is_authenticated:
            return

        obj = getattr(self, "object", None)
        if not obj and hasattr(self, "get_object"):
            try:
                obj = self.get_object()
            except Exception:
                pass

        if not obj:
            return

        try:
            content_type = ContentType.objects.get_for_model(obj)
            object_repr = object_repr or force_str(obj)

            # Use create() directly to avoid manager issues and ensure compatibility
            LogEntry.objects.create(
                user_id=self.request.user.pk,
                content_type_id=content_type.pk,
                object_id=str(obj.pk),
                object_repr=object_repr[:200],
                action_flag=action_flag,
                change_message=change_message,
            )
        except Exception as e:
            # In development, print errors to help debugging
            if settings.DEBUG:
                logger.error(f"Failed to create audit log: {e}")
            pass


class StaffRequiredMixin(UserPassesTestMixin):
    """
    权限混入类：仅允许管理员（is_staff=True）访问。

    用于保护管理后台的所有视图，确保只有具备管理员权限的用户才能访问。
    """

    def test_func(self) -> bool:
        return self.request.user.is_staff


class SuperuserRequiredMixin(UserPassesTestMixin):
    """
    权限混入类：仅允许超级管理员（is_superuser=True）访问。
    """

    def test_func(self) -> bool:
        return self.request.user.is_superuser


class DebugToolRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not getattr(settings, "DEBUG_TOOL_ENABLED", False):
            raise Http404("Not found")
        return super().dispatch(request, *args, **kwargs)


class IndexView(LoginRequiredMixin, StaffRequiredMixin, TemplateView):
    """
    管理后台首页视图

    展示系统概览，包括关键指标、图表数据和服务器状态。
    """

    template_name: str = "administration/index.html"
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context: Dict[str, Any] = super().get_context_data(**kwargs)

        # 1. 关键指标统计 (Key Metrics)
        today = timezone.now()
        last_month = today - timedelta(days=30)

        post_counts = Post.objects.aggregate(
            total=Count("id"),
            last_month=Count("id", filter=Q(created_at__gte=last_month)),
        )
        total_posts = post_counts["total"] or 0
        posts_last_month = post_counts["last_month"] or 0

        # 计算增长率 (净增量 / 上期总量)
        total_prev = total_posts - posts_last_month
        post_growth = 0
        if total_prev > 0:
            post_growth = (posts_last_month / total_prev) * 100
        elif posts_last_month > 0:
            post_growth = 100

        context["total_posts"] = total_posts
        context["post_growth"] = round(post_growth, 1)

        # 评论数据
        comment_counts = Comment.objects.aggregate(
            total=Count("id"),
            pending=Count("id", filter=Q(active=False)),
            active=Count("id", filter=Q(active=True)),
        )
        total_comments = comment_counts["total"] or 0
        pending_comments = comment_counts["pending"] or 0
        context["total_comments"] = total_comments
        context["pending_comments"] = pending_comments

        # 2. 图表数据 (Charts Data)

        # 评论状态分布 (饼图)
        active_comments = comment_counts["active"] or 0
        inactive_comments = pending_comments
        context["comment_status_data"] = [active_comments, inactive_comments]

        # 用户角色分布 (环形图)
        user_counts = User.objects.aggregate(
            superusers=Count("id", filter=Q(is_superuser=True)),
            staff=Count("id", filter=Q(is_staff=True, is_superuser=False)),
            normal=Count("id", filter=Q(is_staff=False)),
        )
        superusers = user_counts["superusers"] or 0
        staff = user_counts["staff"] or 0
        normal_users = user_counts["normal"] or 0
        context["user_role_data"] = [superusers, staff, normal_users]

        # 评论趋势 (折线图) - 最近30天
        trend_data = (
            Comment.objects.filter(created_at__gte=last_month)
            .annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )

        # 用户注册趋势
        user_trend = (
            User.objects.filter(date_joined__gte=last_month)
            .annotate(date=TruncDate("date_joined"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )

        # 补全缺失日期的据
        date_map = {item["date"]: item["count"] for item in trend_data}
        user_date_map = {item["date"]: item["count"] for item in user_trend}
        
        dates = []
        counts = []
        user_counts = []
        
        for i in range(30):
            d = (last_month + timedelta(days=i)).date()
            dates.append(d.strftime("%m-%d"))
            counts.append(date_map.get(d, 0))
            user_counts.append(user_date_map.get(d, 0))

        context["trend_dates"] = dates
        context["trend_counts"] = counts
        context["user_trend_counts"] = user_counts

        # 热门文章 Top 5 (柱状图)
        top_posts = list(Post.objects.only("id", "title", "views").order_by("-views")[:5])
        context["top_posts"] = top_posts
        context["top_posts_labels"] = [
            p.title[:10] + "..." if len(p.title) > 10 else p.title for p in top_posts
        ]

        # 分类分布 (饼图)
        category_counts = (
            Category.objects.annotate(count=Count("posts"))
            .values("name", "count")
            .order_by("-count")
        )
        # 使用 json.dumps 确保正确的 JSON 格式
        context["category_labels"] = json.dumps([c["name"] for c in category_counts], ensure_ascii=False)
        context["category_data"] = json.dumps([c["count"] for c in category_counts])

        # 标签使用 Top 10 (柱状图)
        tag_counts = (
            Tag.objects.annotate(count=Count("posts"))
            .values("name", "count")
            .order_by("-count")[:10]
        )
        context["tag_labels"] = json.dumps([t["name"] for t in tag_counts], ensure_ascii=False)
        context["tag_data"] = json.dumps([t["count"] for t in tag_counts])

        # 之前的趋势数据也建议做相同处理
        context["trend_dates"] = json.dumps(dates, ensure_ascii=False)
        context["trend_counts"] = json.dumps(counts)
        context["user_trend_counts"] = json.dumps(user_counts)

        # 评论状态分布
        context["comment_status_data"] = json.dumps([active_comments, inactive_comments])

        # 系统健康状态 (实时数据)
        try:
            cpu_usage = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            # 计算进程运行时间
            p = psutil.Process()
            create_time = p.create_time()
            uptime_seconds = timezone.now().timestamp() - create_time
            uptime = timedelta(seconds=int(uptime_seconds))

            # 格式化运行时间 (例如 "2天 4小时")
            days = uptime.days
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, _ = divmod(remainder, 60)

            uptime_str = ""
            if days > 0:
                uptime_str += f"{days}天 "
            if hours > 0:
                uptime_str += f"{hours}小时 "
            uptime_str += f"{minutes}分钟"
            if not uptime_str:
                uptime_str = "刚刚启动"

            context["system_info"] = {
                "cpu_percent": cpu_usage,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "python_version": platform.python_version(),
                "django_version": django.get_version(),
                "platform_system": platform.system(),
                "platform_release": platform.release(),
                "server_time": timezone.now(),
                "uptime": uptime_str,
            }
            # 简化健康评分 (反向负载)
            health_score = 100 - max(cpu_usage, memory.percent, disk.percent)
            context["system_health"] = int(max(0, health_score))
        except Exception:
            context["system_info"] = {}
            context["system_health"] = 85  # 获取失败时的默认值

        # 最近动态 (用于 Feed 流)
        context["recent_comments"] = Comment.objects.select_related(
            "user", "post"
        ).order_by("-created_at")[:5]

        return context


# --- 通用 CRUD 混入类 (Generic CRUD Mixins) ---
class BaseListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    """
    基础列表视图混入类

    提供通用的列表展示功能，集成了 HTMX 支持。

    特性：
    1. 默认分页大小为 20。
    2. 支持动态排序 (GET sort/order 参数)。
    3. 支持 HTMX 局部刷新：检测 HX-Request 头，返回局部模板或完整页面。
    """

    paginate_by = 20
    template_name_suffix = "_list"

    def get_ordering(self):
        sort_by = self.request.GET.get("sort")
        if sort_by:
            allowed_fields = {field.name for field in self.model._meta.fields}
            if sort_by in allowed_fields:
                order = self.request.GET.get("order", "asc")
                if order == "desc":
                    return f"-{sort_by}"
                return sort_by
        return self.ordering

    def get_template_names(self) -> List[str]:
        # HTMX 局部刷新支持
        # 如果是 HTMX 请求且非 Boosted 请求（全页导航），则仅返回局部模板
        if self.request.headers.get("HX-Request") and not self.request.headers.get(
            "HX-Boosted"
        ):
            return [
                f"administration/partials/{self.model._meta.model_name}_list_rows.html"
            ]

        # 优先使用显式定义的 template_name
        if self.template_name:
            return [self.template_name]

        return [f"administration/{self.model._meta.model_name}_list.html"]


class BaseCreateView(AuditLogMixin, LoginRequiredMixin, StaffRequiredMixin, CreateView):
    """
    基础创建视图混入类

    提供通用的对象创建功能。

    特性：
    1. 自动查找模板 ({model}_form.html 或 generic_form.html)。
    2. 处理保存后的跳转逻辑 (保存并继续编辑、保存并新增另一个)。
    3. 集成消息提示 (创建成功)。
    4. 自动记录操作日志 (AuditLogMixin)。
    """

    template_name_suffix = "_form"

    def get_template_names(self) -> List[str]:
        return [
            f"administration/{self.model._meta.model_name}_form.html",
            "administration/generic_form.html",
        ]

    def get_success_url(self):
        if "_continue" in self.request.POST:
            return reverse_lazy(
                f"administration:{self.model._meta.model_name}_edit",
                kwargs={"pk": self.object.pk},
            )
        if "_addanother" in self.request.POST:
            return reverse_lazy(f"administration:{self.model._meta.model_name}_create")
        return super().get_success_url()

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"{self.model._meta.verbose_name} 创建成功")
        self.log_action(ADDITION, change_message="通过管理后台创建")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        verbose_name = self.model._meta.verbose_name
        context["title"] = f"新建{verbose_name}"
        return context


class BaseUpdateView(AuditLogMixin, LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    """
    基础更新视图混入类

    提供通用的对象更新功能。
    逻辑与 BaseCreateView 类似，但用于编辑现有对象。
    """

    template_name_suffix = "_form"

    def get_template_names(self) -> List[str]:
        return [
            f"administration/{self.model._meta.model_name}_form.html",
            "administration/generic_form.html",
        ]

    def get_success_url(self):
        if "_continue" in self.request.POST:
            return reverse_lazy(
                f"administration:{self.model._meta.model_name}_edit",
                kwargs={"pk": self.object.pk},
            )
        if "_addanother" in self.request.POST:
            return reverse_lazy(f"administration:{self.model._meta.model_name}_create")
        return super().get_success_url()

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"{self.model._meta.verbose_name} 更新成功")
        
        # 尝试检测变更字段 (简单的实现)
        changed_data = form.changed_data
        msg = "通过管理后台更新"
        if changed_data:
            msg = f"更新字段: {', '.join(changed_data)}"
        
        self.log_action(CHANGE, change_message=msg)
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        verbose_name = self.model._meta.verbose_name
        context["title"] = f"编辑{verbose_name}"
        return context


class BaseExportView(LoginRequiredMixin, StaffRequiredMixin, View):
    """
    基础导出视图

    将模型数据导出为 JSON 文件。
    """

    model = None

    def get(self, request, *args, **kwargs):
        if not self.model:
            raise NotImplementedError("BaseExportView requires a model definition")

        queryset = self.model.objects.all()
        data = list(queryset.values())

        # 处理 datetime 和 UUID 等无法序列化的对象
        response = HttpResponse(
            json.dumps(data, cls=DjangoJSONEncoder, ensure_ascii=False, indent=2),
            content_type="application/json",
        )
        filename = f"{self.model._meta.model_name}_export_{timezone.now().strftime('%Y%m%d%H%M%S')}.json"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class BaseImportView(LoginRequiredMixin, StaffRequiredMixin, View):
    """
    基础导入视图

    从 JSON 文件导入数据。
    """

    model = None
    success_url = None

    def post(self, request, *args, **kwargs):
        if not self.model:
            raise NotImplementedError("BaseImportView requires a model definition")

        if "json_file" not in request.FILES:
            messages.error(request, "请上传 JSON 文件")
            return redirect(self.success_url)

        json_file = request.FILES["json_file"]
        try:
            data = json.load(json_file)
            if not isinstance(data, list):
                raise ValueError("JSON 格式错误：根元素应为列表")

            success_count = 0
            for item in data:
                # 移除 id 以避免冲突，或用于查找
                item_id = item.pop("id", None)

                # 尝试查找唯一键
                lookup_fields = {}
                if hasattr(self.model, "slug") and "slug" in item:
                    lookup_fields["slug"] = item["slug"]
                elif hasattr(self.model, "username") and "username" in item:
                    lookup_fields["username"] = item["username"]
                elif hasattr(self.model, "name") and "name" in item:
                    lookup_fields["name"] = item["name"]
                elif item_id:
                    lookup_fields["id"] = item_id

                if lookup_fields:
                    obj, created = self.model.objects.update_or_create(
                        defaults=item, **lookup_fields
                    )
                    success_count += 1
                else:
                    self.model.objects.create(**item)
                    success_count += 1

            messages.success(request, f"成功导入 {success_count} 条数据")

        except Exception as e:
            messages.error(request, f"导入失败: {str(e)}")

        return redirect(self.success_url)


class BaseDeleteView(AuditLogMixin, LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    """
    基础删除视图混入类

    提供通用的对象删除确认功能。
    支持标准 POST 删除和 HTMX 删除。
    """

    template_name = "administration/generic_confirm_delete.html"

    def form_valid(self, form):
        success_url = self.get_success_url()
        
        # 在删除前记录日志
        try:
            self.object = self.get_object()
            self.log_action(DELETION, change_message="通过管理后台删除")
        except Exception:
            pass

        self.object.delete()

        # HTMX Support
        if self.request.headers.get("HX-Request"):
            # 返回空内容以移除行，并触发 Toast 消息
            response = HttpResponse("")
            response["HX-Trigger"] = json.dumps(
                {
                    "show-toast": {
                        "message": f"{self.model._meta.verbose_name} 删除成功",
                        "type": "success",
                    }
                }
            )
            return response

        messages.success(self.request, f"{self.model._meta.verbose_name} 删除成功")
        return HttpResponseRedirect(success_url)


from django.shortcuts import get_object_or_404, redirect
from django.db.models import Count
import uuid


# --- Post Views (文章管理视图) ---
class PostListView(BaseListView):
    """
    文章列表视图

    展示博客文章列表。
    支持：
    - 关键词搜索 (标题)
    - 状态过滤 (草稿/发布)
    - 关联查询优化 (author, category)
    """

    model = Post
    context_object_name = "posts"
    ordering = ["-is_pinned", "-published_at", "-created_at"]
    paginate_by = 20

    def get_queryset(self) -> QuerySet[Post]:
        qs = super().get_queryset()
        qs = qs.select_related("author", "category").prefetch_related("tags")

        query = self.request.GET.get("q")
        status = self.request.GET.get("status")

        if query:
            qs = qs.filter(title__icontains=query)

        if status:
            qs = qs.filter(status=status)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 统计数据
        context["total_count"] = Post.objects.count()
        context["published_count"] = Post.objects.filter(status="published").count()
        context["draft_count"] = Post.objects.filter(status="draft").count()
        return context

    def get_template_names(self) -> List[str]:
        # HTMX 局部刷新支持
        if self.request.headers.get("HX-Request") and not self.request.headers.get(
            "HX-Boosted"
        ):
            return [
                f"administration/partials/{self.model._meta.model_name}_list_rows.html"
            ]
        return [f"administration/{self.model._meta.model_name}_list.html"]


class PostCreateView(BaseCreateView):
    """
    文章创建视图

    创建新文章。
    自动将当前登录用户设置为文章作者。
    """

    model = Post
    form_class = PostForm
    success_url = reverse_lazy("administration:post_list")

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(BaseUpdateView):
    """
    文章更新视图

    编辑现有文章的内容、状态、分类等。
    """

    model = Post
    form_class = PostForm
    success_url = reverse_lazy("administration:post_list")


class PostDeleteView(BaseDeleteView):
    """
    文章删除视图

    物理删除文章记录。
    """

    model = Post
    success_url = reverse_lazy("administration:post_list")


class PostDuplicateView(LoginRequiredMixin, StaffRequiredMixin, View):
    """
    文章复制视图

    快速复制一篇文章及其标签，用于创建相似内容的草稿。
    新文章状态默认为"草稿"，标题追加"(副本)"后缀。
    """

    def post(self, request, pk):
        try:
            post = get_object_or_404(Post, pk=pk)
            # 在清除 pk 之前保存 M2M 数据
            tags = list(post.tags.all())

            post.pk = None
            post.slug = f"{post.slug}-{uuid.uuid4().hex[:6]}"
            post.title = f"{post.title} (副本)"
            post.status = "draft"
            post.views = 0
            post.save()

            # 恢复 M2M 关系
            post.tags.set(tags)

            messages.success(request, "文章已复制为草稿")
        except Exception as e:
            messages.error(request, f"复制失败: {str(e)}")

        return redirect("administration:post_list")


# --- Category Views (分类管理视图) ---
class CategoryListView(BaseListView):
    """
    分类列表视图

    展示文章分类。
    支持按名称搜索，并统计每个分类下的文章数量。
    """

    model = Category
    context_object_name = "categories"
    ordering = ["name"]

    def get_queryset(self) -> QuerySet[Category]:
        qs = super().get_queryset().annotate(post_count=Count("posts"))
        query = self.request.GET.get("q")
        if query:
            qs = qs.filter(name__icontains=query)
        return qs


class CategoryCreateView(BaseCreateView):
    """
    分类创建视图
    """

    model = Category
    form_class = CategoryForm
    success_url = reverse_lazy("administration:category_list")


class CategoryUpdateView(BaseUpdateView):
    """
    分类更新视图
    """

    model = Category
    form_class = CategoryForm
    success_url = reverse_lazy("administration:category_list")


class CategoryDeleteView(BaseDeleteView):
    """
    分类删除视图
    """

    model = Category
    success_url = reverse_lazy("administration:category_list")


class CategoryExportView(BaseExportView):
    """
    分类导出视图
    """

    model = Category


class CategoryImportView(BaseImportView):
    """
    分类导入视图
    """

    model = Category
    success_url = reverse_lazy("administration:category_list")


# --- Tag Views (标签管理视图) ---
class TagListView(BaseListView):
    """
    标签列表视图

    展示文章标签。
    支持按名称搜索，并统计每个标签下的文章数量。
    """

    model = Tag
    context_object_name = "tags"
    ordering = ["name"]

    def get_queryset(self) -> QuerySet[Tag]:
        qs = super().get_queryset().annotate(post_count=Count("posts"))
        query = self.request.GET.get("q")
        status = self.request.GET.get("status")

        if query:
            qs = qs.filter(name__icontains=query)

        if status == "active":
            qs = qs.filter(is_active=True)
        elif status == "inactive":
            qs = qs.filter(is_active=False)

        return qs


class TagCreateView(BaseCreateView):
    """
    标签创建视图
    """

    model = Tag
    form_class = TagForm
    success_url = reverse_lazy("administration:tag_list")


class TagUpdateView(BaseUpdateView):
    """
    标签更新视图
    """

    model = Tag
    form_class = TagForm
    success_url = reverse_lazy("administration:tag_list")


class TagDeleteView(BaseDeleteView):
    """
    标签删除视图
    """

    model = Tag
    success_url = reverse_lazy("administration:tag_list")


class TagAutocompleteView(LoginRequiredMixin, StaffRequiredMixin, View):
    """
    标签自动补全视图

    返回 JSON 格式的标签建议列表，用于前端输入联想。
    """

    def get(self, request):
        query = request.GET.get("q", "")
        if len(query) < 1:
            return JsonResponse({"results": []})

        tags = Tag.objects.filter(name__icontains=query).values_list("name", flat=True)[
            :10
        ]
        return JsonResponse({"results": list(tags)})


class TagExportView(BaseExportView):
    """
    标签导出视图
    """

    model = Tag


class TagImportView(BaseImportView):
    """
    标签导入视图
    """

    model = Tag
    success_url = reverse_lazy("administration:tag_list")


# --- Comment Views (评论管理视图) ---
class CommentListView(BaseListView):
    """
    评论列表视图

    展示所有评论。
    支持：
    - 内容搜索
    - 状态过滤 (已审核/待审核)
    - 关联查询优化 (post, user, parent)
    """

    model = Comment
    context_object_name = "comments"
    ordering = ["-created_at"]
    paginate_by = 20

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .select_related("post", "user", "parent", "parent__user")
        )
        query = self.request.GET.get("q")
        status = self.request.GET.get("status")
        user_id = self.request.GET.get("user")
        post_id = self.request.GET.get("post")

        if query:
            qs = qs.filter(content__icontains=query)

        if status == "active":
            qs = qs.filter(active=True)
        elif status == "pending":
            qs = qs.filter(active=False)

        if user_id:
            qs = qs.filter(user_id=user_id)

        if post_id:
            qs = qs.filter(post_id=post_id)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 添加统计数据
        context["total_count"] = Comment.objects.count()
        context["pending_count"] = Comment.objects.filter(active=False).count()
        context["active_count"] = Comment.objects.filter(active=True).count()
        return context


class CommentUpdateView(BaseUpdateView):
    """
    评论更新视图

    支持修改评论内容和审核状态 (active)。
    """

    model = Comment
    fields = ["content", "active"]
    success_url = reverse_lazy("administration:comment_list")


class CommentReplyView(LoginRequiredMixin, StaffRequiredMixin, View):
    """
    评论回复视图

    管理员直接在后台回复用户评论。
    """

    def post(self, request, pk):
        parent_comment = get_object_or_404(Comment, pk=pk)
        content = request.POST.get("content")

        if not content:
            messages.error(request, "回复内容不能为空")
            return redirect("administration:comment_list")

        Comment.objects.create(
            post=parent_comment.post,
            user=request.user,
            parent=parent_comment,
            content=content,
            active=True,  # 管理员回复默认可见
        )

        messages.success(request, "回复已发布")
        return redirect("administration:comment_list")


class CommentDeleteView(BaseDeleteView):
    """
    评论删除视图
    """

    model = Comment
    success_url = reverse_lazy("administration:comment_list")


# --- Page Views (单页面管理视图) ---
class PageListView(BaseListView):
    """
    单页面列表视图

    展示独立页面（如关于我们、联系我们）。
    支持按标题搜索和状态过滤。
    """

    model = Page
    context_object_name = "pages"
    ordering = ["-created_at"]

    def get_queryset(self) -> QuerySet[Page]:
        qs = super().get_queryset()
        query = self.request.GET.get("q")
        status = self.request.GET.get("status")

        if query:
            qs = qs.filter(title__icontains=query)

        if status:
            qs = qs.filter(status=status)

        return qs


class PageCreateView(BaseCreateView):
    """
    单页面创建视图
    """

    model = Page
    form_class = PageForm
    success_url = reverse_lazy("administration:page_list")


class PageUpdateView(BaseUpdateView):
    """
    单页面更新视图
    """

    model = Page
    form_class = PageForm
    success_url = reverse_lazy("administration:page_list")


class PageDeleteView(BaseDeleteView):
    """
    单页面删除视图
    """

    model = Page
    success_url = reverse_lazy("administration:page_list")


class PageDuplicateView(LoginRequiredMixin, StaffRequiredMixin, View):
    """
    单页面复制视图

    快速复制一个页面，新页面标题追加"(副本)"后缀，状态为草稿。
    """

    def post(self, request, pk):
        try:
            page = get_object_or_404(Page, pk=pk)
            page.pk = None
            page.slug = f"{page.slug}-{uuid.uuid4().hex[:6]}"
            page.title = f"{page.title} (副本)"
            page.status = "draft"
            page.save()

            messages.success(request, "页面已复制为草稿")
        except Exception as e:
            messages.error(request, f"复制失败: {str(e)}")

        return redirect("administration:page_list")


# --- Navigation Views (导航菜单视图) ---
class NavigationListView(BaseListView):
    """
    导航菜单列表视图

    展示前台导航栏菜单项。
    支持按标题搜索，默认按 order 字段排序。
    """

    model = Navigation
    context_object_name = "navigations"
    ordering = ["order"]

    def get_queryset(self) -> QuerySet[Navigation]:
        qs = super().get_queryset()
        query = self.request.GET.get("q")
        location = self.request.GET.get("location")

        if query:
            qs = qs.filter(title__icontains=query)

        if location:
            qs = qs.filter(location=location)

        return qs


class NavigationCreateView(BaseCreateView):
    """
    导航菜单创建视图
    """

    model = Navigation
    form_class = NavigationForm
    success_url = reverse_lazy("administration:navigation_list")


class NavigationUpdateView(BaseUpdateView):
    """
    导航菜单更新视图
    """

    model = Navigation
    form_class = NavigationForm
    success_url = reverse_lazy("administration:navigation_list")


class NavigationDeleteView(BaseDeleteView):
    """
    导航删除视图
    """

    model = Navigation
    success_url = reverse_lazy("administration:navigation_list")


class NavigationExportView(BaseExportView):
    """
    导航导出视图
    """

    model = Navigation


class NavigationImportView(BaseImportView):
    """
    导航导入视图
    """

    model = Navigation
    success_url = reverse_lazy("administration:navigation_list")


class NavigationExportView(BaseExportView):
    """
    导航菜单导出视图
    """

    model = Navigation


class NavigationImportView(BaseImportView):
    """
    导航菜单导入视图
    """

    model = Navigation
    success_url = reverse_lazy("administration:navigation_list")


# --- FriendLink Views (友情链接视图) ---
class FriendLinkListView(BaseListView):
    """
    友情链接列表视图

    展示友情链接。
    支持按名称搜索，默认按 order 字段排序。
    """

    model = FriendLink
    context_object_name = "friendlinks"
    ordering = ["order"]

    def get_queryset(self) -> QuerySet[FriendLink]:
        qs = super().get_queryset()
        query = self.request.GET.get("q")
        is_active = self.request.GET.get("is_active")

        if query:
            qs = qs.filter(name__icontains=query)

        if is_active == "true":
            qs = qs.filter(is_active=True)
        elif is_active == "false":
            qs = qs.filter(is_active=False)

        return qs


class FriendLinkCreateView(BaseCreateView):
    """
    友情链接创建视图
    """

    model = FriendLink
    form_class = FriendLinkForm
    success_url = reverse_lazy("administration:friendlink_list")


class FriendLinkUpdateView(BaseUpdateView):
    """
    友情链接更新视图
    """

    model = FriendLink
    form_class = FriendLinkForm
    success_url = reverse_lazy("administration:friendlink_list")


class FriendLinkDeleteView(BaseDeleteView):
    """
    友情链接删除视图
    """

    model = FriendLink
    success_url = reverse_lazy("administration:friendlink_list")


class FriendLinkExportView(BaseExportView):
    """
    友情链接导出视图
    """

    model = FriendLink


class FriendLinkImportView(BaseImportView):
    """
    友情链接导入视图
    """

    model = FriendLink
    success_url = reverse_lazy("administration:friendlink_list")


# --- Search Placeholder Views (搜索占位符视图) ---
class SearchPlaceholderListView(BaseListView):
    """
    搜索占位符列表视图

    管理前台搜索框的动态提示文字。
    """

    model = SearchPlaceholder
    template_name = "administration/searchplaceholder_list.html"
    context_object_name = "placeholders"
    ordering = ["order", "-created_at"]

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get("q")
        is_active = self.request.GET.get("is_active")

        if q:
            qs = qs.filter(text__icontains=q)

        if is_active == "true":
            qs = qs.filter(is_active=True)
        elif is_active == "false":
            qs = qs.filter(is_active=False)

        return qs


class SearchPlaceholderCreateView(BaseCreateView):
    """
    搜索占位符创建视图
    """

    model = SearchPlaceholder
    form_class = SearchPlaceholderForm
    success_url = reverse_lazy("administration:searchplaceholder_list")


class SearchPlaceholderUpdateView(BaseUpdateView):
    """
    搜索占位符更新视图
    """

    model = SearchPlaceholder
    form_class = SearchPlaceholderForm
    success_url = reverse_lazy("administration:searchplaceholder_list")


class SearchPlaceholderDeleteView(BaseDeleteView):
    """
    搜索占位符删除视图
    """

    model = SearchPlaceholder
    success_url = reverse_lazy("administration:searchplaceholder_list")


class SearchPlaceholderExportView(BaseExportView):
    """
    搜索占位符导出视图
    """

    model = SearchPlaceholder


class SearchPlaceholderImportView(BaseImportView):
    """
    搜索占位符导入视图
    """

    model = SearchPlaceholder
    success_url = reverse_lazy("administration:searchplaceholder_list")


# --- User Views (用户管理视图) ---
class UserListView(BaseListView):
    """
    用户列表视图

    展示注册用户列表。
    支持按用户名搜索。
    """

    model = User
    context_object_name = "users"
    ordering = ["-date_joined"]

    def get_queryset(self):
        qs = super().get_queryset().select_related("title")
        query = self.request.GET.get("q")
        is_staff = self.request.GET.get("is_staff")
        is_active = self.request.GET.get("is_active")

        if query:
            qs = qs.filter(username__icontains=query)

        if is_staff == "true":
            qs = qs.filter(is_staff=True)
        elif is_staff == "false":
            qs = qs.filter(is_staff=False)

        if is_active == "true":
            qs = qs.filter(is_active=True)
        elif is_active == "false":
            qs = qs.filter(is_active=False)

        return qs


class UserCreateView(BaseCreateView):
    """
    用户创建视图

    允许管理员在后台直接创建用户。
    包含密码设置逻辑（在 UserForm 中处理）。
    """

    model = User
    form_class = UserForm
    success_url = reverse_lazy("administration:user_list")

    def form_valid(self, form):
        # 密码处理逻辑在 UserForm.save() 中
        return super().form_valid(form)


class UserUpdateView(BaseUpdateView):
    """
    用户更新视图

    编辑用户信息（如权限、状态、基本资料）。
    """

    model = User
    form_class = UserForm
    success_url = reverse_lazy("administration:user_list")


class UserDeleteView(BaseDeleteView):
    """
    用户删除视图
    """

    model = User
    success_url = reverse_lazy("administration:user_list")


class UserExportView(BaseExportView):
    """
    用户导出视图
    """

    model = User
    exclude_fields = [
        "password",
        "is_superuser",
        "is_staff",
        "groups",
        "user_permissions",
    ]


class UserImportView(BaseImportView):
    """
    用户导入视图
    """

    model = User
    success_url = reverse_lazy("administration:user_list")
    exclude_fields = [
        "password",
        "is_superuser",
        "is_staff",
        "groups",
        "user_permissions",
        "last_login",  # 避免覆盖登录时间
    ]


# --- User Title Views (用户称号视图) ---
class UserTitleListView(BaseListView):
    """
    用户称号列表视图
    """

    model = UserTitle
    context_object_name = "titles"


class UserTitleCreateView(BaseCreateView):
    """
    用户称号创建视图
    """

    model = UserTitle
    form_class = UserTitleForm
    success_url = reverse_lazy("administration:usertitle_list")


class UserTitleUpdateView(BaseUpdateView):
    """
    用户称号更新视图
    """

    model = UserTitle
    form_class = UserTitleForm
    success_url = reverse_lazy("administration:usertitle_list")


class UserTitleDeleteView(BaseDeleteView):
    """
    用户称号删除视图
    """

    model = UserTitle
    success_url = reverse_lazy("administration:usertitle_list")


class UserTitleExportView(BaseExportView):
    """
    用户称号导出视图
    """

    model = UserTitle


class UserTitleImportView(BaseImportView):
    """
    用户称号导入视图
    """

    model = UserTitle
    success_url = reverse_lazy("administration:usertitle_list")


# --- Group Views (用户组管理视图) ---
class GroupListView(BaseListView):
    """
    用户组列表视图
    """

    model = Group
    context_object_name = "groups"
    ordering = ["name"]


class GroupCreateView(BaseCreateView):
    """
    用户组创建视图
    """

    model = Group
    form_class = GroupForm
    success_url = reverse_lazy("administration:group_list")


class GroupUpdateView(BaseUpdateView):
    """
    用户组更新视图
    """

    model = Group
    form_class = GroupForm
    success_url = reverse_lazy("administration:group_list")


class GroupDeleteView(BaseDeleteView):
    """
    用户组删除视图
    """

    model = Group
    success_url = reverse_lazy("administration:group_list")


class GroupExportView(BaseExportView):
    """
    用户组导出视图
    """

    model = Group


class GroupImportView(BaseImportView):
    """
    用户组导入视图
    """

    model = Group
    success_url = reverse_lazy("administration:group_list")


# --- LogEntry Views (操作日志管理视图) ---
class LogEntryListView(BaseListView):
    """
    操作日志列表视图

    展示 Django Admin LogEntry。
    """

    model = LogEntry
    context_object_name = "logentries"
    ordering = ["-action_time"]
    template_name = "administration/logentry_list.html"

    def get_queryset(self):
        qs = super().get_queryset().select_related("user", "content_type")
        query = self.request.GET.get("q")
        if query:
            qs = qs.filter(object_repr__icontains=query)

        user_id = self.request.GET.get("user")
        if user_id:
            qs = qs.filter(user_id=user_id)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 获取所有有日志的用户，用于筛选
        context["users_with_logs"] = User.objects.filter(
            id__in=LogEntry.objects.values_list("user_id", flat=True).distinct()
        )
        return context


class LogEntryDeleteView(BaseDeleteView):
    """
    操作日志删除视图
    """

    model = LogEntry
    success_url = reverse_lazy("administration:logentry_list")


class LogEntryExportView(LoginRequiredMixin, StaffRequiredMixin, View):
    """
    操作日志导出视图
    """

    def get(self, request):
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="audit_logs.csv"'

        writer = csv.writer(response)
        writer.writerow(["Time", "User", "Action", "Content Type", "Object", "Message"])

        logs = LogEntry.objects.select_related("user", "content_type").order_by(
            "-action_time"
        )
        for log in logs.iterator():
            writer.writerow(
                [
                    log.action_time,
                    log.user.username,
                    log.get_action_flag_display(),
                    str(log.content_type),
                    log.object_repr,
                    log.change_message,
                ]
            )

        return response


# --- System Log File Views (系统日志文件视图) ---
class LogFileListView(LoginRequiredMixin, StaffRequiredMixin, TemplateView):
    """
    系统日志文件查看器

    支持文件列表和内容查看，支持 AJAX 切换文件。
    """

    template_name = "administration/logfile_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        log_dir = settings.BASE_DIR / "logs"
        files = []

        # 1. 获取文件列表
        if log_dir.exists():
            for f in log_dir.iterdir():
                if f.is_file() and (f.suffix == ".log" or f.suffix == ".zip"):
                    stat = f.stat()
                    files.append(
                        {
                            "name": f.name,
                            "size": stat.st_size,
                            "mtime": datetime.fromtimestamp(stat.st_mtime),
                            "path": str(f),
                        }
                    )
        # 按修改时间倒序
        files.sort(key=lambda x: x["mtime"], reverse=True)
        context["log_files"] = files

        # 2. 确定当前选中的文件
        current_file = self.request.GET.get("file")
        if not current_file and files:
            current_file = files[0]["name"]  # 默认选中最新的

        context["current_file"] = current_file

        # 3. 读取当前文件内容
        content = ""
        file_info = None

        if current_file:
            # 查找选中的文件信息
            for f in files:
                if f["name"] == current_file:
                    file_info = f
                    break

            if file_info and file_info["name"].endswith(".log"):
                file_path = log_dir / current_file
                try:
                    # 读取最后 2000 行
                    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                        from collections import deque

                        lines = list(deque(f, 2000))
                        content = "".join(lines)
                except Exception as e:
                    content = f"Error reading file: {str(e)}"
            elif file_info and file_info["name"].endswith(".zip"):
                content = (
                    "ZIP archives cannot be viewed directly. Please download to view."
                )

        context["log_content"] = content
        context["current_file_info"] = file_info

        return context


from datetime import datetime


class LogFileView(LoginRequiredMixin, StaffRequiredMixin, View):
    """
    查看系统日志文件内容
    """

    def get(self, request, filename):
        log_dir = settings.BASE_DIR / "logs"
        file_path = log_dir / filename

        # 安全检查：防止路径遍历
        if not file_path.resolve().is_relative_to(log_dir.resolve()):
            raise Http404("Invalid file path")

        if not file_path.exists():
            raise Http404("File not found")

        # 读取最后 2000 行
        lines = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                # 简单读取，大文件可能需要优化 (seek)
                # 这里假设日志文件不会特别巨大，或者我们只读最后一部分
                # 使用 deque 读取最后 N 行
                from collections import deque

                lines = list(deque(f, 2000))
        except Exception as e:
            lines = [f"Error reading file: {str(e)}"]

        content = "".join(lines)

        return render(
            request,
            "administration/logfile_detail.html",
            {"filename": filename, "content": content},
        )


class LogFileDownloadView(LoginRequiredMixin, StaffRequiredMixin, View):
    """
    下载系统日志文件
    """

    def get(self, request, filename):
        log_dir = settings.BASE_DIR / "logs"
        file_path = log_dir / filename

        if not file_path.resolve().is_relative_to(log_dir.resolve()):
            raise Http404("Invalid file path")

        if not file_path.exists():
            raise Http404("File not found")

        from django.http import FileResponse

        return FileResponse(
            open(file_path, "rb"), as_attachment=True, filename=filename
        )


class LogFileDeleteView(LoginRequiredMixin, StaffRequiredMixin, View):
    """
    删除或清空系统日志文件
    """

    def post(self, request, filename):
        log_dir = settings.BASE_DIR / "logs"
        file_path = log_dir / filename

        if not file_path.resolve().is_relative_to(log_dir.resolve()):
            messages.error(request, "非法文件路径")
        elif not file_path.exists():
            messages.error(request, "文件不存在")
        else:
            try:
                action = request.POST.get("action")
                if action == "clear":
                    # 清空文件内容，但不删除文件
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.truncate()
                    messages.success(request, f"文件 {filename} 内容已清空")
                else:
                    # 默认行为：删除文件
                    os.remove(file_path)
                    messages.success(request, f"文件 {filename} 已删除")
            except Exception as e:
                messages.error(request, f"操作失败: {str(e)}")

        return redirect("administration:logfile_list")


# --- Bulk Action View (批量操作视图) ---
from django.apps import apps


class BulkActionView(LoginRequiredMixin, StaffRequiredMixin, View):
    """
    批量操作视图

    处理列表页面的批量操作请求。

    支持的操作 (action):
    - delete: 删除
    - published: 发布 (Post)
    - draft: 转为草稿 (Post)
    - active: 启用 (Comment/User/FriendLink/Tag)
    - inactive: 禁用 (Comment/User/FriendLink/Tag)
    - export_json: 导出选中项为 JSON
    - set_staff: 设为管理员 (User)
    - remove_staff: 移除管理员权限 (User)
    """

    def post(self, request, model):
        action = request.POST.get("action")
        selected_ids = request.POST.getlist("selected_ids")

        if not action or not selected_ids:
            messages.warning(request, "请选择要操作的项目")
            return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))

        try:
            model_cls = None
            # 尝试查找模型
            try:
                model_cls = apps.get_model("blog", model)
            except LookupError:
                try:
                    model_cls = apps.get_model("core", model)
                except LookupError:
                    if model.lower() == "user":
                        model_cls = User

            if not model_cls:
                messages.error(request, f"未知模型: {model}")
                return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))

            if action == "delete":
                # 记录删除日志
                objects = model_cls.objects.filter(id__in=selected_ids)
                if request.user.is_authenticated:
                    content_type = ContentType.objects.get_for_model(model_cls)
                    user_id = request.user.pk
                    for obj in objects:
                        try:
                            LogEntry.objects.create(
                                user_id=user_id,
                                content_type_id=content_type.pk,
                                object_id=str(obj.pk),
                                object_repr=force_str(obj)[:200],
                                action_flag=DELETION,
                                change_message="通过管理后台批量删除",
                            )
                        except Exception as e:
                            logger.error(f"批量删除日志记录失败: {e}")
                
                objects.delete()
                messages.success(request, "批量删除成功")
            elif action == "published":
                if hasattr(model_cls, "status"):
                    model_cls.objects.filter(id__in=selected_ids).update(
                        status="published"
                    )
                    # 记录日志
                    if request.user.is_authenticated:
                        content_type = ContentType.objects.get_for_model(model_cls)
                        user_id = request.user.pk
                        for obj in model_cls.objects.filter(id__in=selected_ids):
                            try:
                                LogEntry.objects.create(
                                    user_id=user_id,
                                    content_type_id=content_type.pk,
                                    object_id=str(obj.pk),
                                    object_repr=force_str(obj)[:200],
                                    action_flag=CHANGE,
                                    change_message="批量发布",
                                )
                            except Exception as e:
                                logger.error(f"批量发布日志记录失败: {e}")
                    messages.success(request, "批量发布成功")
            elif action == "draft":
                if hasattr(model_cls, "status"):
                    model_cls.objects.filter(id__in=selected_ids).update(status="draft")
                    messages.success(request, "批量转为草稿成功")
            elif action == "active":
                if hasattr(model_cls, "active"):
                    model_cls.objects.filter(id__in=selected_ids).update(active=True)
                    messages.success(request, "批量启用成功")
                elif hasattr(model_cls, "is_active"):
                    model_cls.objects.filter(id__in=selected_ids).update(is_active=True)
                    messages.success(request, "批量启用成功")
            elif action == "inactive":
                if hasattr(model_cls, "active"):
                    model_cls.objects.filter(id__in=selected_ids).update(active=False)
                    messages.success(request, "批量禁用成功")
                elif hasattr(model_cls, "is_active"):
                    model_cls.objects.filter(id__in=selected_ids).update(
                        is_active=False
                    )
                    messages.success(request, "批量禁用成功")
            elif action == "export_json":
                from django.http import HttpResponse
                import json
                from django.core.serializers.json import DjangoJSONEncoder

                data = list(model_cls.objects.filter(id__in=selected_ids).values())
                response = HttpResponse(
                    json.dumps(data, cls=DjangoJSONEncoder, indent=4),
                    content_type="application/json",
                )
                response["Content-Disposition"] = (
                    f'attachment; filename="{model}_export.json"'
                )
                return response
            elif action == "set_staff":
                if model.lower() == "user":
                    model_cls.objects.filter(id__in=selected_ids).update(is_staff=True)
                    messages.success(request, "批量设为管理员成功")
            elif action == "remove_staff":
                if model.lower() == "user":
                    model_cls.objects.filter(id__in=selected_ids).update(is_staff=False)
                    messages.success(request, "批量移除管理员权限成功")

        except Exception as e:
            messages.error(request, f"操作失败: {str(e)}")

        return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))


# --- Export/Import Views (导入导出视图) ---
class ExportAllView(LoginRequiredMixin, StaffRequiredMixin, View):
    """
    导出全部数据视图

    将指定模型的所有数据导出为 JSON 文件。
    """

    def get(self, request, model):
        try:
            model_cls = None
            # 1. Try to find model in known apps
            for app_label in ["blog", "core", "users"]:
                try:
                    model_cls = apps.get_model(app_label, model)
                    break
                except LookupError:
                    continue

            # 2. Handle special cases
            if not model_cls:
                if model.lower() == "user":
                    model_cls = User
                elif model.lower() == "usertitle":
                    from users.models import UserTitle

                    model_cls = UserTitle
                elif model.lower() == "group":
                    model_cls = Group
                elif model.lower() == "logentry":
                    model_cls = LogEntry

            if not model_cls:
                messages.error(request, f"未知模型: {model}")
                return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))

            from django.http import HttpResponse
            import json
            from django.core.serializers.json import DjangoJSONEncoder

            data = list(model_cls.objects.all().values())
            response = HttpResponse(
                json.dumps(data, cls=DjangoJSONEncoder, indent=4, ensure_ascii=False),
                content_type="application/json",
            )
            response["Content-Disposition"] = (
                f'attachment; filename="{model}_all_export.json"'
            )
            return response
        except Exception as e:
            messages.error(request, f"导出失败: {str(e)}")
            return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))


class ImportJsonView(LoginRequiredMixin, StaffRequiredMixin, View):
    """
    导入 JSON 数据视图

    从 JSON 文件导入数据到指定模型。
    支持更新现有记录 (基于 ID 或其他唯一键) 或创建新记录。
    """

    def post(self, request, model):
        if "json_file" not in request.FILES:
            messages.error(request, "请上传文件")
            return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))

        json_file = request.FILES["json_file"]
        if not json_file.name.endswith(".json"):
            messages.error(request, "请上传 JSON 文件")
            return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))

        try:
            model_cls = None
            # 1. Try to find model in known apps
            for app_label in ["blog", "core", "users"]:
                try:
                    model_cls = apps.get_model(app_label, model)
                    break
                except LookupError:
                    continue

            # 2. Handle special cases
            if not model_cls:
                if model.lower() == "user":
                    model_cls = User
                elif model.lower() == "usertitle":
                    from users.models import UserTitle

                    model_cls = UserTitle
                elif model.lower() == "group":
                    model_cls = Group
                elif model.lower() == "logentry":
                    model_cls = LogEntry

            if not model_cls:
                messages.error(request, f"未知模型: {model}")
                return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))

            import json

            data = json.load(json_file)

            if not isinstance(data, list):
                messages.error(request, "JSON 格式错误: 必须是列表")
                return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))

            success_count = 0
            for item in data:
                # 尝试智能匹配唯一键
                pk = item.pop("id", None)
                lookup_fields = {}

                # 优先使用 slug, username, name 等作为唯一标识
                if hasattr(model_cls, "slug") and "slug" in item:
                    lookup_fields["slug"] = item["slug"]
                elif hasattr(model_cls, "username") and "username" in item:
                    lookup_fields["username"] = item["username"]
                elif hasattr(model_cls, "name") and "name" in item:
                    # name 并不总是唯一的，但对于 Category/Tag 来说通常是
                    # 检查 name 是否 unique
                    name_field = model_cls._meta.get_field("name")
                    if name_field.unique:
                        lookup_fields["name"] = item["name"]

                # 如果没有找到语义化的唯一键，回退到 ID
                if not lookup_fields and pk:
                    lookup_fields["id"] = pk

                if lookup_fields:
                    model_cls.objects.update_or_create(defaults=item, **lookup_fields)
                    success_count += 1
                else:
                    # 如果没有任何唯一键，直接创建
                    model_cls.objects.create(**item)
                    success_count += 1

            messages.success(request, f"成功导入 {success_count} 条记录")

        except Exception as e:
            messages.error(request, f"导入失败: {str(e)}")

        return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))


# --- Debug Views (调试工具视图) ---
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django.core.cache import cache
from django.core.mail import send_mail
from django.urls import get_resolver, reverse
from django.db import connection
from django.apps import apps
import re
import sys
import platform
import django

try:
    from faker import Faker
except ImportError:
    Faker = None


class DebugDashboardView(
    DebugToolRequiredMixin, LoginRequiredMixin, StaffRequiredMixin, TemplateView
):
    """
    调试仪表盘视图

    展示系统调试信息，包括：
    - 数据库连接状态
    - 关键对象数量统计
    - 系统所有 URL 模式列表 (前 50 条)
    - 系统环境信息 (Python/Django 版本)
    """

    template_name = "administration/debug.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 显式添加 debug_mode 到上下文
        context["debug_mode"] = settings.DEBUG

        # 系统环境信息
        context["system_info"] = {
            "python_version": sys.version.split()[0],
            "django_version": django.get_version(),
            "platform": platform.platform(),
            "server_time": timezone.now(),
            "base_dir": settings.BASE_DIR,
        }

        # 数据库连接检查
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            context["db_ok"] = True
        except Exception:
            context["db_ok"] = False

        # 对象计数
        context["counts"] = {
            "users": User.objects.count(),
            "posts": Post.objects.count(),
            "comments": Comment.objects.count(),
        }

        # URL 路由解析与展示
        url_patterns = []
        resolver = get_resolver()

        def process_patterns(patterns, prefix="", namespace_prefix=""):
            for pattern in patterns:
                if hasattr(pattern, "url_patterns"):
                    # 递归处理 include()
                    new_prefix = prefix + str(pattern.pattern)

                    # 处理命名空间
                    new_ns = namespace_prefix
                    if hasattr(pattern, "namespace") and pattern.namespace:
                        if new_ns:
                            new_ns = f"{new_ns}:{pattern.namespace}"
                        else:
                            new_ns = pattern.namespace

                    process_patterns(pattern.url_patterns, new_prefix, new_ns)
                elif hasattr(pattern, "name") and pattern.name:
                    # 叶子节点 (实际视图)
                    full_pattern = prefix + str(pattern.pattern)

                    # 构建包含命名空间的完整名称
                    full_name = pattern.name
                    if namespace_prefix:
                        full_name = f"{namespace_prefix}:{pattern.name}"

                    # 清理正则表达式符号，用于显示
                    display_pattern = full_pattern.replace("^", "").replace("$", "")
                    if not display_pattern.startswith("/"):
                        display_pattern = "/" + display_pattern

                    # 尝试生成示例 URL
                    sample_url = None
                    description = ""

                    # --- 自动生成描述逻辑 ---

                    # 1. 自动解析 Admin 视图
                    if "admin" in full_name:
                        try:
                            local_name = pattern.name

                            action = ""
                            model_info = ""

                            if local_name == "index":
                                description = "后台管理首页"
                            elif local_name == "password_change":
                                description = "修改密码"
                            elif local_name == "logout":
                                description = "注销登录"
                            elif local_name.endswith("_changelist"):
                                action = "列表"
                                model_info = local_name[:-11]
                            elif local_name.endswith("_add"):
                                action = "添加"
                                model_info = local_name[:-4]
                            elif local_name.endswith("_change"):
                                action = "编辑"
                                model_info = local_name[:-7]
                            elif local_name.endswith("_delete"):
                                action = "删除"
                                model_info = local_name[:-7]
                            elif local_name.endswith("_history"):
                                action = "历史"
                                model_info = local_name[:-8]

                            if action and model_info:
                                parts = model_info.split("_")
                                found_model = None
                                # 尝试解析 App 和 Model
                                for i in range(1, len(parts)):
                                    app_label = "_".join(parts[:i])
                                    model_name = "_".join(parts[i:])
                                    try:
                                        found_model = apps.get_model(
                                            app_label, model_name
                                        )
                                        break
                                    except LookupError:
                                        continue

                                if found_model:
                                    description = (
                                        f"{found_model._meta.verbose_name} {action}"
                                    )
                                else:
                                    formatted_name = model_info.replace(
                                        "_", " "
                                    ).title()
                                    description = f"{formatted_name} {action}"

                            if not description:
                                description = "后台管理功能"

                        except Exception:
                            description = "后台管理"

                    # 2. 手动映射 (高优先级覆盖)
                    if full_name == "home":
                        description = "前台首页"
                    elif full_name == "post_list":
                        description = "文章列表"
                    elif full_name == "post_detail":
                        description = "文章详情"
                    elif full_name == "archive":
                        description = "文章归档"
                    elif full_name == "category_list":
                        description = "分类列表"
                    elif full_name == "tag_list":
                        description = "标签列表"
                    elif full_name == "search":
                        description = "搜索页面"
                    elif full_name == "about":
                        description = "关于页面"
                    elif full_name == "contact":
                        description = "联系页面"
                    elif full_name.startswith("administration:"):
                        description = "自定义管理面板"

                    # --- URL 反向解析逻辑 ---

                    # 尝试反向解析无参数 URL
                    try:
                        sample_url = reverse(full_name)
                    except Exception:
                        pass

                    # 判断是否需要参数
                    has_args = "<" in full_pattern or "(?P" in full_pattern

                    # 如果有 sample_url，说明不需要参数（或使用了默认值）
                    needs_args = has_args and not sample_url

                    url_patterns.append(
                        {
                            "pattern": full_pattern,
                            "display_pattern": display_pattern,
                            "name": full_name,
                            "sample_url": sample_url,
                            "description": description,
                            "needs_args": needs_args,
                        }
                    )

        process_patterns(resolver.url_patterns)

        # 按名称排序以提高可读性
        url_patterns.sort(key=lambda x: x["name"] or "")

        context["url_patterns"] = url_patterns
        return context


from core.services import generate_mock_data


class DebugMockView(DebugToolRequiredMixin, LoginRequiredMixin, StaffRequiredMixin, TemplateView):
    """
    Mock 数据生成视图

    用于生成测试数据 (User, Post, Comment)。
    依赖 Faker 库。
    """

    template_name = "administration/debug/mock.html"

    def post(self, request, *args, **kwargs):
        # 仅在调试模式下允许生成 Mock 数据
        if not settings.DEBUG:
            messages.error(request, "生产环境禁止生成 Mock 数据")
            return redirect("administration:index")

        try:
            # 从表单提取数量
            users_count = int(request.POST.get("users_count", 0))
            categories_count = int(request.POST.get("categories_count", 0))
            tags_count = int(request.POST.get("tags_count", 0))
            posts_count = int(request.POST.get("posts_count", 0))
            comments_count = int(request.POST.get("comments_count", 0))
            password = request.POST.get("password", "password123")
            generate_extras = request.POST.get("generate_extras") == "on"

            results = generate_mock_data(
                users_count=users_count,
                categories_count=categories_count,
                tags_count=tags_count,
                posts_count=posts_count,
                comments_count=comments_count,
                password=password,
                generate_extras=generate_extras,
            )

            msg_parts = []
            if results["users"]:
                msg_parts.append(f"{results['users']} 用户")
            if results["categories"]:
                msg_parts.append(f"{results['categories']} 分类")
            if results["tags"]:
                msg_parts.append(f"{results['tags']} 标签")
            if results["posts"]:
                msg_parts.append(f"{results['posts']} 文章")
            if results["comments"]:
                msg_parts.append(f"{results['comments']} 评论")

            if msg_parts:
                messages.success(request, f"成功生成: {', '.join(msg_parts)}")
            else:
                messages.warning(request, "没有生成任何数据 (数量均为 0)")

        except Exception as e:
            messages.error(request, f"生成失败: {str(e)}")

        return self.get(request, *args, **kwargs)


class DebugCacheView(
    DebugToolRequiredMixin, LoginRequiredMixin, StaffRequiredMixin, TemplateView
):
    """
    缓存调试视图

    提供缓存清理功能，用于开发调试或解决缓存一致性问题。
    """

    template_name = "administration/debug/cache.html"

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        if action == "clear_all":
            cache.clear()
            messages.success(request, "全站缓存已清理")
        elif action == "clear_templates":
            # 清理模板缓存
            cache.clear()
            messages.success(request, "模板缓存已清理")
        return self.get(request, *args, **kwargs)


class DebugEmailView(
    DebugToolRequiredMixin, LoginRequiredMixin, StaffRequiredMixin, TemplateView
):
    """
    邮件发送调试视图

    用于测试 SMTP 配置是否正确，可以发送测试邮件。
    显示当前 SMTP 配置信息 (SMTP_HOST, SMTP_PORT, etc.)。
    """

    template_name = "administration/debug/email.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 从 config (Constance) 获取当前动态配置，用于展示
        context["email_host"] = getattr(config, "SMTP_HOST", "Unknown")
        context["email_port"] = getattr(config, "SMTP_PORT", "Unknown")
        context["email_host_user"] = getattr(config, "SMTP_USER", "Unknown")
        context["email_use_tls"] = getattr(config, "SMTP_USE_TLS", "Unknown")
        return context

    def post(self, request, *args, **kwargs):
        recipient = request.POST.get("recipient")
        subject = request.POST.get("subject")
        message = request.POST.get("message")

        if not recipient or not subject or not message:
            messages.error(request, "请填写完整信息")
            return self.get(request, *args, **kwargs)

        # 优先使用动态配置的发送地址，否则回退到系统默认
        from_email = (
            getattr(config, "SMTP_FROM_EMAIL", None) or settings.DEFAULT_FROM_EMAIL
        )

        try:
            send_mail(
                subject,
                message,
                from_email,
                [recipient],
                fail_silently=False,
            )
            messages.success(request, f"测试邮件已发送至 {recipient}")
        except Exception as e:
            messages.error(request, f"邮件发送失败: {str(e)}")

        return self.get(request, *args, **kwargs)


from constance import config
from django.conf import settings as django_settings
from django.contrib.sites.models import Site
from pygments.styles import get_all_styles


class SystemToolsView(LoginRequiredMixin, StaffRequiredMixin, TemplateView):
    """
    系统工具视图

    提供系统维护工具，如搜索索引重建、图片预处理等。
    """
    template_name = "administration/system_tools.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "系统工具"
        context["breadcrumbs"] = [
            {"label": "设置", "url": reverse_lazy("administration:settings")},
            {"label": "系统工具"},
        ]

        latest_task_key = cache.get("watson:rebuild:latest")
        watson_status = cache.get(latest_task_key) if latest_task_key else None
        context["watson_rebuild_status"] = (
            watson_status.get("status") if watson_status else "idle"
        )
        watson_updated = watson_status.get("updated_at") if watson_status else None
        if watson_updated:
             context["watson_rebuild_updated_at"] = parse_datetime(watson_updated)
        else:
             context["watson_rebuild_updated_at"] = ""

        latest_image_key = cache.get("image:queue:latest")
        image_status = cache.get(latest_image_key) if latest_image_key else None
        context["image_queue_status"] = (
            image_status.get("status") if image_status else "idle"
        )
        image_updated = image_status.get("updated_at") if image_status else None
        if image_updated:
            context["image_queue_updated_at"] = parse_datetime(image_updated)
        else:
            context["image_queue_updated_at"] = ""

        context["image_queue_queued"] = (
            image_status.get("queued") if image_status else 0
        )
        context["image_queue_processed"] = (
            image_status.get("processed") if image_status else 0
        )

        # Media Cleaner Status
        latest_scan_key = cache.get("media:scan:latest")
        scan_status = cache.get(latest_scan_key) if latest_scan_key else None
        context["media_scan_status"] = scan_status.get("status") if scan_status else "idle"
        
        scan_updated = scan_status.get("updated_at") if scan_status else None
        if scan_updated:
            context["media_scan_updated_at"] = parse_datetime(scan_updated)
        else:
             context["media_scan_updated_at"] = ""
             
        context["media_scan_orphaned_count"] = scan_status.get("orphaned_count") if scan_status else 0
        context["media_scan_orphaned_size"] = scan_status.get("orphaned_size") if scan_status else 0

        latest_clean_key = cache.get("media:clean:latest")
        clean_status = cache.get(latest_clean_key) if latest_clean_key else None
        context["media_clean_status"] = clean_status.get("status") if clean_status else "idle"
        context["media_clean_cleaned_count"] = clean_status.get("cleaned_count") if clean_status else 0
        context["media_clean_cleaned_size"] = clean_status.get("cleaned_size") if clean_status else 0
        context["media_clean_error"] = clean_status.get("detail") if clean_status and clean_status.get("status") == "error" else ""
        
        # Database Backups
        context["backups"] = list_backups()

        # Privacy Policy Status
        context["privacy_policy_exists"] = Page.objects.filter(slug="privacy-policy").exists()

        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        
        if action == "init_privacy_policy":
            try:
                if Page.objects.filter(slug="privacy-policy").exists():
                    messages.info(request, "隐私政策页面已存在")
                else:
                    privacy_content = """# 隐私政策

**生效日期：** 2024年01月01日

欢迎访问 {{ config.SITE_NAME }}（以下简称“本站”）。我们非常重视您的隐私保护。本隐私政策旨在向您说明我们如何收集、使用、存储和保护您的个人信息。

## 1. 我们收集的信息

当您访问本站或使用我们的服务时，我们可能会收集以下类型的信息：

*   **日志信息：** 包括您的 IP 地址、浏览器类型、访问时间、访问页面等服务器日志信息。
*   **交互信息：** 如果您发表评论或留言，我们会收集您提交的昵称、邮箱地址（仅用于通知，不会公开）和评论内容。
*   **Cookie：** 我们使用 Cookie 来改善用户体验，例如记住您的偏好设置。

## 2. 信息的使用

我们收集的信息主要用于：

*   提供和维护本站的服务。
*   改善网站内容和用户体验。
*   在您同意的情况下，向您发送相关通知（如评论回复）。
*   保障网站安全，防止欺诈和滥用。

## 3. 信息共享与披露

我们要么不共享您的个人信息，除非：

*   获得您的明确同意。
*   法律法规要求或响应政府部门的强制性命令。
*   为了保护本站或公众的权利、财产或安全。

## 4. 数据安全

我们采取合理的安全措施来保护您的个人信息，防止未经授权的访问、使用或泄露。

## 5. 您的权利

您有权查阅、更正或删除您的个人信息。如果您希望行使这些权利，请通过 {{ config.CONTACT_EMAIL }} 联系我们。

## 6. 变更通知

我们可能会不时更新本隐私政策。更新后的政策将发布在本页面，并更新“生效日期”。

## 7. 联系我们

如果您对本隐私政策有任何疑问，请联系：{{ config.SITE_EMAIL }}"""

                    Page.objects.create(
                        title="隐私政策",
                        slug="privacy-policy",
                        content=privacy_content,
                        status="published",
                    )
                    messages.success(request, "隐私政策页面初始化成功")
            except Exception as e:
                messages.error(request, f"初始化失败: {str(e)}")
            return redirect("administration:system_tools")

        if action == "rebuild_watson":
            result = trigger_watson_rebuild_async()
            if result["accepted"]:
                messages.success(request, "搜索索引重建已开始")
            else:
                messages.info(request, "已有重建任务在执行，请稍后再试")
            return redirect("administration:system_tools")

        if action == "queue_images":
            try:
                limit = max(1, int(request.POST.get("limit") or 20))
                delay = max(
                    0,
                    int(
                        request.POST.get("delay")
                        or getattr(settings, "IMAGE_PROCESSING_DELAY", 120)
                    ),
                )
            except (TypeError, ValueError):
                messages.error(request, "参数不合法，请检查输入")
                return redirect("administration:system_tools")

            result = queue_post_images_async(limit=limit, delay_seconds=delay)
            if result["accepted"]:
                messages.success(request, "图片处理队列已开始")
            else:
                messages.info(request, "已有图片处理任务在执行，请稍后再试")
            return redirect("administration:system_tools")

        # Media Cleaner Actions
        if action == "scan_media":
            result = trigger_media_scan_async()
            if result["accepted"]:
                messages.success(request, "媒体文件扫描已开始")
            else:
                messages.info(request, "已有扫描任务在执行，请稍后再试")
            return redirect("administration:system_tools")
            
        if action == "clean_media":
            result = trigger_media_clean_async()
            if result["accepted"]:
                messages.success(request, "孤儿文件清理已开始")
            elif result.get("error"):
                 messages.error(request, f"清理失败: {result['error']}")
            else:
                messages.info(request, "已有清理任务在执行，请稍后再试")
            return redirect("administration:system_tools")
            
        # Backup Actions
        if action == "create_backup":
            try:
                filename = create_backup()
                messages.success(request, f"备份创建成功: {filename}")
            except Exception as e:
                messages.error(request, f"备份创建失败: {str(e)}")
            return redirect("administration:system_tools")
            
        if action == "delete_backup":
            filename = request.POST.get("filename")
            try:
                if delete_backup(filename):
                    messages.success(request, f"备份 {filename} 已删除")
                else:
                    messages.error(request, "文件不存在或无法删除")
            except Exception as e:
                messages.error(request, f"删除失败: {str(e)}")
            return redirect("administration:system_tools")
            
        if action == "restore_backup":
            filename = request.POST.get("filename")
            try:
                restore_backup(filename)
                messages.success(request, f"数据库已从 {filename} 恢复")
            except Exception as e:
                messages.error(request, f"恢复失败: {str(e)}")
            return redirect("administration:system_tools")
            
        return redirect("administration:system_tools")


class SystemMonitorView(LoginRequiredMixin, StaffRequiredMixin, TemplateView):
    """
    系统监控视图 (HTMX Partial)

    返回系统 CPU、内存、磁盘使用情况的 HTML 片段。
    """
    template_name = "administration/partials/system_monitor.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            
            context.update({
                "cpu_percent": round(cpu_percent),
                "memory_percent": round(memory.percent),
                "memory_used": memory.used,
                "memory_total": memory.total,
                "disk_percent": round(disk.percent),
                "disk_free": disk.free,
            })
        except Exception as e:
            # Log error for debugging
            import traceback
            logger.error(f"[SystemMonitor Error] {str(e)}")
            logger.error(traceback.format_exc())
            
            context.update({
                "cpu_percent": 0,
                "memory_percent": 0,
                "memory_used": 0,
                "memory_total": 0,
                "disk_percent": 0,
                "disk_free": 0,
            })
        return context


class BackupDownloadView(LoginRequiredMixin, StaffRequiredMixin, View):
    """
    下载数据库备份文件
    """
    def get(self, request, filename):
        backup_dir = settings.BASE_DIR / "backups"
        file_path = backup_dir / filename
        
        # 安全检查
        if not file_path.resolve().is_relative_to(backup_dir.resolve()):
            raise Http404("Invalid file path")
            
        if not file_path.exists():
            raise Http404("File not found")
            
        from django.http import FileResponse
        return FileResponse(open(file_path, "rb"), as_attachment=True, filename=filename)


class SettingsView(LoginRequiredMixin, StaffRequiredMixin, TemplateView):
    """
    系统设置视图

    基于 django-constance 动态管理网站配置。
    """

    template_name = "administration/settings.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"label": "站点设置"},
        ]
        
        # 获取当前站点信息
        try:
            context["current_site"] = Site.objects.get_current()
        except Exception:
            context["current_site"] = None

        # 获取所有可用的 Pygments 风格并排序
        context["pygments_styles"] = sorted(list(get_all_styles()))

        # 辅助函数：获取配置项数据
        def get_item_data(key):
            if (
                not hasattr(django_settings, "CONSTANCE_CONFIG")
                or key not in django_settings.CONSTANCE_CONFIG
            ):
                return None

            options = django_settings.CONSTANCE_CONFIG[key]
            value = getattr(config, key)
            help_text = options[1] if len(options) > 1 else ""

            return {
                "key": key,
                "value": value,
                "help_text": help_text,
                "type": type(value).__name__,
            }

        fieldsets = []
        if hasattr(django_settings, "CONSTANCE_CONFIG_FIELDSETS"):
            for title, keys in django_settings.CONSTANCE_CONFIG_FIELDSETS.items():
                items = []
                for key in keys:
                    item_data = get_item_data(key)
                    if item_data:
                        items.append(item_data)

                # UI 映射：将标题映射为图标和 Slug
                icon = "settings"
                slug = "general"

                if "基本设置" in title or "General" in title:
                    icon = "tune"
                    slug = "general"
                elif "外观设置" in title or "Appearance" in title:
                    icon = "palette"
                    slug = "appearance"
                elif "后台界面" in title or "Admin" in title:
                    icon = "admin_panel_settings"
                    slug = "admin"
                elif "社交与联系" in title or "Social" in title:
                    icon = "share"
                    slug = "social"
                elif "邮件服务" in title or "Email" in title:
                    icon = "mail"
                    slug = "email"
                elif "功能开关" in title or "Feature" in title:
                    icon = "toggle_on"
                    slug = "features"
                elif "自定义代码" in title or "Code" in title:
                    icon = "code"
                    slug = "code"

                fieldsets.append(
                    {"title": title, "slug": slug, "icon": icon, "items": items}
                )
        else:
            # 降级处理：如果未定义分组配置
            items = []
            if hasattr(django_settings, "CONSTANCE_CONFIG"):
                for key in django_settings.CONSTANCE_CONFIG.keys():
                    item_data = get_item_data(key)
                    if item_data:
                        items.append(item_data)
            fieldsets.append(
                {"title": "General", "slug": "general", "icon": "tune", "items": items}
            )

        context["fieldsets"] = fieldsets
        latest_task_key = cache.get("watson:rebuild:latest")
        watson_status = cache.get(latest_task_key) if latest_task_key else None
        context["watson_rebuild_status"] = (
            watson_status.get("status") if watson_status else "idle"
        )
        context["watson_rebuild_updated_at"] = (
            watson_status.get("updated_at") if watson_status else ""
        )
        latest_image_key = cache.get("image:queue:latest")
        image_status = cache.get(latest_image_key) if latest_image_key else None
        context["image_queue_status"] = (
            image_status.get("status") if image_status else "idle"
        )
        context["image_queue_updated_at"] = (
            image_status.get("updated_at") if image_status else ""
        )
        context["image_queue_queued"] = (
            image_status.get("queued") if image_status else 0
        )
        context["image_queue_processed"] = (
            image_status.get("processed") if image_status else 0
        )
        context["image_queue_failed"] = (
            image_status.get("failed") if image_status else 0
        )
        context["image_queue_skipped"] = (
            image_status.get("skipped") if image_status else 0
        )
        context["image_queue_delay"] = (
            image_status.get("delay")
            if image_status
            else getattr(settings, "IMAGE_PROCESSING_DELAY", 120)
        )
        context["cover_image_count"] = (
            Post.objects.filter(cover_image__isnull=False)
            .exclude(cover_image="")
            .count()
        )
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        if action == "rebuild_watson":
            result = trigger_watson_rebuild_async()
            if result["accepted"]:
                messages.success(request, "搜索索引重建已开始")
            else:
                messages.info(request, "已有重建任务在执行，请稍后再试")
            return self.get(request, *args, **kwargs)

        if action == "queue_images":
            try:
                limit = max(1, int(request.POST.get("limit") or 20))
                delay = max(
                    0,
                    int(
                        request.POST.get("delay")
                        or getattr(settings, "IMAGE_PROCESSING_DELAY", 120)
                    ),
                )
            except (TypeError, ValueError):
                messages.error(request, "参数不合法，请检查输入")
                return self.get(request, *args, **kwargs)

            result = queue_post_images_async(limit=limit, delay_seconds=delay)
            if result["accepted"]:
                messages.success(request, "图片处理队列已开始")
            else:
                messages.info(request, "已有图片处理任务在执行，请稍后再试")
            return self.get(request, *args, **kwargs)

        # 保存设置
        # 处理 Site 更新
        site_domain = request.POST.get("site_domain")
        site_name = request.POST.get("site_name")
        
        if site_domain and site_name:
            try:
                site = Site.objects.get_current()
                site.domain = site_domain
                site.name = site_name
                site.save()
            except Exception as e:
                messages.error(request, f"更新站点信息失败: {str(e)}")

        if hasattr(django_settings, "CONSTANCE_CONFIG"):
            for key in django_settings.CONSTANCE_CONFIG.keys():
                if key in request.POST:
                    new_value = request.POST.get(key)
                    # 简单类型转换 (后续可优化布尔值、整数等的处理)
                    current_value = getattr(config, key)
                    if isinstance(current_value, bool):
                        setattr(config, key, new_value == "on")
                    elif isinstance(current_value, int):
                        try:
                            setattr(config, key, int(new_value))
                        except ValueError:
                            pass
                    else:
                        setattr(config, key, new_value)
                elif isinstance(getattr(config, key), bool):
                    # 处理未选中的复选框 (HTML 表单不提交未选中的 checkbox)
                    setattr(config, key, False)

        messages.success(request, "设置已保存")
        return self.get(request, *args, **kwargs)


class DebugUITestView(
    DebugToolRequiredMixin, LoginRequiredMixin, StaffRequiredMixin, TemplateView
):
    """
    UI 组件测试视图

    展示常用 UI 组件以测试主题一致性。
    """

    template_name = "administration/debug/ui_test.html"


class DebugPermissionView(
    DebugToolRequiredMixin, LoginRequiredMixin, StaffRequiredMixin, TemplateView
):
    """
    权限调试视图

    检查指定用户的权限详情。
    """

    template_name = "administration/debug/permission.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        username = self.request.GET.get("username")
        if username:
            try:
                target_user = User.objects.get(username=username)
                context["target_user"] = target_user
                context["user_permissions"] = sorted(
                    list(target_user.get_all_permissions())
                )
                context["group_permissions"] = sorted(
                    list(target_user.get_group_permissions())
                )
                context["groups"] = target_user.groups.all()
            except User.DoesNotExist:
                context["error"] = f"用户 '{username}' 不存在"
        return context

class PollListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Poll
    template_name = "administration/poll_list.html"
    context_object_name = "polls"
    paginate_by = 20
    ordering = ["-created_at"]

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        queryset = super().get_queryset()
        q = self.request.GET.get("q")
        if q:
            queryset = queryset.filter(title__icontains=q)
        return queryset


class PollCreateView(LoginRequiredMixin, UserPassesTestMixin, AuditLogMixin, CreateView):
    model = Poll
    form_class = PollForm
    template_name = "administration/poll_form.html"
    success_url = reverse_lazy("administration:poll_list")

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data["choice_formset"] = ChoiceFormSet(self.request.POST)
        else:
            data["choice_formset"] = ChoiceFormSet()
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        choice_formset = context["choice_formset"]
        if choice_formset.is_valid():
            response = super().form_valid(form)
            choice_formset.instance = self.object
            choice_formset.save()
            self.log_action(ADDITION, change_message="创建了投票")
            messages.success(self.request, "投票创建成功！")
            if "_addanother" in self.request.POST:
                return HttpResponseRedirect(reverse_lazy("administration:poll_create"))
            elif "_continue" in self.request.POST:
                return HttpResponseRedirect(
                    reverse_lazy("administration:poll_edit", kwargs={"pk": self.object.pk})
                )
            return response
        else:
            return self.form_invalid(form)


class PollUpdateView(LoginRequiredMixin, UserPassesTestMixin, AuditLogMixin, UpdateView):
    model = Poll
    form_class = PollForm
    template_name = "administration/poll_form.html"
    success_url = reverse_lazy("administration:poll_list")

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data["choice_formset"] = ChoiceFormSet(self.request.POST, instance=self.object)
        else:
            data["choice_formset"] = ChoiceFormSet(instance=self.object)
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        choice_formset = context["choice_formset"]
        if choice_formset.is_valid():
            response = super().form_valid(form)
            choice_formset.instance = self.object
            choice_formset.save()
            self.log_action(CHANGE, change_message="更新了投票")
            messages.success(self.request, "投票更新成功！")
            if "_addanother" in self.request.POST:
                return HttpResponseRedirect(reverse_lazy("administration:poll_create"))
            elif "_continue" in self.request.POST:
                return HttpResponseRedirect(
                    reverse_lazy("administration:poll_edit", kwargs={"pk": self.object.pk})
                )
            return response
        else:
            return self.form_invalid(form)


class PollDeleteView(LoginRequiredMixin, UserPassesTestMixin, AuditLogMixin, DeleteView):
    model = Poll
    template_name = "administration/generic_confirm_delete.html"
    success_url = reverse_lazy("administration:poll_list")
    context_object_name = "object"

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        self.log_action(DELETION, change_message="删除了投票")
        messages.success(self.request, "投票删除成功！")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "删除投票"
        context["cancel_url"] = self.success_url
        return context
