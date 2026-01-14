from django.test import TestCase
from django.core import mail
from django.contrib.auth import get_user_model
from blog.models import Post, Category, Subscriber

User = get_user_model()


class BlogPostSignalTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="author", password="password")
        self.category = Category.objects.create(name="Test Category")
        self.subscriber = Subscriber.objects.create(
            email="sub@example.com", is_active=True
        )

    def test_notification_sent_on_publish(self):
        # Create a published post
        post = Post.objects.create(
            title="New Post",
            content="Content",
            author=self.user,
            category=self.category,
            status="published",
        )

        # Check email sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject, f"【Rosetta Blog】新文章发布: {post.title}"
        )
        self.assertIn(post.slug, mail.outbox[0].body)

        # Check flag updated
        post.refresh_from_db()
        self.assertTrue(post.notification_sent)

    def test_no_notification_on_draft(self):
        Post.objects.create(
            title="Draft Post",
            content="Content",
            author=self.user,
            category=self.category,
            status="draft",
        )
        self.assertEqual(len(mail.outbox), 0)

    def test_no_double_notification(self):
        # Create post (sends email)
        post = Post.objects.create(
            title="First Publish",
            content="Content",
            author=self.user,
            category=self.category,
            status="published",
        )
        self.assertEqual(len(mail.outbox), 1)

        # Clear outbox
        mail.outbox = []

        # Update post
        post.title = "Updated Title"
        post.save()

        # Should not send again
        self.assertEqual(len(mail.outbox), 0)
