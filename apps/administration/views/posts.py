from typing import List
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
        context["total_count"] = Post.objects.count()
        context["published_count"] = Post.objects.filter(status="published").count()
        context["draft_count"] = Post.objects.filter(status="draft").count()
        return context


class PostCreateView(BaseCreateView):
    model = Post
    form_class = PostForm
    success_url = reverse_lazy("administration:post_list")

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(BaseUpdateView):
    model = Post
    form_class = PostForm
    success_url = reverse_lazy("administration:post_list")


class PostDeleteView(BaseDeleteView):
    model = Post
    success_url = reverse_lazy("administration:post_list")


class PostDuplicateView(LoginRequiredMixin, StaffRequiredMixin, View):
    def post(self, request, pk):
        try:
            post = get_object_or_404(Post, pk=pk)
            tags = list(post.tags.all())

            post.pk = None
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
