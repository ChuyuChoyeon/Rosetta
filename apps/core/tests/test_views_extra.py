
import pytest
import os
import json
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from django.db import connection
from core.models import Page
from django.test import override_settings

User = get_user_model()

@pytest.mark.django_db
class TestCoreExtraViews:
    @pytest.fixture(autouse=True)
    def setup(self, client):
        self.client = client
        self.user = User.objects.create_user(username="testuser", password="password")
        self.staff_user = User.objects.create_user(username="staff", password="password", is_staff=True)
        self.superuser = User.objects.create_superuser(username="admin", password="password")

    def test_robots_txt(self):
        url = reverse("robots_txt")
        response = self.client.get(url)
        assert response.status_code == 200
        assert response["Content-Type"] == "text/plain"
        assert b"User-agent: *" in response.content

    def test_upload_image_unauthenticated(self):
        url = reverse("upload_image")
        response = self.client.post(url)
        assert response.status_code == 403

    def test_upload_image_no_file(self):
        self.client.force_login(self.user)
        url = reverse("upload_image")
        response = self.client.post(url)
        assert response.status_code == 400

    def test_upload_image_success(self):
        self.client.force_login(self.user)
        url = reverse("upload_image")
        
        image = SimpleUploadedFile(
            "test_image.jpg",
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82",
            content_type="image/jpeg"
        )
        
        # We should mock default_storage to avoid writing files to disk during tests
        with patch("core.views.default_storage") as mock_storage:
            mock_storage.save.return_value = "uploads/mock_file.jpg"
            mock_storage.url.return_value = "/media/uploads/mock_file.jpg"
            
            response = self.client.post(url, {"image": image})
            
            assert response.status_code == 200
            assert response.json()["url"] == "/media/uploads/mock_file.jpg"

    def test_health_check_ok(self):
        url = reverse("health_check")
        response = self.client.get(url)
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    @patch("core.views.GoogleTranslator")
    def test_translate_text(self, mock_translator):
        self.client.force_login(self.staff_user)
        url = reverse("translate_text")
        
        mock_translator.return_value.translate.return_value = "Translated"
        
        data = {
            "text": "Hello",
            "target_langs": ["zh-hans"]
        }
        response = self.client.post(url, json.dumps(data), content_type="application/json")
        assert response.status_code == 200
        assert response.json()["translations"]["zh-hans"] == "Translated"

        # Test failure handling
        mock_translator.return_value.translate.side_effect = Exception("API Error")
        response = self.client.post(url, json.dumps(data), content_type="application/json")
        assert response.status_code == 200
        assert "error" in response.json()["translations"]["zh-hans"]

    def test_translate_text_permission(self):
        self.client.force_login(self.user) # Not staff
        url = reverse("translate_text")
        response = self.client.post(url, {}, content_type="application/json")
        assert response.status_code == 302 # Redirect to login

    def test_page_view(self):
        page = Page.objects.create(
            title="About",
            slug="about",
            content="Hello {{ config.SITE_NAME }}",
            status="published"
        )
        url = reverse("page_detail", kwargs={"slug": "about"})
        response = self.client.get(url)
        assert response.status_code == 200
        assert "rendered_content" in response.context
        # Rendered content depends on config mock, but at least it shouldn't crash

    @override_settings(DEBUG_TOOL_ENABLED=True)
    def test_debug_api_migrations(self):
        self.client.force_login(self.superuser)
        url = reverse("debug_api_migrations")
        response = self.client.get(url)
        assert response.status_code == 200
        assert "pending" in response.json()

    @override_settings(DEBUG_TOOL_ENABLED=True)
    def test_debug_api_stats(self):
        self.client.force_login(self.superuser)
        url = reverse("debug_api_stats")
        response = self.client.get(url)
        assert response.status_code == 200
        assert response.json()["db_ok"] is True
        assert "counts" in response.json()

    @override_settings(DEBUG_TOOL_ENABLED=False)
    def test_debug_api_disabled(self):
        self.client.force_login(self.superuser)
        url = reverse("debug_api_stats")
        response = self.client.get(url)
        assert response.status_code == 404
