from django import forms
from blog.models import Post, Category, Tag, Comment
from core.models import Page, Navigation, FriendLink
from django.contrib.auth import get_user_model

User = get_user_model()


class PostForm(forms.ModelForm):
    """
    文章表单
    用于创建和编辑文章。
    """
    class Meta:
        model = Post
        fields = [
            "title",
            "slug",
            "cover_image",
            "content",
            "excerpt",
            "status",
            "category",
            "tags",
            "password",
        ]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 20}),
            "excerpt": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()

    def apply_styles(self):
        """应用 Tailwind CSS 样式到表单字段"""
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({"class": "checkbox checkbox-primary"})
            elif isinstance(field.widget, (forms.ClearableFileInput, forms.FileInput)):
                field.widget.attrs.update(
                    {"class": "file-input file-input-bordered w-full"}
                )
            else:
                field.widget.attrs.update({"class": "input input-bordered w-full"})
                if isinstance(field.widget, forms.Textarea):
                    field.widget.attrs.update(
                        {"class": "textarea textarea-bordered w-full"}
                    )
                if isinstance(field.widget, forms.Select):
                    field.widget.attrs.update(
                        {"class": "select select-bordered w-full"}
                    )


class CategoryForm(forms.ModelForm):
    """
    分类表单
    """
    class Meta:
        model = Category
        fields = ["name", "slug", "description"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.update({"class": "input input-bordered w-full"})
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update(
                    {"class": "textarea textarea-bordered w-full"}
                )


class TagForm(forms.ModelForm):
    """
    标签表单
    """
    class Meta:
        model = Tag
        fields = ["name", "slug", "color", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({"class": "checkbox checkbox-primary"})
            else:
                field.widget.attrs.update({"class": "input input-bordered w-full"})
            
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update({"class": "select select-bordered w-full"})


class PageForm(forms.ModelForm):
    """
    单页面表单
    """
    class Meta:
        model = Page
        fields = ["title", "slug", "content", "status"]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 20}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.update({"class": "input input-bordered w-full"})
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update(
                    {"class": "textarea textarea-bordered w-full"}
                )
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update({"class": "select select-bordered w-full"})


class NavigationForm(forms.ModelForm):
    """
    导航菜单表单
    """
    class Meta:
        model = Navigation
        fields = ["title", "url", "order"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.update({"class": "input input-bordered w-full"})


class FriendLinkForm(forms.ModelForm):
    """
    友链表单
    """
    class Meta:
        model = FriendLink
        fields = ["name", "url", "description", "logo", "order", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({"class": "checkbox checkbox-primary"})
            elif isinstance(field.widget, (forms.ClearableFileInput, forms.FileInput)):
                field.widget.attrs.update(
                    {"class": "file-input file-input-bordered w-full"}
                )
            else:
                field.widget.attrs.update({"class": "input input-bordered w-full"})


class UserForm(forms.ModelForm):
    """
    用户表单
    支持修改基本信息、密码和标签。
    """
    new_password = forms.CharField(
        required=False, 
        widget=forms.PasswordInput(attrs={"class": "input input-bordered w-full"}), 
        label="新密码",
        help_text="如需修改密码请在此输入，否则留空"
    )
    labels_str = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={"class": "input input-bordered w-full", "placeholder": "VIP, 作者"}), 
        label="用户标签",
        help_text="使用逗号分隔多个标签"
    )

    class Meta:
        model = User
        fields = ["username", "nickname", "email", "avatar", "cover_image", "is_staff", "is_active", "is_superuser"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["labels_str"].initial = ", ".join([l.name for l in self.instance.labels.all()])
        else:
            self.fields["new_password"].required = True
            self.fields["new_password"].help_text = "创建新用户必须设置密码"

        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({"class": "checkbox checkbox-primary"})
            elif isinstance(field.widget, (forms.ClearableFileInput, forms.FileInput)):
                field.widget.attrs.update(
                    {"class": "file-input file-input-bordered w-full"}
                )
            elif isinstance(field.widget, forms.SelectMultiple):
                field.widget.attrs.update({"class": "select select-bordered w-full h-auto py-2"})
            elif name != "new_password" and name != "labels_str": # Skip manually styled fields
                 field.widget.attrs.update({"class": "input input-bordered w-full"})

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data.get("new_password"):
            user.set_password(self.cleaned_data["new_password"])
        
        if commit:
            user.save()
            # Handle labels
            labels_str = self.cleaned_data.get("labels_str", "")
            names = [n.strip() for n in labels_str.split(",") if n.strip()]
            labels = []
            from users.models import UserLabel
            for name in names:
                label, _ = UserLabel.objects.get_or_create(name=name)
                labels.append(label)
            user.labels.set(labels)
        return user
