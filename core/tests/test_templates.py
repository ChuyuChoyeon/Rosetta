from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.conf import settings
from core.models import FriendLink, Notification, Page, Navigation
from blog.models import Post, Category, Comment, Tag

User = get_user_model()


class TemplateRenderTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create user
        cls.user = User.objects.create_user(
            username="testuser", password="password123", email="test@example.com"
        )
        cls.admin_user = User.objects.create_superuser(
            username="admin", password="password123", email="admin@example.com"
        )

        # Create category and tag
        cls.category = Category.objects.create(
            name="Test Category", slug="test-category"
        )
        cls.tag = Tag.objects.create(name="Test Tag", slug="test-tag")

        # Create post
        cls.post = Post.objects.create(
            title="Test Post",
            slug="test-post",
            content="Test content",
            author=cls.user,
            category=cls.category,
            status="published",
        )
        cls.post.tags.add(cls.tag)

        # Create page
        cls.page = Page.objects.create(
            title="Test Page",
            slug="test-page",
            content="Page content",
            status="published",
        )

        # Create comment
        cls.comment = Comment.objects.create(
            post=cls.post, user=cls.user, content="Test comment"
        )

        # Create notification
        cls.notification = Notification.objects.create(
            user=cls.user,
            title="Test Notification",
            message="notified you",
            level="info",
        )

        # Create FriendLink
        cls.friendlink = FriendLink.objects.create(
            name="Test Link", url="https://example.com", description="Test Description"
        )

        # Create Navigation
        cls.navigation = Navigation.objects.create(
            title="Test Nav", url="/test/", order=1
        )

    def check_url(self, url_name, kwargs=None, status_code=200, user=None):
        if user:
            self.client.force_login(user)
        else:
            self.client.logout()

        url = reverse(url_name, kwargs=kwargs)
        response = self.client.get(url)

        # Handle redirects (e.g., login required)
        if response.status_code == 302 and status_code == 200:
            # Follow redirect to check final page if needed, or just accept redirect
            # For login required pages, we expect 302 if not logged in
            if not user and "/users/login/" in response.url:
                return  # Expected redirect

        self.assertEqual(
            response.status_code,
            status_code,
            f"URL: {url} returned {response.status_code}, expected {status_code}",
        )
        return response

    # --- Core / Blog URLs ---
    def test_home(self):
        self.check_url("home")

    def test_post_list(self):
        self.check_url("post_list")

    def test_post_detail(self):
        self.check_url("post_detail", kwargs={"slug": self.post.slug})

    def test_category_list(self):
        self.check_url("category_list")

    def test_post_by_category(self):
        self.check_url("post_by_category", kwargs={"slug": self.category.slug})

    def test_search(self):
        response = self.client.get(reverse("search") + "?q=test")
        self.assertEqual(response.status_code, 200)

    def test_about(self):
        # 'about' is defined in core/urls.py pointing to PageView with slug='about'
        # We need to create the 'about' page first or expect 404 if not present.
        # But we can create it in setUpTestData if we want to test success.
        # Let's create it dynamically here or check if it exists.
        if not Page.objects.filter(slug="about").exists():
            Page.objects.create(
                title="About", slug="about", content="About Content", status="published"
            )
        self.check_url("about")

    # --- Users URLs ---
    def test_login(self):
        self.check_url("users:login")

    def test_register(self):
        self.check_url("users:register")

    def test_profile(self):
        self.check_url("users:profile", user=self.user)

    def test_user_public_profile(self):
        self.check_url(
            "users:user_public_profile", kwargs={"username": self.user.username}
        )

    def test_password_change(self):
        self.check_url("users:password_change", user=self.user)

    # --- Administration URLs ---
    def test_admin_index(self):
        self.check_url("administration:index", user=self.admin_user)

    def test_admin_post_list(self):
        self.check_url("administration:post_list", user=self.admin_user)

    def test_admin_post_create(self):
        self.check_url("administration:post_create", user=self.admin_user)

    def test_admin_post_edit(self):
        self.check_url(
            "administration:post_edit",
            kwargs={"pk": self.post.pk},
            user=self.admin_user,
        )

    def test_admin_post_delete(self):
        self.check_url(
            "administration:post_delete",
            kwargs={"pk": self.post.pk},
            user=self.admin_user,
        )

    def test_admin_category_list(self):
        self.check_url("administration:category_list", user=self.admin_user)

    def test_admin_category_edit(self):
        self.check_url(
            "administration:category_edit",
            kwargs={"pk": self.category.pk},
            user=self.admin_user,
        )

    def test_admin_category_delete(self):
        self.check_url(
            "administration:category_delete",
            kwargs={"pk": self.category.pk},
            user=self.admin_user,
        )

    def test_admin_tag_list(self):
        self.check_url("administration:tag_list", user=self.admin_user)

    def test_admin_tag_edit(self):
        self.check_url(
            "administration:tag_edit", kwargs={"pk": self.tag.pk}, user=self.admin_user
        )

    def test_admin_tag_delete(self):
        self.check_url(
            "administration:tag_delete",
            kwargs={"pk": self.tag.pk},
            user=self.admin_user,
        )

    def test_admin_comment_list(self):
        self.check_url("administration:comment_list", user=self.admin_user)

    def test_admin_comment_edit(self):
        self.check_url(
            "administration:comment_edit",
            kwargs={"pk": self.comment.pk},
            user=self.admin_user,
        )

    def test_admin_comment_delete(self):
        self.check_url(
            "administration:comment_delete",
            kwargs={"pk": self.comment.pk},
            user=self.admin_user,
        )

    def test_admin_user_list(self):
        self.check_url("administration:user_list", user=self.admin_user)

    def test_admin_user_edit(self):
        self.check_url(
            "administration:user_edit",
            kwargs={"pk": self.user.pk},
            user=self.admin_user,
        )

    def test_admin_page_list(self):
        self.check_url("administration:page_list", user=self.admin_user)

    def test_admin_page_create(self):
        self.check_url("administration:page_create", user=self.admin_user)

    def test_admin_page_edit(self):
        self.check_url(
            "administration:page_edit",
            kwargs={"pk": self.page.pk},
            user=self.admin_user,
        )

    def test_admin_page_delete(self):
        self.check_url(
            "administration:page_delete",
            kwargs={"pk": self.page.pk},
            user=self.admin_user,
        )

    def test_admin_friendlink_list(self):
        self.check_url("administration:friendlink_list", user=self.admin_user)

    def test_admin_friendlink_create(self):
        self.check_url("administration:friendlink_create", user=self.admin_user)

    def test_admin_friendlink_edit(self):
        self.check_url(
            "administration:friendlink_edit",
            kwargs={"pk": self.friendlink.pk},
            user=self.admin_user,
        )

    def test_admin_friendlink_delete(self):
        self.check_url(
            "administration:friendlink_delete",
            kwargs={"pk": self.friendlink.pk},
            user=self.admin_user,
        )

    def test_admin_navigation_list(self):
        self.check_url("administration:navigation_list", user=self.admin_user)

    def test_admin_navigation_create(self):
        self.check_url("administration:navigation_create", user=self.admin_user)

    def test_admin_navigation_edit(self):
        self.check_url(
            "administration:navigation_edit",
            kwargs={"pk": self.navigation.pk},
            user=self.admin_user,
        )

    def test_admin_navigation_delete(self):
        self.check_url(
            "administration:navigation_delete",
            kwargs={"pk": self.navigation.pk},
            user=self.admin_user,
        )

    def test_admin_settings(self):
        self.check_url("administration:settings", user=self.admin_user)
