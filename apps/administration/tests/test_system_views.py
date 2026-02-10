import pytest
from unittest.mock import patch
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import Page

User = get_user_model()


@pytest.mark.django_db
class TestSystemToolsView:
    @pytest.fixture(autouse=True)
    def setup(self, client):
        self.client = client
        self.superuser = User.objects.create_superuser(
            username="admin", password="password"
        )
        self.client.force_login(self.superuser)
        self.url = reverse("administration:system_tools")

    def test_get_system_tools(self):
        response = self.client.get(self.url)
        assert response.status_code == 200
        assert "media_scan_status" in response.context

    @patch("core.utils.trigger_media_scan_async")
    def test_scan_media(self, mock_trigger):
        mock_trigger.return_value = {"accepted": True}
        response = self.client.post(self.url, {"action": "scan_media"})
        assert response.status_code == 302
        mock_trigger.assert_called_once()

        # Test already running
        with patch("django.core.cache.cache.get", return_value="running"):
            response = self.client.post(self.url, {"action": "scan_media"})
            assert response.status_code == 302
            # Should show warning, but we just check redirect

    @patch("core.utils.trigger_media_clean_async")
    def test_clean_media(self, mock_trigger):
        mock_trigger.return_value = {"accepted": True}
        response = self.client.post(self.url, {"action": "clean_media"})
        assert response.status_code == 302
        mock_trigger.assert_called_once()

    @patch("core.utils.trigger_watson_rebuild_async")
    def test_rebuild_watson(self, mock_trigger):
        mock_trigger.return_value = {"accepted": True}
        response = self.client.post(self.url, {"action": "rebuild_watson"})
        assert response.status_code == 302
        mock_trigger.assert_called_once()

    def test_init_privacy_policy(self):
        assert not Page.objects.filter(slug="privacy-policy").exists()
        response = self.client.post(self.url, {"action": "init_privacy_policy"})
        assert response.status_code == 302
        assert Page.objects.filter(slug="privacy-policy").exists()

        # Test already exists
        response = self.client.post(self.url, {"action": "init_privacy_policy"})
        assert response.status_code == 302

    @patch("core.utils.queue_post_images_async")
    def test_queue_images(self, mock_queue):
        mock_queue.return_value = {"accepted": True}
        response = self.client.post(self.url, {"action": "queue_images"})
        assert response.status_code == 302
        mock_queue.assert_called_once()

    @patch("core.tasks.backup_database_task.delay")
    def test_create_backup(self, mock_task_delay):
        response = self.client.post(self.url, {"action": "create_backup"})
        assert response.status_code == 302
        mock_task_delay.assert_called_once()

    @patch("core.utils.restore_backup")
    def test_restore_backup(self, mock_restore):
        response = self.client.post(
            self.url, {"action": "restore_backup", "filename": "backup.json"}
        )
        assert response.status_code == 302
        mock_restore.assert_called_with("backup.json")

    @patch("core.utils.delete_backup")
    def test_delete_backup(self, mock_delete):
        response = self.client.post(
            self.url, {"action": "delete_backup", "filename": "backup.json"}
        )
        assert response.status_code == 302
        mock_delete.assert_called_with("backup.json")

    def test_unknown_action(self):
        response = self.client.post(self.url, {"action": "unknown"})
        assert response.status_code == 302


@pytest.mark.django_db
class TestSettingsView:
    def test_settings_view(self, client):
        user = User.objects.create_user(
            username="staff", password="password", is_staff=True
        )
        client.force_login(user)
        url = reverse("administration:settings")
        response = client.get(url)
        assert response.status_code == 200
