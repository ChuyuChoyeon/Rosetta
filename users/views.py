import json
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, UpdateView, View, DetailView
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from .forms import RegisterForm, UserPreferenceForm, UserProfileForm
from .models import User, UserPreference, Notification
from blog.models import PostViewHistory, Comment


class RegisterView(CreateView):
    """
    用户注册视图
    处理新用户注册逻辑，成功后重定向到登录页面。
    """
    model = User
    form_class = RegisterForm
    template_name = "users/register.html"
    success_url = reverse_lazy("users:login")

    def form_valid(self, form):
        messages.success(self.request, "注册成功，请登录")
        return super().form_valid(form)


class CustomLoginView(LoginView):
    """
    自定义登录视图
    使用自定义模板，并支持已登录用户自动重定向。
    """
    template_name = "users/login.html"
    redirect_authenticated_user = True


class UpdateThemeView(LoginRequiredMixin, View):
    """
    更新主题视图
    处理用户切换主题的 AJAX 请求。
    """
    def post(self, request):
        try:
            data = json.loads(request.body)
            theme = data.get("theme")
            if theme:
                preference, created = UserPreference.objects.get_or_create(
                    user=request.user
                )
                preference.theme = theme
                preference.save()
                return JsonResponse({"status": "success"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
        return JsonResponse(
            {"status": "error", "message": "Invalid request"}, status=400
        )


class UnifiedProfileView(View):
    """
    统一用户个人资料视图
    整合了公开资料展示和个人设置编辑功能。
    支持通过 tab 参数切换不同内容（文章、历史、通知、设置）。
    """
    template_name = "users/public_profile.html"

    def get_object(self, username=None):
        if username:
            return get_object_or_404(User, username=username)
        if self.request.user.is_authenticated:
            return self.request.user
        return None

    def get(self, request, username=None):
        profile_user = self.get_object(username)

        # 如果未找到用户（例如未登录且访问 /profile/），重定向到登录页
        if not profile_user:
            return redirect("users:login")

        active_tab = request.GET.get("tab", "posts")
        context = {
            "profile_user": profile_user,
            "active_tab": active_tab,
        }

        # 计算侧边栏评论数（所有标签页可见）
        context["comments_count"] = Comment.objects.filter(
            user=profile_user, active=True
        ).count()

        # 公开数据（评论） - 仅在 posts 标签页加载
        if active_tab == "posts":
            context["comments"] = (
                Comment.objects.filter(user=profile_user, active=True)
                .select_related("post")
                .order_by("-created_at")[:20]
            )

        # 私有数据（仅查看自己时）
        if request.user.is_authenticated and request.user == profile_user:
            # 编辑表单（模态框始终需要）
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
                # 偏好设置表单
                if not hasattr(request.user, "preference"):
                    UserPreference.objects.create(user=request.user)
                    request.user.refresh_from_db()
                context["preference_form"] = UserPreferenceForm(
                    instance=request.user.preference
                )

        # 检查是否为 HTMX 请求
        if request.headers.get("HX-Request"):
            return render(request, "users/includes/profile_content.html", context)

        return render(request, self.template_name, context)

    def post(self, request, username=None):
        if not request.user.is_authenticated:
            return redirect("users:login")

        profile_user = self.get_object(username)

        # 安全检查：只能编辑自己的资料
        if profile_user != request.user:
            messages.error(request, "您只能编辑自己的资料")
            return redirect("users:user_public_profile", username=profile_user.username)

        # 处理偏好设置保存
        if "save_preferences" in request.POST:
            preference_form = UserPreferenceForm(
                request.POST, instance=request.user.preference
            )
            if preference_form.is_valid():
                preference_form.save()
                messages.success(request, "偏好设置已更新")
            else:
                messages.error(request, "偏好设置更新失败")
            return redirect(
                f"{reverse_lazy('users:user_public_profile', kwargs={'username': request.user.username})}?tab=settings"
            )

        # 处理个人资料更新
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "个人信息更新成功")
        else:
            messages.error(request, "个人信息更新失败")

        next_url = request.GET.get("next")
        if next_url:
            return redirect(next_url)

        return redirect(
            f"{reverse_lazy('users:user_public_profile', kwargs={'username': request.user.username})}?tab=info"
        )


class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    """
    自定义密码修改视图
    """
    template_name = "users/password_change.html"
    success_url = reverse_lazy("users:profile")

    def form_valid(self, form):
        messages.success(self.request, "密码修改成功")
        return super().form_valid(form)


class MarkNotificationReadView(LoginRequiredMixin, View):
    def get(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
        notification.is_read = True
        notification.save()

        next_url = request.GET.get("next")
        if next_url:
            return redirect(next_url)
        return redirect("users:profile")


class DeleteNotificationView(LoginRequiredMixin, View):
    """
    删除通知视图
    """
    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
        notification.delete()
        messages.success(request, "通知已删除")
        return redirect("users:profile")
