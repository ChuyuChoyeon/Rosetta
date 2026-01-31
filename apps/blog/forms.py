from django import forms
from .models import Comment


class CommentForm(forms.ModelForm):
    """
    评论表单
    
    用于前台用户提交评论。
    包含前端样式类 (Tailwind CSS) 和基本的长度验证。
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
                    "maxlength": "2000",  # 前端限制
                }
            )
        }

    def clean_content(self):
        """
        验证评论内容长度
        """
        content = self.cleaned_data.get("content")
        if len(content) > 2000:
            raise forms.ValidationError("评论内容过长，请控制在 2000 字以内。")
        return content
