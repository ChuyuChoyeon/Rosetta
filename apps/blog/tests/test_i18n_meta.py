from django.test import TestCase
from django.utils import translation
from blog.models import Post
from django.contrib.auth import get_user_model
from apps.core.sitemaps import PostSitemap

User = get_user_model()


class I18nMetaTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.post = Post.objects.create(
            title="Test Post",
            content="Content",
            author=self.user,
            status="published",
            meta_title_en="English Meta Title",
            meta_title_zh_hans="中文 Meta 标题",
            meta_description_en="English Meta Desc",
            meta_description_zh_hans="中文 Meta 描述",
            meta_keywords_en="django, python",
            meta_keywords_zh_hans="django, python, 中文",
        )

    def test_meta_fields_translation(self):
        """Test that meta fields are correctly translated"""
        post = Post.objects.get(id=self.post.id)

        with translation.override("en"):
            self.assertEqual(post.meta_title, "English Meta Title")
            self.assertEqual(post.meta_description, "English Meta Desc")
            self.assertEqual(post.meta_keywords, "django, python")

        with translation.override("zh-hans"):
            self.assertEqual(post.meta_title, "中文 Meta 标题")
            self.assertEqual(post.meta_description, "中文 Meta 描述")
            self.assertEqual(post.meta_keywords, "django, python, 中文")

    def test_sitemap_i18n(self):
        """Test that sitemap class has i18n enabled"""
        sitemap = PostSitemap()
        self.assertTrue(sitemap.i18n)

        # In a real request, sitemap view would generate urls for all languages
        # Here we just verify the attribute is set correctly
