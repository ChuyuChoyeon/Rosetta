import json
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, UpdateView, View, DetailView
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from .forms import RegisterForm, UserPreferenceForm, UserProfileForm
from .models import User, UserPreference, Notification
from blog.models import PostViewHistory, Comment


class RegisterView(CreateView):
    """
    用户注册视图
    
    功能:
    1. 处理新用户注册请求
    2. 验证注册表单
    3. 注册成功后重定向至登录页
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
    
    功能:
    1. 使用自定义登录模板
    2. 若用户已登录，自动重定向至首页或 Next URL
    """
    template_name = "users/login.html"
    redirect_authenticated_user = True


class UpdateThemeView(LoginRequiredMixin, View):
    """
    更新主题视图 (AJAX)
    
    功能:
    1. 接收前端发送的主题切换请求
    2. 更新用户偏好设置中的主题字段
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
    
    功能:
    1. 展示用户公开资料（文章、评论等）
    2. 展示用户私有资料（浏览历史、通知、设置），仅限本人查看
    3. 处理个人资料更新和偏好设置保存
    4. 支持 Tab 切换查看不同内容
    """
    template_name = "users/public_profile.html"

    def get_object(self, username=None):
        """获取目标用户对象"""
        if username:
            return get_object_or_404(User, username=username)
        # 如果未提供 username 且用户已登录，则默认为当前用户
        if self.request.user.is_authenticated:
            return self.request.user
        return None

    def get(self, request, username=None):
        profile_user = self.get_object(username)

        # 未找到用户或未登录访问 /profile/ 时重定向
        if not profile_user:
            return redirect("users:login")

        active_tab = request.GET.get("tab", "posts")
        context = {
            "profile_user": profile_user,
            "active_tab": active_tab,
        }

        # --- 公共数据 ---
        # 侧边栏评论总数
        context["comments_count"] = Comment.objects.filter(
            user=profile_user, active=True
        ).count()

        # 文章/评论列表 (默认 Tab)
        if active_tab == "posts":
            context["comments"] = (
                Comment.objects.filter(user=profile_user, active=True)
                .select_related("post")
                .order_by("-created_at")[:20]
            )

        # --- 私有数据 (仅限本人) ---
        if request.user.is_authenticated and request.user == profile_user:
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
                # 确保 UserPreference 存在
                if not hasattr(request.user, "preference"):
                    UserPreference.objects.create(user=request.user)
                    request.user.refresh_from_db()
                
                context["preference_form"] = UserPreferenceForm(
                    instance=request.user.preference
                )

        # HTMX 请求支持 (局部刷新)
        if request.headers.get("HX-Request"):
            return render(request, "users/includes/profile_content.html", context)

        return render(request, self.template_name, context)

    def post(self, request, username=None):
        if not request.user.is_authenticated:
            return redirect("users:login")

        profile_user = self.get_object(username)

        # 权限检查：只能编辑自己的资料
        if profile_user != request.user:
            messages.error(request, "您只能编辑自己的资料")
            return redirect("users:user_public_profile", username=profile_user.username)

        # --- 处理偏好设置更新 ---
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

        # --- 处理个人资料更新 (头像、封面、基本信息) ---
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "个人信息更新成功")
        else:
            messages.error(request, "个人信息更新失败，请检查输入")

        # 保持在当前页面或重定向
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
    """
    标记通知为已读
    支持 POST 和 GET 请求
    """
    def action(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
        notification.is_read = True
        notification.save()

        # 如果是 HTMX 请求，返回空响应或更新后的 HTML
        if request.headers.get("HX-Request"):
            return HttpResponse("") # 简单移除按钮或更新状态

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
    支持 DELETE 和 POST 请求
    """
    def action(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
        notification.delete()
        
        # 如果是 HTMX 请求，返回空响应让前端移除元素
        if request.headers.get("HX-Request"):
            return HttpResponse("")

        messages.success(request, "通知已删除")
        return redirect("users:profile")

    def post(self, request, pk):
        return self.action(request, pk)

    def delete(self, request, pk):
        return self.action(request, pk)
