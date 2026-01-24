from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.views.generic import ListView, DetailView
from django.db.models import Q, Count
from django.contrib import messages
from django.http import HttpResponse
from .models import Post, Category, Tag, Comment, PostViewHistory
from core.models import Page
from .forms import CommentForm
from users.models import Notification, User
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import re
from meta.views import Meta
from .services import create_comment
from .schemas import CommentCreateSchema


class SidebarContextMixin:
    """
    侧边栏数据混入类 (Mixin)

    为视图提供侧边栏所需的上下文数据，包括：
    - 热门标签 (Top 30)
    - 最新评论 (Top 5)
    - 热门文章 (Top 5)
    - 热门分类 (Top 10)
    """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ttl = getattr(settings, "SIDEBAR_CACHE_TTL", 300)

        def load_cached(key, builder):
            data = cache.get(key)
            if data is None:
                data = builder()
                cache.set(key, data, ttl)
            return data

        context["sidebar_tags"] = load_cached(
            "sidebar:tags",
            lambda: list(
                Tag.objects.filter(is_active=True)
                .annotate(count=Count("posts"))
                .order_by("-count")[:30]
            ),
        )
        context["sidebar_comments"] = load_cached(
            "sidebar:comments",
            lambda: list(
                Comment.objects.filter(active=True)
                .select_related("user", "post")
                .order_by("-created_at")[:5]
            ),
        )
        context["sidebar_popular_posts"] = load_cached(
            "sidebar:popular_posts",
            lambda: list(
                Post.objects.filter(status="published").order_by("-views")[:5]
            ),
        )
        context["sidebar_categories"] = load_cached(
            "sidebar:categories",
            lambda: list(
                Category.objects.annotate(count=Count("posts")).order_by("-count")[:10]
            ),
        )
        return context


class HomeView(SidebarContextMixin, ListView):
    """
    博客首页视图

    展示最新发布的文章列表，支持分页。
    """

    model = Post
    template_name = "blog/post_list.html"
    context_object_name = "posts"
    paginate_by = 9
    queryset = (
        Post.objects.filter(status="published")
        .select_related("author", "category")
        .prefetch_related("tags")
    )


class ArchiveView(SidebarContextMixin, ListView):
    """
    文章归档视图

    按时间轴展示所有已发布文章。
    """

    model = Post
    template_name = "blog/archive.html"
    context_object_name = "posts"
    queryset = (
        Post.objects.filter(status="published")
        .select_related("author", "category")
        .prefetch_related("tags")
        .order_by("-created_at")
    )
    paginate_by = 100  # 归档页显示更多文章，便于快速浏览


class PostDetailView(DetailView):
    """
    文章详情视图

    展示文章完整内容、评论区，并处理密码保护、阅读计数和评论提交。
    """

    model = Post
    template_name = "blog/post_detail.html"
    context_object_name = "post"

    def get_queryset(self):
        return (
            Post.objects.select_related("author", "category")
            .prefetch_related("tags")
            .all()
        )

    def get_context_data(self, **kwargs):
        """添加评论、评论表单和 Meta 信息到上下文"""
        context = super().get_context_data(**kwargs)
        ttl = getattr(settings, "SIDEBAR_CACHE_TTL", 300)

        def load_cached(key, builder):
            data = cache.get(key)
            if data is None:
                data = builder()
                cache.set(key, data, ttl)
            return data

        # 预加载回复以避免模板中的 N+1 查询问题
        # 注意：只获取顶级评论，子回复通过 prefetch_related 加载
        from django.db.models import Prefetch

        replies_prefetch = Prefetch(
            "replies",
            queryset=Comment.objects.filter(active=True).select_related("user"),
            to_attr="active_replies_list",
        )
        context["comments"] = (
            self.object.comments.filter(active=True, parent__isnull=True)
            .select_related("user")
            .prefetch_related(replies_prefetch)
        )

        context["comment_form"] = CommentForm()

        # 生成 SEO Meta 数据
        context["meta"] = self.get_meta_data()

        # 获取相关文章 (基于相同标签，排除当前文章)
        # 算法：
        # 1. 获取当前文章的所有标签 ID
        # 2. 查找包含这些标签的其他文章
        # 3. 按匹配标签的数量降序排序
        # 4. 取前 3 篇
        post_tags_ids = list(self.object.tags.values_list("id", flat=True))
        related_posts = load_cached(
            f"post:{self.object.id}:related",
            lambda: list(
                Post.objects.filter(tags__in=post_tags_ids, status="published")
                .exclude(id=self.object.id)
                .annotate(same_tags=Count("tags"))
                .order_by("-same_tags", "-created_at")[:3]
            ),
        )

        # 如果相关文章不足 3 篇，补充同分类下的最新文章
        if len(related_posts) < 3 and self.object.category:
            remaining_count = 3 - len(related_posts)
            category_posts = list(
                Post.objects.filter(category=self.object.category, status="published")
                .exclude(id=self.object.id)
                .exclude(id__in=[p.id for p in related_posts])
                .order_by("-created_at")[:remaining_count]
            )

            related_posts = related_posts + category_posts

        context["related_posts"] = related_posts

        # 上一篇和下一篇 (Previous & Next Post)
        # 仅获取已发布的文章，且按时间排序
        context["previous_post"] = load_cached(
            f"post:{self.object.id}:previous",
            lambda: Post.objects.filter(
                status="published", created_at__lt=self.object.created_at
            )
            .order_by("-created_at")
            .first(),
        )

        context["next_post"] = load_cached(
            f"post:{self.object.id}:next",
            lambda: Post.objects.filter(
                status="published", created_at__gt=self.object.created_at
            )
            .order_by("created_at")
            .first(),
        )

        return context

    def get_meta_data(self):
        """生成页面 Meta 数据用于 SEO"""
        post = self.object
        ttl = getattr(settings, "SIDEBAR_CACHE_TTL", 300)
        cache_key = f"post:{post.id}:{int(post.updated_at.timestamp())}:meta_desc"
        description = cache.get(cache_key)

        # 处理描述：优先使用摘要，否则截取内容并去除 Markdown/HTML 标签
        if not description:
            description = post.excerpt
            if not description:
                from django.utils.html import strip_tags
                import markdown

                html_content = markdown.markdown(post.content)
                text_content = strip_tags(html_content)
                description = (
                    text_content[:150] + "..."
                    if len(text_content) > 150
                    else text_content
                )
            cache.set(cache_key, description, ttl)

        return Meta(
            title=post.title,
            description=description,
            keywords=list(post.tags.values_list("name", flat=True)),
            image=post.cover_image.url if post.cover_image else None,
            url=self.request.build_absolute_uri(),
            object_type="article",
            published_time=post.created_at,
            modified_time=post.updated_at,
            author=post.author.username,
        )

    def get(self, request, *args, **kwargs):
        """处理 GET 请求：文章展示、密码验证逻辑、阅读计数"""
        from django.db.models import F

        self.object = self.get_object()

        # 密码保护检查
        # 作者和超级用户可直接查看，其他用户需验证密码
        if self.object.password:
            is_author = request.user == self.object.author
            is_superuser = request.user.is_superuser
            if not (is_author or is_superuser):
                session_key = f"post_unlocked_{self.object.pk}"
                if not request.session.get(session_key, False):
                    return render(
                        request, "blog/password_required.html", {"post": self.object}
                    )

        # 增加阅读量 (使用原子更新，避免竞态条件)
        # update_fields 避免副作用（如更新 updated_at）
        Post.objects.filter(pk=self.object.pk).update(views=F("views") + 1)
        self.object.refresh_from_db(fields=["views"])

        # 记录已登录用户的阅读历史
        if request.user.is_authenticated:
            PostViewHistory.objects.update_or_create(
                user=request.user,
                post=self.object,
                defaults={"viewed_at": timezone.now()},
            )

        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        """处理 POST 请求：文章密码验证或评论提交"""
        self.object = self.get_object()

        # 处理密码提交
        if "post_password" in request.POST:
            password = request.POST.get("post_password")
            if self.object.check_password(password):
                request.session[f"post_unlocked_{self.object.pk}"] = True
                messages.success(request, "密码验证通过")
                return redirect("post_detail", slug=self.object.slug)
            else:
                messages.error(request, "密码错误，请重试")
                return render(
                    request, "blog/password_required.html", {"post": self.object}
                )

        # 处理评论提交
        # 确保文章已解锁（如有密码）
        if self.object.password:
            is_author = request.user == self.object.author
            is_superuser = request.user.is_superuser
            if not (is_author or is_superuser):
                session_key = f"post_unlocked_{self.object.pk}"
                if not request.session.get(session_key, False):
                    return render(
                        request, "blog/password_required.html", {"post": self.object}
                    )

        form = CommentForm(request.POST)
        if form.is_valid():
            if not request.user.is_authenticated:
                return redirect("users:login")

            try:
                comment_data = CommentCreateSchema(
                    content=form.cleaned_data["content"],
                    parent_id=(
                        int(request.POST.get("parent_id"))
                        if request.POST.get("parent_id")
                        else None
                    ),
                )

                create_comment(post=self.object, user=request.user, data=comment_data)

                messages.success(request, "您的评论已发布！")
                return redirect("post_detail", slug=self.object.slug)
            except ValueError as e:
                messages.error(request, f"评论创建失败: {str(e)}")
                return redirect("post_detail", slug=self.object.slug)
        else:
            context = self.get_context_data()
            context["comment_form"] = form
            return self.render_to_response(context)


class CategoryListView(ListView):
    """
    分类列表视图

    展示所有文章分类。
    """

    model = Category
    template_name = "blog/category_list.html"
    context_object_name = "categories"
    queryset = Category.objects.order_by("name")


class TagListView(ListView):
    """
    标签列表视图

    展示所有标签，支持按首字母分组或标签云展示。
    """

    model = Tag
    template_name = "blog/tag_list.html"
    context_object_name = "tags"

    def get_queryset(self):
        return (
            Tag.objects.filter(is_active=True)
            .annotate(count=Count("posts"))
            .order_by("-count", "name")
        )


class PostByCategoryView(SidebarContextMixin, ListView):
    """
    分类文章列表视图

    展示特定分类下的所有已发布文章。
    """

    model = Post
    template_name = "blog/post_list.html"
    context_object_name = "posts"
    paginate_by = 9

    def get_queryset(self):
        """获取指定分类下的已发布文章，并优化数据库查询"""
        self.category = get_object_or_404(Category, slug=self.kwargs["slug"])
        return (
            Post.objects.filter(category=self.category, status="published")
            .select_related("author", "category")
            .prefetch_related("tags")
        )

    def get_context_data(self, **kwargs):
        """添加当前分类信息到上下文"""
        context = super().get_context_data(**kwargs)
        context["title"] = f"分类: {self.category.name}"
        context["category"] = self.category
        return context


class PostByTagView(SidebarContextMixin, ListView):
    """
    标签文章列表视图

    展示特定标签下的所有已发布文章。
    """

    model = Post
    template_name = "blog/post_list.html"
    context_object_name = "posts"
    paginate_by = 9

    def get_queryset(self):
        self.tag = get_object_or_404(Tag, slug=self.kwargs["slug"])
        return (
            Post.objects.filter(tags=self.tag, status="published")
            .select_related("author", "category")
            .prefetch_related("tags")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"标签: {self.tag.name}"
        context["tag"] = self.tag
        return context


class SearchView(SidebarContextMixin, ListView):
    """
    搜索结果视图

    支持全文搜索（如果安装了 django-watson）或简单的标题/内容匹配。
    """

    model = Post
    template_name = "blog/search_results.html"
    context_object_name = "posts"
    paginate_by = 9

    def get_queryset(self):
        """根据查询参数过滤文章"""
        query = self.request.GET.get("q") or ""
        query = re.sub(r"\s+", " ", query).strip()
        if not query:
            return Post.objects.none()

        published_posts = (
            Post.objects.filter(status="published")
            .select_related("author", "category")
            .prefetch_related("tags")
        )
        try:
            from watson import search as watson

            results = watson.filter(published_posts, query)
            if results:
                return results
        except Exception:
            pass

        return published_posts.filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = (self.request.GET.get("q") or "").strip()
        return context


@login_required
@require_POST
def delete_comment(request, pk):
    """
    删除评论视图

    仅限评论作者或管理员删除评论。
    支持 HTMX 请求，删除后在前端移除评论元素。
    """
    comment = get_object_or_404(Comment, pk=pk)

    # 权限检查
    if request.user != comment.user and not request.user.is_staff:
        messages.error(request, "您没有权限删除此评论")
        return redirect(comment.post.get_absolute_url())

    post_url = comment.post.get_absolute_url()
    comment.delete()

    # HTMX 支持：返回空响应或触发前端事件
    if request.headers.get("HX-Request"):
        return HttpResponse("")

    messages.success(request, "评论已删除")
    return redirect(post_url)
