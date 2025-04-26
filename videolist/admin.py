from django.contrib import admin
from .models import VideoSite

@admin.register(VideoSite)
class VideoSiteAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'description', 'update_time', 'is_invalid', 'category')
    list_filter = ('is_invalid', 'update_time', 'category')
    search_fields = ('name', 'description', 'url')
    list_per_page = 20
    
    # 自定义列表显示
    def get_list_display(self, request):
        return ('name', 'url', 'description', 'update_time', 'is_invalid', 'category')
    
    # 自定义搜索字段
    def get_search_fields(self, request):
        return ('name', 'description', 'url')
    
    # 自定义过滤器
    def get_list_filter(self, request):
        return ('is_invalid', 'update_time', 'category')
    
    # 自定义只读字段
    readonly_fields = ('update_time',)
    
    # 自定义列表操作
    actions = ['mark_as_invalid', 'mark_as_valid', 'mark_as_movie', 'mark_as_anime']
    
    def mark_as_invalid(self, request, queryset):
        queryset.update(is_invalid=True)
    mark_as_invalid.short_description = "标记为失效"
    
    def mark_as_valid(self, request, queryset):
        queryset.update(is_invalid=False)
    mark_as_valid.short_description = "标记为有效"
    
    def mark_as_movie(self, request, queryset):
        queryset.update(category='movie')
    mark_as_movie.short_description = "设置为影视分类"
    
    def mark_as_anime(self, request, queryset):
        queryset.update(category='anime')
    mark_as_anime.short_description = "设置为动漫分类"
