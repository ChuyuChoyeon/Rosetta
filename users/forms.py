from django import forms
from django.contrib.auth.forms import UserCreationForm
from captcha.fields import CaptchaField
from .models import User, UserPreference


class RegisterForm(UserCreationForm):
    captcha = CaptchaField(label="验证码")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ("nickname", "email", "avatar")

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError("该邮箱已被注册")
        return email


class UserPreferenceForm(forms.ModelForm):
    class Meta:
        model = UserPreference
        fields = ["public_profile", "theme"]
        widgets = {
            "theme": forms.Select(attrs={"class": "select select-bordered w-full"}),
            "public_profile": forms.CheckboxInput(attrs={"class": "checkbox"}),
        }


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            "avatar",
            "cover_image",
            "nickname",
            "bio",
            "website",
            "github",
            "email",
        ]
        widgets = {
            "avatar": forms.FileInput(
                attrs={"class": "file-input file-input-bordered w-full"}
            ),
            "cover_image": forms.FileInput(
                attrs={"class": "file-input file-input-bordered w-full"}
            ),
            "bio": forms.Textarea(
                attrs={"class": "textarea textarea-bordered h-24 w-full"}
            ),
            "nickname": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "website": forms.URLInput(attrs={"class": "input input-bordered w-full"}),
            "github": forms.URLInput(attrs={"class": "input input-bordered w-full"}),
            "email": forms.EmailInput(attrs={"class": "input input-bordered w-full"}),
        }
