from modeltranslation.translator import register, TranslationOptions
from .models import Navigation, FriendLink, SearchPlaceholder, Page


@register(Navigation)
class NavigationTranslationOptions(TranslationOptions):
    fields = ("title",)


@register(FriendLink)
class FriendLinkTranslationOptions(TranslationOptions):
    fields = ("name", "description")


@register(SearchPlaceholder)
class SearchPlaceholderTranslationOptions(TranslationOptions):
    fields = ("text",)


@register(Page)
class PageTranslationOptions(TranslationOptions):
    fields = ("title", "content")
