from django import template
from django.db.models import Q
from django.utils import timezone
from voting.models import Vote, Poll

register = template.Library()


@register.filter
def has_voted(user, poll):
    if not user.is_authenticated:
        return False
    return Vote.objects.filter(user=user, poll=poll).exists()


@register.simple_tag
def get_active_polls(limit=3):
    """
    获取活跃的投票
    """
    now = timezone.now()
    return (
        Poll.objects.filter(is_active=True)
        .filter(Q(end_date__isnull=True) | Q(end_date__gte=now))
        .order_by("-created_at")[:limit]
    )
