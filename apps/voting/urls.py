from django.urls import path
from .views import PollDetailView, PollVoteView, PollListView

app_name = "voting"

urlpatterns = [
    path("", PollListView.as_view(), name="list"),
    path("<int:pk>/", PollDetailView.as_view(), name="detail"),
    path("<int:pk>/vote/", PollVoteView.as_view(), name="vote"),
]
