import json
import re
from django.contrib import messages
from django.utils.translation import gettext as _
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, View
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from .forms import RegisterForm, UserPreferenceForm, UserProfileForm
from .models import User, UserPreference, Notification
from blog.models import PostViewHistory, Comment, Post
from constance import config


class RegisterView(CreateView):
    """
    用户注册视图

    处理新用户的注册流程。
    继承自 CreateView，使用自定义的 RegisterForm。

    流程:
    1. 展示包含验证码的注册表单。
    2. 验证用户提交的信息（用户名、密码、邮箱、验证码）。
    3. 创建新用户。
    4. 注册成功后重定向到登录页面，并显示成功消息。
    """

    model = User
    form_class = RegisterForm
    template_name = "users/register.html"
    success_url = reverse_lazy("users:login")

    def dispatch(self, request, *args, **kwargs):
        if not getattr(config, "ENABLE_REGISTRATION", True):
            messages.warning(request, _("本站目前暂停开放注册。"))
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, _("注册成功，请登录"))
        return super().form_valid(form)


class CustomLoginView(LoginView):
    """
    自定义登录视图

    继承自 Django 内置 LoginView。

    特性:
    - 使用自定义模板 users/login.html。
    - 若用户已登录，访问此页面会自动重定向到首页 (redirect_authenticated_user=True)。
    - 增加封禁用户检查。
    """

    template_name = "users/login.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        user = form.get_user()
        if user.is_banned:
            messages.error(self.request, _("您的账号已被封禁，禁止登录。"))
            return self.form_invalid(form)
        return super().form_valid(form)


class UpdateThemeView(LoginRequiredMixin, View):
    """
    更新主题视图 (AJAX)

    处理前端通过 Fetch API 发送的主题切换请求。

    请求方式: POST
    数据格式: JSON {"theme": "theme_name"}

    功能:
    1. 解析请求体中的 JSON 数据。
    2. 获取或创建当前用户的 UserPreference 对象。
    3. 更新 theme 字段并保存。
    4. 返回 JSON 响应表示成功或失败。
    """

    def post(self, request):
        try:
            data = json.loads(request.body or "{}")
            theme = data.get("theme")
            if theme:
                # Validate theme name to prevent XSS (alphanumeric and hyphens only)
                if not re.match(r"^[a-zA-Z0-9-]+$", theme):
                    return JsonResponse(
                        {"status": "error", "message": "Invalid theme name"}, status=400
                    )

                UserPreference.objects.update_or_create(
                    user=request.user, defaults={"theme": theme}
                )
                return JsonResponse({"status": "success"})
        except json.JSONDecodeError:
            return JsonResponse(
                {"status": "error", "message": "Invalid JSON"}, status=400
            )
        except Exception as e:
            return JsonResponse(
                {"status": "error", "message": str(e)},
                status=400,
            )
        return JsonResponse(
            {"status": "error", "message": "Invalid request"}, status=400
        )


class UnifiedProfileView(View):
    """
    统一用户个人资料视图

    这是一个功能丰富的复合视图，用于处理用户个人主页的所有交互。
    支持查看他人资料和管理自己的资料。

    功能模块:
    1. **资料展示**: 显示用户头像、封面、简介、统计数据等。
    2. **Tab 切换**:
       - `posts`: 展示用户发布的文章和评论（公开）。
       - `history`: 展示用户的浏览历史（仅限本人）。
       - `notifications`: 展示用户的通知消息（仅限本人）。
       - `settings`: 展示偏好设置表单（仅限本人）。
       - `info`: 展示基本资料编辑表单（仅限本人）。
    3. **数据更新**: 处理资料修改、密码修改、偏好设置保存等 POST 请求。
    4. **HTMX 支持**: 针对 HTMX 请求仅返回部分 HTML 片段，实现无刷新切换 Tab。
    """

    template_name = "users/public_profile.html"

    def get_object(self, username=None):
        """
        获取目标用户对象

        策略:
        - 如果 URL 中提供了 username，则查找对应用户（查看他人）。
        - 如果未提供 username 且当前用户已登录，则返回当前用户（查看自己）。
        - 否则返回 None。
        """
        from django.db.models import Sum
        if username:
            return get_object_or_404(
                User.objects.select_related("preference").annotate(
                    total_views_annotated=Sum("posts__views")
                ),
                username=username,
            )
        # 如果未提供 username 且用户已登录，则默认为当前用户
        if self.request.user.is_authenticated:
            # Re-fetch user to get annotation if needed, or rely on property
            # Ideally we should annotate current user too if we use total_views
            return User.objects.select_related("preference").annotate(
                total_views_annotated=Sum("posts__views")
            ).get(pk=self.request.user.pk)
        return None

    def get(self, request, username=None):
        profile_user = self.get_object(username)

        # 未找到用户或未登录访问 /profile/ 时重定向
        if not profile_user:
            return redirect("users:login")

        # --- 隐私检查 ---
        # 1. 如果是本人，允许
        # 2. 如果是管理员，允许
        # 3. 如果 public_profile 为 True，允许
        # 4. 否则，标记为私密模式
        is_me = request.user.is_authenticated and request.user == profile_user
        is_staff = request.user.is_authenticated and request.user.is_staff

        preference, _ = UserPreference.objects.get_or_create(user=profile_user)
        profile_user.preference = preference
        is_public = preference.public_profile
        is_private_profile = False

        if not (is_me or is_staff or is_public):
            is_private_profile = True

        active_tab = request.GET.get("tab", "articles")
        context = {
            "profile_user": profile_user,
            "active_tab": active_tab,
            "is_private_profile": is_private_profile,
        }

        # --- 公共数据 (所有人都可见，除非私密) ---
        # 侧边栏评论总数
        context["comments_count"] = Comment.objects.filter(
            user=profile_user, active=True
        ).count()

        if is_private_profile:
            # 私密模式下，不加载具体内容
            pass
        else:
            # Tab Data Loading
            if active_tab == "articles":
                context["posts"] = (
                    Post.objects.filter(
                        author=profile_user,
                        status="published",
                    )
                    .select_related("category")
                    .prefetch_related("tags")
                    .order_by("-published_at", "-created_at")[:20]
                )
            elif active_tab == "comments":
                context["comments"] = (
                    Comment.objects.filter(user=profile_user, active=True)
                    .select_related("post")
                    .order_by("-created_at")[:20]
                )

        # --- 私有数据 (仅限本人查看) ---
        if is_me:
            # 个人资料编辑表单
            context["form"] = UserProfileForm(instance=profile_user)

            if active_tab == "history":
                context["view_history"] = PostViewHistory.objects.filter(
                    user=request.user
                ).select_related("post")[:20]

            elif active_tab == "notifications":
                context["notifications"] = (
                    request.user.user_notifications.select_related("actor")
                    .prefetch_related("target")
                    .all()[:50]
                )

            elif active_tab == "settings":
                context["preference_form"] = UserPreferenceForm(
                    instance=preference
                )
            
            elif active_tab == "security":
                context["password_form"] = PasswordChangeForm(user=request.user)

        # HTMX 请求支持 (局部刷新内容区域)
        if request.headers.get("HX-Request"):
            return render(
                request,
                "users/includes/profile_content.html",
                context,
            )

        return render(request, self.template_name, context)

    def post(self, request, username=None):
        if not request.user.is_authenticated:
            return redirect("users:login")

        profile_user = self.get_object(username)

        # 权限检查：只能编辑自己的资料
        if profile_user != request.user:
            messages.error(request, _("您只能编辑自己的资料"))
            return redirect(
                "users:user_public_profile",
                username=profile_user.username,
            )

        profile_url = reverse_lazy(
            "users:user_public_profile",
            kwargs={"username": request.user.username},
        )

        # --- 处理偏好设置更新 ---
        if "save_preferences" in request.POST:
            preference_form = UserPreferenceForm(
                request.POST, instance=request.user.preference
            )
            if preference_form.is_valid():
                preference_form.save()
                messages.success(request, _("偏好设置已更新"))
            else:
                messages.error(request, _("偏好设置更新失败"))
            return redirect(f"{profile_url}?tab=settings")
        
        # --- 处理密码修改 ---
        if "change_password" in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # Important!
                messages.success(request, _("密码修改成功"))
                return redirect(f"{profile_url}?tab=security")
            else:
                messages.error(request, _("密码修改失败，请检查输入"))
                # 重新渲染页面以显示表单错误
                # 我们需要重新构建上下文，这有点麻烦，但为了显示错误是必须的
                # 或者我们可以简单地重定向并带上错误（但这不会显示具体的字段错误）
                # 为了更好的体验，我们这里手动调用 get 方法的部分逻辑来重新渲染
                
                # 构建基本上下文
                profile_user = request.user
                preference, _ = UserPreference.objects.get_or_create(user=profile_user)
                profile_user.preference = preference
                
                context = {
                    "profile_user": profile_user,
                    "active_tab": "security",
                    "is_private_profile": False,
                    "comments_count": Comment.objects.filter(user=profile_user, active=True).count(),
                    "password_form": password_form, # 包含错误的表单
                }
                return render(request, self.template_name, context)

        # --- 处理个人资料更新 (头像、封面、基本信息) ---
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _("个人信息更新成功"))
        else:
            messages.error(request, _("个人信息更新失败，请检查输入"))

        # 保持在当前页面或重定向
        next_url = request.GET.get("next")
        if next_url:
            return redirect(next_url)

        return redirect(f"{profile_url}?tab=info")


class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    """
    自定义密码修改视图

    继承自 PasswordChangeView。
    修改成功后重定向到个人资料页。
    """

    template_name = "users/password_change.html"
    success_url = reverse_lazy("users:profile")

    def form_valid(self, form):
        messages.success(self.request, _("密码修改成功"))
        return super().form_valid(form)


class MarkNotificationReadView(LoginRequiredMixin, View):
    """
    标记通知为已读

    支持 POST 和 GET 请求（为了方便某些场景下的直接链接访问，但建议使用 POST）。
    HTMX 支持：如果请求来自 HTMX，则返回空响应以支持前端移除元素或更新状态。
    """

    def action(self, request, pk):
        notification = get_object_or_404(
            Notification,
            pk=pk,
            recipient=request.user,
        )
        notification.is_read = True
        notification.save()

        # 如果是 HTMX 请求，返回空响应或更新后的 HTML
        if request.headers.get("HX-Request"):
            return HttpResponse("")

        next_url = request.GET.get("next")
        if next_url:
            return redirect(next_url)
        return redirect("users:profile")

    def get(self, request, pk):
        return self.action(request, pk)

    def post(self, request, pk):
        return self.action(request, pk)


class DeleteNotificationView(LoginRequiredMixin, View):
    """
    删除通知

    物理删除 Notification 对象。
    支持 DELETE (RESTful) 和 POST (表单) 请求。
    """

    def action(self, request, pk):
        notification = get_object_or_404(
            Notification,
            pk=pk,
            recipient=request.user,
        )
        notification.delete()

        # 如果是 HTMX 请求，返回空响应让前端移除元素
        if request.headers.get("HX-Request"):
            return HttpResponse("")

        messages.success(request, _("通知已删除"))
        return redirect("users:profile")

    def post(self, request, pk):
        return self.action(request, pk)

    def delete(self, request, pk):
        return self.action(request, pk)
