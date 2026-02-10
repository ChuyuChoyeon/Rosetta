from django.urls import reverse_lazy
from django.views import View
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from core.models import Page, Navigation, FriendLink, SearchPlaceholder, Media
from ..forms import (
    PageForm,
    NavigationForm,
    FriendLinkForm,
    SearchPlaceholderForm,
    MediaForm,
)
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
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


# --- Media Views ---
class MediaListView(BaseListView):
    model = Media
    context_object_name = "media_list"
    ordering = ["-created_at"]
    paginate_by = 24  # Grid view needs more items

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add filter params for pagination
        context["type"] = self.request.GET.get("type", "")
        context["q"] = self.request.GET.get("q", "")
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        media_type = self.request.GET.get("type")
        q = self.request.GET.get("q")

        if media_type:
            queryset = queryset.filter(file_type=media_type)
        if q:
            queryset = queryset.filter(filename__icontains=q)

        return queryset

    def render_to_response(self, context, **response_kwargs):
        # Support JSON response for editor modal
        if (
            self.request.headers.get("x-requested-with") == "XMLHttpRequest"
            and self.request.GET.get("format") == "json"
        ):
            media_list = []
            for media in context["media_list"]:
                media_list.append(
                    {
                        "id": media.id,
                        "url": media.file.url,
                        "filename": media.filename,
                        "file_type": media.file_type,
                        "title": media.title,
                        "alt_text": media.alt_text,
                        "created_at": media.created_at.strftime("%Y-%m-%d"),
                    }
                )

            # Pagination info
            page_obj = context["page_obj"]
            pagination = {
                "has_next": page_obj.has_next(),
                "has_previous": page_obj.has_previous(),
                "num_pages": page_obj.paginator.num_pages,
                "current_page": page_obj.number,
            }

            return JsonResponse({"results": media_list, "pagination": pagination})

        return super().render_to_response(context, **response_kwargs)


class MediaCreateView(BaseCreateView):
    model = Media
    form_class = MediaForm
    success_url = reverse_lazy("administration:media_list")

    def form_valid(self, form):
        form.instance.uploaded_by = self.request.user
        return super().form_valid(form)


@method_decorator(csrf_exempt, name="dispatch")
class MediaUploadView(View):
    """
    Handle Dropzone.js uploads
    """

    def post(self, request):
        if not request.user.is_staff:
            return JsonResponse({"error": "Permission denied"}, status=403)

        if "file" not in request.FILES:
            return JsonResponse({"error": "No file uploaded"}, status=400)

        file = request.FILES["file"]
        try:
            media = Media.objects.create(
                file=file, uploaded_by=request.user, filename=file.name
            )
            return JsonResponse(
                {"id": media.id, "url": media.file.url, "filename": media.filename}
            )
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


class MediaUpdateView(BaseUpdateView):
    model = Media
    form_class = MediaForm
    success_url = reverse_lazy("administration:media_list")

    def post(self, request, *args, **kwargs):
        # Handle JSON request from Alpine.js
        if request.content_type == "application/json":
            try:
                data = json.loads(request.body)
                self.object = self.get_object()
                form = self.get_form_class()(data, instance=self.object)
                if form.is_valid():
                    self.object = form.save()
                    return JsonResponse(
                        {
                            "status": "success",
                            "message": "Media updated successfully",
                            "data": {
                                "title": self.object.title,
                                "alt_text": self.object.alt_text,
                                "description": self.object.description,
                            },
                        }
                    )
                return JsonResponse(
                    {"status": "error", "errors": form.errors}, status=400
                )
            except Exception as e:
                return JsonResponse({"status": "error", "message": str(e)}, status=400)

        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        # If it's an AJAX request (from modal) but not JSON, return JSON
        if (
            self.request.headers.get("x-requested-with") == "XMLHttpRequest"
            or self.request.htmx
        ):
            return JsonResponse(
                {
                    "status": "success",
                    "message": "Media updated successfully",
                    "data": {
                        "title": self.object.title,
                        "alt_text": self.object.alt_text,
                        "description": self.object.description,
                    },
                }
            )
        return response


class MediaDeleteView(BaseDeleteView):
    model = Media
    success_url = reverse_lazy("administration:media_list")

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Also delete the physical file
        try:
            # Django's FileField doesn't auto-delete files on model delete by default anymore
            # We can rely on django-cleanup if installed, or do it manually
            if self.object.file:
                self.object.file.delete(save=False)
        except Exception:
            pass  # File might not exist

        self.object.delete()

        # Handle AJAX/HTMX response
        if (
            self.request.headers.get("x-requested-with") == "XMLHttpRequest"
            or self.request.htmx
        ):
            return JsonResponse(
                {"status": "success", "message": "Media deleted successfully"}
            )

        return redirect(self.get_success_url())


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
