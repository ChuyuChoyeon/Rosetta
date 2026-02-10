from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import translation
from blog.models import Post, Category, Comment

User = get_user_model()


class BlogPostTests(TestCase):
    def setUp(self):
        translation.activate("zh-hans")
        self.client = Client()
        self.user = User.objects.create_user(username="author", password="password")
        self.other_user = User.objects.create_user(
            username="other", password="password"
        )
        self.category = Category.objects.create(name="Test Category")

        self.public_post = Post.objects.create(
            title="Public Post",
            content="Content",
            author=self.user,
            category=self.category,
            status="published",
        )

        self.protected_post = Post(
            title="Protected Post",
            content="Secret Content",
            author=self.user,
            category=self.category,
            status="published",
        )
        self.protected_post.set_password("secretpassword")
        self.protected_post.save()

    def test_post_detail_renders_comment_user_profile_link(self):
        Comment.objects.create(
            post=self.public_post,
            user=self.user,
            content="Nice post!",
            active=True,
        )
        response = self.client.get(
            reverse("post_detail", kwargs={"slug": self.public_post.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "blog/post_detail.html")
        expected_profile_url = reverse(
            "users:user_public_profile", kwargs={"username": self.user.username}
        )
        self.assertContains(response, expected_profile_url)

    def test_public_post_access(self):
        response = self.client.get(
            reverse("post_detail", kwargs={"slug": self.public_post.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "blog/post_detail.html")

    def test_protected_post_requires_password(self):
        response = self.client.get(
            reverse("post_detail", kwargs={"slug": self.protected_post.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "blog/password_required.html")

    def test_protected_post_author_bypass(self):
        self.client.login(username="author", password="password")
        response = self.client.get(
            reverse("post_detail", kwargs={"slug": self.protected_post.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "blog/post_detail.html")

    def test_protected_post_other_user_requires_password(self):
        self.client.login(username="other", password="password")
        response = self.client.get(
            reverse("post_detail", kwargs={"slug": self.protected_post.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "blog/password_required.html")

    def test_protected_post_correct_password(self):
        response = self.client.post(
            reverse("post_detail", kwargs={"slug": self.protected_post.slug}),
            {"post_password": "secretpassword"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "blog/post_detail.html")
        self.assertContains(response, "Secret Content")

    def test_protected_post_wrong_password(self):
        response = self.client.post(
            reverse("post_detail", kwargs={"slug": self.protected_post.slug}),
            {"post_password": "wrongpassword"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "blog/password_required.html")

    def test_search_view(self):
        response = self.client.get(reverse("search") + "?q=Public")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Public Post")
        self.assertNotContains(response, "Protected Post")

    def test_delete_comment_owner(self):
        self.client.login(username="author", password="password")
        comment = Comment.objects.create(
            post=self.public_post, user=self.user, content="My comment"
        )
        delete_url = reverse("delete_comment", kwargs={"pk": comment.pk})
        response = self.client.post(delete_url, follow=True)
        self.assertFalse(Comment.objects.filter(pk=comment.pk).exists())
        self.assertContains(response, "评论已删除")

    def test_delete_comment_other_forbidden(self):
        self.client.login(username="other", password="password")
        comment = Comment.objects.create(
            post=self.public_post, user=self.user, content="My comment"
        )
        delete_url = reverse("delete_comment", kwargs={"pk": comment.pk})
        response = self.client.post(delete_url, follow=True)
        self.assertTrue(Comment.objects.filter(pk=comment.pk).exists())
        self.assertContains(response, "您没有权限删除此评论")

    def test_delete_comment_staff(self):
        User.objects.create_user(
            username="staff", password="password", is_staff=True
        )
        self.client.login(username="staff", password="password")
        comment = Comment.objects.create(
            post=self.public_post, user=self.user, content="User comment"
        )
        delete_url = reverse("delete_comment", kwargs={"pk": comment.pk})
        self.client.post(delete_url, follow=True)
        self.assertFalse(Comment.objects.filter(pk=comment.pk).exists())

    def test_comment_mentions_notification(self):
        self.client.force_login(self.user)
        # Create a comment mentioning other_user
        response = self.client.post(
            reverse("post_detail", kwargs={"slug": self.public_post.slug}),
            {"content": "Hello @other, check this out!", "post": self.public_post.id},
            follow=True,
        )

        self.assertContains(response, "您的评论已发布")
        # Check notification for other_user
        from users.models import Notification

        self.assertTrue(
            Notification.objects.filter(
                recipient=self.other_user, verb="在评论中提到了你"
            ).exists()
        )

    def test_comment_reply_notification(self):
        self.client.force_login(self.other_user)
        # Parent comment by user
        parent_comment = Comment.objects.create(
            post=self.public_post, user=self.user, content="Parent comment"
        )

        # Reply by other_user
        response = self.client.post(
            reverse("post_detail", kwargs={"slug": self.public_post.slug}),
            {
                "content": "Reply to you",
                "parent_id": parent_comment.id,
                "post": self.public_post.id,
            },
            follow=True,
        )

        self.assertContains(response, "您的评论已发布")
        # Check notification for user (author of parent comment)
        from users.models import Notification

        self.assertTrue(
            Notification.objects.filter(
                recipient=self.user, verb="回复了你的评论"
            ).exists()
        )

    def test_comment_on_locked_post_fails(self):
        self.client.force_login(self.other_user)
        response = self.client.post(
            reverse("post_detail", kwargs={"slug": self.protected_post.slug}),
            {"content": "Hacking in", "post": self.protected_post.id},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "blog/password_required.html")
        self.assertFalse(Comment.objects.filter(content="Hacking in").exists())

    def test_comment_on_unlocked_post_success(self):
        self.client.force_login(self.other_user)
        # Unlock first
        session = self.client.session
        session[f"post_unlocked_{self.protected_post.pk}"] = True
        session.save()

        response = self.client.post(
            reverse("post_detail", kwargs={"slug": self.protected_post.slug}),
            {"content": "Valid comment", "post": self.protected_post.id},
            follow=True,
        )

        self.assertContains(response, "您的评论已发布")
        self.assertTrue(Comment.objects.filter(content="Valid comment").exists())
