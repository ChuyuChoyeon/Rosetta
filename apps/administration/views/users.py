from django.urls import reverse_lazy
from django.db.models import QuerySet, Q
from django.contrib.auth import get_user_model
from users.models import UserTitle
from ..forms import UserForm, UserTitleForm
from ..generics import (
    BaseListView,
    BaseCreateView,
    BaseUpdateView,
    BaseDeleteView,
    BaseExportView,
    BaseImportView,
)

User = get_user_model()


# --- 用户管理视图 ---
class UserListView(BaseListView):
    """
    用户列表视图。

    支持搜索（用户名、邮箱、昵称）和角色筛选（管理员、超级用户）。
    """
    model = User
    context_object_name = "users"
    ordering = ["-date_joined"]

    def get_queryset(self) -> QuerySet:
        qs = super().get_queryset()
        query = self.request.GET.get("q")
        role = self.request.GET.get("role")

        if query:
            qs = qs.filter(
                Q(username__icontains=query)
                | Q(email__icontains=query)
                | Q(nickname__icontains=query)
            )

        if role == "staff":
            qs = qs.filter(is_staff=True)
        elif role == "superuser":
            qs = qs.filter(is_superuser=True)

        return qs


class UserCreateView(BaseCreateView):
    """创建新用户视图。"""
    model = User
    form_class = UserForm
    success_url = reverse_lazy("administration:user_list")


class UserUpdateView(BaseUpdateView):
    """更新用户信息视图。"""
    model = User
    form_class = UserForm
    success_url = reverse_lazy("administration:user_list")


class UserDeleteView(BaseDeleteView):
    """删除用户视图。"""
    model = User
    success_url = reverse_lazy("administration:user_list")


class UserExportView(BaseExportView):
    """导出用户数据视图 (CSV/Excel)。"""
    model = User


class UserImportView(BaseImportView):
    """导入用户数据视图。"""
    model = User
    success_url = reverse_lazy("administration:user_list")


# --- 用户头衔管理视图 ---
class UserTitleListView(BaseListView):
    """用户头衔列表视图。"""
    model = UserTitle
    context_object_name = "titles"
    ordering = ["name"]


class UserTitleCreateView(BaseCreateView):
    model = UserTitle
    form_class = UserTitleForm
    success_url = reverse_lazy("administration:usertitle_list")


class UserTitleUpdateView(BaseUpdateView):
    model = UserTitle
    form_class = UserTitleForm
    success_url = reverse_lazy("administration:usertitle_list")


class UserTitleDeleteView(BaseDeleteView):
    model = UserTitle
    success_url = reverse_lazy("administration:usertitle_list")


class UserTitleExportView(BaseExportView):
    model = UserTitle


class UserTitleImportView(BaseImportView):
    model = UserTitle
    success_url = reverse_lazy("administration:usertitle_list")
