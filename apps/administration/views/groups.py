from django.contrib.auth.models import Group
from django.urls import reverse_lazy
from django.db.models import QuerySet
from ..forms import GroupForm
from ..generics import (
    BaseListView,
    BaseCreateView,
    BaseUpdateView,
    BaseDeleteView,
    BaseExportView,
    BaseImportView,
)

class GroupListView(BaseListView):
    model = Group
    context_object_name = "groups"
    ordering = ["name"]

    def get_queryset(self) -> QuerySet:
        qs = super().get_queryset()
        query = self.request.GET.get("q")
        if query:
            qs = qs.filter(name__icontains=query)
        return qs

class GroupCreateView(BaseCreateView):
    model = Group
    form_class = GroupForm
    success_url = reverse_lazy("administration:group_list")

class GroupUpdateView(BaseUpdateView):
    model = Group
    form_class = GroupForm
    success_url = reverse_lazy("administration:group_list")

class GroupDeleteView(BaseDeleteView):
    model = Group
    success_url = reverse_lazy("administration:group_list")

class GroupExportView(BaseExportView):
    model = Group

class GroupImportView(BaseImportView):
    model = Group
    success_url = reverse_lazy("administration:group_list")
