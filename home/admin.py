from django.contrib import admin
from unfold.admin import ModelAdmin
from django.utils.html import format_html
from django import forms
from .models import Profile, Skill, Link, Contact

@admin.register(Profile)
class ProfileAdmin(ModelAdmin):
    list_display = ('name', 'title')
    fieldsets = (
        ('个人信息', {
            'fields': ('name', 'title', 'avatar')
        }),
        ('详细介绍', {
            'fields': ('about_me',)
        }),
    )

@admin.register(Skill)
class SkillAdmin(ModelAdmin):
    list_display = ('name', 'color', 'color_sample', 'order')
    list_filter = ('color',)
    search_fields = ('name',)
    list_editable = ('order', 'color')

    def color_sample(self, obj):
        """显示颜色样本"""
        color_map = {
            'blue': '#3b82f6',     # bg-blue-500
            'green': '#22c55e',    # bg-green-500
            'purple': '#a855f7',   # bg-purple-500
            'red': '#ef4444',      # bg-red-500
            'yellow': '#eab308',   # bg-yellow-500
            'pink': '#ec4899',     # bg-pink-500
            'indigo': '#6366f1',   # bg-indigo-500
            'gray': '#71717a',     # bg-gray-500
            'teal': '#14b8a6',     # bg-teal-500
            'orange': '#f97316',   # bg-orange-500
            'cyan': '#06b6d4',     # bg-cyan-500
            'lime': '#84cc16',     # bg-lime-500
            'amber': '#f59e0b',    # bg-amber-500
            'emerald': '#10b981',  # bg-emerald-500
            'fuchsia': '#d946ef',  # bg-fuchsia-500
            'rose': '#f43f5e',     # bg-rose-500
            'sky': '#0ea5e9',      # bg-sky-500
            'violet': '#8b5cf6',   # bg-violet-500
        }
        color = color_map.get(obj.color, '#3b82f6')
        return format_html(
            '<div style="background-color: {}; width: 30px; height: 30px; border-radius: 4px;"></div>',
            color
        )
    
    color_sample.short_description = '颜色预览'

@admin.register(Link)
class LinkAdmin(ModelAdmin):
    list_display = ('name', 'url', 'is_relative', 'username', 'icon','display_icon', 'order', 'is_navigation')
    list_filter = ('is_navigation', 'is_relative')
    search_fields = ('name', 'url', 'username')
    list_editable = ('order', 'is_navigation', 'is_relative')
    def display_icon(self, obj):
        """显示图标预览"""
        if not obj.icon:
            return '-'
        return format_html(
            '<i class="{}" style="font-size: 1.2rem;"></i>',
            obj.icon
        )
    display_icon.short_description = '图标'
    class Media:
        css = {
            'all': ['https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'],
        }

@admin.register(Contact)
class ContactAdmin(ModelAdmin):
    list_display = ('method', 'value', 'icon', 'display_icon','color', 'color_sample', 'order')
    list_editable = ('order', 'color')
    search_fields = ('method', 'value')

    def color_sample(self, obj):
        """显示颜色样本"""
        return format_html(
            '<div style="background-color: {}; width: 30px; height: 30px; border-radius: 4px;"></div>',
            self.get_tailwind_color(obj.color)
        )
    def display_icon(self, obj):
        """显示图标预览"""
        if not obj.icon:
            return '-'
        return format_html(
            '<i class="{}" style="font-size: 1.2rem;"></i>',
            obj.icon
        )
    display_icon.short_description = '图标'
    
    def get_tailwind_color(self, color_name):
        """将Tailwind颜色名称转换为对应的HEX值"""
        color_map = {
            'blue': '#3b82f6',     # bg-blue-500
            'red': '#ef4444',      # bg-red-500
            'green': '#22c55e',    # bg-green-500
            'yellow': '#eab308',   # bg-yellow-500
            'purple': '#a855f7',   # bg-purple-500
            'pink': '#ec4899',     # bg-pink-500
            'indigo': '#6366f1',   # bg-indigo-500
            'gray': '#71717a',     # bg-gray-500
            'teal': '#14b8a6',     # bg-teal-500
            'orange': '#f97316',   # bg-orange-500
            'cyan': '#06b6d4',     # bg-cyan-500
            'lime': '#84cc16',     # bg-lime-500
            'amber': '#f59e0b',    # bg-amber-500
            'emerald': '#10b981',  # bg-emerald-500
            'fuchsia': '#d946ef',  # bg-fuchsia-500
            'rose': '#f43f5e',     # bg-rose-500
            'sky': '#0ea5e9',      # bg-sky-500
            'violet': '#8b5cf6',   # bg-violet-500
        }
        return color_map.get(color_name, '#3b82f6')  # 默认返回蓝色
    
    color_sample.short_description = '颜色预览'
    class Media:
        css = {
            'all': ['https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'],
        }

