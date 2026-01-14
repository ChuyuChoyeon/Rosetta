from .models import FriendLink, Navigation
from users.models import UserPreference


def site_settings(request):
    # Convert tuple choices to list of dicts for template usage
    themes = [
        {"id": code, "name": label} for code, label in UserPreference.THEME_CHOICES
    ]

    return {
        "friend_links": FriendLink.objects.filter(is_active=True),
        "navigations": Navigation.objects.filter(is_active=True),
        "themes": themes,
    }
