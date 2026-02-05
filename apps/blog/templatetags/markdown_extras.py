import re
import bleach
import markdown
from bs4 import BeautifulSoup
from django import template
from django.conf import settings
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from PIL import Image
import os
from urllib.parse import urlparse

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
    - SEO & UX 增强:
        - 外链自动添加 rel="noopener noreferrer" 和 target="_blank"
        - 图片自动添加 width/height (如果本地存在) 以减少 CLS
        - 图片自动添加 loading="lazy"
        - DaisyUI 样式适配
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

    # 使用 BeautifulSoup 进行后处理 (Post-processing)
    soup = BeautifulSoup(cleaned_html, "html.parser")

    # 1. 处理链接 (Links): 外链添加 noopener noreferrer
    current_domain = urlparse(settings.META_SITE_DOMAIN).netloc if hasattr(settings, 'META_SITE_DOMAIN') else 'choyeon.cc'
    
    for a in soup.find_all("a"):
        href = a.get("href")
        if href:
            parsed_href = urlparse(href)
            # 如果是绝对路径且域名不匹配当前域名，则视为外链
            if parsed_href.scheme and parsed_href.netloc and parsed_href.netloc != current_domain:
                a["target"] = "_blank"
                a["rel"] = "noopener noreferrer"

    # 2. 处理图片 (Images): 添加 width/height 和 loading="lazy"
    for img in soup.find_all("img"):
        # 强制懒加载
        img["loading"] = "lazy"
        
        # 如果已有宽高，跳过
        if img.get("width") and img.get("height"):
            continue

        src = img.get("src")
        if not src:
            continue

        # 尝试获取本地图片尺寸
        local_path = None
        if src.startswith(settings.MEDIA_URL):
            # /media/foo.jpg -> /path/to/media/foo.jpg
            relative_path = src[len(settings.MEDIA_URL):]
            local_path = os.path.join(settings.MEDIA_ROOT, relative_path)
        elif src.startswith(settings.STATIC_URL):
            # /static/foo.jpg -> /path/to/static/foo.jpg
            relative_path = src[len(settings.STATIC_URL):]
            local_path = os.path.join(settings.STATIC_ROOT, relative_path)
        
        if local_path and os.path.exists(local_path):
            try:
                with Image.open(local_path) as im:
                    width, height = im.size
                    img["width"] = width
                    img["height"] = height
            except Exception:
                # 图片读取失败，忽略
                pass

    # 3. DaisyUI 样式注入
    
    # Tables
    for table in soup.find_all("table"):
        # 包装 table
        wrapper = soup.new_tag("div", **{"class": "overflow-x-auto"})
        table.wrap(wrapper)
        table["class"] = table.get("class", []) + ["table", "table-zebra"]

    final_html = str(soup)

    return mark_safe(final_html)


@register.filter(name="markdown_text")
def markdown_text(text):
    if not text:
        return ""
    html_content = markdown.markdown(text, extensions=["extra", "codehilite", "toc"])
    plain_text = strip_tags(html_content)
    plain_text = re.sub(r"\s+", " ", plain_text).strip()
    return plain_text
