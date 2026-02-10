import json
import datetime
import sys
from unittest.mock import MagicMock, patch
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType

from core.validators import FileValidator
from core.templatetags.core_extras import time_ago, sanitize_svg, model_verbose_name
from core.models import Page


@pytest.mark.django_db
class TestFileValidator:
    def test_file_size_exceeded(self):
        validator = FileValidator(max_size=10)
        file = SimpleUploadedFile("test.txt", b"12345678901")
        with pytest.raises(ValidationError) as excinfo:
            validator(file)
        assert "文件大小不能超过" in str(excinfo.value)

    def test_invalid_extension(self):
        validator = FileValidator(allowed_extensions=["jpg"])
        file = SimpleUploadedFile("test.txt", b"content")
        with pytest.raises(ValidationError) as excinfo:
            validator(file)
        assert "不支持的文件扩展名" in str(excinfo.value)

    @patch("core.validators.magic")
    def test_invalid_mimetype_magic(self, mock_magic):
        # Mock magic to return text/plain
        mock_magic.from_buffer.return_value = "text/plain"

        validator = FileValidator(allowed_mimetypes=["image/jpeg"])
        file = SimpleUploadedFile("test.jpg", b"not an image")

        with pytest.raises(ValidationError) as excinfo:
            validator(file)
        assert "不支持的文件类型" in str(excinfo.value)

    @patch("core.validators.magic")
    def test_valid_mimetype_magic(self, mock_magic):
        # Mock magic to return image/jpeg
        mock_magic.from_buffer.return_value = "image/jpeg"

        validator = FileValidator(allowed_mimetypes=["image/jpeg"])
        file = SimpleUploadedFile("test.jpg", b"image content")

        # Should not raise exception
        validator(file)

    @patch("core.validators.magic", None)
    @patch("core.validators.Image")
    def test_valid_image_fallback(self, mock_image):
        # Mock PIL Image
        mock_img_instance = MagicMock()
        mock_img_instance.format = "JPEG"
        mock_image.open.return_value = mock_img_instance

        validator = FileValidator(allowed_mimetypes=["image/jpeg"])
        file = SimpleUploadedFile("test.jpg", b"image content")

        # Should not raise exception
        validator(file)


class TestCoreExtras:
    def test_time_ago_future(self):
        future = timezone.now() + datetime.timedelta(minutes=5)
        assert time_ago(future) == "刚刚"

    def test_time_ago_just_now(self):
        now = timezone.now()
        assert time_ago(now) == "刚刚"

    def test_time_ago_minutes(self):
        past = timezone.now() - datetime.timedelta(minutes=10)
        assert time_ago(past) == "10分钟前"

    def test_time_ago_hours(self):
        past = timezone.now() - datetime.timedelta(hours=2)
        assert time_ago(past) == "2小时前"

    def test_time_ago_days(self):
        past = timezone.now() - datetime.timedelta(days=3)
        assert time_ago(past) == "3天前"

    def test_time_ago_naive(self):
        # Create a naive datetime
        naive = datetime.datetime.now() - datetime.timedelta(minutes=10)
        # Should handle it without error (assuming default timezone is set correctly in settings)
        # The result depends on system time vs django time, but it should return a string
        assert isinstance(time_ago(naive), str)

    def test_sanitize_svg(self):
        malicious_svg = '<svg><script>alert(1)</script><rect x="10" y="10" width="30" height="30" stroke="black" fill="transparent" stroke-width="5"/></svg>'
        cleaned = sanitize_svg(malicious_svg)
        assert "<script>" not in cleaned
        assert "rect" in cleaned
        assert "stroke" in cleaned

    @pytest.mark.django_db
    def test_model_verbose_name(self):
        ct = ContentType.objects.get_for_model(Page)
        assert model_verbose_name(ct) == "页面"

    def test_model_verbose_name_none(self):
        assert model_verbose_name(None) == ""


@pytest.mark.django_db
class TestCoreViewsExtra:
    def test_upload_image_unauthenticated(self, client):
        url = reverse("upload_image")
        response = client.post(url)
        assert response.status_code == 403

    def test_upload_image_no_file(self, admin_client):
        url = reverse("upload_image")
        response = admin_client.post(url)
        assert response.status_code == 400
        assert response.json()["error"] == "No image provided"

    def test_upload_image_invalid_extension(self, admin_client):
        url = reverse("upload_image")
        file = SimpleUploadedFile("test.txt", b"content")
        response = admin_client.post(url, {"image": file})
        assert response.status_code == 400
        assert response.json()["error"] == "Unsupported file extension"

    def test_upload_image_invalid_content(self, admin_client):
        mock_magic = MagicMock()
        mock_magic.from_buffer.return_value = "text/plain"
        with patch.dict(sys.modules, {"magic": mock_magic}):
            url = reverse("upload_image")
            file = SimpleUploadedFile("test.jpg", b"not an image")
            response = admin_client.post(url, {"image": file})
            assert response.status_code == 400
            assert "Invalid file content" in response.json()["error"]

    def test_upload_image_svg_rejected(self, admin_client):
        mock_magic = MagicMock()
        mock_magic.from_buffer.return_value = "image/svg+xml"
        with patch.dict(sys.modules, {"magic": mock_magic}):
            url = reverse("upload_image")
            # Use .jpg extension to pass the initial extension check
            file = SimpleUploadedFile("test.jpg", b"<svg></svg>")
            response = admin_client.post(url, {"image": file})
            assert response.status_code == 400
            assert "SVG images are not allowed" in response.json()["error"]

    def test_translate_text_missing_params(self, admin_client):
        url = reverse("translate_text")
        response = admin_client.post(
            url, json.dumps({}), content_type="application/json"
        )
        assert response.status_code == 400
        assert "Missing text or target languages" in response.json()["error"]

    @patch("core.views.GoogleTranslator")
    def test_translate_text_exception(self, mock_translator, admin_client):
        mock_instance = MagicMock()
        mock_instance.translate.side_effect = Exception("Translation failed")
        mock_translator.return_value = mock_instance

        url = reverse("translate_text")
        data = {"text": "Hello", "target_langs": ["zh-cn"]}
        response = admin_client.post(
            url, json.dumps(data), content_type="application/json"
        )
        assert response.status_code == 200
        assert "Translation error" in response.json()["translations"]["zh-cn"]
