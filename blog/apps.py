from django.apps import AppConfig


class BlogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "blog"
    verbose_name = "博客管理"

    def ready(self):
        import blog.signals

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
