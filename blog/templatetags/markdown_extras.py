from django import template
from django.utils.safestring import mark_safe
import markdown
import bleach

register = template.Library()


@register.filter(name="markdown")
def markdown_format(text):
    """
    Markdown 渲染过滤器
    
    将 Markdown 文本转换为 HTML，并进行安全过滤 (Sanitization)。
    
    特性:
    - 扩展支持: extra (表格等), codehilite (代码高亮), toc (目录)
    - 安全过滤: 使用 bleach 移除潜在的 XSS 攻击标签 (如 script, iframe 等)
    - 允许标签: 常用文本标签, 代码块, 图片, 表格等
    """
    if not text:
        return ""
        
    # 转换为 HTML (Convert Markdown to HTML)
    html_content = markdown.markdown(text, extensions=["extra", "codehilite", "toc"])
    
    # 定义允许的标签白名单 (Define allowed tags and attributes)
    allowed_tags = list(bleach.sanitizer.ALLOWED_TAGS) + [
        'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'br', 'hr',
        'pre', 'code', 'blockquote',
        'img', 'table', 'thead', 'tbody', 'tr', 'th', 'td',
        'div', 'span', 'strong', 'em', 'u', 's', 'del'
    ]
    
    # 定义允许的属性白名单
    allowed_attributes = {
        '*': ['class', 'id'],
        'a': ['href', 'title', 'target', 'rel'],
        'img': ['src', 'alt', 'title', 'width', 'height'],
        'code': ['class'],
        'pre': ['class'],
        'div': ['class'],
        'span': ['class'],
    }
    
    # 清洗 HTML (Sanitize HTML)
    cleaned_html = bleach.clean(
        html_content,
        tags=allowed_tags,
        attributes=allowed_attributes,
        strip=True
    )
    
    return mark_safe(cleaned_html)
