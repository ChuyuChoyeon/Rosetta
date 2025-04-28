from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet
from .models import BlogCategory

# 注意：此文件中的Django admin配置已移至wagtail_hooks.py
# 所有模型现在通过Wagtail snippets进行管理
# 请参考wagtail_hooks.py文件中的配置

