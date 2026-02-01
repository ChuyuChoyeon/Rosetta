from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _
from users.models import UserTitle
from .mixins import StyleFormMixin

User = get_user_model()

class UserTitleForm(StyleFormMixin, forms.ModelForm):
    class Meta:
        model = UserTitle
        fields = [
            "name", "name_zh_hans", "name_en", "name_ja", "name_zh_hant",
            "color", "icon",
            "description", "description_zh_hans", "description_en", "description_ja", "description_zh_hant",
        ]
        widgets = {
            "color": forms.TextInput(attrs={"type": "color", "class": "h-10 p-1 cursor-pointer"}),
            "icon": forms.Textarea(attrs={"class": "h-24 font-mono text-xs", "placeholder": "<svg...>"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].required = False
        self.fields["description"].required = False


class GroupForm(StyleFormMixin, forms.ModelForm):
    class Meta:
        model = Group
        fields = ["name", "permissions"]
        widgets = {
            "permissions": forms.SelectMultiple(attrs={"class": "h-64"}),
        }


class UserForm(StyleFormMixin, forms.ModelForm):
    new_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        label=_("新密码"),
        help_text=_("如需修改密码请在此输入，否则留空"),
    )

    class Meta:
        model = User
        fields = [
            "username", "nickname", "email", "avatar", "cover_image",
            "bio", "website", "github", "title",
            "is_active", "is_banned", "is_staff", "is_superuser",
            "groups", "user_permissions",
        ]
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 3}),
            "groups": forms.CheckboxSelectMultiple(),
            "user_permissions": forms.SelectMultiple(attrs={"class": "h-48"}),
        }

    def save(self, commit=True):
        user = super(forms.ModelForm, self).save(commit=False)
        new_password = self.cleaned_data.get("new_password")
        if new_password:
            user.set_password(new_password)
        if commit:
            user.save()
            self.save_m2m()
        return user
