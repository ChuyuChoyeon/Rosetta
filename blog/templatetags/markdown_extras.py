from django import template
from django.utils.safestring import mark_safe
import markdown
import bleach

register = template.Library()


@register.filter(name="markdown")
def markdown_format(text):
    if not text:
        return ""
        
    # Convert Markdown to HTML
    html_content = markdown.markdown(text, extensions=["extra", "codehilite", "toc"])
    
    # Define allowed tags and attributes
    allowed_tags = list(bleach.sanitizer.ALLOWED_TAGS) + [
        'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'br', 'hr',
        'pre', 'code', 'blockquote',
        'img', 'table', 'thead', 'tbody', 'tr', 'th', 'td',
        'div', 'span', 'strong', 'em', 'u', 's', 'del'
    ]
    
    allowed_attributes = {
        '*': ['class', 'id'],
        'a': ['href', 'title', 'target', 'rel'],
        'img': ['src', 'alt', 'title', 'width', 'height'],
        'code': ['class'],
        'pre': ['class'],
        'div': ['class'],
        'span': ['class'],
    }
    
    # Sanitize HTML
    cleaned_html = bleach.clean(
        html_content,
        tags=allowed_tags,
        attributes=allowed_attributes,
        strip=True
    )
    
    return mark_safe(cleaned_html)
