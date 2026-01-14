from django import forms
from blog.models import Post, Category, Tag, Comment
from core.models import Page, Navigation, FriendLink
from django.contrib.auth import get_user_model

User = get_user_model()


class PostForm(forms.ModelForm):
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
    class Meta:
        model = Navigation
        fields = ["title", "url", "order"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.update({"class": "input input-bordered w-full"})


class FriendLinkForm(forms.ModelForm):
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
        fields = ["username", "nickname", "email", "avatar", "is_staff", "is_active", "is_superuser"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["labels_str"].initial = ", ".join([l.name for l in self.instance.labels.all()])

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
            for name in names:
                label, _ = UserLabel.objects.get_or_create(name=name)
                labels.append(label)
            user.labels.set(labels)
        return user
