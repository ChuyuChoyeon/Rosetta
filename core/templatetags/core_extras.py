from django import template
from django.utils import timezone
from datetime import timedelta

register = template.Library()

@register.filter
def time_ago(value):
    """
    Custom time filter for Chinese platform style:
    - If < 1 minute: "刚刚"
    - If < 1 hour: "X分钟前"
    - If < 1 day: "X小时前"
    - If >= 1 day: "X天前" (ignores hours)
    """
    if not value:
        return ""
    
    now = timezone.now()
    if timezone.is_naive(value):
        value = timezone.make_aware(value, timezone.get_current_timezone())
    
    # Ensure value is not in the future
    if value > now:
        return "刚刚"

    diff = now - value
    
    if diff < timedelta(minutes=1):
        return "刚刚"
    elif diff < timedelta(hours=1):
        return f"{diff.seconds // 60}分钟前"
    elif diff < timedelta(days=1):
        return f"{diff.seconds // 3600}小时前"
    else:
        return f"{diff.days}天前"
