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
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(next_page="users:login"), name="logout"),
    path("profile/", UnifiedProfileView.as_view(), name="profile"),
    path(
        "profile/<str:username>/",
        UnifiedProfileView.as_view(),
        name="user_public_profile",
    ),
    path("update-theme/", UpdateThemeView.as_view(), name="update_theme"),
    path(
        "notification/<int:pk>/read/",
        MarkNotificationReadView.as_view(),
        name="mark_notification_read",
    ),
    path(
        "notification/<int:pk>/delete/",
        DeleteNotificationView.as_view(),
        name="delete_notification",
    ),
    path(
        "password-change/", CustomPasswordChangeView.as_view(), name="password_change"
    ),
    # JWT Auth
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
