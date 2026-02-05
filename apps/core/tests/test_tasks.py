
import pytest
from unittest.mock import patch, MagicMock
from django.conf import settings
from apps.core import tasks
from pathlib import Path
import os

@pytest.mark.django_db
class TestCoreTasks:
    def test_debug_task(self):
        # Mock request
        task_instance = MagicMock()
        task_instance.request = "Test Request"
        
        # When bind=True, the first arg is self. 
        # But when called as a python function, celery tasks usually don't need self passed explicitly 
        # IF they are not bound, but here it IS bound.
        # However, calling the task instance directly invokes __call__.
        # Let's try calling it without arguments first, if that fails, we check other ways.
        # Actually, for bound tasks, we can just call the function directly if we access the original function.
        # But simpler: rely on celery's behavior.
        
        # Calling the task object directly
        # tasks.debug_task(self=task_instance) might work if we pass it as kwarg or arg.
        
        # Let's try passing it as first arg.
        try:
            result = tasks.debug_task(task_instance)
        except TypeError:
            # Fallback for some celery versions/configs
            result = tasks.debug_task()
            
        assert "Debug task executed at" in str(result)

    @patch("apps.core.tasks.send_mail")
    def test_send_test_email(self, mock_send_mail):
        recipient_list = ["test@example.com"]
        subject = "Test Subject"
        
        result = tasks.send_test_email(recipient_list, subject)
        
        assert result == f"Email sent to {len(recipient_list)} recipients"
        mock_send_mail.assert_called_once()
        args, kwargs = mock_send_mail.call_args
        assert args[0] == subject
        assert args[3] == recipient_list

    @patch("apps.core.tasks.send_mail")
    def test_send_test_email_failure(self, mock_send_mail):
        mock_send_mail.side_effect = Exception("SMTP Error")
        
        with pytest.raises(Exception, match="SMTP Error"):
            tasks.send_test_email(["test@example.com"])

    @patch("apps.core.tasks.cache")
    def test_clear_cache_task(self, mock_cache):
        result = tasks.clear_cache_task()
        assert result == "Cache cleared"
        mock_cache.clear.assert_called_once()

    def test_long_running_process(self):
        # Mock time.sleep to avoid waiting
        with patch("time.sleep"):
            task_instance = MagicMock()
            # Try calling with keyword argument
            try:
                result = tasks.long_running_process(task_instance, seconds=2)
            except TypeError:
                # If bound task magic fails, try calling without instance
                result = tasks.long_running_process(seconds=2)
                
            assert result == "Process completed"

    @patch("shutil.copy")
    @patch("pathlib.Path.exists")
    def test_backup_database_task_sqlite(self, mock_exists, mock_copy, settings, tmp_path):
        # Setup settings for SQLite
        settings.DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': 'db.sqlite3'
            }
        }
        # Use tmp_path fixture which is a valid path object
        settings.BASE_DIR = tmp_path
        
        mock_exists.return_value = True
        
        result = tasks.backup_database_task()
        
        assert "Backup created" in result
        assert ".sqlite3" in result

    @patch("core.utils.create_backup")
    def test_backup_database_task_other_db(self, mock_create_backup, settings):
        # Setup settings for PostgreSQL
        settings.DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': 'rosetta'
            }
        }

        mock_create_backup.return_value = "backup.json"
        
        result = tasks.backup_database_task()
        
        assert "Backup created" in result
        assert "backup.json" in result

    @patch("pathlib.Path.exists")
    def test_backup_database_task_sqlite_no_file(self, mock_exists, settings, tmp_path):
        settings.DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': 'missing.sqlite3'
            }
        }
        settings.BASE_DIR = tmp_path
        mock_exists.return_value = False
        
        with pytest.raises(FileNotFoundError):
            tasks.backup_database_task()
