import re
import bleach
import markdown
from django import template
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe

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
        "p",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "br",
        "hr",
        "pre",
        "code",
        "blockquote",
        "img",
        "table",
        "thead",
        "tbody",
        "tr",
        "th",
        "td",
        "div",
        "span",
        "strong",
        "em",
        "u",
        "s",
        "del",
    ]

    # 定义允许的属性白名单
    allowed_attributes = {
        "*": ["class", "id"],
        "a": ["href", "title", "target", "rel"],
        "img": ["src", "alt", "title", "width", "height", "loading"],
        "code": ["class"],
        "pre": ["class"],
        "div": ["class"],
        "span": ["class"],
    }

    # 清洗 HTML (Sanitize HTML)
    cleaned_html = bleach.clean(
        html_content, tags=allowed_tags, attributes=allowed_attributes, strip=True
    )

    # 注入 DaisyUI mockup-code 样式
    # 将 Pygments 生成的 .codehilite 容器转换为 DaisyUI 的 .mockup-code 组件
    # 结构: <div class="codehilite"> -> <div class="mockup-code codehilite">
    # 注意：mockup-code 默认有 min-width: 18rem，可能需要 CSS 覆盖以适应移动端
    final_html = cleaned_html.replace(
        '<div class="codehilite">', '<div class="mockup-code codehilite">'
    )

    # 为所有表格添加 DaisyUI 样式
    final_html = final_html.replace(
        "<table>", '<div class="overflow-x-auto"><table class="table table-zebra">'
    )
    final_html = final_html.replace("</table>", "</table></div>")
    
    # Auto-add loading="lazy" to images
    final_html = final_html.replace('<img ', '<img loading="lazy" ')

    return mark_safe(final_html)


@register.filter(name="markdown_text")
def markdown_text(text):
    if not text:
        return ""
    html_content = markdown.markdown(text, extensions=["extra", "codehilite", "toc"])
    plain_text = strip_tags(html_content)
    plain_text = re.sub(r"\s+", " ", plain_text).strip()
    return plain_text
