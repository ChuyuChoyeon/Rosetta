from django import forms
from .models import Comment


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
