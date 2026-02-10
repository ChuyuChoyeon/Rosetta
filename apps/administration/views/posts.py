from django.db.models import QuerySet
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
import uuid

from blog.models import Post
from ..forms import PostForm
from ..mixins import StaffRequiredMixin
from ..generics import (
    BaseListView,
    BaseCreateView,
    BaseUpdateView,
    BaseDeleteView,
)


class PostListView(BaseListView):
    """
    文章列表管理视图。

    支持按标题搜索和按状态筛选（草稿/已发布）。
    """
    model = Post
    context_object_name = "posts"
    ordering = ["-is_pinned", "-published_at", "-created_at"]
    paginate_by = 20

    def get_queryset(self) -> QuerySet[Post]:
        qs = super().get_queryset()
        # 预加载关联数据以减少数据库查询
        qs = qs.select_related("author", "category").prefetch_related("tags")

        query = self.request.GET.get("q")
        status = self.request.GET.get("status")

        if query:
            qs = qs.filter(title__icontains=query)

        if status:
            qs = qs.filter(status=status)

        return qs

    def get_context_data(self, **kwargs):
        """添加文章统计数据到上下文"""
        context = super().get_context_data(**kwargs)
        context["total_count"] = Post.objects.count()
        context["published_count"] = Post.objects.filter(status="published").count()
        context["draft_count"] = Post.objects.filter(status="draft").count()
        return context


class PostCreateView(BaseCreateView):
    """
    创建新文章视图。

    自动将当前登录用户设置为文章作者。
    """
    model = Post
    form_class = PostForm
    success_url = reverse_lazy("administration:post_list")

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(BaseUpdateView):
    """编辑文章视图。"""
    model = Post
    form_class = PostForm
    success_url = reverse_lazy("administration:post_list")


class PostDeleteView(BaseDeleteView):
    """删除文章视图。"""
    model = Post
    success_url = reverse_lazy("administration:post_list")


class PostDuplicateView(LoginRequiredMixin, StaffRequiredMixin, View):
    """
    文章复制视图（快速克隆）。

    将现有文章复制为草稿，自动处理 Slug 冲突（追加 UUID），
    并保留原有的标签关联，重置浏览量。
    """
    def post(self, request, pk):
        try:
            post = get_object_or_404(Post, pk=pk)
            # 由于 M2M 关系需要在对象保存后处理，先缓存标签
            tags = list(post.tags.all())

            post.pk = None  # 设置 pk 为 None 以触发创建新记录
            post.slug = f"{post.slug}-{uuid.uuid4().hex[:6]}"
            post.title = f"{post.title} (副本)"
            post.status = "draft"
            post.views = 0
            post.save()

            post.tags.set(tags)
            messages.success(request, "文章已复制为草稿")
        except Exception as e:
            messages.error(request, f"复制失败: {str(e)}")

        return redirect("administration:post_list")
