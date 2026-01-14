from django.test import TestCase
from django.core.management import call_command
from io import StringIO
from django.contrib.auth import get_user_model
from blog.models import Category, Post, Comment

User = get_user_model()


class GenerateMockDataTest(TestCase):
    def test_generate_mock_data(self):
        out = StringIO()
        call_command(
            "generate_mock_data", users=2, categories=2, posts=2, comments=2, stdout=out
        )

        self.assertIn("mock 数据已生成", out.getvalue())

        # Exclude AnonymousUser if present (from guardian)
        user_count = User.objects.exclude(username="AnonymousUser").count()
        self.assertEqual(user_count, 2)
        self.assertEqual(Category.objects.count(), 2)
        self.assertEqual(Post.objects.count(), 2)
        self.assertEqual(Comment.objects.count(), 2)

    def test_generate_mock_data_empty(self):
        out = StringIO()
        call_command(
            "generate_mock_data", users=0, categories=0, posts=0, comments=0, stdout=out
        )
        user_count = User.objects.exclude(username="AnonymousUser").count()
        self.assertEqual(user_count, 0)
        self.assertEqual(Category.objects.count(), 0)
