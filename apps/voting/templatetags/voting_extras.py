from django import template
from voting.models import Vote

register = template.Library()

@register.filter
def has_voted(user, poll):
    if not user.is_authenticated:
        return False
    return Vote.objects.filter(user=user, poll=poll).exists()
