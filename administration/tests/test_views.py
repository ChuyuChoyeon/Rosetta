import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from blog.models import Post, Category, Comment
from model_bakery import baker

User = get_user_model()


@pytest.mark.django_db
class TestAdministrationViews:

    @pytest.fixture(autouse=True)
    def setup_data(self, client):
        self.client = client
        self.user = User.objects.create_superuser(username="admin", password="password")
        self.client.force_login(self.user)
        self.category = baker.make(Category, name="Test Cat")
        self.post1 = baker.make(
            Post, title="Alpha Post", status="published", author=self.user
        )
        self.post2 = baker.make(
            Post, title="Beta Post", status="draft", author=self.user
        )

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
        baker.make(Category, name="Python")
        baker.make(Category, name="Java")

        url = reverse("administration:category_list")
        response = self.client.get(url, {"q": "Python"})
        assert response.status_code == 200
        content = response.content.decode()
        assert "Python" in content
        assert "Java" not in content

    def test_comment_list_filter(self):
        c1 = baker.make(Comment, content="Good comment", active=True)
        c2 = baker.make(Comment, content="Bad comment", active=False)

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
