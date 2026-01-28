from django import forms
from .models import GuestbookEntry
from captcha.fields import CaptchaField

class GuestbookForm(forms.ModelForm):
    captcha = CaptchaField(label="验证码")
    
    class Meta:
        model = GuestbookEntry
        fields = ["nickname", "email", "website", "content", "show_email"]
        widgets = {
            "nickname": forms.TextInput(attrs={"class": "input input-bordered w-full", "placeholder": "您的昵称"}),
            "email": forms.EmailInput(attrs={"class": "input input-bordered w-full", "placeholder": "您的邮箱 (保密)"}),
            "website": forms.URLInput(attrs={"class": "input input-bordered w-full", "placeholder": "您的网站 (可选)"}),
            "show_email": forms.CheckboxInput(attrs={"class": "toggle toggle-primary"}),
            "content": forms.Textarea(attrs={"class": "textarea textarea-bordered w-full h-32", "placeholder": "写下您的留言..."}),
        }
