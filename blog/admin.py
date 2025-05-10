from django.contrib import admin
from unfold.admin import ModelAdmin
from django import forms
from taggit.models import Tag
from .models import Post, Category, Comment, Link
from unfold.contrib.forms.widgets import WysiwygWidget
from django.forms.widgets import TextInput

class PostAdminForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = "__all__"
        widgets = {
            "content": WysiwygWidget,
        }


@admin.register(Post)
class PostAdmin(ModelAdmin):
    form = PostAdminForm
    list_display = ("title", "author", "status", "published_at")
    search_fields = ("title", "author__username")
    list_filter = ("status", "category")
    ordering = ("-published_at",)

@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)


@admin.register(Comment)
class CommentAdmin(ModelAdmin):
    list_display = ("post", "author", "status", "created_at")
    search_fields = ("author", "content")
    list_filter = ("status",)

@admin.register(Link)
class LinkAdmin(ModelAdmin):
    list_display = ("name", "url", "is_active", "created_at")
    search_fields = ("name", "url")
    list_filter = ("is_active",)