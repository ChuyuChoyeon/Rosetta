from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.views.generic import ListView, DetailView
from django.db.models import Q, Count
from django.db.models.functions import Coalesce
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
from constance import config


def _parse_keywords(value):
    if not value:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [item.strip() for item in str(value).split(",") if item.strip()]


def _build_meta(title, request, description=None, keywords=None, object_type="website"):
    return Meta(
        title=title,
        description=description or "",
        keywords=keywords or [],
        url=request.build_absolute_uri(),
        object_type=object_type,
    )


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
        context["sidebar_cache_ttl"] = ttl

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
        
        # Dynamic search placeholders
        context["search_placeholders"] = load_cached(
            "sidebar:search_placeholders",
            lambda: [f"搜索 {tag.name}..." for tag in Tag.objects.annotate(count=Count("posts")).order_by("-count")[:5]] or ["搜索文章...", "Python", "Django", "Tailwind"]
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
    def get_queryset(self):
        """
        获取文章列表
        - 仅显示已发布文章
        - 预加载关联数据以优化查询
        """
        return (
            Post.objects.filter(status="published")
            .select_related("author", "category")
            .prefetch_related("tags", "polls", "polls__choices")  # 预加载 Polls 及其 Choices
            .order_by("-is_pinned", "-published_at", "-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        site_name = getattr(config, "SITE_NAME", "Rosetta Blog")
        site_desc = getattr(config, "SITE_DESCRIPTION", "")
        site_keywords = _parse_keywords(getattr(config, "SITE_KEYWORDS", ""))
        context["meta"] = _build_meta(
            f"{site_name} - 首页", self.request, site_desc, site_keywords
        )
        
        # Add WebSite JSON-LD
        import json
        website_schema = {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": site_name,
            "url": self.request.build_absolute_uri("/"),
            "description": site_desc,
            "potentialAction": {
                "@type": "SearchAction",
                "target": self.request.build_absolute_uri("/") + "search/?q={search_term_string}",
                "query-input": "required name=search_term_string"
            }
        }
        context["website_schema"] = json.dumps(website_schema)
        
        return context


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
        .annotate(published_at_fallback=Coalesce("published_at", "created_at"))
        .order_by("-published_at_fallback")
    )
    paginate_by = 100  # 归档页显示更多文章，便于快速浏览

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        site_name = getattr(config, "SITE_NAME", "Rosetta Blog")
        site_desc = getattr(config, "SITE_DESCRIPTION", "")
        site_keywords = _parse_keywords(getattr(config, "SITE_KEYWORDS", ""))
        
        # Enhanced SEO for Archive
        post_count = self.object_list.count() if hasattr(self, 'object_list') else 0
        archive_desc = f"{site_name}文章归档。共收录 {post_count} 篇文章，记录了从建站至今的所有技术分享与生活感悟。"
        if site_desc:
            archive_desc = f"{archive_desc} {site_desc}"
            
        context["meta"] = _build_meta(
            f"{site_name} - 归档", self.request, archive_desc, site_keywords + ["文章归档", "历史文章", "全站索引"]
        )
        return context


class PostDetailView(DetailView):
    """
    文章详情视图

    展示文章完整内容、评论区，并处理密码保护、阅读计数和评论提交。
    """

    model = Post
    template_name = "blog/post_detail.html"
    context_object_name = "post"

    def get_queryset(self):
        """
        获取文章对象
        - 仅显示已发布文章
        - 作者和超级用户可见草稿
        """
        if (
            self.request.user.is_authenticated
            and self.request.user.is_staff
            or self.request.user.is_superuser
        ):
            return Post.objects.select_related("author", "category").prefetch_related(
                "tags", "polls", "polls__choices"
            )
        return Post.objects.filter(status="published").select_related(
            "author", "category"
        ).prefetch_related("tags", "polls", "polls__choices")

    def get_context_data(self, **kwargs):
        """添加评论、评论表单和 Meta 信息到上下文"""
        context = super().get_context_data(**kwargs)
        ttl = getattr(settings, "SIDEBAR_CACHE_TTL", 300)
        context["sidebar_cache_ttl"] = ttl

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
                .order_by("-same_tags", "-published_at", "-created_at")[:3]
            ),
        )

        # 如果相关文章不足 3 篇，补充同分类下的最新文章
        if len(related_posts) < 3 and self.object.category:
            remaining_count = 3 - len(related_posts)
            category_posts = list(
                Post.objects.filter(category=self.object.category, status="published")
                .exclude(id=self.object.id)
                .exclude(id__in=[p.id for p in related_posts])
                .order_by("-published_at", "-created_at")[:remaining_count]
            )

            related_posts = related_posts + category_posts

        context["related_posts"] = related_posts

        # 上一篇和下一篇 (Previous & Next Post)
        # 仅获取已发布的文章，且按时间排序
        context["previous_post"] = load_cached(
            f"post:{self.object.id}:previous",
            lambda: Post.objects.filter(
                status="published",
                published_at__lt=(self.object.published_at or self.object.created_at),
            )
            .order_by("-published_at", "-created_at")
            .first(),
        )

        context["next_post"] = load_cached(
            f"post:{self.object.id}:next",
            lambda: Post.objects.filter(
                status="published",
                published_at__gt=(self.object.published_at or self.object.created_at),
            )
            .order_by("published_at", "created_at")
            .first(),
        )

        return context

    def get_meta_data(self):
        """生成页面 Meta 数据用于 SEO"""
        post = self.object
        ttl = getattr(settings, "SIDEBAR_CACHE_TTL", 300)
        cache_key = f"post:{post.id}:meta_desc"
        description = cache.get(cache_key)

        # 处理描述：优先使用自定义描述，其次是缓存，否则生成
        if post.meta_description:
            description = post.meta_description
        elif not description:
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

        # 处理关键词：优先使用自定义关键词
        if post.meta_keywords:
            keywords = [k.strip() for k in post.meta_keywords.split(",") if k.strip()]
        else:
            keywords = list(post.tags.values_list("name", flat=True))

        published_time = post.published_at or post.created_at
        return Meta(
            title=post.meta_title or post.title,
            description=description,
            keywords=keywords,
            image=post.cover_image.url if post.cover_image else None,
            url=self.request.build_absolute_uri(),
            object_type="article",
            published_time=published_time,
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
                # 如果 session 中没有解锁标记，或者标记为 False，则显示密码输入页
                if not request.session.get(session_key, False):
                    # 注意：这里直接返回密码页面，不渲染 post_detail.html
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
            # 兼容明文密码和哈希密码
            # 如果密码字段是哈希值（以 pbkdf2_sha256 等开头），使用 check_password
            # 否则直接比较明文（为了兼容旧数据或简单设置）
            is_valid = False
            if self.object.password.startswith('pbkdf2_sha256$') or self.object.password.startswith('argon2'):
                 is_valid = self.object.check_password(password)
            else:
                 is_valid = self.object.password == password

            if is_valid:
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        site_name = getattr(config, "SITE_NAME", "Rosetta Blog")
        site_desc = getattr(config, "SITE_DESCRIPTION", "")
        site_keywords = _parse_keywords(getattr(config, "SITE_KEYWORDS", ""))
        context["meta"] = _build_meta(
            f"{site_name} - 分类", self.request, site_desc, site_keywords
        )
        return context


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        site_name = getattr(config, "SITE_NAME", "Rosetta Blog")
        site_desc = getattr(config, "SITE_DESCRIPTION", "")
        site_keywords = _parse_keywords(getattr(config, "SITE_KEYWORDS", ""))
        context["meta"] = _build_meta(
            f"{site_name} - 标签", self.request, site_desc, site_keywords
        )
        return context


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
            .order_by("-published_at", "-created_at")
        )

    def get_context_data(self, **kwargs):
        """添加当前分类信息到上下文"""
        context = super().get_context_data(**kwargs)
        context["title"] = f"分类: {self.category.name}"
        context["category"] = self.category
        site_name = getattr(config, "SITE_NAME", "Rosetta Blog")
        site_desc = getattr(config, "SITE_DESCRIPTION", "")
        site_keywords = _parse_keywords(getattr(config, "SITE_KEYWORDS", ""))
        keywords = site_keywords + [self.category.name]
        context["meta"] = _build_meta(
            f"{site_name} - 分类: {self.category.name}",
            self.request,
            site_desc,
            keywords,
        )
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
            .order_by("-published_at", "-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"标签: {self.tag.name}"
        context["tag"] = self.tag
        site_name = getattr(config, "SITE_NAME", "Rosetta Blog")
        site_desc = getattr(config, "SITE_DESCRIPTION", "")
        site_keywords = _parse_keywords(getattr(config, "SITE_KEYWORDS", ""))
        keywords = site_keywords + [self.tag.name]
        context["meta"] = _build_meta(
            f"{site_name} - 标签: {self.tag.name}",
            self.request,
            site_desc,
            keywords,
        )
        return context


from django.http import HttpResponse, JsonResponse

class SearchView(SidebarContextMixin, ListView):
    """
    全站搜索视图
    - 支持多模型搜索 (Post, Category, Tag, User, Poll)
    - 支持按类型筛选
    - 使用 django-watson 进行全文检索
    """

    template_name = "blog/search_results.html"
    context_object_name = "results"
    paginate_by = 12

    def get(self, request, *args, **kwargs):
        # Handle JSON suggestions
        if request.GET.get('type') == 'suggest':
            return self.get_suggestions(request)

        # Handle empty query -> Search Home
        if not request.GET.get('q'):
            self.template_name = "blog/search_index.html"
            # Manually trigger get_context_data with empty object_list
            self.object_list = []
            context = self.get_context_data()
            return render(request, self.template_name, context)

        return super().get(request, *args, **kwargs)

    def get_suggestions(self, request):
        query = request.GET.get('q', '').strip()
        if not query:
            return JsonResponse({'results': []})
        
        results = []
        seen = set()
        
        # Helper to add unique results
        def add_result(text, url, type_name):
            if text not in seen:
                seen.add(text)
                results.append({'text': text, 'url': url, 'type': type_name})

        # 1. Pinyin Search (if query is ASCII)
        if all(ord(c) < 128 for c in query):
            try:
                from xpinyin import Pinyin
                p = Pinyin()
                
                def match_pinyin(text, q):
                    if not text: return False
                    try:
                        # Convert to pinyin without separator: "测试" -> "ceshi"
                        py_full = p.get_pinyin(text, "")
                        # Convert to initials: "测试" -> "cs"
                        py_initials = p.get_initials(text, "")
                        
                        q_lower = q.lower()
                        return q_lower in py_full.lower() or q_lower in py_initials.lower()
                    except Exception:
                        return False

                # Search Tags
                for tag in Tag.objects.all():
                    if match_pinyin(tag.name, query):
                        add_result(tag.name, f"{request.path}?q={tag.name}&type=tag", "标签")
                        if len(results) >= 5: break
                
                # Search Posts
                for post in Post.objects.filter(status='published'):
                    if match_pinyin(post.title, query):
                        add_result(post.title, post.get_absolute_url(), "文章")
                        if len(results) >= 10: break
                        
            except ImportError:
                pass
        
        # 2. Standard DB Search
        if len(results) < 10:
            # Tags
            for tag in Tag.objects.filter(name__icontains=query)[:5]:
                add_result(tag.name, f"{request.path}?q={tag.name}&type=tag", "标签")
            
            # Posts
            for post in Post.objects.filter(title__icontains=query, status='published')[:5]:
                add_result(post.title, post.get_absolute_url(), "文章")

        return JsonResponse({'results': results[:10]})

    def get_queryset(self):
        from voting.models import Poll
        try:
            from watson import search as watson
        except ImportError:
            watson = None

        query = self.request.GET.get("q", "").strip()
        search_type = self.request.GET.get("type", "all")

        if not query:
            return []

        models = []
        if search_type == "all":
            models = [Post, Category, Tag, User, Poll]
        elif search_type == "post":
            models = [Post]
        elif search_type == "category":
            models = [Category]
        elif search_type == "tag":
            models = [Tag]
        elif search_type == "user":
            models = [User]
        elif search_type == "poll":
            models = [Poll]

        # Watson search
        if watson:
            try:
                return watson.filter(models, query)
            except Exception:
                pass
        
        # Fallback if watson is not set up or fails
        # Fallback search for specific models if watson fails
        fallback_results = []
        
        # 1. Standard DB Search (icontains)
        if search_type in ["all", "post"]:
            fallback_results.extend(Post.objects.filter(Q(title__icontains=query) | Q(content__icontains=query)))
        if search_type in ["all", "category"]:
            fallback_results.extend(Category.objects.filter(name__icontains=query))
        if search_type in ["all", "tag"]:
            fallback_results.extend(Tag.objects.filter(name__icontains=query))
        if search_type in ["all", "user"]:
            fallback_results.extend(User.objects.filter(Q(username__icontains=query) | Q(nickname__icontains=query)))
        if search_type in ["all", "poll"]:
            fallback_results.extend(Poll.objects.filter(Q(title__icontains=query) | Q(description__icontains=query)))
            
        # 2. Pinyin Search (if query is ASCII)
        # Supports matching "cs" -> "测试" (Initials) or "ceshi" -> "测试" (Full Pinyin)
        if query and all(ord(c) < 128 for c in query):
            try:
                from xpinyin import Pinyin
                p = Pinyin()
                
                def match_pinyin(text, q):
                    if not text: return False
                    try:
                        # Convert to pinyin without separator: "测试" -> "ceshi"
                        py_full = p.get_pinyin(text, "")
                        # Convert to initials: "测试" -> "cs"
                        py_initials = p.get_initials(text, "")
                        
                        q_lower = q.lower()
                        return q_lower in py_full.lower() or q_lower in py_initials.lower()
                    except Exception:
                        return False

                # Track existing IDs to avoid duplicates
                existing_ids = { (type(r), r.pk) for r in fallback_results }

                def check_and_add(queryset, field_names):
                    # Iterate over all objects - Note: This is O(N) and may be slow for large datasets
                    # For a blog with < 1000 posts, it's acceptable.
                    for obj in queryset:
                        if (type(obj), obj.pk) in existing_ids:
                            continue
                        
                        matched = False
                        for field in field_names:
                            val = getattr(obj, field, "")
                            if match_pinyin(val, query):
                                matched = True
                                break
                        
                        if matched:
                            fallback_results.append(obj)
                            existing_ids.add((type(obj), obj.pk))

                if search_type in ["all", "post"]:
                    check_and_add(Post.objects.all(), ['title'])
                if search_type in ["all", "category"]:
                    check_and_add(Category.objects.all(), ['name'])
                if search_type in ["all", "tag"]:
                    check_and_add(Tag.objects.all(), ['name'])
                if search_type in ["all", "user"]:
                    check_and_add(User.objects.all(), ['nickname', 'username'])
                if search_type in ["all", "poll"]:
                    check_and_add(Poll.objects.all(), ['title'])
                    
            except ImportError:
                pass
            except Exception as e:
                # Fail silently for pinyin search errors
                print(f"Pinyin search error: {e}")

        return fallback_results

    def get_context_data(self, **kwargs):
        from django.contrib.contenttypes.models import ContentType
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "")
        context["search_type"] = self.request.GET.get("type", "all")
        context["post_content_type_id"] = ContentType.objects.get_for_model(Post).id
        
        # Preserve SEO meta
        site_name = getattr(config, "SITE_NAME", "Rosetta Blog")
        site_desc = getattr(config, "SITE_DESCRIPTION", "")
        site_keywords = _parse_keywords(getattr(config, "SITE_KEYWORDS", ""))
        description = site_desc
        query = context["query"]
        if query:
            description = f"{site_desc} 搜索：{query}" if site_desc else f"搜索：{query}"
        context["meta"] = _build_meta(
            f"{site_name} - 搜索", self.request, description, site_keywords
        )
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
