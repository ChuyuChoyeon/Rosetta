from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.forms import inlineformset_factory
from voting.models import Poll, Choice
from .mixins import StyleFormMixin

class PollForm(StyleFormMixin, forms.ModelForm):
    end_date = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        input_formats=["%Y-%m-%dT%H:%M"],
        label="结束时间",
    )

    class Meta:
        model = Poll
        fields = [
            "title", "title_zh_hans", "title_en", "title_ja", "title_zh_hant",
            "description", "description_zh_hans", "description_en", "description_ja", "description_zh_hant",
            "is_active", "allow_multiple_choices", "end_date", "related_post",
        ]
        widgets = {
            "title": forms.HiddenInput(),
            "description": forms.HiddenInput(),
            "description_zh_hans": forms.Textarea(attrs={"rows": 3}),
            "description_en": forms.Textarea(attrs={"rows": 3}),
            "description_ja": forms.Textarea(attrs={"rows": 3}),
            "description_zh_hant": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["title"].required = False
        self.fields["description"].required = False

        if self.instance.pk and self.instance.end_date:
            self.fields["end_date"].initial = timezone.localtime(
                self.instance.end_date
            ).strftime("%Y-%m-%dT%H:%M")


class ChoiceForm(StyleFormMixin, forms.ModelForm):
    class Meta:
        model = Choice
        fields = [
            "text", "text_zh_hans", "text_en", "text_ja", "text_zh_hant",
            "votes_count",
        ]
        widgets = {
            "text": forms.HiddenInput(),
            "text_zh_hans": forms.TextInput(attrs={"placeholder": _("选项文本 (简中)")}),
            "text_en": forms.TextInput(attrs={"placeholder": _("选项文本 (英文)")}),
            "text_ja": forms.TextInput(attrs={"placeholder": _("选项文本 (日文)")}),
            "text_zh_hant": forms.TextInput(attrs={"placeholder": _("选项文本 (繁中)")}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["text"].required = False


ChoiceFormSet = inlineformset_factory(
    Poll,
    Choice,
    form=ChoiceForm,
    extra=1,
    can_delete=True,
)
