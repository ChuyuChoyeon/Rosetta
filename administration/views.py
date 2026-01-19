from typing import Any, Dict, List
from django.db.models import QuerySet, Sum
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
from blog.models import Post, Comment, Category, Tag, PostViewHistory
from core.models import Page, Navigation, FriendLink, SearchPlaceholder
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
    SearchPlaceholderForm,
    UserTitleForm,
)

User = get_user_model()
from users.models import UserTitle


class StaffRequiredMixin(UserPassesTestMixin):
    """
    权限混入类：仅允许管理员（is_staff=True）访问。
    
    用于保护管理后台的所有视图，确保只有具备管理员权限的用户才能访问。
    """
    def test_func(self) -> bool:
        return self.request.user.is_staff


from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import TruncDate
from datetime import timedelta
import psutil
import sys
import platform

class IndexView(LoginRequiredMixin, StaffRequiredMixin, TemplateView):
    """
    管理后台首页视图
    """
    template_name: str = "administration/index.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        
        # 1. Key Metrics
        today = timezone.now()
        last_month = today - timedelta(days=30)
        
        # Posts
        total_posts = Post.objects.count()
        posts_last_month = Post.objects.filter(created_at__gte=last_month).count()
        
        # Calculate growth of Total Posts (Net Additions / Previous Total)
        total_prev = total_posts - posts_last_month
        post_growth = 0
        if total_prev > 0:
            post_growth = (posts_last_month / total_prev) * 100
        elif posts_last_month > 0:
            post_growth = 100
            
        context['total_posts'] = total_posts
        context['post_growth'] = round(post_growth, 1)
        
        # Comments
        total_comments = Comment.objects.count()
        pending_comments = Comment.objects.filter(active=False).count()
        context['total_comments'] = total_comments
        context['pending_comments'] = pending_comments
        
        # 2. Charts Data
        
        # Comment Status (Pie)
        active_comments = Comment.objects.filter(active=True).count()
        inactive_comments = pending_comments
        context['comment_status_data'] = [active_comments, inactive_comments]
        
        # User Roles (Donut)
        superusers = User.objects.filter(is_superuser=True).count()
        staff = User.objects.filter(is_staff=True, is_superuser=False).count()
        normal_users = User.objects.filter(is_staff=False).count()
        context['user_role_data'] = [superusers, staff, normal_users]
        
        # Comment Trend (Line) - Last 30 Days
        # We need a list of dates and counts.
        trend_data = (
            Comment.objects.filter(created_at__gte=last_month)
            .annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )
        
        # Fill in missing dates
        date_map = {item['date']: item['count'] for item in trend_data}
        dates = []
        counts = []
        for i in range(30):
            d = (last_month + timedelta(days=i)).date()
            dates.append(d.strftime('%m-%d'))
            counts.append(date_map.get(d, 0))
            
        context['trend_dates'] = dates
        context['trend_counts'] = counts
        
        # Top 5 Popular Articles (Bar)
        top_posts = Post.objects.order_by('-views')[:5]
        context['top_posts'] = top_posts  # Pass full objects for template links
        context['top_posts_labels'] = [p.title[:10] + '...' if len(p.title) > 10 else p.title for p in top_posts]
        
        # System Health (Real Data)
        try:
            cpu_usage = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            context['system_info'] = {
                'cpu_percent': cpu_usage,
                'memory_percent': memory.percent,
                'disk_percent': disk.percent,
                'python_version': platform.python_version(),
                'platform_system': platform.system(),
                'platform_release': platform.release(),
                'server_time': timezone.now(),
            }
            # Simplified health score (inverse of average load)
            health_score = 100 - max(cpu_usage, memory.percent, disk.percent)
            context['system_health'] = int(max(0, health_score))
        except Exception:
            context['system_info'] = {}
            context['system_health'] = 85 # Fallback
        
        # Recent Activity (for feed)
        context['recent_comments'] = Comment.objects.select_related('user', 'post').order_by('-created_at')[:5]
        
        return context


# --- Generic CRUD Mixins ---
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
    
    提供通用的对象创建功能。
    
    特性：
    1. 自动查找模板 ({model}_form.html 或 generic_form.html)。
    2. 处理保存后的跳转逻辑 (保存并继续编辑、保存并新增另一个)。
    3. 集成消息提示 (创建成功)。
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
        messages.success(self.request, f"{self.model._meta.verbose_name} 更新成功")
        return super().form_valid(form)


class BaseDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    """
    基础删除视图混入类
    
    提供通用的对象删除确认功能。
    删除成功后显示消息提示。
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
    
    展示博客文章列表。
    支持：
    - 关键词搜索 (标题)
    - 状态过滤 (草稿/发布)
    - 关联查询优化 (author, category)
    """
    model = Post
    template_name = "dashboard/post_list.html"
    context_object_name = "posts"
    ordering = ["-created_at"]

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
    
    展示文章分类。
    支持按名称搜索，并统计每个分类下的文章数量。
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
    
    展示文章标签。
    支持按名称搜索，并统计每个标签下的文章数量。
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


class TagAutocompleteView(LoginRequiredMixin, StaffRequiredMixin, View):
    """
    标签自动补全视图
    
    返回 JSON 格式的标签建议列表
    """
    def get(self, request):
        query = request.GET.get('q', '')
        if len(query) < 1:
            return JsonResponse({'results': []})
        
        tags = Tag.objects.filter(name__icontains=query).values_list('name', flat=True)[:10]
        return JsonResponse({'results': list(tags)})


# --- Comment Views ---
class CommentListView(BaseListView):
    """
    评论列表视图
    
    展示所有评论。
    支持：
    - 内容搜索
    - 状态过滤 (已审核/待审核)
    - 关联查询优化 (post, user)
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
    
    支持修改评论内容和审核状态 (active)。
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
            page.status = 'draft'
            page.save()
            
            messages.success(request, "页面已复制为草稿")
        except Exception as e:
            messages.error(request, f"复制失败: {str(e)}")
            
        return redirect('administration:page_list')


# --- Navigation Views ---
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
        if query:
            qs = qs.filter(title__icontains=query)
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
    导航菜单删除视图
    """
    model = Navigation
    success_url = reverse_lazy("administration:navigation_list")


# --- FriendLink Views ---
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
        if query:
            qs = qs.filter(name__icontains=query)
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


# --- Search Placeholder Management ---

class SearchPlaceholderListView(BaseListView):
    model = SearchPlaceholder
    template_name = "administration/searchplaceholder_list.html"
    context_object_name = "placeholders"
    ordering = ["order", "-created_at"]

    def get_queryset(self):
        qs = super().get_queryset()
        query = self.request.GET.get("q")
        if query:
            qs = qs.filter(text__icontains=query)
        return qs


class SearchPlaceholderCreateView(BaseCreateView):
    model = SearchPlaceholder
    form_class = SearchPlaceholderForm
    success_url = reverse_lazy("administration:searchplaceholder_list")


class SearchPlaceholderUpdateView(BaseUpdateView):
    model = SearchPlaceholder
    form_class = SearchPlaceholderForm
    success_url = reverse_lazy("administration:searchplaceholder_list")


class SearchPlaceholderDeleteView(BaseDeleteView):
    model = SearchPlaceholder
    success_url = reverse_lazy("administration:searchplaceholder_list")


# --- User Views ---
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
        qs = super().get_queryset()
        query = self.request.GET.get("q")
        if query:
            qs = qs.filter(username__icontains=query)
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
        # 密码处理在 UserForm.save() 中
        return super().form_valid(form)


class UserUpdateView(BaseUpdateView):
    """
    用户更新视图
    
    编辑用户信息（如权限、状态、基本资料）。
    """
    model = User
    form_class = UserForm
    success_url = reverse_lazy("administration:user_list")


# --- User Title Views ---
class UserTitleListView(BaseListView):
    model = UserTitle
    context_object_name = "titles"


class UserTitleCreateView(BaseCreateView):
    model = UserTitle
    form_class = UserTitleForm
    success_url = reverse_lazy("administration:usertitle_list")


class UserTitleUpdateView(BaseUpdateView):
    model = UserTitle
    form_class = UserTitleForm
    success_url = reverse_lazy("administration:usertitle_list")


class UserTitleDeleteView(BaseDeleteView):
    model = UserTitle
    success_url = reverse_lazy("administration:usertitle_list")


# --- Bulk Action View ---
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
    
    逻辑:
    1. 根据 model 参数动态查找模型类。
    2. 根据 action 参数执行相应的批量更新或删除操作。
    3. 返回操作结果消息。
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
    
    将指定模型的所有数据导出为 JSON 文件。
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
    
    从 JSON 文件导入数据到指定模型。
    支持更新现有记录 (基于 ID) 或创建新记录。
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
    """
    调试仪表盘视图
    
    展示系统调试信息，包括：
    - 数据库连接状态
    - 关键对象数量统计
    - 系统所有 URL 模式列表 (前 50 条)
    """
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


from core.services import generate_mock_data

class DebugMockView(LoginRequiredMixin, StaffRequiredMixin, TemplateView):
    """
    Mock 数据生成视图
    
    用于生成测试数据 (User, Post, Comment)。
    依赖 Faker 库。
    """
    template_name = "administration/debug/mock.html"

    def post(self, request, *args, **kwargs):
        try:
            # Extract counts from form
            users_count = int(request.POST.get("users_count", 0))
            categories_count = int(request.POST.get("categories_count", 0))
            tags_count = int(request.POST.get("tags_count", 0))
            posts_count = int(request.POST.get("posts_count", 0))
            comments_count = int(request.POST.get("comments_count", 0))
            password = request.POST.get("password", "password123")
            generate_extras = request.POST.get("generate_extras") == "on"
            
            # If "Generate All" or specific section, we can handle logic here.
            # But simpler to just pass all non-zero values to the service.
            # The UI might send 0 for hidden sections or we might need to check which section is active.
            # Let's assume the new UI will submit all relevant fields.
            
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
            if results['users']: msg_parts.append(f"{results['users']} 用户")
            if results['categories']: msg_parts.append(f"{results['categories']} 分类")
            if results['tags']: msg_parts.append(f"{results['tags']} 标签")
            if results['posts']: msg_parts.append(f"{results['posts']} 文章")
            if results['comments']: msg_parts.append(f"{results['comments']} 评论")
            
            if msg_parts:
                messages.success(request, f"成功生成: {', '.join(msg_parts)}")
            else:
                messages.warning(request, "没有生成任何数据 (数量均为 0)")
                
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
            
        from_email = getattr(config, "SMTP_FROM_EMAIL", None) or settings.DEFAULT_FROM_EMAIL

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


class SettingsView(LoginRequiredMixin, StaffRequiredMixin, TemplateView):
    """
    系统设置视图
    基于 django-constance 动态管理网站配置。
    """
    template_name = "administration/settings.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Helper to get item data
        def get_item_data(key):
            if not hasattr(django_settings, "CONSTANCE_CONFIG") or key not in django_settings.CONSTANCE_CONFIG:
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
                
                # Map titles to icons/slugs for UI
                icon = "settings"
                slug = "general"
                
                if "基本设置" in title or "General" in title:
                    icon = "tune"
                    slug = "general"
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

                fieldsets.append({
                    "title": title,
                    "slug": slug,
                    "icon": icon,
                    "items": items
                })
        else:
            # Fallback if no fieldsets defined
            items = []
            if hasattr(django_settings, "CONSTANCE_CONFIG"):
                for key in django_settings.CONSTANCE_CONFIG.keys():
                    item_data = get_item_data(key)
                    if item_data:
                        items.append(item_data)
            fieldsets.append({
                "title": "General",
                "slug": "general",
                "icon": "tune",
                "items": items
            })

        context["fieldsets"] = fieldsets
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
