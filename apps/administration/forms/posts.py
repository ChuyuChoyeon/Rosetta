from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from blog.models import Post, Category, Tag
from .mixins import StyleFormMixin

class PostForm(StyleFormMixin, forms.ModelForm):
    """
    文章表单
    """
    tags_str = forms.CharField(required=False, widget=forms.HiddenInput, label=_("标签"))
    published_at = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        input_formats=["%Y-%m-%dT%H:%M"],
        label=_("发布时间"),
    )

    class Meta:
        model = Post
        fields = [
            "title", "title_zh_hans", "title_en", "title_ja", "title_zh_hant",
            "subtitle", "subtitle_zh_hans", "subtitle_en", "subtitle_ja", "subtitle_zh_hant",
            "slug", "cover_image",
            "content", "content_zh_hans", "content_en", "content_ja", "content_zh_hant",
            "excerpt", "excerpt_zh_hans", "excerpt_en", "excerpt_ja", "excerpt_zh_hant",
            "status", "published_at", "category", "password", "is_pinned", "allow_comments",
            "meta_title", "meta_title_zh_hans", "meta_title_en", "meta_title_ja", "meta_title_zh_hant",
            "meta_description", "meta_description_zh_hans", "meta_description_en", "meta_description_ja", "meta_description_zh_hant",
            "meta_keywords", "meta_keywords_zh_hans", "meta_keywords_en", "meta_keywords_ja", "meta_keywords_zh_hant",
        ]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 20}),
            "content_zh_hans": forms.Textarea(attrs={"rows": 20}),
            "content_en": forms.Textarea(attrs={"rows": 20}),
            "content_ja": forms.Textarea(attrs={"rows": 20}),
            "content_zh_hant": forms.Textarea(attrs={"rows": 20}),
            "excerpt": forms.Textarea(attrs={"rows": 3}),
            "excerpt_zh_hans": forms.Textarea(attrs={"rows": 3}),
            "excerpt_en": forms.Textarea(attrs={"rows": 3}),
            "excerpt_ja": forms.Textarea(attrs={"rows": 3}),
            "excerpt_zh_hant": forms.Textarea(attrs={"rows": 3}),
            "meta_description": forms.Textarea(attrs={"rows": 2}),
            "meta_description_zh_hans": forms.Textarea(attrs={"rows": 2}),
            "meta_description_en": forms.Textarea(attrs={"rows": 2}),
            "meta_description_ja": forms.Textarea(attrs={"rows": 2}),
            "meta_description_zh_hant": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["title"].required = False
        self.fields["content"].required = False

        if self.instance.pk:
            self.fields["tags_str"].initial = ",".join(
                [t.name for t in self.instance.tags.all()]
            )
            if self.instance.published_at:
                self.fields["published_at"].initial = timezone.localtime(
                    self.instance.published_at
                ).strftime("%Y-%m-%dT%H:%M")

    def save(self, commit=True):
        post = super(forms.ModelForm, self).save(commit=False)

        if "password" in self.changed_data and post.password:
            if not post.password.startswith("pbkdf2_"):
                post.set_password(post.password)

        if commit:
            post.save()
            tags_str = self.cleaned_data.get("tags_str", "")
            if tags_str:
                tag_names = [t.strip() for t in tags_str.split(",") if t.strip()]
                tags = []
                for name in tag_names:
                    try:
                        tag, created = Tag.objects.get_or_create(name=name)
                    except Exception:
                        from django.utils.text import slugify
                        import uuid
                        slug = slugify(name)
                        tag = Tag.objects.filter(slug=slug).first()
                        if not tag:
                            slug = f"{slug}-{uuid.uuid4().hex[:6]}"
                            tag = Tag.objects.create(name=name, slug=slug)
                    if tag:
                        tags.append(tag)
                post.tags.set(tags)
            else:
                post.tags.clear()
        return post


class CategoryForm(StyleFormMixin, forms.ModelForm):
    """
    分类表单
    """
    class Meta:
        model = Category
        fields = [
            "name", "name_zh_hans", "name_en", "name_ja", "name_zh_hant",
            "slug", "description", "description_zh_hans", "description_en", "description_ja", "description_zh_hant",
            "icon", "color", "cover_image",
        ]
        widgets = {
             "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].required = False


class TagForm(StyleFormMixin, forms.ModelForm):
    """
    标签表单
    """
    class Meta:
        model = Tag
        fields = [
            "name", "name_zh_hans", "name_en", "name_ja", "name_zh_hant",
            "slug", "color", "icon", "is_active",
        ]
        widgets = {
            "icon": forms.TextInput(attrs={"class": "font-mono"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].required = False
