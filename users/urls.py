from django.urls import path
from django.contrib.auth.views import LogoutView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import (
    RegisterView,
    CustomLoginView,
    UnifiedProfileView,
    CustomPasswordChangeView,
    MarkNotificationReadView,
    DeleteNotificationView,
    UpdateThemeView,
)

app_name = "users"

urlpatterns = [
    # --- 认证相关 ---
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path(
        "logout/",
        LogoutView.as_view(next_page="users:login"),
        name="logout",
    ),

    # --- 个人资料相关 ---
    # 当前登录用户的个人资料页 (重定向到带 username 的 URL 或显示当前用户)
    path("profile/", UnifiedProfileView.as_view(), name="profile"),
    # 指定用户的公开个人资料页
    path(
        "profile/<str:username>/",
        UnifiedProfileView.as_view(),
        name="user_public_profile",
    ),

    # --- 功能性接口 (AJAX/HTMX) ---
    # 更新主题偏好 (AJAX)
    path("update-theme/", UpdateThemeView.as_view(), name="update_theme"),
    # 标记通知为已读
    path(
        "notification/<int:pk>/read/",
        MarkNotificationReadView.as_view(),
        name="mark_notification_read",
    ),
    # 删除通知
    path(
        "notification/<int:pk>/delete/",
        DeleteNotificationView.as_view(),
        name="delete_notification",
    ),

    # --- 账户安全 ---
    # 修改密码
    path(
        "password-change/",
        CustomPasswordChangeView.as_view(),
        name="password_change",
    ),

    # --- API 接口 (JWT) ---
    path(
        "api/token/",
        TokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path(
        "api/token/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),
]
