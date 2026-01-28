from django.urls import path
from .views import GuestbookView

app_name = "guestbook"

urlpatterns = [
    path("", GuestbookView.as_view(), name="index"),
]
