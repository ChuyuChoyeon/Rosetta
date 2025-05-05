from import_export import resources, fields
from import_export.widgets import DateTimeWidget, BooleanWidget, ForeignKeyWidget, CharWidget
from .models import VideoSite
from django.core.exceptions import ValidationError
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class CategoryWidget(CharWidget):
    """处理分类的自定义 widget，允许使用显示名称或实际值"""
    def clean(self, value, row=None, *args, **kwargs):
        if not value:
            return 'movie'  # 默认为影视分类
            
        if value in dict(VideoSite.CATEGORY_CHOICES).values():
            # 如果是显示名称，则转换为实际值
            for key, display in VideoSite.CATEGORY_CHOICES:
                if display == value:
                    return key
        return value

class VideoSiteResource(resources.ModelResource):
    # 自定义字段展示
    update_time = fields.Field(
        column_name='更新时间',
        attribute='update_time',
        widget=DateTimeWidget(format='%Y-%m-%d %H:%M:%S'),
        default=None
    )
    
    category_display = fields.Field(
        column_name='分类名称',
        attribute='get_category_display',
        readonly=True  # 只读字段，仅用于导出
    )
    
    is_invalid = fields.Field(
        column_name='是否失效',
        attribute='is_invalid',
        widget=BooleanWidget()
    )
    
    category = fields.Field(
        column_name='分类',
        attribute='category',
        widget=CategoryWidget()
    )

    class Meta:
        model = VideoSite
        fields = ('id', 'name', 'url', 'description', 'update_time', 'is_invalid', 'category', 'category_display')
        export_order = ('id', 'name', 'url', 'description', 'update_time', 'is_invalid', 'category', 'category_display')
        import_id_fields = ('name',)  # 使用名称作为唯一标识符
        skip_unchanged = True
        report_skipped = True
        use_transactions = True
        
    def before_import_row(self, row, **kwargs):
        """在导入每一行之前进行处理"""
        # 处理空值
        for key in row:
            if row[key] == '':
                row[key] = None
                
        # 处理 URL 格式
        if 'url' in row and row['url']:
            if not row['url'].startswith(('http://', 'https://')):
                row['url'] = 'https://' + row['url']
        
        # 如果没有提供名称，使用 URL 作为名称
        if 'name' in row and not row['name'] and 'url' in row and row['url']:
            domain = urlparse(row['url']).netloc
            row['name'] = domain
                
    def skip_row(self, instance, original, row, import_validation_errors=None):
        """决定是否跳过某行"""
        # 如果没有提供 URL 和名称，则跳过
        if not row.get('url') and not row.get('name'):
            return True
        return super().skip_row(instance, original, row, import_validation_errors)
        
    def before_save_instance(self, instance, using_transactions, dry_run):
        """在保存实例前执行额外验证"""
        try:
            instance.full_clean()
        except ValidationError as e:
            logger.error(f"验证错误: {e.message_dict}")
            # 记录错误但继续保存
        return super().before_save_instance(instance, using_transactions, dry_run)