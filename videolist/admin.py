from django.contrib import admin
from unfold.admin import ModelAdmin
from import_export.admin import ImportExportModelAdmin
from unfold.contrib.import_export.forms import ImportForm, ExportForm
from import_export import resources
from .models import VideoSite

class VideoSiteResource(resources.ModelResource):
    """VideoSite 的导入导出资源配置"""
    class Meta:
        model = VideoSite
        import_id_fields = ('id',)
        fields = ('id', 'name', 'url', 'description', 'is_invalid', 'category')
        export_order = fields

@admin.register(VideoSite)
class VideoSiteAdmin(ModelAdmin, ImportExportModelAdmin):
    """VideoSite 的管理界面配置"""
    resource_class = VideoSiteResource
    import_form_class = ImportForm
    export_form_class = ExportForm
    
    # 列表页配置
    list_display = ('name', 'url', 'category', 'update_time', 'is_invalid')
    list_filter = ('category', 'is_invalid', 'update_time')
    search_fields = ('name', 'description', 'url')
    ordering = ('-update_time',)
    
    # 详情页配置
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'url', 'category')
        }),
        ('详细描述', {
            'fields': ('description',)
        }),
        ('状态', {
            'fields': ('is_invalid',)
        }),
    )
