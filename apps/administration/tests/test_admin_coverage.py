
import os
import shutil
import tempfile
from unittest.mock import MagicMock, patch, mock_open
import pytest
from django.urls import reverse
from django.conf import settings
from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model

from apps.administration.services.tasks import get_registered_tasks, get_task_info_map
from apps.administration.views.logs import LogFileListView, LogFileDeleteView

User = get_user_model()

class TestTaskServices:
    @patch("apps.administration.services.tasks.current_app")
    def test_get_registered_tasks(self, mock_app):
        # Setup mock tasks
        mock_app.tasks = {
            "task1": MagicMock(),
            "task2": MagicMock(),
            "celery.backend_cleanup": MagicMock()
        }
        
        tasks = get_registered_tasks()
        assert ("task1", "task1") in tasks
        assert ("task2", "task2") in tasks
        assert ("celery.backend_cleanup", "celery.backend_cleanup") not in tasks

    @patch("apps.administration.services.tasks.current_app")
    def test_get_task_info_map(self, mock_app):
        # Setup mock tasks with docstrings and run methods
        task1 = MagicMock()
        task1.__doc__ = "Task 1 doc"
        task1.run = lambda x: x
        
        task2 = MagicMock()
        task2.__doc__ = None
        # task2 has no run method, simulating a function task
        
        mock_app.tasks = {
            "task1": task1,
            "task2": task2
        }
        
        info_map = get_task_info_map()
        
        assert info_map["task1"]["doc"] == "Task 1 doc"
        assert "x" in info_map["task1"]["signature"]
        assert info_map["task2"]["doc"] == ""


@pytest.mark.django_db
class TestLogViews:
    @pytest.fixture(autouse=True)
    def setup_logs(self):
        # Create a temp directory for logs
        self.temp_dir = tempfile.mkdtemp()
        self.logs_dir = os.path.join(self.temp_dir, "logs")
        os.makedirs(self.logs_dir)
        
        # Create some log files
        with open(os.path.join(self.logs_dir, "test.log"), "w", encoding="utf-8") as f:
            f.write("Log line 1\nLog line 2\n")
            
        with open(os.path.join(self.logs_dir, "empty.log"), "w", encoding="utf-8") as f:
            f.write("")
            
        # Patch settings.BASE_DIR
        # We need to patch it such that BASE_DIR / "logs" points to self.logs_dir
        # Since BASE_DIR is a Path object, we need to mock it carefully or patch where it's used.
        # Ideally, we patch settings.BASE_DIR to be Path(self.temp_dir)
        from pathlib import Path
        self.patcher = patch("django.conf.settings.BASE_DIR", Path(self.temp_dir))
        self.patcher.start()
        
        yield
        
        self.patcher.stop()
        shutil.rmtree(self.temp_dir)

    def test_logfile_list(self, admin_client):
        url = reverse("administration:logfile_list")
        response = admin_client.get(url)
        assert response.status_code == 200
        assert "test.log" in response.content.decode()

    def test_logfile_view_content(self, admin_client):
        url = reverse("administration:logfile_list")
        response = admin_client.get(url, {"file": "test.log"})
        assert response.status_code == 200
        assert "Log line 1" in response.content.decode()

    def test_logfile_not_found(self, admin_client):
        url = reverse("administration:logfile_list")
        response = admin_client.get(url, {"file": "nonexistent.log"})
        assert response.status_code == 200
        # Should show error message
        messages = list(response.context["messages"])
        assert len(messages) > 0
        assert "文件不存在" in str(messages[0])

    def test_logfile_traversal_attempt(self, admin_client):
        url = reverse("administration:logfile_list")
        response = admin_client.get(url, {"file": "../secret.txt"})
        assert response.status_code == 200
        messages = list(response.context["messages"])
        assert "非法的文件名" in str(messages[0])

    def test_logfile_download(self, admin_client):
        url = reverse("administration:logfile_download", kwargs={"filename": "test.log"})
        response = admin_client.get(url)
        assert response.status_code == 200
        assert response["Content-Disposition"] == 'attachment; filename="test.log"'
        assert b"Log line 1" in response.getvalue()

    def test_logfile_download_not_found(self, admin_client):
        url = reverse("administration:logfile_download", kwargs={"filename": "missing.log"})
        response = admin_client.get(url)
        assert response.status_code == 404

    def test_logfile_clear(self, admin_client):
        url = reverse("administration:logfile_delete", kwargs={"filename": "test.log"})
        response = admin_client.post(url, {"action": "clear"})
        assert response.status_code == 302
        
        # Verify content is cleared
        with open(os.path.join(self.logs_dir, "test.log"), "r") as f:
            content = f.read()
        assert content == ""

    def test_logfile_delete(self, admin_client):
        url = reverse("administration:logfile_delete", kwargs={"filename": "test.log"})
        response = admin_client.post(url, {"action": "delete"})
        assert response.status_code == 302
        
        # Verify file is deleted
        assert not os.path.exists(os.path.join(self.logs_dir, "test.log"))

    def test_logentry_list(self, admin_client, user):
        # Create a log entry
        LogEntry.objects.create(
            user=user,
            content_type=ContentType.objects.get_for_model(User),
            object_id=user.id,
            object_repr=str(user),
            action_flag=1,
            change_message="Created user"
        )
        
        url = reverse("administration:logentry_list")
        response = admin_client.get(url)
        assert response.status_code == 200
        assert "Created user" in response.content.decode()

    def test_logentry_search(self, admin_client, user):
        LogEntry.objects.create(
            user=user,
            content_type=ContentType.objects.get_for_model(User),
            object_id=user.id,
            object_repr="UniqueUser",
            action_flag=1,
            change_message="Created user"
        )
        
        url = reverse("administration:logentry_list")
        response = admin_client.get(url, {"q": "UniqueUser"})
        assert response.status_code == 200
        assert "UniqueUser" in response.content.decode()
        
        response = admin_client.get(url, {"q": "NotFound"})
        assert response.status_code == 200
        assert "UniqueUser" not in response.content.decode()
