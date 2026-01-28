from django.views.generic import DetailView, View, ListView
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F
from .models import Poll, Choice, Vote

class PollListView(ListView):
    model = Poll
    template_name = "voting/poll_list.html"
    context_object_name = "polls"
    paginate_by = 12
    
    def get_queryset(self):
        return Poll.objects.filter(is_active=True).order_by('-created_at')

class PollDetailView(DetailView):
    model = Poll
    template_name = "voting/poll_detail.html"
    context_object_name = "poll"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_authenticated:
            context["has_voted"] = Vote.objects.filter(poll=self.object, user=user).exists()
        else:
            context["has_voted"] = False
        return context

class PollVoteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        poll = get_object_or_404(Poll, pk=pk)
        
        # Check if already voted
        if Vote.objects.filter(poll=poll, user=request.user).exists():
            # If already voted, return the results directly
            context = {
                "poll": poll,
                "has_voted": True
            }
            return render(request, "voting/partials/poll_results.html", context)

        choice_id = request.POST.get("choice")
        if not choice_id:
            return HttpResponse('<div class="alert alert-warning">请选择一个选项！</div>')

        choice = get_object_or_404(Choice, pk=choice_id, poll=poll)

        # Create Vote
        Vote.objects.create(poll=poll, user=request.user, choice=choice)
        
        # Increment Count (Atomic)
        Choice.objects.filter(pk=choice_id).update(votes_count=F("votes_count") + 1)

        # Return updated poll results (HTMX)
        context = {
            "poll": poll,
            "has_voted": True
        }
        return render(request, "voting/partials/poll_results.html", context)
