from django.apps import AppConfig


class BlogConfig(AppConfig):
    """
    博客应用配置

    Blog 应用是系统的核心内容管理模块，负责处理文章、分类、标签和评论等功能。
    在此配置类中，我们还注册了 django-watson 搜索适配器，以支持全文搜索。
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "blog"
    verbose_name = "博客管理"

    def ready(self):
        """
        应用启动时的初始化操作

        主要用于注册 Watson 搜索引擎的模型索引。
        """
        try:
            from watson import search as watson
            from watson.search import RegistrationError
            from .models import Post

            try:
                watson.register(
                    Post,
                    fields=(
                        "title",
                        "content",
                        "excerpt",
                        "category__name",
                        "tags__name",
                    ),
                )
            except RegistrationError:
                pass
        except ImportError:
            pass
