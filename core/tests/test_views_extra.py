import pytest
import os
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from django.db import connection

User = get_user_model()

@pytest.mark.django_db
class TestCoreExtraViews:
    @pytest.fixture(autouse=True)
    def setup(self, client, user):
        self.client = client
        self.user = user

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

