from django import forms
from blog.models import Post, Category, Tag, Comment
from core.models import Page, Navigation, FriendLink, SearchPlaceholder
from users.models import UserTitle
from django.contrib.auth import get_user_model

User = get_user_model()


class UserTitleForm(forms.ModelForm):
    """
    用户称号表单
    """
    class Meta:
        model = UserTitle
        fields = ["name", "color", "icon", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "color": forms.Select(attrs={"class": "select select-bordered w-full"}),
            "icon": forms.Textarea(attrs={"class": "textarea textarea-bordered w-full h-24 font-mono text-xs", "placeholder": "<svg...>"}),
            "description": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
        }


class PostForm(forms.ModelForm):
    """
    文章表单
    
    用于创建和编辑文章。
    支持：
    - 基本信息 (标题, slug, 封面图)
    - 内容编辑 (内容, 摘要)
    - 元数据 (状态, 分类, 标签, 密码保护)
    
    样式：
    - 使用 Tailwind CSS 类美化表单控件。
    - Textarea 默认行数为 20。
    """
    tags_str = forms.CharField(
        required=False, 
        widget=forms.HiddenInput, 
        label="标签"
    )

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
            "password",
            "is_pinned",
            "allow_comments",
        ]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 20}),
            "excerpt": forms.Textarea(attrs={"rows": 3}),
            "cover_image": forms.FileInput(attrs={"class": "file-input file-input-bordered w-full"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["tags_str"].initial = ",".join([t.name for t in self.instance.tags.all()])
        self.apply_styles()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply styles to all fields
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({"class": "toggle toggle-success"})
            elif isinstance(field.widget, (forms.ClearableFileInput, forms.FileInput)):
                field.widget.attrs.update({"class": "file-input file-input-bordered w-full"})
            elif isinstance(field.widget, forms.CheckboxSelectMultiple):
                pass # CheckboxSelectMultiple needs special handling in template or custom widget
            else:
                field.widget.attrs.update({"class": "input input-bordered w-full"})
                
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({"class": "textarea textarea-bordered w-full"})
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update({"class": "select select-bordered w-full"})

    def save(self, commit=True):
        post = super().save(commit=False)
        
        # 密码哈希处理
        if 'password' in self.changed_data and post.password:
            # 如果密码字段已更改且不为空，则进行哈希
            # 注意：如果 PostForm 传递的是 raw password
            from django.contrib.auth.hashers import make_password
            if not post.password.startswith('pbkdf2_'): # 简单检查是否已哈希，防止重复哈希
                post.set_password(post.password)

        if commit:
            post.save()
            # 处理标签 (Handle tags)
            tags_str = self.cleaned_data.get("tags_str", "")
            if tags_str:
                tag_names = [t.strip() for t in tags_str.split(",") if t.strip()]
                tags = []
                for name in tag_names:
                    # 创建或获取标签
                    try:
                        tag, created = Tag.objects.get_or_create(name=name)
                    except Exception:
                        # 处理潜在的 slug 冲突或其他错误
                        # 如果名称相同但创建失败（例如 slug 冲突），尝试通过 slug 查找
                        from django.utils.text import slugify
                        slug = slugify(name)
                        tag = Tag.objects.filter(slug=slug).first()
                        if not tag:
                            # 如果 slug 冲突但名称不同，尝试添加随机后缀
                            import uuid
                            slug = f"{slug}-{uuid.uuid4().hex[:6]}"
                            tag = Tag.objects.create(name=name, slug=slug)
                    
                    if tag:
                        tags.append(tag)
                post.tags.set(tags)
            else:
                post.tags.clear()
        return post

    def apply_styles(self):
        """
        应用 Tailwind CSS 样式到表单字段
        
        遍历所有字段，根据控件类型添加相应的 daisyUI/Tailwind 类名。
        - Checkbox: checkbox checkbox-primary
        - FileInput: file-input ...
        - Textarea: textarea ...
        - Select: select ...
        - 其他: input ...
        """
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
    
    用于管理文章分类。
    """
    class Meta:
        model = Category
        fields = ["name", "slug", "description", "icon", "color"]

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
    
    用于管理文章标签。
    包含颜色选择和激活状态控制。
    """
    class Meta:
        model = Tag
        fields = ["name", "slug", "color", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({"class": "toggle toggle-success"})
            else:
                field.widget.attrs.update({"class": "input input-bordered w-full"})
            
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update({"class": "select select-bordered w-full"})


class PageForm(forms.ModelForm):
    """
    单页面表单
    
    用于管理独立页面（如关于、联系）。
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
    
    用于管理前台导航栏链接。
    """
    class Meta:
        model = Navigation
        fields = ["title", "url", "location", "order", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({"class": "toggle toggle-success"})
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({"class": "select select-bordered w-full"})
            else:
                field.widget.attrs.update({"class": "input input-bordered w-full"})


class SearchPlaceholderForm(forms.ModelForm):
    """
    搜索占位符表单
    """
    class Meta:
        model = SearchPlaceholder
        fields = ["text", "order", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({"class": "toggle toggle-success"})
            else:
                field.widget.attrs.update({"class": "input input-bordered w-full"})


class FriendLinkForm(forms.ModelForm):
    """
    友情链接表单
    
    用于管理友情链接展示。
    """
    class Meta:
        model = FriendLink
        fields = ["name", "url", "description", "logo", "order", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({"class": "toggle toggle-success"})
            elif isinstance(field.widget, (forms.ClearableFileInput, forms.FileInput)):
                field.widget.attrs.update(
                    {"class": "file-input file-input-bordered w-full"}
                )
            else:
                field.widget.attrs.update({"class": "input input-bordered w-full"})


from django.contrib.auth.models import Group

class GroupForm(forms.ModelForm):
    """
    用户组表单
    """
    class Meta:
        model = Group
        fields = ["name", "permissions"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "permissions": forms.SelectMultiple(attrs={"class": "select select-bordered w-full h-64"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 可以在这里优化 permissions 的显示，例如分组显示


class UserForm(forms.ModelForm):
    """
    用户表单
    
    用于管理员管理用户信息。
    支持：
    - 修改基本信息 (昵称, 邮箱, 头像等)
    - 权限管理 (管理员, 激活状态, 超级用户)
    - 密码重置 (可选)
    - 标签管理 (通过逗号分隔的字符串输入)
    """
    new_password = forms.CharField(
        required=False, 
        widget=forms.PasswordInput(attrs={"class": "input input-bordered w-full"}), 
        label="新密码",
        help_text="如需修改密码请在此输入，否则留空"
    )
    
    class Meta:
        model = User
        fields = [
            "username", 
            "nickname", 
            "email", 
            "password", 
            "avatar", 
            "cover_image", 
            "bio", 
            "website", 
            "github",
            "title",
            "is_active",
            "is_banned",
            "is_staff",
            "is_superuser",
            "groups",
            "user_permissions"
        ]
        widgets = {
            "username": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "nickname": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "email": forms.EmailInput(attrs={"class": "input input-bordered w-full"}),
            "title": forms.Select(attrs={"class": "select select-bordered w-full"}),
            "avatar": forms.FileInput(attrs={"class": "file-input file-input-bordered w-full"}),
            "bio": forms.Textarea(attrs={"class": "textarea textarea-bordered w-full h-24", "rows": 3}),
            "groups": forms.CheckboxSelectMultiple(),
            "user_permissions": forms.SelectMultiple(attrs={"class": "select select-bordered w-full h-48"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply styles to all fields
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({"class": "toggle toggle-success"})
            elif isinstance(field.widget, (forms.ClearableFileInput, forms.FileInput)):
                field.widget.attrs.update({"class": "file-input file-input-bordered w-full"})
            elif isinstance(field.widget, forms.CheckboxSelectMultiple):
                pass # CheckboxSelectMultiple needs special handling in template or custom widget
            else:
                field.widget.attrs.update({"class": "input input-bordered w-full"})
                
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({"class": "textarea textarea-bordered w-full"})
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update({"class": "select select-bordered w-full"})

    def save(self, commit=True):
        user = super().save(commit=False)
        
        # 处理密码
        # 如果提供了新密码，则使用 set_password 加密存储
        new_password = self.cleaned_data.get("new_password")
        if new_password:
            user.set_password(new_password)
            
        if commit:
            user.save()
            
        return user
