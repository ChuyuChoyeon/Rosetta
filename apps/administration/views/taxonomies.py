from django.db.models import QuerySet, Count
from django.urls import reverse_lazy
from django.views import View
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin

from blog.models import Category, Tag
from ..forms import CategoryForm, TagForm
from ..mixins import StaffRequiredMixin
from ..generics import (
    BaseListView,
    BaseCreateView,
    BaseUpdateView,
    BaseDeleteView,
    BaseExportView,
    BaseImportView,
)


# --- Category Views ---
class CategoryListView(BaseListView):
    model = Category
    context_object_name = "categories"
    ordering = ["name"]

    def get_queryset(self) -> QuerySet[Category]:
        qs = super().get_queryset().annotate(post_count=Count("posts"))
        query = self.request.GET.get("q")
        if query:
            qs = qs.filter(name__icontains=query)
        return qs


class CategoryCreateView(BaseCreateView):
    model = Category
    form_class = CategoryForm
    success_url = reverse_lazy("administration:category_list")


class CategoryQuickCreateView(View):
    def post(self, request, *args, **kwargs):
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            category = form.save()
            return JsonResponse(
                {
                    "status": "success",
                    "id": category.id,
                    "name": category.name,
                    "icon": category.icon,
                    "color": category.color,
                }
            )
        else:
            return JsonResponse({"status": "error", "errors": form.errors}, status=400)


class CategoryUpdateView(BaseUpdateView):
    model = Category
    form_class = CategoryForm
    success_url = reverse_lazy("administration:category_list")


class CategoryDeleteView(BaseDeleteView):
    model = Category
    success_url = reverse_lazy("administration:category_list")


class CategoryExportView(BaseExportView):
    model = Category


class CategoryImportView(BaseImportView):
    model = Category
    success_url = reverse_lazy("administration:category_list")


# --- Tag Views ---
class TagListView(BaseListView):
    model = Tag
    context_object_name = "tags"
    ordering = ["name"]

    def get_queryset(self) -> QuerySet[Tag]:
        qs = super().get_queryset().annotate(post_count=Count("posts"))
        query = self.request.GET.get("q")
        status = self.request.GET.get("status")

        if query:
            qs = qs.filter(name__icontains=query)

        if status == "active":
            qs = qs.filter(is_active=True)
        elif status == "inactive":
            qs = qs.filter(is_active=False)

        return qs


class TagCreateView(BaseCreateView):
    model = Tag
    form_class = TagForm
    success_url = reverse_lazy("administration:tag_list")


class TagUpdateView(BaseUpdateView):
    model = Tag
    form_class = TagForm
    success_url = reverse_lazy("administration:tag_list")


class TagDeleteView(BaseDeleteView):
    model = Tag
    success_url = reverse_lazy("administration:tag_list")


class TagExportView(BaseExportView):
    model = Tag


class TagImportView(BaseImportView):
    model = Tag
    success_url = reverse_lazy("administration:tag_list")


class TagAutocompleteView(LoginRequiredMixin, StaffRequiredMixin, View):
    def get(self, request):
        query = request.GET.get("q", "")
        if len(query) < 1:
            return JsonResponse({"results": []})

        tags = Tag.objects.filter(name__icontains=query).values_list("name", flat=True)[
            :10
        ]
        return JsonResponse({"results": list(tags)})
