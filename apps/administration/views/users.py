from django.urls import reverse_lazy
from django.db.models import QuerySet, Q
from django.contrib.auth import get_user_model
from users.models import UserTitle
from ..forms import UserForm, GroupForm, UserTitleForm
from ..generics import (
    BaseListView,
    BaseCreateView,
    BaseUpdateView,
    BaseDeleteView,
    BaseExportView,
    BaseImportView,
)

User = get_user_model()

# --- User Views ---
class UserListView(BaseListView):
    model = User
    context_object_name = "users"
    ordering = ["-date_joined"]

    def get_queryset(self) -> QuerySet:
        qs = super().get_queryset()
        query = self.request.GET.get("q")
        role = self.request.GET.get("role")

        if query:
            qs = qs.filter(
                Q(username__icontains=query) | 
                Q(email__icontains=query) |
                Q(nickname__icontains=query)
            )
        
        if role == "staff":
            qs = qs.filter(is_staff=True)
        elif role == "superuser":
            qs = qs.filter(is_superuser=True)
        
        return qs

class UserCreateView(BaseCreateView):
    model = User
    form_class = UserForm
    success_url = reverse_lazy("administration:user_list")

class UserUpdateView(BaseUpdateView):
    model = User
    form_class = UserForm
    success_url = reverse_lazy("administration:user_list")

class UserDeleteView(BaseDeleteView):
    model = User
    success_url = reverse_lazy("administration:user_list")

class UserExportView(BaseExportView):
    model = User

class UserImportView(BaseImportView):
    model = User
    success_url = reverse_lazy("administration:user_list")

# --- UserTitle Views ---
class UserTitleListView(BaseListView):
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
