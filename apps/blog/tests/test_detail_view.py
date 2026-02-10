import pytest
from django.urls import reverse
from blog.models import Post, Category, Tag
from users.models import User
from django.core.cache import cache


@pytest.mark.django_db
class TestPostDetailView:
    @pytest.fixture(autouse=True)
    def setup(self, client):
        self.client = client
        self.user = User.objects.create_user(username="reader", password="password")
        self.staff = User.objects.create_user(
            username="staff", password="password", is_staff=True
        )
        self.superuser = User.objects.create_superuser(
            username="admin", password="password"
        )

        self.category = Category.objects.create(name="Python", slug="python")
        self.tag_django = Tag.objects.create(name="Django", slug="django")
        self.tag_web = Tag.objects.create(name="Web", slug="web")

        self.post = Post.objects.create(
            title="Main Post",
            slug="main-post",
            content="# Heading\n\nContent here.",
            author=self.superuser,
            category=self.category,
            status="published",
        )
        self.post.tags.add(self.tag_django)
        self.url = reverse("post_detail", kwargs={"slug": self.post.slug})

    def test_draft_access(self):
        """Test draft access for different user types"""
        draft_post = Post.objects.create(
            title="Draft Post",
            slug="draft-post",
            content="Draft",
            author=self.superuser,
            status="draft",
        )
        url = reverse("post_detail", kwargs={"slug": draft_post.slug})

        # Anonymous -> 404
        response = self.client.get(url)
        assert response.status_code == 404

        # Regular User -> 404
        self.client.force_login(self.user)
        response = self.client.get(url)
        assert response.status_code == 404

        # Staff -> 200
        self.client.force_login(self.staff)
        response = self.client.get(url)
        assert response.status_code == 200

        # Superuser -> 200
        self.client.force_login(self.superuser)
        response = self.client.get(url)
        assert response.status_code == 200

    def test_related_posts_by_tags(self):
        """Test related posts logic based on shared tags"""
        # Post 1: Same tag (Django)
        related1 = Post.objects.create(
            title="Related 1",
            slug="related-1",
            content="Content",
            author=self.superuser,
            status="published",
        )
        related1.tags.add(self.tag_django)

        # Post 2: No tags
        unrelated = Post.objects.create(
            title="Unrelated",
            slug="unrelated",
            content="Content",
            author=self.superuser,
            status="published",
        )

        cache.clear()  # Clear sidebar/related cache
        response = self.client.get(self.url)
        assert response.status_code == 200

        related_posts = response.context["related_posts"]
        assert related1 in related_posts
        assert unrelated not in related_posts

    def test_related_posts_fallback_category(self):
        """Test related posts fallback to category if not enough tag matches"""
        # Current post has tag "Django" and category "Python"

        # Post 1: Same Category, No Tags
        cat_post = Post.objects.create(
            title="Category Post",
            slug="cat-post",
            content="Content",
            author=self.superuser,
            category=self.category,
            status="published",
        )

        cache.clear()
        response = self.client.get(self.url)
        related_posts = response.context["related_posts"]

        # Should be included because we need 3, and we have 0 tag matches
        assert cat_post in related_posts

    def test_meta_description_generation(self):
        """Test meta description generation logic"""
        # 1. Explicit meta_description
        self.post.meta_description = "Explicit Meta"
        self.post.save()
        cache.clear()

        response = self.client.get(self.url)
        assert "Explicit Meta" in str(response.context["meta"].description)

        # 2. Excerpt
        self.post.meta_description = ""
        self.post.excerpt = "Excerpt Meta"
        self.post.save()
        cache.clear()

        response = self.client.get(self.url)
        assert "Excerpt Meta" in str(response.context["meta"].description)

        # 3. Content Auto-generation
        self.post.excerpt = ""
        self.post.content = "# Hello\n\nThis is **bold** text."
        self.post.save()
        cache.clear()

        response = self.client.get(self.url)
        # Should strip markdown: "Hello\n\nThis is bold text."
        desc = response.context["meta"].description
        assert "Hello" in desc
        assert "bold" in desc
        assert "**" not in desc

    def test_password_protection_plain(self):
        """Test plain text password protection"""
        self.post.password = "simplepass"
        self.post.save()

        # 1. Access without password
        response = self.client.get(self.url)
        assert "blog/password_required.html" in [t.name for t in response.templates]

        # 2. Wrong password
        response = self.client.post(self.url, {"post_password": "wrong"})
        assert "blog/password_required.html" in [t.name for t in response.templates]

        # 3. Correct password
        response = self.client.post(self.url, {"post_password": "simplepass"})
        assert response.status_code == 302  # Redirect to self
        assert response.url == self.url

        # 4. Access after unlock
        response = self.client.get(self.url)
        assert "blog/post_detail.html" in [t.name for t in response.templates]

    def test_comment_submission_error(self):
        """Test comment submission error handling"""
        self.client.force_login(self.user)

        # Invalid form (empty content)
        response = self.client.post(self.url, {"content": ""})
        assert response.status_code == 200
        assert "comment_form" in response.context
        assert response.context["comment_form"].errors
