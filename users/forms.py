from django import forms
from django.contrib.auth.forms import UserCreationForm
from captcha.fields import CaptchaField
from .models import User, UserPreference


class RegisterForm(UserCreationForm):
    """
    用户注册表单
    
    继承自 UserCreationForm，添加了以下字段：
    - nickname: 昵称
    - email: 邮箱 (具有唯一性验证)
    - avatar: 头像
    - captcha: 验证码 (防止机器人注册)
    """
    captcha = CaptchaField(label="验证码")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ("nickname", "email", "avatar")

    def clean_email(self):
        """
        验证邮箱唯一性
        如果邮箱已被注册，抛出 ValidationError。
        """
        email = self.cleaned_data.get("email")
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError("该邮箱已被注册")
        return email


class UserPreferenceForm(forms.ModelForm):
    """
    用户偏好设置表单
    
    用于更新 UserPreference 模型。
    字段:
    - public_profile: 是否公开个人资料
    - theme: 界面主题选择 (Light/Dark)
    """
    class Meta:
        model = UserPreference
        fields = ["public_profile", "theme"]
        widgets = {
            "theme": forms.RadioSelect(attrs={"class": "radio"}),
            "public_profile": forms.CheckboxInput(attrs={"class": "toggle toggle-primary"}),
        }


class UserProfileForm(forms.ModelForm):
    """
    用户个人资料表单
    
    用于更新 User 模型的基本信息。
    字段包括: 头像、封面、昵称、简介、个人网站、GitHub、邮箱。
    
    使用了 DaisyUI 样式的 Widget。
    """
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
