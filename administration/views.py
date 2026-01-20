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
    GroupForm,
    SearchPlaceholderForm,
    UserTitleForm,
)
from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import TruncDate
from datetime import timedelta
import psutil
import sys
from users.models import UserTitle
from django.contrib.auth.models import Group
from django.contrib.admin.models import LogEntry
from django.conf import settings
import os
from django.http import HttpResponse, Http404

User = get_user_model()


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
        
        # 文章数据
        total_posts = Post.objects.count()
        posts_last_month = Post.objects.filter(created_at__gte=last_month).count()
        
        # 计算增长率 (净增量 / 上期总量)
        total_prev = total_posts - posts_last_month
        post_growth = 0
        if total_prev > 0:
            post_growth = (posts_last_month / total_prev) * 100
        elif posts_last_month > 0:
            post_growth = 100
            
        context['total_posts'] = total_posts
        context['post_growth'] = round(post_growth, 1)
        
        # 评论数据
        total_comments = Comment.objects.count()
        pending_comments = Comment.objects.filter(active=False).count()
        context['total_comments'] = total_comments
        context['pending_comments'] = pending_comments
        
        # 2. 图表数据 (Charts Data)
        
        # 评论状态分布 (饼图)
        active_comments = Comment.objects.filter(active=True).count()
        inactive_comments = pending_comments
        context['comment_status_data'] = [active_comments, inactive_comments]
        
        # 用户角色分布 (环形图)
        superusers = User.objects.filter(is_superuser=True).count()
        staff = User.objects.filter(is_staff=True, is_superuser=False).count()
        normal_users = User.objects.filter(is_staff=False).count()
        context['user_role_data'] = [superusers, staff, normal_users]
        
        # 评论趋势 (折线图) - 最近30天
        trend_data = (
            Comment.objects.filter(created_at__gte=last_month)
            .annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )
        
        # 补全缺失日期的据
        date_map = {item['date']: item['count'] for item in trend_data}
        dates = []
        counts = []
        for i in range(30):
            d = (last_month + timedelta(days=i)).date()
            dates.append(d.strftime('%m-%d'))
            counts.append(date_map.get(d, 0))
            
        context['trend_dates'] = dates
        context['trend_counts'] = counts
        
        # 热门文章 Top 5 (柱状图)
        top_posts = Post.objects.order_by('-views')[:5]
        context['top_posts'] = top_posts
        context['top_posts_labels'] = [p.title[:10] + '...' if len(p.title) > 10 else p.title for p in top_posts]
        
        # 系统健康状态 (实时数据)
        try:
            cpu_usage = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
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
            
            context['system_info'] = {
                'cpu_percent': cpu_usage,
                'memory_percent': memory.percent,
                'disk_percent': disk.percent,
                'python_version': platform.python_version(),
                'platform_system': platform.system(),
                'platform_release': platform.release(),
                'server_time': timezone.now(),
                'uptime': uptime_str,
            }
            # 简化健康评分 (反向负载)
            health_score = 100 - max(cpu_usage, memory.percent, disk.percent)
            context['system_health'] = int(max(0, health_score))
        except Exception:
            context['system_info'] = {}
            context['system_health'] = 85 # 获取失败时的默认值
        
        # 最近动态 (用于 Feed 流)
        context['recent_comments'] = Comment.objects.select_related('user', 'post').order_by('-created_at')[:5]
        
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
            post.status = 'draft'
            post.views = 0
            post.save()
            
            # 恢复 M2M 关系
            post.tags.set(tags)
            
            messages.success(request, "文章已复制为草稿")
        except Exception as e:
            messages.error(request, f"复制失败: {str(e)}")
            
        return redirect('administration:post_list')


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
    
    返回 JSON 格式的标签建议列表，用于前端输入联想。
    """
    def get(self, request):
        query = request.GET.get('q', '')
        if len(query) < 1:
            return JsonResponse({'results': []})
        
        tags = Tag.objects.filter(name__icontains=query).values_list('name', flat=True)[:10]
        return JsonResponse({'results': list(tags)})


# --- Comment Views (评论管理视图) ---
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
            page.status = 'draft'
            page.save()
            
            messages.success(request, "页面已复制为草稿")
        except Exception as e:
            messages.error(request, f"复制失败: {str(e)}")
            
        return redirect('administration:page_list')


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
        qs = super().get_queryset().select_related("title")
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(text__icontains=query)
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
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="audit_logs.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Time', 'User', 'Action', 'Content Type', 'Object', 'Message'])
        
        logs = LogEntry.objects.select_related('user', 'content_type').order_by('-action_time')
        for log in logs:
            writer.writerow([
                log.action_time,
                log.user.username,
                log.get_action_flag_display(),
                str(log.content_type),
                log.object_repr,
                log.change_message
            ])
            
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
                if f.is_file() and (f.suffix == '.log' or f.suffix == '.zip'):
                    files.append({
                        "name": f.name,
                        "size": f.stat().st_size,
                        "mtime": datetime.fromtimestamp(f.stat().st_mtime),
                        "path": str(f)
                    })
        # 按修改时间倒序
        files.sort(key=lambda x: x["mtime"], reverse=True)
        context["log_files"] = files
        
        # 2. 确定当前选中的文件
        current_file = self.request.GET.get('file')
        if not current_file and files:
            current_file = files[0]['name'] # 默认选中最新的
            
        context["current_file"] = current_file
        
        # 3. 读取当前文件内容
        content = ""
        file_info = None
        
        if current_file:
            # 查找选中的文件信息
            for f in files:
                if f['name'] == current_file:
                    file_info = f
                    break
            
            if file_info and file_info['name'].endswith('.log'):
                file_path = log_dir / current_file
                try:
                    # 读取最后 2000 行
                    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                        from collections import deque
                        lines = list(deque(f, 2000))
                        content = "".join(lines)
                except Exception as e:
                    content = f"Error reading file: {str(e)}"
            elif file_info and file_info['name'].endswith('.zip'):
                content = "ZIP archives cannot be viewed directly. Please download to view."
                
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
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                # 简单读取，大文件可能需要优化 (seek)
                # 这里假设日志文件不会特别巨大，或者我们只读最后一部分
                # 使用 deque 读取最后 N 行
                from collections import deque
                lines = list(deque(f, 2000))
        except Exception as e:
            lines = [f"Error reading file: {str(e)}"]
            
        content = "".join(lines)
        
        return render(request, "administration/logfile_detail.html", {
            "filename": filename,
            "content": content
        })


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
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=filename)


class LogFileDeleteView(LoginRequiredMixin, StaffRequiredMixin, View):
    """
    删除系统日志文件
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
                os.remove(file_path)
                messages.success(request, f"文件 {filename} 已删除")
            except Exception as e:
                messages.error(request, f"删除失败: {str(e)}")
                
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


# --- Export/Import Views (导入导出视图) ---
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


# --- Debug Views (调试工具视图) ---
from django.core.cache import cache
from django.core.mail import send_mail
from django.urls import get_resolver, reverse
from django.db import connection
from django.apps import apps
import re

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
    template_name = "administration/debug.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 显式添加 debug_mode 到上下文
        context['debug_mode'] = settings.DEBUG

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
                if hasattr(pattern, 'url_patterns'):
                    # 递归处理 include()
                    new_prefix = prefix + str(pattern.pattern)
                    
                    # 处理命名空间
                    new_ns = namespace_prefix
                    if hasattr(pattern, 'namespace') and pattern.namespace:
                        if new_ns:
                            new_ns = f"{new_ns}:{pattern.namespace}"
                        else:
                            new_ns = pattern.namespace
                    
                    process_patterns(pattern.url_patterns, new_prefix, new_ns)
                elif hasattr(pattern, 'name') and pattern.name:
                    # 叶子节点 (实际视图)
                    full_pattern = prefix + str(pattern.pattern)
                    
                    # 构建包含命名空间的完整名称
                    full_name = pattern.name
                    if namespace_prefix:
                        full_name = f"{namespace_prefix}:{pattern.name}"
                    
                    # 清理正则表达式符号，用于显示
                    display_pattern = full_pattern.replace('^', '').replace('$', '')
                    if not display_pattern.startswith('/'):
                        display_pattern = '/' + display_pattern
                        
                    # 尝试生成示例 URL
                    sample_url = None
                    description = ""
                    
                    # --- 自动生成描述逻辑 ---
                    
                    # 1. 自动解析 Admin 视图
                    if 'admin' in full_name:
                        try:
                            local_name = pattern.name
                            
                            action = ""
                            model_info = ""
                            
                            if local_name == 'index':
                                description = "后台管理首页"
                            elif local_name == 'password_change':
                                description = "修改密码"
                            elif local_name == 'logout':
                                description = "注销登录"
                            elif local_name.endswith('_changelist'):
                                action = "列表"
                                model_info = local_name[:-11]
                            elif local_name.endswith('_add'):
                                action = "添加"
                                model_info = local_name[:-4]
                            elif local_name.endswith('_change'):
                                action = "编辑"
                                model_info = local_name[:-7]
                            elif local_name.endswith('_delete'):
                                action = "删除"
                                model_info = local_name[:-7]
                            elif local_name.endswith('_history'):
                                action = "历史"
                                model_info = local_name[:-8]
                            
                            if action and model_info:
                                parts = model_info.split('_')
                                found_model = None
                                # 尝试解析 App 和 Model
                                for i in range(1, len(parts)):
                                    app_label = '_'.join(parts[:i])
                                    model_name = '_'.join(parts[i:])
                                    try:
                                        found_model = apps.get_model(app_label, model_name)
                                        break
                                    except LookupError:
                                        continue
                                
                                if found_model:
                                    description = f"{found_model._meta.verbose_name} {action}"
                                else:
                                    formatted_name = model_info.replace('_', ' ').title()
                                    description = f"{formatted_name} {action}"
                            
                            if not description:
                                description = "后台管理功能"
                                
                        except Exception:
                            description = "后台管理"
                    
                    # 2. 手动映射 (高优先级覆盖)
                    if full_name == 'home': description = "前台首页"
                    elif full_name == 'post_list': description = "文章列表"
                    elif full_name == 'post_detail': description = "文章详情"
                    elif full_name == 'archive': description = "文章归档"
                    elif full_name == 'category_list': description = "分类列表"
                    elif full_name == 'tag_list': description = "标签列表"
                    elif full_name == 'search': description = "搜索页面"
                    elif full_name == 'about': description = "关于页面"
                    elif full_name == 'contact': description = "联系页面"
                    elif full_name.startswith('administration:'): description = "自定义管理面板"
                    
                    # --- URL 反向解析逻辑 ---
                    
                    # 尝试反向解析无参数 URL
                    try:
                        sample_url = reverse(full_name)
                    except Exception:
                        pass
                    
                    # 判断是否需要参数
                    has_args = '<' in full_pattern or '(?P' in full_pattern
                    
                    # 如果有 sample_url，说明不需要参数（或使用了默认值）
                    needs_args = has_args and not sample_url
                    
                    url_patterns.append({
                        "pattern": full_pattern,
                        "display_pattern": display_pattern,
                        "name": full_name,
                        "sample_url": sample_url,
                        "description": description,
                        "needs_args": needs_args
                    })

        process_patterns(resolver.url_patterns)
        
        # 按名称排序以提高可读性
        url_patterns.sort(key=lambda x: x['name'] or '')
        
        context["url_patterns"] = url_patterns
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


class DebugEmailView(LoginRequiredMixin, StaffRequiredMixin, TemplateView):
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
from pygments.styles import get_all_styles


class SettingsView(LoginRequiredMixin, StaffRequiredMixin, TemplateView):
    """
    系统设置视图
    
    基于 django-constance 动态管理网站配置。
    """
    template_name = "administration/settings.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 获取所有可用的 Pygments 风格并排序
        context["pygments_styles"] = sorted(list(get_all_styles()))
        
        # 辅助函数：获取配置项数据
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

                fieldsets.append({
                    "title": title,
                    "slug": slug,
                    "icon": icon,
                    "items": items
                })
        else:
            # 降级处理：如果未定义分组配置
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
        # 保存设置
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
