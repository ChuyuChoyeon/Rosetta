from modeltranslation.translator import register, TranslationOptions
from .models import UserTitle


@register(UserTitle)
class UserTitleTranslationOptions(TranslationOptions):
    fields = ("name", "description")
