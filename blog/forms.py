from django import forms
from .models import Comment, Subscriber


class SubscriberForm(forms.ModelForm):
    """
    订阅表单
    用于用户提交邮箱进行订阅。
    """
    class Meta:
        model = Subscriber
        fields = ["email"]
        widgets = {
            "email": forms.EmailInput(
                attrs={
                    "class": "input input-bordered join-item w-full",
                    "placeholder": "输入您的邮箱地址...",
                    "required": True,
                }
            )
        }


class CommentForm(forms.ModelForm):
    """
    评论表单
    用于用户提交评论内容。
    """
    class Meta:
        model = Comment
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(
                attrs={
                    "class": "textarea textarea-bordered w-full focus:textarea-primary transition-all",
                    "placeholder": "参与讨论...",
                    "rows": 3,
                }
            )
        }
