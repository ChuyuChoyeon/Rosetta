from django.test import TestCase
from django.utils import translation
from blog.models import Post, Category
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


class MultilingualTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.category = Category.objects.create(
            name_zh_hans="测试分类",
            name_en="Test Category",
            name_ja="テストカテゴリ",
            name_zh_hant="測試分類",
        )
        self.post = Post.objects.create(
            title_zh_hans="中文标题",
            title_en="English Title",
            title_ja="日本語タイトル",
            title_zh_hant="繁體標題",
            content_zh_hans="中文内容",
            content_en="English Content",
            content_ja="日本語内容",
            content_zh_hant="繁體內容",
            author=self.user,
            category=self.category,
            status="published",
        )

    def test_model_translation(self):
        """Verify model fields store and retrieve correct languages"""
        post = Post.objects.get(id=self.post.id)

        # Test explicit fields
        self.assertEqual(post.title_zh_hans, "中文标题")
        self.assertEqual(post.title_en, "English Title")
        self.assertEqual(post.title_ja, "日本語タイトル")
        self.assertEqual(post.title_zh_hant, "繁體標題")

        # Test current language context
        with translation.override("en"):
            self.assertEqual(post.title, "English Title")

        with translation.override("ja"):
            self.assertEqual(post.title, "日本語タイトル")

        with translation.override("zh-hant"):
            self.assertEqual(post.title, "繁體標題")

    def test_view_translation_ja(self):
        """Verify Japanese view returns Japanese content"""
        # Ensure we get the URL for Japanese
        with translation.override("ja"):
            url = reverse("post_detail", kwargs={"slug": self.post.slug})

        # url should contain /ja/ if i18n_patterns is working
        # self.assertIn('/ja/', url)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "日本語タイトル")
        self.assertContains(response, "日本語内容")

    def test_view_translation_en(self):
        """Verify English view returns English content"""
        with translation.override("en"):
            url = reverse("post_detail", kwargs={"slug": self.post.slug})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "English Title")
        self.assertContains(response, "English Content")

    def test_fallback(self):
        """Verify fallback to default language if translation missing"""
        # Create post with only default language
        post = Post.objects.create(
            title_zh_hans="仅中文标题",
            content="内容",
            author=self.user,
            slug="only-chinese",
            status="published",
        )

        # Even in English context, accessing .title should return Chinese if English is missing
        # This depends on MODELTRANSLATION_FALLBACK_LANGUAGES setting
        with translation.override("en"):
            self.assertEqual(post.title, "仅中文标题")
