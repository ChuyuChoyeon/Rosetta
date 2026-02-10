from django import template
from django.utils import timezone
from datetime import timedelta
import bleach
from django.utils.safestring import mark_safe
from django.urls import translate_url as django_translate_url

register = template.Library()


@register.simple_tag(takes_context=True)
def translate_url(context, language_code):
    """
    Get the current URL in the specified language.
    """
    request = context.get("request")
    if not request:
        return ""
    path = request.get_full_path()
    return django_translate_url(path, language_code)


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


@register.filter(name="sanitize_svg")
def sanitize_svg(value):
    """
    Sanitize SVG content using bleach to prevent XSS.
    Allows common SVG tags and attributes.
    """
    if not value:
        return ""

    allowed_tags = [
        "svg",
        "g",
        "path",
        "rect",
        "circle",
        "line",
        "polyline",
        "polygon",
        "ellipse",
        "defs",
        "linearGradient",
        "stop",
        "style",
        "use",
        "symbol",
        "desc",
        "title",
    ]

    allowed_attributes = {
        "*": [
            "class",
            "style",
            "id",
            "fill",
            "stroke",
            "stroke-width",
            "stroke-linecap",
            "stroke-linejoin",
            "viewBox",
            "width",
            "height",
            "d",
            "opacity",
            "transform",
            "points",
            "x",
            "y",
            "x1",
            "y1",
            "x2",
            "y2",
            "cx",
            "cy",
            "r",
            "rx",
            "ry",
            "xmlns",
            "version",
            "preserveAspectRatio",
            "offset",
            "stop-color",
            "stop-opacity",
        ],
    }

    cleaned = bleach.clean(
        value, tags=allowed_tags, attributes=allowed_attributes, strip=True
    )
    return mark_safe(cleaned)


@register.filter
def model_verbose_name(content_type):
    """
    Returns the verbose name of the model represented by the ContentType.
    """
    if not content_type:
        return ""
    try:
        model = content_type.model_class()
        if model:
            return model._meta.verbose_name
        return content_type.name
    except Exception:
        return str(content_type)
