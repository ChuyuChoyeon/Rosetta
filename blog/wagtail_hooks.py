from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet
from .models import BlogCategory

class BlogCategoryAdmin(SnippetViewSet):
    model = BlogCategory
    menu_label = '博客分类'
    menu_icon = 'folder-open-inverse'
    list_display = ('name', 'slug', 'parent')
    search_fields = ('name', 'slug')
    list_filter = ('parent',)
    ordering = ['name']

register_snippet(BlogCategoryAdmin)