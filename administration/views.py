from typing import Any, Dict, List
from django.db.models import QuerySet, Sum
from django.http import HttpRequest, HttpResponseRedirect
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
from blog.models import Post, Comment, Category, Tag, PostViewHistory
from core.models import Page, Navigation, FriendLink
from django.conf import settings
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
)

User = get_user_model()


class StaffRequiredMixin(UserPassesTestMixin):
    """
    权限混入类：仅允许管理员（is_staff=True）访问。
    """
    def test_func(self) -> bool:
        return self.request.user.is_staff


class IndexView(LoginRequiredMixin, StaffRequiredMixin, TemplateView):
    """
    管理后台首页视图，展示统计数据、近期活动和图表。
    """
    template_name: str = "administration/index.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context: Dict[str, Any] = super().get_context_data(**kwargs)

        # Stats (统计数据)
        context["total_posts"] = Post.objects.count()
        context["total_users"] = User.objects.count()
        context["total_views"] = (
            Post.objects.aggregate(total_views=Sum("views"))["total_views"] or 0
        )
        context["pending_comments"] = Comment.objects.filter(active=False).count()
        context["total_comments"] = Comment.objects.count()

        # Recent activity (近期活动)
        context["recent_posts"] = Post.objects.select_related("author").order_by(
            "-created_at"
        )[:5]
        context["recent_comments"] = Comment.objects.select_related(
            "user", "post"
        ).order_by("-created_at")[:5]
        context["popular_posts"] = Post.objects.order_by("-views")[:5]

        # Chart Data (图表数据)
        from django.db.models.functions import TruncDay
        from django.db.models import Count
        from django.utils import timezone
        import datetime
        import json
        import psutil
        import os

        # --- 1. Content Overview ---
        media_root = settings.MEDIA_ROOT
        media_count = 0
        media_size = 0
        for dirpath, dirnames, filenames in os.walk(media_root):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    media_count += 1
                    media_size += os.path.getsize(fp)
        media_size_mb = round(media_size / (1024 * 1024), 2)

        content_stats = {
            "posts_total": Post.objects.count(),
            "posts_published": Post.objects.filter(status="published").count(),
            "posts_draft": Post.objects.filter(status="draft").count(),
            "pages_total": Page.objects.count(),
            "categories_total": Category.objects.count(),
            "tags_total": Tag.objects.count(),
            "media_count": media_count,
            "media_size_mb": media_size_mb,
        }
        context["content_stats"] = content_stats

        # --- 2. Comment Analytics ---
        # Status Distribution
        comment_status = {
            "total": Comment.objects.count(),
            "pending": Comment.objects.filter(active=False).count(),
            "approved": Comment.objects.filter(active=True).count(),
        }
        
        # Daily Trend (Last 30 Days)
        last_30_days = timezone.now() - datetime.timedelta(days=30)
        comments_trend = (
            Comment.objects.filter(created_at__gte=last_30_days)
            .annotate(day=TruncDay("created_at"))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )
        
        trend_labels = []
        trend_data = []
        date_map = {item["day"].strftime("%Y-%m-%d"): item["count"] for item in comments_trend}
        
        for i in range(29, -1, -1):
            date = (timezone.now() - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            trend_labels.append(date)
            trend_data.append(date_map.get(date, 0))

        # Top Commenters
        top_commenters = (
            User.objects.annotate(comment_count=Count("comment"))
            .order_by("-comment_count")[:5]
            .values("username", "comment_count")
        )

        context["chart_comments"] = {
            "status": [comment_status["approved"], comment_status["pending"]],
            "trend_labels": trend_labels,
            "trend_data": trend_data,
            "top_users": [u["username"] for u in top_commenters],
            "top_counts": [u["comment_count"] for u in top_commenters]
        }

        # --- 3. User Activity ---
        # Role Distribution
        user_roles = {
            "superuser": User.objects.filter(is_superuser=True).count(),
            "staff": User.objects.filter(is_staff=True, is_superuser=False).count(),
            "active": User.objects.filter(is_active=True, is_staff=False).count(),
            "inactive": User.objects.filter(is_active=False).count(),
        }
        
        # Active Users (Last 7 Days)
        active_users_7d = User.objects.filter(last_login__gte=timezone.now() - datetime.timedelta(days=7)).count()

        # New Users Trend (This Week vs Last Week)
        today = timezone.now()
        start_week = today - datetime.timedelta(days=today.weekday())
        start_last_week = start_week - datetime.timedelta(days=7)
        
        new_users_this_week = User.objects.filter(date_joined__gte=start_week).count()
        new_users_last_week = User.objects.filter(
            date_joined__gte=start_last_week, 
            date_joined__lt=start_week
        ).count()
        
        user_trend_diff = new_users_this_week - new_users_last_week
        user_trend_direction = "up" if user_trend_diff >= 0 else "down"

        context["user_stats"] = {
            "roles": user_roles,
            "active_7d": active_users_7d,
            "new_this_week": new_users_this_week,
            "diff": abs(user_trend_diff),
            "direction": user_trend_direction
        }
        
        context["chart_users"] = {
            "roles_data": [user_roles["superuser"], user_roles["staff"], user_roles["active"], user_roles["inactive"]],
            "roles_labels": ["超级管理员", "管理员", "活跃用户", "禁用用户"]
        }

        # --- 4. Traffic Analytics ---
        # Traffic Trend (Last 30 Days) using PostViewHistory
        traffic_trend = (
            PostViewHistory.objects.filter(viewed_at__gte=last_30_days)
            .annotate(day=TruncDay("viewed_at"))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )
        traffic_map = {item["day"].strftime("%Y-%m-%d"): item["count"] for item in traffic_trend}
        traffic_data_list = []
        for i in range(29, -1, -1):
            date = (timezone.now() - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            traffic_data_list.append(traffic_map.get(date, 0))

        # Top Articles
        top_articles = Post.objects.order_by("-views")[:5]
        top_articles_data = [
            {"title": p.title, "views": p.views, "url": p.get_absolute_url()}
            for p in top_articles
        ]
        
        context["chart_traffic"] = {
            "trend_labels": trend_labels,
            "trend_data": traffic_data_list,
            "top_articles_labels": [p["title"] for p in top_articles_data],
            "top_articles_data": [p["views"] for p in top_articles_data],
            "top_articles_urls": [p["url"] for p in top_articles_data],
        }

        # --- 5. System Status ---
        try:
            cpu_usage = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            system_stats_dict = {
                "cpu": cpu_usage,
                "memory_percent": memory.percent,
                "memory_used": round(memory.used / (1024**3), 2),
                "memory_total": round(memory.total / (1024**3), 2),
                "disk_percent": disk.percent,
                "disk_used": round(disk.used / (1024**3), 2),
                "disk_total": round(disk.total / (1024**3), 2),
                "media_size_mb": media_size_mb,
            }
            context["system_stats"] = system_stats_dict
            context["system_stats_obj"] = system_stats_dict # For HTML rendering
        except Exception:
            context["system_stats"] = None
            context["system_stats_obj"] = None

        # System Info
        context["python_version"] = platform.python_version()
        context["django_version"] = get_version()

        return context


# --- Generic CRUD Mixins ---
class BaseListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    """
    基础列表视图混入类
    提供通用的列表展示功能，支持 HTMX 局部刷新。
    """
    paginate_by = 20
    template_name_suffix = "_list"

    def get_ordering(self):
        sort_by = self.request.GET.get("sort")
        if sort_by:
            order = self.request.GET.get("order", "asc")
            if order == "desc":
                return f"-{sort_by}"
            return sort_by
        return self.ordering

    def get_template_names(self) -> List[str]:
        # Support HTMX partials
        # Only return partial if it's an HTMX request AND NOT a boosted request (full page nav)
        if self.request.headers.get("HX-Request") and not self.request.headers.get(
            "HX-Boosted"
        ):
            return [
                f"administration/partials/{self.model._meta.model_name}_list_rows.html"
            ]
        return [f"administration/{self.model._meta.model_name}_list.html"]


class BaseCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    """
    基础创建视图混入类
    提供通用的对象创建功能，成功后显示提示信息。
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
        messages.success(self.request, f"{self.model._meta.verbose_name} 创建成功")
        return super().form_valid(form)


class BaseUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    """
    基础更新视图混入类
    提供通用的对象更新功能，成功后显示提示信息。
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
        messages.success(self.request, f"{self.model._meta.verbose_name} 更新成功")
        return super().form_valid(form)


class BaseDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    """
    基础删除视图混入类
    提供通用的对象删除功能，成功后显示提示信息。
    """
    template_name = "administration/generic_confirm_delete.html"

    def form_valid(self, form):
        messages.success(self.request, f"{self.model._meta.verbose_name} 删除成功")
        return super().form_valid(form)


from django.shortcuts import get_object_or_404, redirect
from django.db.models import Count
import uuid

# --- Post Views ---
class PostListView(BaseListView):
    """
    文章列表视图
    展示文章列表，支持搜索和状态过滤。
    """
    model = Post
    template_name = "dashboard/post_list.html"
    context_object_name = "posts"
    ordering = ["-created_at"]

    def get_queryset(self) -> QuerySet[Post]:
        qs = super().get_queryset()
        query = self.request.GET.get("q")
        status = self.request.GET.get("status")

        if query:
            qs = qs.filter(title__icontains=query)

        if status:
            qs = qs.filter(status=status)

        return qs.select_related('author', 'category')

    def get_template_names(self) -> List[str]:
        # Support HTMX partials
        # Only return partial if it's an HTMX request AND NOT a boosted request (full page nav)
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
    创建新文章，自动关联当前登录用户为作者。
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
    编辑现有文章内容。
    """
    model = Post
    form_class = PostForm
    success_url = reverse_lazy("administration:post_list")


class PostDeleteView(BaseDeleteView):
    """
    文章删除视图
    删除指定文章。
    """
    model = Post
    success_url = reverse_lazy("administration:post_list")


class PostDuplicateView(LoginRequiredMixin, StaffRequiredMixin, View):
    """
    文章复制视图
    """
    def post(self, request, pk):
        try:
            post = get_object_or_404(Post, pk=pk)
            # Save M2M data before clearing pk
            tags = list(post.tags.all())
            
            post.pk = None
            post.slug = f"{post.slug}-{uuid.uuid4().hex[:6]}"
            post.title = f"{post.title} (副本)"
            post.status = 'draft'
            post.views = 0
            post.save()
            
            # Restore M2M
            post.tags.set(tags)
            
            messages.success(request, "文章已复制为草稿")
        except Exception as e:
            messages.error(request, f"复制失败: {str(e)}")
            
        return redirect('administration:post_list')


# --- Category Views ---
class CategoryListView(BaseListView):
    """
    分类列表视图
    展示分类列表，支持搜索。
    """
    model = Category
    context_object_name = "categories"
    ordering = ["name"]

    def get_queryset(self) -> QuerySet[Category]:
        qs = super().get_queryset().annotate(post_count=Count('posts'))
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


# --- Tag Views ---
class TagListView(BaseListView):
    """
    标签列表视图
    """
    model = Tag
    context_object_name = "tags"
    ordering = ["name"]

    def get_queryset(self) -> QuerySet[Tag]:
        qs = super().get_queryset().annotate(post_count=Count('posts'))
        query = self.request.GET.get("q")
        if query:
            qs = qs.filter(name__icontains=query)
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


# --- Comment Views ---
class CommentListView(BaseListView):
    """
    评论列表视图
    展示评论列表，支持内容搜索和状态过滤。
    """
    model = Comment
    context_object_name = "comments"
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = super().get_queryset().select_related("post", "user")
        query = self.request.GET.get("q")
        status = self.request.GET.get("status")

        if query:
            qs = qs.filter(content__icontains=query)

        if status == "active":
            qs = qs.filter(active=True)
        elif status == "pending":
            qs = qs.filter(active=False)

        return qs


class CommentUpdateView(BaseUpdateView):
    """
    评论更新视图
    支持修改评论内容和审核状态。
    """
    model = Comment
    fields = ["content", "active"]
    success_url = reverse_lazy("administration:comment_list")


class CommentDeleteView(BaseDeleteView):
    """
    评论删除视图
    """
    model = Comment
    success_url = reverse_lazy("administration:comment_list")


# --- Page Views ---
class PageListView(BaseListView):
    """
    单页面列表视图
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
    """
    def post(self, request, pk):
        try:
            page = get_object_or_404(Page, pk=pk)
            page.pk = None
            page.slug = f"{page.slug}-{uuid.uuid4().hex[:6]}"
            page.title = f"{page.title} (副本)"
            page.status = 'draft'
            page.save()
            
            messages.success(request, "页面已复制为草稿")
        except Exception as e:
            messages.error(request, f"复制失败: {str(e)}")
            
        return redirect('administration:page_list')


# --- Navigation Views ---
class NavigationListView(BaseListView):
    model = Navigation
    context_object_name = "navigations"
    ordering = ["order"]

    def get_queryset(self) -> QuerySet[Navigation]:
        qs = super().get_queryset()
        query = self.request.GET.get("q")
        if query:
            qs = qs.filter(title__icontains=query)
        return qs


class NavigationCreateView(BaseCreateView):
    model = Navigation
    form_class = NavigationForm
    success_url = reverse_lazy("administration:navigation_list")


class NavigationUpdateView(BaseUpdateView):
    model = Navigation
    form_class = NavigationForm
    success_url = reverse_lazy("administration:navigation_list")


class NavigationDeleteView(BaseDeleteView):
    model = Navigation
    success_url = reverse_lazy("administration:navigation_list")


# --- FriendLink Views ---
class FriendLinkListView(BaseListView):
    model = FriendLink
    context_object_name = "friendlinks"
    ordering = ["order"]

    def get_queryset(self) -> QuerySet[FriendLink]:
        qs = super().get_queryset()
        query = self.request.GET.get("q")
        if query:
            qs = qs.filter(name__icontains=query)
        return qs


class FriendLinkCreateView(BaseCreateView):
    model = FriendLink
    form_class = FriendLinkForm
    success_url = reverse_lazy("administration:friendlink_list")


class FriendLinkUpdateView(BaseUpdateView):
    model = FriendLink
    form_class = FriendLinkForm
    success_url = reverse_lazy("administration:friendlink_list")


class FriendLinkDeleteView(BaseDeleteView):
    model = FriendLink
    success_url = reverse_lazy("administration:friendlink_list")


# --- User Views ---
class UserListView(BaseListView):
    model = User
    context_object_name = "users"
    ordering = ["-date_joined"]

    def get_queryset(self):
        qs = super().get_queryset()
        query = self.request.GET.get("q")
        if query:
            qs = qs.filter(username__icontains=query)
        return qs


class UserUpdateView(BaseUpdateView):
    model = User
    form_class = UserForm
    success_url = reverse_lazy("administration:user_list")


# --- Bulk Action View ---
from django.apps import apps

class BulkActionView(LoginRequiredMixin, StaffRequiredMixin, View):
    """
    批量操作视图
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
                model_cls.objects.filter(id__in=selected_ids).delete()
                messages.success(request, "批量删除成功")
            elif action == "published":
                if hasattr(model_cls, 'status'):
                    model_cls.objects.filter(id__in=selected_ids).update(status='published')
                    messages.success(request, "批量发布成功")
            elif action == "draft":
                if hasattr(model_cls, 'status'):
                    model_cls.objects.filter(id__in=selected_ids).update(status='draft')
                    messages.success(request, "批量转为草稿成功")
            elif action == "active":
                if hasattr(model_cls, 'active'):
                    model_cls.objects.filter(id__in=selected_ids).update(active=True)
                    messages.success(request, "批量启用成功")
                elif hasattr(model_cls, 'is_active'):
                    model_cls.objects.filter(id__in=selected_ids).update(is_active=True)
                    messages.success(request, "批量启用成功")
            elif action == "inactive":
                if hasattr(model_cls, 'active'):
                    model_cls.objects.filter(id__in=selected_ids).update(active=False)
                    messages.success(request, "批量禁用成功")
                elif hasattr(model_cls, 'is_active'):
                    model_cls.objects.filter(id__in=selected_ids).update(is_active=False)
                    messages.success(request, "批量禁用成功")
            elif action == "export_json":
                from django.http import HttpResponse
                import json
                from django.core.serializers.json import DjangoJSONEncoder
                
                data = list(model_cls.objects.filter(id__in=selected_ids).values())
                response = HttpResponse(
                    json.dumps(data, cls=DjangoJSONEncoder, indent=4), 
                    content_type="application/json"
                )
                response['Content-Disposition'] = f'attachment; filename="{model}_export.json"'
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


# --- Export/Import Views ---
class ExportAllView(LoginRequiredMixin, StaffRequiredMixin, View):
    """
    导出全部数据视图
    """
    def get(self, request, model):
        try:
            model_cls = None
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

            from django.http import HttpResponse
            import json
            from django.core.serializers.json import DjangoJSONEncoder
            
            data = list(model_cls.objects.all().values())
            response = HttpResponse(
                json.dumps(data, cls=DjangoJSONEncoder, indent=4), 
                content_type="application/json"
            )
            response['Content-Disposition'] = f'attachment; filename="{model}_all_export.json"'
            return response
        except Exception as e:
            messages.error(request, f"导出失败: {str(e)}")
            return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))


class ImportJsonView(LoginRequiredMixin, StaffRequiredMixin, View):
    """
    导入 JSON 数据视图
    """
    def post(self, request, model):
        if 'json_file' not in request.FILES:
            messages.error(request, "请上传文件")
            return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
            
        json_file = request.FILES['json_file']
        if not json_file.name.endswith('.json'):
             messages.error(request, "请上传 JSON 文件")
             return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))

        try:
            model_cls = None
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

            import json
            data = json.load(json_file)
            
            if not isinstance(data, list):
                messages.error(request, "JSON 格式错误: 必须是列表")
                return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))

            success_count = 0
            for item in data:
                pk = item.pop('id', None)
                if pk:
                    model_cls.objects.update_or_create(id=pk, defaults=item)
                    success_count += 1
                else:
                    model_cls.objects.create(**item)
                    success_count += 1
            
            messages.success(request, f"成功导入 {success_count} 条记录")

        except Exception as e:
            messages.error(request, f"导入失败: {str(e)}")
            
        return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))


# --- Debug Views ---
from django.core.cache import cache
from django.core.mail import send_mail
from django.urls import get_resolver
from django.db import connection
try:
    from faker import Faker
except ImportError:
    Faker = None

class DebugDashboardView(LoginRequiredMixin, StaffRequiredMixin, TemplateView):
    template_name = "administration/debug/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Database check
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            context["db_ok"] = True
        except Exception:
            context["db_ok"] = False

        # Counts
        context["counts"] = {
            "users": User.objects.count(),
            "posts": Post.objects.count(),
            "comments": Comment.objects.count(),
        }

        # URL Patterns
        url_patterns = []
        resolver = get_resolver()
        for pattern in resolver.url_patterns:
            if hasattr(pattern, 'url_patterns'):
                for sub_pattern in pattern.url_patterns:
                    try:
                        url_patterns.append({
                            "pattern": str(pattern.pattern) + str(sub_pattern.pattern),
                            "name": sub_pattern.name,
                            "lookup_str": sub_pattern.lookup_str
                        })
                    except Exception:
                        pass
            elif hasattr(pattern, 'name'):
                url_patterns.append({
                    "pattern": str(pattern.pattern),
                    "name": pattern.name,
                    "lookup_str": pattern.lookup_str
                })
        
        context["url_patterns"] = url_patterns[:50]
        return context


class DebugMockView(LoginRequiredMixin, StaffRequiredMixin, TemplateView):
    template_name = "administration/debug/mock.html"

    def post(self, request, *args, **kwargs):
        if not Faker:
            messages.error(request, "Faker 库未安装，无法生成数据。请运行 'pip install faker'")
            return self.get(request, *args, **kwargs)

        fake = Faker("zh_CN")
        section = request.POST.get("mock_section")
        
        try:
            if section == "on" or request.POST.get("users_count"): # Users
                count = int(request.POST.get("users_count", 10))
                with_avatar = request.POST.get("users_avatar") == "on"
                
                for _ in range(count):
                    username = fake.user_name()
                    email = fake.email()
                    if not User.objects.filter(username=username).exists():
                        user = User.objects.create_user(
                            username=username,
                            email=email,
                            password="password123",
                            nickname=fake.name(),
                            bio=fake.text(max_nb_chars=100)
                        )
                        if with_avatar:
                            # Using UI Avatars for consistent mock images without external dependency issues
                            # In a real scenario, we might download images, but that's slow.
                            pass 
                messages.success(request, f"成功生成 {count} 个用户")

            elif request.POST.get("posts_count"): # Content
                cat_count = int(request.POST.get("categories_count", 5))
                tag_count = int(request.POST.get("tags_count", 10))
                post_count = int(request.POST.get("posts_count", 20))
                
                # Categories
                cats = []
                for _ in range(cat_count):
                    name = fake.word() + "分类"
                    cat, _ = Category.objects.get_or_create(name=name)
                    cats.append(cat)
                
                # Tags
                tags = []
                for _ in range(tag_count):
                    name = fake.word()
                    tag, _ = Tag.objects.get_or_create(name=name)
                    tags.append(tag)
                
                # Posts
                users = list(User.objects.all())
                if not users:
                    messages.error(request, "没有用户，无法生成文章")
                    return self.get(request, *args, **kwargs)
                
                import random
                for _ in range(post_count):
                    title = fake.sentence(nb_words=6)
                    author = random.choice(users)
                    category = random.choice(cats) if cats else None
                    post = Post.objects.create(
                        title=title,
                        author=author,
                        category=category,
                        content=fake.text(max_nb_chars=2000),
                        excerpt=fake.text(max_nb_chars=100),
                        status="published"
                    )
                    if tags:
                        post.tags.set(random.sample(tags, k=min(len(tags), 3)))
                
                messages.success(request, f"成功生成 {post_count} 篇文章, {cat_count} 个分类, {tag_count} 个标签")

            elif request.POST.get("comments_per_post"): # Interaction
                max_comments = int(request.POST.get("comments_per_post", 5))
                posts = Post.objects.all()
                users = list(User.objects.all())
                
                if not posts or not users:
                    messages.error(request, "缺少文章或用户，无法生成评论")
                    return self.get(request, *args, **kwargs)
                
                import random
                count = 0
                for post in posts:
                    for _ in range(random.randint(0, max_comments)):
                        Comment.objects.create(
                            post=post,
                            user=random.choice(users),
                            content=fake.sentence(),
                            active=True
                        )
                        count += 1
                messages.success(request, f"成功生成 {count} 条评论")

        except Exception as e:
            messages.error(request, f"生成失败: {str(e)}")

        return self.get(request, *args, **kwargs)


class DebugCacheView(LoginRequiredMixin, StaffRequiredMixin, TemplateView):
    template_name = "administration/debug/cache.html"

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        if action == "clear_all":
            cache.clear()
            messages.success(request, "全站缓存已清理")
        elif action == "clear_templates":
            # Django templates might not use the default cache backend directly, 
            # but usually cache.clear() handles standard caching.
            # Specific template loader cache clearing depends on loader.
            cache.clear() 
            messages.success(request, "模板缓存已清理")
        return self.get(request, *args, **kwargs)


class DebugEmailView(LoginRequiredMixin, StaffRequiredMixin, TemplateView):
    template_name = "administration/debug/email.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["email_host"] = getattr(settings, "EMAIL_HOST", "Unknown")
        context["email_port"] = getattr(settings, "EMAIL_PORT", "Unknown")
        context["email_host_user"] = getattr(settings, "EMAIL_HOST_USER", "Unknown")
        context["email_use_tls"] = getattr(settings, "EMAIL_USE_TLS", "Unknown")
        return context

    def post(self, request, *args, **kwargs):
        recipient = request.POST.get("recipient")
        subject = request.POST.get("subject")
        message = request.POST.get("message")

        if not recipient or not subject or not message:
            messages.error(request, "请填写完整信息")
            return self.get(request, *args, **kwargs)

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [recipient],
                fail_silently=False,
            )
            messages.success(request, f"测试邮件已发送至 {recipient}")
        except Exception as e:
            messages.error(request, f"邮件发送失败: {str(e)}")
        
        return self.get(request, *args, **kwargs)
from constance import config
from django.conf import settings as django_settings


class SettingsView(LoginRequiredMixin, StaffRequiredMixin, TemplateView):
    """
    系统设置视图
    基于 django-constance 动态管理网站配置。
    """
    template_name = "administration/settings.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Manually construct config dict based on CONSTANCE_CONFIG
        config_data = {}
        if hasattr(django_settings, "CONSTANCE_CONFIG"):
            for key, options in django_settings.CONSTANCE_CONFIG.items():
                value = getattr(config, key)
                help_text = options[1] if len(options) > 1 else ""
                config_data[key] = {
                    "value": value,
                    "help_text": help_text,
                    "type": type(value).__name__,
                }
        context["config"] = config_data
        return context

    def post(self, request, *args, **kwargs):
        # Save settings
        if hasattr(django_settings, "CONSTANCE_CONFIG"):
            for key in django_settings.CONSTANCE_CONFIG.keys():
                if key in request.POST:
                    new_value = request.POST.get(key)
                    # Simple type conversion (improve this for booleans, ints etc)
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
                    # Checkbox unchecked
                    setattr(config, key, False)
                    
        messages.success(request, "设置已保存")
        return self.get(request, *args, **kwargs)
