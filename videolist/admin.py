from django.contrib import admin
from unfold.admin import ModelAdmin
from import_export.admin import ImportExportModelAdmin
from unfold.contrib.import_export.forms import ImportForm, ExportForm
from django.utils.html import format_html
from import_export import resources
from .models import VideoSite,SiteView
from .resources import VideoSiteResource

class VideoSiteResource(resources.ModelResource):
    """视频站点资源类"""
    
    class Meta:
        model = VideoSite
        import_id_fields = ('id',)
        skip_unchanged = True
        report_skipped = False
        
    def before_save_instance(self, instance, row, **kwargs):
        """在保存实例前进行处理，接受file_name等额外参数"""
        # 可以添加自定义处理逻辑
        pass

@admin.register(VideoSite)
class VideoSiteAdmin(ModelAdmin, ImportExportModelAdmin):
    """视频站点管理类"""
    resource_class = VideoSiteResource
    import_form_class = ImportForm
    export_form_class = ExportForm
    
    # 列表页配置
    list_display = ('name', 'url_link','view_count','category_badge', 'update_time', 'is_invalid')
    list_filter = ('category', 'is_invalid', 'update_time')
    search_fields = ('name', 'description', 'url')
    ordering = ('-update_time',)
    list_per_page = 25
    actions = ['mark_as_valid', 'mark_as_invalid']
    date_hierarchy = 'update_time'
    
    # 详情页配置
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'url', 'category', 'view_count', 'update_time')
        }),
        ('详细描述', {
            'fields': ('description',)
        }),
        ('状态', {
            'fields': ('is_invalid',)
        }),
    )
    
    # 自定义方法
    def url_link(self, obj):
        """生成可点击链接"""
        return format_html('<a href="{}" target="_blank">{}</a>', obj.url, obj.url)
    
    url_link.short_description = '网站地址'
    
    def category_badge(self, obj):
        """生成分类徽章"""
        colors = {
            'movie': '#3b82f6',  # 蓝色
            'anime': '#a855f7',  # 紫色
        }
        color = colors.get(obj.category, '#3b82f6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 12px;">{}</span>',
            color, obj.get_category_display()
        )
    
    category_badge.short_description = '分类'
    
    # 批量操作
    def mark_as_valid(self, request, queryset):
        """将选中站点标记为有效"""
        updated = queryset.update(is_invalid=False)
        self.message_user(request, f'{updated} 个站点已被标记为有效')
    mark_as_valid.short_description = '标记为有效'
    
    def mark_as_invalid(self, request, queryset):
        """将选中站点标记为无效"""
        updated = queryset.update(is_invalid=True)
        self.message_user(request, f'{updated} 个站点已被标记为无效')
    mark_as_invalid.short_description = '标记为无效'
    
    # 改进表单保存
    def save_model(self, request, obj, form, change):
        """保存模型时记录额外信息"""
        super().save_model(request, obj, form, change)

@admin.register(SiteView)
class SiteViewAdmin(ModelAdmin):
    """站点访问记录管理类"""
    list_display = ('view_date', 'ip_address', 'user_agent')
    list_filter = ('view_date', 'ip_address')
    search_fields = ('ip_address',)
    ordering = ('-view_date',)
    list_per_page = 25