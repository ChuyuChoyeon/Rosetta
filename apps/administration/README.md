# Administration App Development Guide

本应用提供了一个高度定制的管理后台，基于 Django CBV (Class-Based Views)、Tailwind CSS 和 HTMX 构建。
为了简化开发流程，我们提取了通用的 Mixin 和 Base View。

## 目录结构

*   `views.py`: 具体业务视图实现 (Post, Category, Tag 等)。
*   `mixins.py`: 通用 Mixin (权限控制、审计日志等)。
*   `generics.py`: 通用 CRUD 基类视图 (BaseListView, BaseCreateView 等)。
*   `forms.py`: 表单定义 (使用 DaisyUI 样式)。
*   `templates/administration/`: 模板文件。

## 快速添加新模型管理

假设我们要为一个名为 `Product` 的模型添加管理功能。

### 1. 定义表单 (`forms.py`)

首先在 `apps/administration/forms.py` 中创建 ModelForm。建议继承 `StyleFormMixin` (如果存在) 或手动添加 Tailwind 样式类。

```python
from django import forms
from shop.models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "price", "description", "is_active"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 为所有字段添加 DaisyUI 样式
        for field in self.fields.values():
            field.widget.attrs.update({"class": "input input-bordered w-full"})
        self.fields["is_active"].widget.attrs.update({"class": "toggle toggle-primary"})
```

### 2. 创建视图 (`views.py`)

在 `apps/administration/views.py` 中继承通用视图。

```python
from shop.models import Product
from .forms import ProductForm
from .generics import (
    BaseListView,
    BaseCreateView,
    BaseUpdateView,
    BaseDeleteView
)

# 列表视图
class ProductListView(BaseListView):
    model = Product
    context_object_name = "products"
    ordering = ["-created_at"]
    # 搜索字段支持 (需在 get_queryset 中实现)
    
    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(name__icontains=q)
        return qs

# 创建视图
class ProductCreateView(BaseCreateView):
    model = Product
    form_class = ProductForm
    success_url = reverse_lazy("administration:product_list")

# 更新视图
class ProductUpdateView(BaseUpdateView):
    model = Product
    form_class = ProductForm
    success_url = reverse_lazy("administration:product_list")

# 删除视图
class ProductDeleteView(BaseDeleteView):
    model = Product
    success_url = reverse_lazy("administration:product_list")
```

### 3. 配置 URL (`urls.py`)

在 `apps/administration/urls.py` 中注册路由。

```python
path("products/", views.ProductListView.as_view(), name="product_list"),
path("products/create/", views.ProductCreateView.as_view(), name="product_create"),
path("products/<int:pk>/edit/", views.ProductUpdateView.as_view(), name="product_edit"),
path("products/<int:pk>/delete/", views.ProductDeleteView.as_view(), name="product_delete"),
```

### 4. 创建模板

你需要至少创建列表模板和列表行模板 (用于 HTMX)。表单通常可以使用通用的 `generic_form.html`，除非需要定制。

#### 4.1 列表模板 (`templates/administration/product_list.html`)

可以直接复制 `category_list.html` 或其他列表模板并修改。关键包含：
*   搜索栏
*   创建按钮
*   表格头
*   `{% include "administration/partials/product_list_rows.html" %}`

#### 4.2 列表行模板 (`templates/administration/partials/product_list_rows.html`)

这是 HTMX 局部刷新的关键。

```html
{% for product in products %}
<tr>
    <td>{{ product.id }}</td>
    <td>
        <div class="font-bold">{{ product.name }}</div>
    </td>
    <td>{{ product.price }}</td>
    <td>
        <!-- 状态徽章 -->
        {% if product.is_active %}
        <div class="badge badge-success gap-2">上架</div>
        {% else %}
        <div class="badge badge-ghost gap-2">下架</div>
        {% endif %}
    </td>
    <td>
        <!-- 操作按钮 -->
        <div class="flex gap-2">
            <a href="{% url 'administration:product_edit' product.pk %}" class="btn btn-square btn-sm btn-ghost">
                <span class="material-symbols-outlined">edit</span>
            </a>
            <button onclick="delete_modal_{{ product.pk }}.showModal()" class="btn btn-square btn-sm btn-ghost text-error">
                <span class="material-symbols-outlined">delete</span>
            </button>
            <!-- 包含删除确认模态框 (或使用 HTMX 删除) -->
        </div>
    </td>
</tr>
{% empty %}
<tr>
    <td colspan="5" class="text-center py-10 opacity-50">暂无数据</td>
</tr>
{% endfor %}
```

## 核心基类说明

### `BaseListView`
*   **功能**: 分页、排序、HTMX 局部刷新支持。
*   **属性**:
    *   `paginate_by`: 每页数量 (默认 20)。
    *   `template_name_suffix`: 默认 `_list`。
*   **HTMX**: 自动检测请求头，如果是 HTMX 请求则返回 `partials/{model}_list_rows.html`。

### `BaseCreateView` / `BaseUpdateView`
*   **功能**: 表单处理、成功消息、审计日志、"保存并继续"逻辑。
*   **属性**:
    *   `form_class`: 使用的 Form 类。
    *   `success_url`: 成功跳转地址。
*   **模板**: 优先查找 `{model}_form.html`，找不到则使用 `generic_form.html`。

### `BaseDeleteView`
*   **功能**: 删除确认、审计日志、HTMX 删除支持。
*   **HTMX**: 如果是 HTMX 请求，删除后返回空内容并触发 Toast 提示，实现无刷新删除。
