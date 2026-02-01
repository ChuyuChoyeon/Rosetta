from django import forms
from core.models import Page, Navigation, FriendLink, SearchPlaceholder
from .mixins import StyleFormMixin
import bleach
from bleach.css_sanitizer import CSSSanitizer

class PageForm(StyleFormMixin, forms.ModelForm):
    class Meta:
        model = Page
        fields = [
            "title", "title_zh_hans", "title_en", "title_ja", "title_zh_hant",
            "slug", "content", "content_zh_hans", "content_en", "content_ja", "content_zh_hant",
            "status",
        ]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 20}),
            "content_zh_hans": forms.Textarea(attrs={"rows": 20}),
            "content_en": forms.Textarea(attrs={"rows": 20}),
            "content_ja": forms.Textarea(attrs={"rows": 20}),
            "content_zh_hant": forms.Textarea(attrs={"rows": 20}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["title"].required = False
        self.fields["content"].required = False

    def clean(self):
        cleaned_data = super().clean()
        for lang in ['zh_hans', 'en', 'ja', 'zh_hant']:
            field_name = f'content_{lang}'
            content = cleaned_data.get(field_name)
            if content:
                allowed_tags = list(bleach.sanitizer.ALLOWED_TAGS) + [
                    "h1", "h2", "h3", "h4", "h5", "h6", "p", "div", "span", "br", "hr",
                    "ul", "ol", "li", "dl", "dt", "dd", "img", "pre", "code", "blockquote",
                    "table", "thead", "tbody", "tr", "th", "td", "strong", "em", "b", "i",
                    "u", "s", "strike", "iframe", "figure", "figcaption", "video", "audio", "source",
                ]
                allowed_attrs = {
                    "*": ["class", "id", "style", "title", "data-theme"],
                    "a": ["href", "target", "rel"],
                    "img": ["src", "alt", "width", "height"],
                    "iframe": ["src", "width", "height", "frameborder", "allow", "allowfullscreen"],
                    "video": ["src", "controls", "width", "height", "poster", "autoplay", "loop", "muted", "playsinline"],
                    "audio": ["src", "controls", "autoplay", "loop", "muted"],
                    "source": ["src", "type"],
                }
                allowed_styles = [
                    "color", "background-color", "text-align", "font-size", "font-weight",
                    "text-decoration", "width", "height", "display", "margin", "padding",
                    "border", "border-radius",
                ]
                
                css_sanitizer = CSSSanitizer(allowed_css_properties=allowed_styles)

                content = bleach.clean(
                    content,
                    tags=allowed_tags,
                    attributes=allowed_attrs,
                    css_sanitizer=css_sanitizer,
                    strip=True,
                )
                cleaned_data[field_name] = content
        
        return cleaned_data


class NavigationForm(StyleFormMixin, forms.ModelForm):
    class Meta:
        model = Navigation
        fields = [
            "title", "title_zh_hans", "title_en", "title_ja", "title_zh_hant",
            "url", "location", "order", "is_active", "target_blank",
        ]
        widgets = {
            "title": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["title"].required = False


class SearchPlaceholderForm(StyleFormMixin, forms.ModelForm):
    class Meta:
        model = SearchPlaceholder
        fields = [
            "text", "text_zh_hans", "text_en", "text_ja", "text_zh_hant",
            "order", "is_active",
        ]
        widgets = {
            "text": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["text"].required = False


class FriendLinkForm(StyleFormMixin, forms.ModelForm):
    class Meta:
        model = FriendLink
        fields = [
            "name", "name_zh_hans", "name_en", "name_ja", "name_zh_hant",
            "url", "description", "description_zh_hans", "description_en", "description_ja", "description_zh_hant",
            "logo", "order", "is_active",
        ]
        widgets = {
            "name": forms.HiddenInput(),
            "description": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].required = False
        self.fields["description"].required = False
