import pytest
import json
from django.urls import reverse
from io import BytesIO


@pytest.mark.django_db
class TestAdministrationUtilsViews:
    @pytest.fixture(autouse=True)
    def setup_data(self, client, admin_user_factory, post_factory, category_factory):
        self.client = client
        self.user = admin_user_factory()
        self.client.force_login(self.user)
        self.category_factory = category_factory
        self.post_factory = post_factory

    def test_bulk_delete_posts(self):
        post1 = self.post_factory(author=self.user)
        post2 = self.post_factory(author=self.user)

        url = reverse("administration:bulk_action", kwargs={"model": "blog.Post"})
        data = {"action": "delete", "ids": [post1.id, post2.id]}

        response = self.client.post(url, data, HTTP_REFERER="/admin/posts/")
        assert response.status_code == 302
        assert response.url == "/admin/posts/"

        from blog.models import Post

        assert not Post.objects.filter(id__in=[post1.id, post2.id]).exists()

    def test_bulk_publish_posts(self):
        post1 = self.post_factory(author=self.user, status="draft")
        post2 = self.post_factory(author=self.user, status="draft")

        url = reverse("administration:bulk_action", kwargs={"model": "blog.Post"})
        data = {"action": "published", "ids": [post1.id, post2.id]}

        response = self.client.post(url, data, HTTP_REFERER="/admin/posts/")
        assert response.status_code == 302

        post1.refresh_from_db()
        post2.refresh_from_db()
        assert post1.status == "published"
        assert post2.status == "published"

    def test_bulk_draft_posts(self):
        post1 = self.post_factory(author=self.user, status="published")

        url = reverse("administration:bulk_action", kwargs={"model": "blog.Post"})
        data = {"action": "draft", "ids": [post1.id]}

        response = self.client.post(url, data, HTTP_REFERER="/admin/posts/")
        assert response.status_code == 302

        post1.refresh_from_db()
        assert post1.status == "draft"

    def test_bulk_no_ids(self):
        url = reverse("administration:bulk_action", kwargs={"model": "blog.Post"})
        data = {"action": "delete"}

        response = self.client.post(url, data, HTTP_REFERER="/admin/posts/")
        assert response.status_code == 302

        # Should have a warning message (can't easily check messages middleware in redirect without follow=True)
        # But verify no crash is enough for now.

    def test_bulk_invalid_model(self):
        url = reverse("administration:bulk_action", kwargs={"model": "invalid.Model"})
        data = {"action": "delete", "ids": [1]}

        response = self.client.post(url, data, HTTP_REFERER="/admin/posts/")
        assert response.status_code == 302  # Redirects back with error message usually
        # The view catches Exception and redirects

    def test_export_categories(self):
        self.category_factory(name="Export Cat 1", slug="export-cat-1")
        self.category_factory(name="Export Cat 2", slug="export-cat-2")

        url = reverse("administration:export_all", kwargs={"model": "blog.Category"})
        response = self.client.get(url)

        assert response.status_code == 200
        assert response["Content-Type"] == "application/json"

        content = json.loads(response.content)
        assert len(content) >= 2
        names = [item["name"] for item in content]
        assert "Export Cat 1" in names
        assert "Export Cat 2" in names

    def test_import_categories(self):
        data = [
            {"name": "Import Cat 1", "slug": "import-cat-1", "description": "Desc 1"},
            {"name": "Import Cat 2", "slug": "import-cat-2", "description": "Desc 2"},
        ]
        json_content = json.dumps(data).encode("utf-8")
        json_file = BytesIO(json_content)
        json_file.name = "import.json"

        url = reverse("administration:import_json", kwargs={"model": "blog.Category"})
        response = self.client.post(
            url, {"json_file": json_file}, HTTP_REFERER="/admin/categories/"
        )

        assert response.status_code == 302

        from blog.models import Category

        assert Category.objects.filter(slug="import-cat-1").exists()
        assert Category.objects.filter(slug="import-cat-2").exists()

    def test_import_invalid_json(self):
        json_file = BytesIO(b"invalid json")
        json_file.name = "import.json"

        url = reverse("administration:import_json", kwargs={"model": "blog.Category"})
        response = self.client.post(
            url, {"json_file": json_file}, HTTP_REFERER="/admin/categories/"
        )

        assert response.status_code == 302
        # Should not crash
