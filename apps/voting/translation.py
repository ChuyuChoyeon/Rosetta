from modeltranslation.translator import register, TranslationOptions
from .models import Poll, Choice


@register(Poll)
class PollTranslationOptions(TranslationOptions):
    fields = ("title", "description")


@register(Choice)
class ChoiceTranslationOptions(TranslationOptions):
    fields = ("text",)
