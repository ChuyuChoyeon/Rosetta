from .models import FriendLink, Navigation, SearchPlaceholder
from users.models import UserPreference


def site_settings(request):
    # Convert tuple choices to list of dicts for template usage
    themes = [
        {"id": code, "name": label} for code, label in UserPreference.THEME_CHOICES
    ]
    
    # Get search placeholders
    placeholders = list(SearchPlaceholder.objects.filter(is_active=True).values_list('text', flat=True))
    if not placeholders:
        placeholders = ["搜索文章...", "搜索标签..."]

    return {
        "friend_links": FriendLink.objects.filter(is_active=True),
        "navigations": Navigation.objects.filter(is_active=True),
        "themes": themes,
        "search_placeholders": placeholders,
    }
