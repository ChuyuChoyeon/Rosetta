from django.urls import reverse_lazy
from django.views import View
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from core.models import Page, Navigation, FriendLink, SearchPlaceholder
from ..forms import PageForm, NavigationForm, FriendLinkForm, SearchPlaceholderForm
from ..mixins import StaffRequiredMixin
from ..generics import (
    BaseListView,
    BaseCreateView,
    BaseUpdateView,
    BaseDeleteView,
    BaseExportView,
    BaseImportView,
)
import uuid

# --- Page Views ---
class PageListView(BaseListView):
    model = Page
    context_object_name = "pages"
    ordering = ["-created_at"]

class PageCreateView(BaseCreateView):
    model = Page
    form_class = PageForm
    success_url = reverse_lazy("administration:page_list")

class PageUpdateView(BaseUpdateView):
    model = Page
    form_class = PageForm
    success_url = reverse_lazy("administration:page_list")

class PageDeleteView(BaseDeleteView):
    model = Page
    success_url = reverse_lazy("administration:page_list")

class PageDuplicateView(LoginRequiredMixin, StaffRequiredMixin, View):
    def post(self, request, pk):
        try:
            page = get_object_or_404(Page, pk=pk)
            page.pk = None
            page.slug = f"{page.slug}-{uuid.uuid4().hex[:6]}"
            page.title = f"{page.title} (副本)"
            page.status = "draft"
            page.save()
            messages.success(request, "页面已复制为草稿")
        except Exception as e:
            messages.error(request, f"复制失败: {str(e)}")
        return redirect("administration:page_list")

# --- Navigation Views ---
class NavigationListView(BaseListView):
    model = Navigation
    context_object_name = "navigations"
    ordering = ["location", "order"]

class NavigationCreateView(BaseCreateView):
    model = Navigation
    form_class = NavigationForm
    success_url = reverse_lazy("administration:navigation_list")

class NavigationUpdateView(BaseUpdateView):
    model = Navigation
    form_class = NavigationForm
    success_url = reverse_lazy("administration:navigation_list")

class NavigationDeleteView(BaseDeleteView):
    model = Navigation
    success_url = reverse_lazy("administration:navigation_list")

class NavigationExportView(BaseExportView):
    model = Navigation

class NavigationImportView(BaseImportView):
    model = Navigation
    success_url = reverse_lazy("administration:navigation_list")

# --- FriendLink Views ---
class FriendLinkListView(BaseListView):
    model = FriendLink
    context_object_name = "friendlinks"
    ordering = ["order"]

class FriendLinkCreateView(BaseCreateView):
    model = FriendLink
    form_class = FriendLinkForm
    success_url = reverse_lazy("administration:friendlink_list")

class FriendLinkUpdateView(BaseUpdateView):
    model = FriendLink
    form_class = FriendLinkForm
    success_url = reverse_lazy("administration:friendlink_list")

class FriendLinkDeleteView(BaseDeleteView):
    model = FriendLink
    success_url = reverse_lazy("administration:friendlink_list")

class FriendLinkExportView(BaseExportView):
    model = FriendLink

class FriendLinkImportView(BaseImportView):
    model = FriendLink
    success_url = reverse_lazy("administration:friendlink_list")

# --- SearchPlaceholder Views ---
class SearchPlaceholderListView(BaseListView):
    model = SearchPlaceholder
    context_object_name = "placeholders"
    ordering = ["order"]

class SearchPlaceholderCreateView(BaseCreateView):
    model = SearchPlaceholder
    form_class = SearchPlaceholderForm
    success_url = reverse_lazy("administration:searchplaceholder_list")

class SearchPlaceholderUpdateView(BaseUpdateView):
    model = SearchPlaceholder
    form_class = SearchPlaceholderForm
    success_url = reverse_lazy("administration:searchplaceholder_list")

class SearchPlaceholderDeleteView(BaseDeleteView):
    model = SearchPlaceholder
    success_url = reverse_lazy("administration:searchplaceholder_list")

class SearchPlaceholderExportView(BaseExportView):
    model = SearchPlaceholder

class SearchPlaceholderImportView(BaseImportView):
    model = SearchPlaceholder
    success_url = reverse_lazy("administration:searchplaceholder_list")
