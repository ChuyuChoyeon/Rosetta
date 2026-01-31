from django.urls import path
from .views import PollDetailView, PollVoteView, PollListView

app_name = "voting"

urlpatterns = [
    # 投票列表
    path("", PollListView.as_view(), name="list"),
    # 投票详情
    path("<int:pk>/", PollDetailView.as_view(), name="detail"),
    # 投票动作 (AJAX/HTMX)
    path("<int:pk>/vote/", PollVoteView.as_view(), name="vote"),
]
