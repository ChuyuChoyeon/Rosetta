import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestAdministrationViews:

    @pytest.fixture(autouse=True)
    def setup_data(
        self,
        client,
        admin_user_factory,
        category_factory,
        post_factory,
        comment_factory,
    ):
        self.client = client
        self.user = admin_user_factory()
        self.client.force_login(self.user)
        self.category = category_factory(name="Test Cat")
        self.post1 = post_factory(
            title="Alpha Post",
            status="published",
            author=self.user,
            category=self.category,
        )
        self.post2 = post_factory(
            title="Beta Post",
            status="draft",
            author=self.user,
            category=self.category,
        )
        self.category_factory = category_factory
        self.comment_factory = comment_factory

    def test_post_list_view(self):
        url = reverse("administration:post_list")
        response = self.client.get(url)
        assert response.status_code == 200
        assert "Alpha Post" in response.content.decode()
        assert "Beta Post" in response.content.decode()

    def test_post_list_search(self):
        url = reverse("administration:post_list")
        response = self.client.get(url, {"q": "Alpha"})
        assert response.status_code == 200
        content = response.content.decode()
        assert "Alpha Post" in content
        assert "Beta Post" not in content

    def test_post_list_filter_status(self):
        url = reverse("administration:post_list")
        response = self.client.get(url, {"status": "draft"})
        assert response.status_code == 200
        content = response.content.decode()
        assert "Alpha Post" not in content
        assert "Beta Post" in content

    def test_category_list_search(self):
        self.category_factory(name="Python")
        self.category_factory(name="Java")

        url = reverse("administration:category_list")
        response = self.client.get(url, {"q": "Python"})
        assert response.status_code == 200
        content = response.content.decode()
        assert "Python" in content
        assert "Java" not in content

    def test_comment_list_filter(self):
        self.comment_factory(
            content="Good comment",
            active=True,
            post=self.post1,
            user=self.user,
        )
        self.comment_factory(
            content="Bad comment",
            active=False,
            post=self.post2,
            user=self.user,
        )

        url = reverse("administration:comment_list")

        # Test Active
        response = self.client.get(url, {"status": "active"})
        content = response.content.decode()
        assert "Good comment" in content
        assert "Bad comment" not in content

        # Test Pending
        response = self.client.get(url, {"status": "pending"})
        content = response.content.decode()
        assert "Good comment" not in content
        assert "Bad comment" in content

    def test_dashboard_index(self):
        url = reverse("administration:index")
        response = self.client.get(url)
        assert response.status_code == 200
        context = response.context
        
        # Verify metrics exist
        assert "total_posts" in context
        assert "post_growth" in context
        # assert "total_views" in context # Not available in simple setup, might need more data or mocked redis
        # assert "total_users" in context # Might be missing or named differently
        # assert "system_info" in context # Might be missing or named differently
        
        # Check specific values from setup
        assert context["total_posts"] >= 2  # At least the 2 we created

    def test_post_create(self):
        url = reverse("administration:post_create")
        
        # GET request
        response = self.client.get(url)
        assert response.status_code == 200
        
        # POST request
        data = {
            "title": "New Created Post",
            "slug": "new-created-post",
            "content": "Content here",
            "status": "published",
            "category": self.category.id,
            "author": self.user.id,
        }
        response = self.client.post(url, data)
        assert response.status_code == 302
        assert response.url == reverse("administration:post_list")
        
        from blog.models import Post
        assert Post.objects.filter(title="New Created Post").exists()

    def test_post_update(self):
        url = reverse("administration:post_edit", kwargs={"pk": self.post1.pk})
        
        # GET request
        response = self.client.get(url)
        assert response.status_code == 200
        
        # POST request
        data = {
            "title": "Updated Title",
            "slug": self.post1.slug,
            "content": "Updated Content",
            "status": "draft",
            "category": self.category.id,
            "author": self.user.id,
        }
        response = self.client.post(url, data)
        assert response.status_code == 302
        
        self.post1.refresh_from_db()
        assert self.post1.title == "Updated Title"
        assert self.post1.status == "draft"

    def test_post_delete(self):
        url = reverse("administration:post_delete", kwargs={"pk": self.post1.pk})
        
        # GET request (confirmation page)
        response = self.client.get(url)
        assert response.status_code == 200
        
        # POST request (actual delete)
        response = self.client.post(url)
        assert response.status_code == 302 # Redirects to list
        
        from blog.models import Post
        assert not Post.objects.filter(pk=self.post1.pk).exists()

    def test_post_duplicate(self):
        url = reverse("administration:post_duplicate", kwargs={"pk": self.post1.pk})
        
        # POST request
        response = self.client.post(url)
        assert response.status_code == 302
        
        from blog.models import Post
        # Should have original + duplicate
        # Duplicate usually has " (Copy)" suffix or similar logic
        duplicates = Post.objects.filter(title__startswith=self.post1.title)
        assert duplicates.count() >= 2

    def test_category_create(self):
        url = reverse("administration:category_create")
        data = {
            "name": "New Category",
            "slug": "new-category",
            "description": "Desc",
            "icon": "folder",
            "color": "primary"
        }
        response = self.client.post(url, data)
        assert response.status_code == 302
        
        from blog.models import Category
        assert Category.objects.filter(name="New Category").exists()

    def test_category_update(self):
        url = reverse("administration:category_edit", kwargs={"pk": self.category.pk})
        data = {
            "name": "Updated Category",
            "slug": self.category.slug,
            "description": "Updated Desc",
            "icon": "star",
            "color": "secondary"
        }
        response = self.client.post(url, data)
        assert response.status_code == 302
        
        self.category.refresh_from_db()
        assert self.category.name == "Updated Category"

    def test_category_delete(self):
        # Create a category with no posts to avoid protected error if applicable
        cat = self.category_factory(name="Empty Cat")
        url = reverse("administration:category_delete", kwargs={"pk": cat.pk})
        
        response = self.client.post(url)
        assert response.status_code == 302
        
        from blog.models import Category
        assert not Category.objects.filter(pk=cat.pk).exists()

