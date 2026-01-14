from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import ListView, DetailView
from django.db.models import Q, Count
from django.contrib import messages
from .models import Post, Category, Tag, Comment, PostViewHistory, Subscriber
from core.models import Page
from .forms import CommentForm, SubscriberForm
from users.models import Notification, User
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import re
from meta.views import Meta


class SidebarContextMixin:
    """
    Mixin to provide sidebar data to context.
    Includes: Tag Cloud, Recent Comments, Popular Posts, Popular Categories, Friend Links.
    """
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Sidebar Data
        context["sidebar_tags"] = Tag.objects.filter(is_active=True).annotate(count=Count('posts')).order_by('-count')[:30]
        context["sidebar_comments"] = Comment.objects.filter(active=True).select_related('user', 'post').order_by('-created_at')[:5]
        context["sidebar_popular_posts"] = Post.objects.filter(status='published').order_by('-views')[:5]
        context["sidebar_categories"] = Category.objects.annotate(count=Count('posts')).order_by('-count')[:10]
        # FriendLinks are already in context_processor, but we can add specific logic if needed.
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


class PostDetailView(DetailView):
    """
    文章详情视图
    展示文章完整内容、评论区，并处理密码保护、阅读计数和评论提交。
    """

    model = Post
    template_name = "blog/post_detail.html"
    context_object_name = "post"

    def get_context_data(self, **kwargs):
        """添加评论、评论表单和Meta信息到上下文"""
        context = super().get_context_data(**kwargs)
        # 只获取顶级评论，回复通过 template 中的 comment.replies.all 访问
        context["comments"] = self.object.comments.filter(
            active=True, parent__isnull=True
        ).select_related("user")
        context["comment_form"] = CommentForm()

        # Meta 数据
        context["meta"] = self.get_meta_data()

        return context

    def get_meta_data(self):
        """生成页面 Meta 数据用于 SEO"""
        post = self.object
        return Meta(
            title=post.title,
            description=post.excerpt or post.content[:150],
            keywords=[tag.name for tag in post.tags.all()],
            image=post.cover_image.url if post.cover_image else None,
            url=self.request.build_absolute_uri(),
            object_type="article",
            published_time=post.created_at,
            modified_time=post.updated_at,
            author=post.author.username,
        )

    def get(self, request, *args, **kwargs):
        """处理 GET 请求：文章展示、密码验证逻辑、阅读计数"""
        self.object = self.get_object()

        # 密码保护检查
        # 作者和超级用户可直接查看
        if self.object.password:
            is_author = request.user == self.object.author
            is_superuser = request.user.is_superuser
            if not (is_author or is_superuser):
                session_key = f"post_unlocked_{self.object.pk}"
                if not request.session.get(session_key, False):
                    return render(
                        request, "blog/password_required.html", {"post": self.object}
                    )

        # 增加阅读量
        self.object.views += 1
        self.object.save()

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
            if password == self.object.password:
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
            comment = form.save(commit=False)
            comment.post = self.object
            comment.user = request.user

            # 先保存评论以生成 ID
            comment.save()

            # 处理父评论（回复）
            parent_id = request.POST.get("parent_id")
            if parent_id:
                try:
                    parent_comment = Comment.objects.get(id=parent_id, post=self.object)
                    comment.parent = parent_comment
                    comment.save()  # 更新父评论关联

                    # 通知被回复的用户
                    if parent_comment.user != request.user:
                        Notification.objects.create(
                            recipient=parent_comment.user,
                            actor=request.user,
                            verb="回复了你的评论",
                            target=comment,
                        )
                except Comment.DoesNotExist:
                    pass

            # 处理 @提及
            mentions = re.findall(r"@(\w+)", comment.content)
            for username in set(mentions):  # 去重
                try:
                    target_user = User.objects.get(username=username)
                    if target_user != request.user:  # 不通知自己
                        Notification.objects.create(
                            recipient=target_user,
                            actor=request.user,
                            verb="在评论中提到了你",
                            target=comment,
                        )
                except User.DoesNotExist:
                    pass

            messages.success(request, "您的评论已发布！")
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
        return Tag.objects.filter(is_active=True).annotate(count=Count('posts')).order_by('-count', 'name')


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
        query = self.request.GET.get("q")
        if query:
            try:
                from watson import search as watson

                return watson.filter(Post.objects.filter(status="published"), query)
            except ImportError:
                # 降级方案：如果未安装/配置 Watson
                return (
                    Post.objects.filter(
                        Q(title__icontains=query) | Q(content__icontains=query),
                        status="published",
                    )
                    .select_related("author", "category")
                    .prefetch_related("tags")
                )
        return Post.objects.none()

    def get_context_data(self, **kwargs):
        """添加查询关键词到上下文"""
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q")
        return context


class PostList(SidebarContextMixin, ListView):
    """
    文章列表视图
    展示所有已发布的文章，支持分页。
    """
    model = Post
    template_name = "blog/post_list.html"
    context_object_name = "posts"
    paginate_by = 9
    queryset = Post.objects.filter(status="published")


@login_required
@require_POST
def delete_comment(request, pk):
    """
    删除评论视图
    仅允许评论作者或管理员删除评论。
    """
    comment = get_object_or_404(Comment, pk=pk)
    if request.user == comment.user or request.user.is_staff:
        post_slug = comment.post.slug
        comment.delete()
        messages.success(request, "评论已删除")

        # Redirect back to where the request came from if possible
        referer = request.META.get("HTTP_REFERER")
        if referer and "profile" in referer:
            return redirect("users:profile")
        return redirect("post_detail", slug=post_slug)
    else:
        messages.error(request, "您没有权限删除此评论")
        return redirect("post_detail", slug=comment.post.slug)


@require_POST
def subscribe_view(request):
    """
    邮件订阅视图
    处理订阅表单提交，支持 HTMX 异步请求。
    """
    form = SubscriberForm(request.POST)
    if form.is_valid():
        form.save()
        if request.headers.get("HX-Request"):
            return render(request, "blog/partials/subscribe_success.html")
        messages.success(request, "订阅成功！")
        return redirect(request.META.get("HTTP_REFERER", "/"))

    if request.headers.get("HX-Request"):
        return render(
            request, "blog/partials/subscribe_form.html", {"subscribe_form": form}
        )

    messages.error(request, "订阅失败，请检查邮箱格式或是否已订阅。")
    return redirect(request.META.get("HTTP_REFERER", "/"))


def unsubscribe_view(request, token):
    """
    退订视图
    通过 UUID token 验证并取消订阅。
    """
    subscriber = get_object_or_404(Subscriber, token=token)
    subscriber.is_active = False
    subscriber.save()
    messages.success(request, "退订成功")
    return redirect("home")
