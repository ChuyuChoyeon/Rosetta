from django.urls import reverse_lazy
from django.views.generic import View
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin

from blog.models import Comment
from voting.models import Poll
from ..forms import PollForm, ChoiceFormSet
from ..mixins import StaffRequiredMixin
from ..generics import (
    BaseListView,
    BaseCreateView,
    BaseUpdateView,
    BaseDeleteView,
)


# --- Comment Views ---
class CommentListView(BaseListView):
    model = Comment
    context_object_name = "comments"
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .select_related("post", "user", "parent", "parent__user", "user__title")
        )
        query = self.request.GET.get("q")
        status = self.request.GET.get("status")
        user_id = self.request.GET.get("user")
        post_id = self.request.GET.get("post")

        if query:
            qs = qs.filter(content__icontains=query)

        if status == "active":
            qs = qs.filter(active=True)
        elif status == "pending":
            qs = qs.filter(active=False)

        if user_id:
            qs = qs.filter(user_id=user_id)

        if post_id:
            qs = qs.filter(post_id=post_id)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_count"] = Comment.objects.count()
        context["pending_count"] = Comment.objects.filter(active=False).count()
        context["active_count"] = Comment.objects.filter(active=True).count()
        return context


class CommentUpdateView(BaseUpdateView):
    model = Comment
    fields = ["content", "active"]
    success_url = reverse_lazy("administration:comment_list")


class CommentReplyView(LoginRequiredMixin, StaffRequiredMixin, View):
    # This view was empty in original code or logic missing, just implementing placeholder for now
    # or redirecting back.
    def post(self, request, pk):
        # Implementation of reply logic would go here
        return redirect("administration:comment_list")


class CommentDeleteView(BaseDeleteView):
    model = Comment
    success_url = reverse_lazy("administration:comment_list")


# --- Poll Views ---
class PollListView(BaseListView):
    model = Poll
    context_object_name = "polls"
    ordering = ["-created_at"]


class PollCreateView(BaseCreateView):
    model = Poll
    form_class = PollForm
    success_url = reverse_lazy("administration:poll_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["choice_formset"] = ChoiceFormSet(self.request.POST)
        else:
            context["choice_formset"] = ChoiceFormSet()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        choice_formset = context["choice_formset"]
        if choice_formset.is_valid():
            self.object = form.save()
            choice_formset.instance = self.object
            choice_formset.save()
            return super().form_valid(form)
        else:
            return self.render_to_response(self.get_context_data(form=form))


class PollUpdateView(BaseUpdateView):
    model = Poll
    form_class = PollForm
    success_url = reverse_lazy("administration:poll_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["choice_formset"] = ChoiceFormSet(
                self.request.POST, instance=self.object
            )
        else:
            context["choice_formset"] = ChoiceFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        choice_formset = context["choice_formset"]
        if choice_formset.is_valid():
            self.object = form.save()
            choice_formset.instance = self.object
            choice_formset.save()
            return super().form_valid(form)
        else:
            return self.render_to_response(self.get_context_data(form=form))


class PollDeleteView(BaseDeleteView):
    model = Poll
    success_url = reverse_lazy("administration:poll_list")
