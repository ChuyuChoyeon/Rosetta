from modeltranslation.translator import register, TranslationOptions
from .models import Category, Tag, Post

@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ('name', 'description')

@register(Tag)
class TagTranslationOptions(TranslationOptions):
    fields = ('name',)

@register(Post)
class PostTranslationOptions(TranslationOptions):
    fields = ('title', 'subtitle', 'content', 'excerpt', 'meta_title', 'meta_description', 'meta_keywords')
