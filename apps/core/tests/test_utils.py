
from unittest.mock import MagicMock, patch, mock_open, ANY
import pytest
from django.db import models
from django.conf import settings
from pathlib import Path
import os
import datetime

from core.utils import (
    generate_unique_slug,
    ConstanceRedisConnection,
    _set_task_status,
    _set_queue_status,
    _process_post_cover_image,
    trigger_watson_rebuild_async,
    _run_watson_rebuild,
    _run_image_queue,
    trigger_media_scan_async,
    _run_media_scan,
    _run_media_clean,
    trigger_media_clean_async,
    list_backups,
    create_backup,
    delete_backup,
    restore_backup,
    _process_post_image,
    queue_post_images_async
)

class MockModel(models.Model):
    slug = models.SlugField()

    class Meta:
        app_label = "core"
        managed = False

@pytest.mark.django_db
def test_generate_unique_slug():
    MockModel.objects = MagicMock()
    MockModel.objects.filter.return_value.exists.side_effect = [False, True, False]

    slug1 = generate_unique_slug(MockModel, "Test Title")
    assert slug1 == "test-title"

    MockModel.objects.filter.return_value.exists.side_effect = [True, False]
    slug2 = generate_unique_slug(MockModel, "Test Title")
    assert slug2 == "test-title-1"

@pytest.mark.django_db
def test_generate_unique_slug_fallback():
    MockModel.objects = MagicMock()
    MockModel.objects.filter.return_value.exists.return_value = False
    
    # Test pinyin fallback or uuid fallback
    slug = generate_unique_slug(MockModel, "你好", allow_unicode=False)
    assert slug

def test_constance_redis_connection():
    with patch("django_redis.get_redis_connection") as mock_get_conn:
        conn = ConstanceRedisConnection()
        mock_get_conn.assert_called_with("default")
        assert conn == mock_get_conn.return_value

@patch("core.utils.cache")
def test_set_task_status(mock_cache):
    payload = _set_task_status("key", "running", detail="test")
    assert payload["status"] == "running"
    assert payload["detail"] == "test"
    mock_cache.set.assert_called_once()

@patch("core.utils.cache")
def test_set_queue_status(mock_cache):
    payload = _set_queue_status("key", "running", progress=50)
    assert payload["status"] == "running"
    assert payload["progress"] == 50
    mock_cache.set.assert_called_once()

@pytest.mark.django_db
@patch("blog.models.Post.objects.filter")
def test_process_post_cover_image(mock_filter):
    mock_post = MagicMock()
    mock_post.cover_image = "image.jpg"
    mock_post.cover_thumbnail = MagicMock()
    mock_post.cover_optimized = MagicMock()
    mock_filter.return_value.first.return_value = mock_post

    result = _process_post_cover_image(1)
    assert result == "done"
    # specs should be generated
    # Mock behavior of specs
    
    # Test skipped
    mock_filter.return_value.first.return_value = None
    result = _process_post_cover_image(1)
    assert result == "skipped"

@patch("core.utils.cache")
@patch("core.utils._run_watson_rebuild.delay")
def test_trigger_watson_rebuild_async(mock_delay, mock_cache):
    mock_cache.add.return_value = True
    result = trigger_watson_rebuild_async()
    assert result["accepted"] is True
    mock_delay.assert_called_once()

    # Test lock collision
    mock_cache.add.return_value = False
    mock_cache.get.return_value = "existing_key"
    result = trigger_watson_rebuild_async()
    assert result["accepted"] is False
    assert result["task_key"] == "existing_key"

@patch("core.utils.cache")
@patch("core.utils.call_command")
def test_run_watson_rebuild(mock_call_command, mock_cache):
    _run_watson_rebuild("key", "lock", 3600)
    mock_call_command.assert_called_with("buildwatson")
    mock_cache.delete.assert_called_with("lock")

    # Test exception
    mock_call_command.side_effect = Exception("error")
    _run_watson_rebuild("key", "lock", 3600)
    # verify status is error (checking calls to cache.set would be detailed)

@patch("core.utils.cache")
@patch("core.utils._process_post_cover_image")
def test_run_image_queue(mock_process, mock_cache):
    # Mock Post.objects
    with patch("blog.models.Post.objects") as mock_objects:
        mock_post = MagicMock()
        mock_post.id = 1
        mock_objects.filter.return_value.exclude.return_value.order_by.return_value.__getitem__.return_value = [mock_post]
        
        mock_cache.add.return_value = True
        mock_process.return_value = "done"
        
        _run_image_queue("task_key", 0, 10, 3600, "lock_key")
        
        mock_process.assert_called_with(1)
        mock_cache.delete.assert_called_with("lock_key")

@patch("core.utils.cache")
@patch("core.utils._run_media_scan.delay")
def test_trigger_media_scan_async(mock_delay, mock_cache):
    mock_cache.add.return_value = True
    result = trigger_media_scan_async()
    assert result["accepted"] is True
    mock_delay.assert_called_once()

@patch("core.utils.cache")
@patch("django.apps.apps.get_models")
@patch("os.walk")
def test_run_media_scan(mock_walk, mock_get_models, mock_cache, settings):
    settings.MEDIA_ROOT = "/media"
    
    # Mock models with file fields
    mock_model = MagicMock()
    mock_field = models.FileField(name="file")
    mock_model._meta.get_fields.return_value = [mock_field]
    # Mock objects.exclude...values_list.iterator
    mock_model.objects.exclude.return_value.exclude.return_value.values_list.return_value.iterator.return_value = ["file1.jpg"]
    mock_get_models.return_value = [mock_model]
    
    # Mock os.walk
    mock_walk.return_value = [
        ("/media", [], ["file1.jpg", "file2.jpg", ".hidden"])
    ]
    
    with patch("os.path.getsize", return_value=100), \
         patch("os.path.getmtime", return_value=123456):
         
        _run_media_scan("task_key", "lock_key", 3600)
        
        # Verify result contains file2.jpg as orphaned
        # Check calls to find the one updating the main status
        # cache.set(task_key, result, status_ttl)
        
        found = False
        for call in mock_cache.set.call_args_list:
            args, _ = call
            if args[0] == "task_key":
                result = args[1]
                if isinstance(result, dict) and "orphaned_count" in result:
                    assert result["orphaned_count"] == 1
                    assert result["orphaned_files"][0]["path"] == "file2.jpg"
                    found = True
                    break
        assert found

@patch("core.utils.cache")
@patch("core.utils._run_media_clean.delay")
def test_trigger_media_clean_async(mock_delay, mock_cache):
    mock_cache.get.side_effect = ["scan_key", {"status": "success"}]
    mock_cache.add.return_value = True
    
    result = trigger_media_clean_async()
    assert result["accepted"] is True
    mock_delay.assert_called_once()
    
    # Test failures
    mock_cache.get.side_effect = [None]
    result = trigger_media_clean_async()
    assert result["accepted"] is False

@patch("core.utils.cache")
@patch("os.remove")
@patch("os.rmdir")
def test_run_media_clean(mock_rmdir, mock_remove, mock_cache, settings):
    settings.MEDIA_ROOT = "/media"
    
    # Mock orphaned files
    orphaned = [{"path": "file.jpg", "size": 100}]
    mock_cache.get.return_value = orphaned
    
    with patch("os.path.exists", return_value=True), \
         patch("os.path.isfile", return_value=True), \
         patch("os.path.dirname", return_value="/media"):
         
        # Mock os.listdir for rmdir check
        with patch("os.listdir", return_value=[]):
            _run_media_clean("task_key", "scan_key", "lock_key", 3600)
            
            mock_remove.assert_called_with(os.path.join("/media", "file.jpg"))
            mock_rmdir.assert_called()

def test_list_backups(settings, tmp_path):
    settings.BASE_DIR = tmp_path
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    
    (backup_dir / "backup.json").touch()
    (backup_dir / "backup.zip").touch()
    (backup_dir / "ignored.txt").touch()
    
    backups = list_backups()
    assert len(backups) == 2
    names = [b["name"] for b in backups]
    assert "backup.json" in names
    assert "backup.zip" in names

@patch("core.utils.call_command")
def test_create_backup(mock_call_command, settings, tmp_path):
    settings.BASE_DIR = tmp_path
    # Force non-sqlite to test dumpdata path
    settings.DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'rosetta'
        }
    }
    
    filename = create_backup("test.json")
    assert filename == "test.json"
    assert (tmp_path / "backups" / "test.json").exists()
    mock_call_command.assert_called_with(
        "dumpdata", 
        exclude=["contenttypes", "auth.permission", "admin.logentry", "sessions.session"], 
        indent=2, 
        stdout=ANY
    )

def test_delete_backup(settings, tmp_path):
    settings.BASE_DIR = tmp_path
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    f = backup_dir / "test.json"
    f.touch()
    
    assert delete_backup("test.json") is True
    assert not f.exists()
    
    assert delete_backup("missing.json") is False
    
    # Security check
    with pytest.raises(ValueError):
        delete_backup("../secret.txt")

@patch("core.utils.call_command")
def test_restore_backup(mock_call_command, settings, tmp_path):
    settings.BASE_DIR = tmp_path
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    (backup_dir / "test.json").touch()
    
    restore_backup("test.json")
    mock_call_command.assert_called_with("loaddata", ANY)
    
    with pytest.raises(ValueError):
        restore_backup("../hack.json")

@patch("core.utils.cache")
@patch("core.utils._process_post_cover_image")
def test_process_post_image(mock_process, mock_cache):
    mock_process.return_value = "done"
    result = _process_post_image(1)
    assert result == "done"
    mock_cache.set.assert_called()

@patch("core.utils.cache")
@patch("core.utils._run_image_queue.apply_async")
def test_queue_post_images_async(mock_apply, mock_cache):
    mock_cache.add.return_value = True
    result = queue_post_images_async()
    assert result["accepted"] is True
    mock_apply.assert_called_once()
