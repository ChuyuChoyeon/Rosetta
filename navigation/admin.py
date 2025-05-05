from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm
from .models import NavigationItem

@admin.register(NavigationItem)
class NavigationItemAdmin(ModelAdmin):
    list_display = ('title', 'url_link', 'display_icon', 'order', 'is_active', 'parent_name')
    list_filter = ('is_active', 'target_blank')
    list_editable = ('order', 'is_active')
    search_fields = ('title', 'url')
    
    fieldsets = (
        ('基本信息', {
            'fields': ('title', 'url', 'icon')
        }),
        ('显示选项', {
            'fields': ('order', 'is_active', 'target_blank')
        }),
        ('层级关系', {
            'fields': ('parent',)
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # 防止将自身选为父级
        if obj:
            form.base_fields['parent'].queryset = NavigationItem.objects.exclude(pk=obj.pk)
        return form
    
    def url_link(self, obj):
        """显示可点击的链接"""
        return format_html(
            '<a href="{}" target="_blank" style="color: #3b82f6;">{}</a>',
            obj.url, obj.url
        )
    url_link.short_description = '链接'
    
    def display_icon(self, obj):
        """显示图标预览"""
        if not obj.icon:
            return '-'
        return format_html(
            '<i class="{}" style="font-size: 1.2rem;"></i>',
            obj.icon
        )
    display_icon.short_description = '图标'
    
    def parent_name(self, obj):
        """显示父级菜单名称"""
        if obj.parent:
            return obj.parent.title
        return '-'
    parent_name.short_description = '父级菜单'
    
    class Media:
        css = {
            'all': ['https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'],
        }
