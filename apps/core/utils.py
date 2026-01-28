from django.utils.text import slugify
from django.conf import settings
from django.core.cache import cache
from django.core.management import call_command
from datetime import datetime, timedelta
from django.utils import timezone
from celery import shared_task
import uuid
import os


def generate_unique_slug(
    model_class, source_text, slug_field="slug", allow_unicode=False
):
    """
    Generate a unique slug for a model instance.

    Args:
        model_class: The Django model class.
        source_text: The text to slugify.
        slug_field: The field name to check for uniqueness (default: "slug").
        allow_unicode: Whether to allow unicode characters in slug (default: False).
    """
    origin_slug = slugify(source_text, allow_unicode=allow_unicode)

    # Fallback for empty slug (e.g. purely non-ASCII text without allow_unicode)
    if not origin_slug:
        # Try pinyin first
        try:
            from xpinyin import Pinyin
            p = Pinyin()
            origin_slug = slugify(p.get_pinyin(source_text, ""))
        except ImportError:
            pass
            
        # If still empty, use UUID
        if not origin_slug:
            origin_slug = str(uuid.uuid4())[:8]
    
    # Ensure lowercase
    origin_slug = origin_slug.lower()

    unique_slug = origin_slug
    n = 1
    # Check if slug exists, excluding the current instance if it were passed (not handling instance exclusion here for simplicity in creation)
    # Ideally this is used for creation. For updates, one might want to keep existing slug.
    # But this simple version is for auto-generating NEW slugs.
    while model_class.objects.filter(**{slug_field: unique_slug}).exists():
        unique_slug = f"{origin_slug}-{n}"
        n += 1

    return unique_slug


class ConstanceRedisConnection:
    """
    Helper class to provide a Redis connection for django-constance
    reusing the django-redis connection pool.

    django-constance expects a class that can be instantiated with no arguments
    and returns a redis client.
    """

    def __new__(cls):
        from django_redis import get_redis_connection

        return get_redis_connection("default")


def _set_task_status(task_key, status, detail=None, ttl=86400):
    payload = {"status": status, "updated_at": timezone.now().isoformat()}
    if detail:
        payload["detail"] = detail
    cache.set(task_key, payload, ttl)
    return payload


def _set_queue_status(task_key, status, ttl=86400, **extra):
    payload = {"status": status, "updated_at": timezone.now().isoformat()}
    payload.update(extra)
    cache.set(task_key, payload, ttl)
    return payload


def _process_post_cover_image(post_id):
    from blog.models import Post

    post = Post.objects.filter(id=post_id).first()
    if not post or not post.cover_image:
        return "skipped"
    
    # Process both thumbnail and optimized
    specs = [post.cover_thumbnail, post.cover_optimized]
    for spec in specs:
        if hasattr(spec, "generate"):
            spec.generate()
        else:
            _ = spec.url
    return "done"


@shared_task
def _run_watson_rebuild(task_key, lock_key, status_ttl):
    _set_task_status(task_key, "running", ttl=status_ttl)
    try:
        call_command("buildwatson")
        _set_task_status(task_key, "success", ttl=status_ttl)
    except Exception as exc:
        import traceback
        traceback.print_exc()
        _set_task_status(task_key, "error", str(exc), ttl=status_ttl)
    finally:
        cache.delete(lock_key)


def trigger_watson_rebuild_async():
    task_id = uuid.uuid4().hex
    task_key = f"watson:rebuild:{task_id}"
    lock_key = "watson:rebuild:lock"
    status_ttl = int(getattr(settings, "WATSON_REBUILD_STATUS_TTL", 86400))
    lock_ttl = int(getattr(settings, "WATSON_REBUILD_LOCK_TTL", 3600))

    if not cache.add(lock_key, task_id, lock_ttl):
        latest_key = cache.get("watson:rebuild:latest")
        return {"accepted": False, "task_key": latest_key}

    _set_task_status(task_key, "queued", ttl=status_ttl)
    cache.set("watson:rebuild:latest", task_key, status_ttl)
    _run_watson_rebuild.delay(task_key, lock_key, status_ttl)
    return {"accepted": True, "task_key": task_key}


@shared_task
def _run_image_queue(task_key, delay, limit, status_ttl, lock_key):
    queued = 0
    processed = 0
    failed = 0
    skipped = 0
    try:
        from blog.models import Post

        posts = list(
            Post.objects.filter(cover_image__isnull=False)
            .exclude(cover_image="")
            .order_by("-updated_at")[:limit]
        )
        post_ids = []
        for post in posts:
            queue_key = f"image:post:{post.id}"
            if cache.add(queue_key, "queued", status_ttl):
                post_ids.append(post.id)

        queued = len(post_ids)
        _set_queue_status(
            task_key,
            "running",
            ttl=status_ttl,
            queued=queued,
            processed=0,
            failed=0,
            skipped=0,
            delay=delay,
            limit=limit,
        )

        for post_id in post_ids:
            try:
                result = _process_post_cover_image(post_id)
                if result == "done":
                    processed += 1
                    cache.set(f"image:post:{post_id}", "done", status_ttl)
                elif result == "skipped":
                    skipped += 1
                    cache.set(f"image:post:{post_id}", "skipped", status_ttl)
                else:
                    failed += 1
                    cache.set(f"image:post:{post_id}", f"error:{result}", status_ttl)
            except Exception as exc:
                failed += 1
                cache.set(f"image:post:{post_id}", f"error:{exc}", status_ttl)

            _set_queue_status(
                task_key,
                "running",
                ttl=status_ttl,
                queued=queued,
                processed=processed,
                failed=failed,
                skipped=skipped,
                delay=delay,
                limit=limit,
            )

        final_status = "success" if failed == 0 else "completed"
        _set_queue_status(
            task_key,
            final_status,
            ttl=status_ttl,
            queued=queued,
            processed=processed,
            failed=failed,
            skipped=skipped,
            delay=delay,
            limit=limit,
        )
    except Exception as exc:
        _set_queue_status(
            task_key,
            "error",
            ttl=status_ttl,
            queued=queued,
            processed=processed,
            failed=failed,
            skipped=skipped,
            delay=delay,
            limit=limit,
            detail=str(exc),
        )
    finally:
        cache.delete(lock_key)


@shared_task
def _process_post_image(post_id, queue_key=None, status_ttl=None):
    if status_ttl is None:
        status_ttl = int(getattr(settings, "IMAGE_QUEUE_STATUS_TTL", 86400))
    if queue_key is None:
        queue_key = f"image:post:{post_id}"
    try:
        result = _process_post_cover_image(post_id)
        cache.set(queue_key, result, status_ttl)
        return result
    except Exception as exc:
        cache.set(queue_key, f"error:{exc}", status_ttl)
        return f"error:{exc}"


def queue_post_images_async(limit=20, delay_seconds=None):
    delay = delay_seconds
    if delay is None:
        delay = int(getattr(settings, "IMAGE_PROCESSING_DELAY", 120))
    status_ttl = int(getattr(settings, "IMAGE_QUEUE_STATUS_TTL", 86400))
    lock_ttl = int(getattr(settings, "IMAGE_QUEUE_LOCK_TTL", 3600))
    task_id = uuid.uuid4().hex
    task_key = f"image:queue:{task_id}"
    lock_key = "image:queue:lock"

    if not cache.add(lock_key, task_id, lock_ttl):
        latest_key = cache.get("image:queue:latest")
        return {"accepted": False, "task_key": latest_key}

    cache.set("image:queue:latest", task_key, status_ttl)
    _set_queue_status(
        task_key,
        "queued",
        ttl=status_ttl,
        queued=0,
        processed=0,
        failed=0,
        skipped=0,
        delay=delay,
        limit=limit,
    )
    _run_image_queue.apply_async(
        args=[task_key, delay, limit, status_ttl, lock_key], countdown=delay
    )
    return {"accepted": True, "task_key": task_key}


# --- Orphaned Media Cleaner ---
@shared_task
def _run_media_scan(task_key, lock_key, status_ttl):
    _set_task_status(task_key, "running", ttl=status_ttl)
    try:
        from django.apps import apps
        from django.db import models
        import os
        
        media_root = settings.MEDIA_ROOT
        
        # 1. 扫描数据库引用 (优先构建白名单，减少内存占用)
        db_files = set()
        for model in apps.get_models():
            file_fields = [f for f in model._meta.get_fields() if isinstance(f, (models.FileField, models.ImageField))]
            if not file_fields:
                continue
            
            for field in file_fields:
                # 优化：使用 iterator() 减少内存占用
                paths = model.objects.exclude(
                    **{f"{field.name}__isnull": True}
                ).exclude(
                    **{f"{field.name}": ""}
                ).values_list(field.name, flat=True).iterator()
                
                for path in paths:
                    if path:
                        # 归一化路径
                        name = str(path).replace("\\", "/")
                        db_files.add(name)

        # 2. 扫描文件系统并实时比对
        orphaned = []
        orphaned_size = 0
        scan_count = 0
        scan_size = 0
        
        for root, dirs, files in os.walk(media_root):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, media_root).replace("\\", "/")
                
                # 忽略隐藏文件、缓存目录和数据库备份
                if file.startswith(".") or "__pycache__" in root:
                    continue
                if rel_path.startswith("backups/"):
                    continue
                if rel_path.startswith("CACHE/"): # ImageKit Cache
                    continue
                    
                size = os.path.getsize(full_path)
                scan_count += 1
                scan_size += size
                
                # 核心比对逻辑：直接检查是否在白名单中
                if rel_path not in db_files:
                    orphaned.append({
                        "path": rel_path,
                        "size": size,
                        "mtime": os.path.getmtime(full_path)
                    })
                    orphaned_size += size

        result = {
            "status": "success",
            "updated_at": timezone.now().isoformat(),
            "scan_count": scan_count,
            "scan_size": scan_size,
            "orphaned_count": len(orphaned),
            "orphaned_size": orphaned_size,
            "orphaned_files": orphaned[:100],  # 只存前100个详情
            "orphaned_files_all_key": f"{task_key}:files"
        }
        cache.set(task_key, result, status_ttl)
        
        if orphaned:
             cache.set(f"{task_key}:files", orphaned, status_ttl)

    except Exception as exc:
        import traceback
        traceback.print_exc()
        _set_task_status(task_key, "error", str(exc), ttl=status_ttl)
    finally:
        cache.delete(lock_key)


def trigger_media_scan_async():
    task_id = uuid.uuid4().hex
    task_key = f"media:scan:{task_id}"
    lock_key = "media:scan:lock"
    status_ttl = 3600 # 1 hour
    
    if not cache.add(lock_key, task_id, 300):
        latest_key = cache.get("media:scan:latest")
        return {"accepted": False, "task_key": latest_key}

    _set_task_status(task_key, "queued", ttl=status_ttl)
    cache.set("media:scan:latest", task_key, status_ttl)
    _run_media_scan.delay(task_key, lock_key, status_ttl)
    return {"accepted": True, "task_key": task_key}


@shared_task
def _run_media_clean(task_key, scan_task_key, lock_key, status_ttl):
    _set_task_status(task_key, "running", ttl=status_ttl)
    try:
        orphaned_files = cache.get(f"{scan_task_key}:files")
        if not orphaned_files:
            # 尝试从主结果取
            scan_result = cache.get(scan_task_key)
            if scan_result and "orphaned_files" in scan_result:
                 orphaned_files = scan_result["orphaned_files"]
        
        if not orphaned_files:
            _set_task_status(task_key, "success", "No files to clean or scan expired", ttl=status_ttl)
            return

        cleaned_count = 0
        cleaned_size = 0
        media_root = settings.MEDIA_ROOT
        
        for f in orphaned_files:
            path = f["path"]
            full_path = os.path.join(media_root, path)
            
            # 使用更安全的删除逻辑
            try:
                if os.path.exists(full_path):
                    if os.path.isfile(full_path):
                        os.remove(full_path)
                        cleaned_count += 1
                        cleaned_size += f["size"]
                    
                    # 尝试删除空目录
                    directory = os.path.dirname(full_path)
                    if os.path.exists(directory) and not os.listdir(directory):
                        os.rmdir(directory)
            except OSError as e:
                # 记录错误但不中断循环，除非是致命错误
                # 这里简单跳过
                pass

        cache.set(task_key, {
            "status": "success", 
            "updated_at": timezone.now().isoformat(),
            "cleaned_count": cleaned_count,
            "cleaned_size": cleaned_size
        }, status_ttl)
        
        # 清除扫描结果，避免重复清理
        cache.delete(scan_task_key)
        cache.delete(f"{scan_task_key}:files")

    except Exception as exc:
        import traceback
        traceback.print_exc()
        _set_task_status(task_key, "error", str(exc), ttl=status_ttl)
    finally:
        cache.delete(lock_key)


def trigger_media_clean_async():
    # 必须基于最近一次成功的扫描
    scan_key = cache.get("media:scan:latest")
    if not scan_key:
        return {"accepted": False, "error": "No scan record"}
    
    scan_result = cache.get(scan_key)
    if not scan_result or scan_result.get("status") != "success":
        return {"accepted": False, "error": "No successful scan result"}

    task_id = uuid.uuid4().hex
    task_key = f"media:clean:{task_id}"
    lock_key = "media:clean:lock"
    status_ttl = 3600
    
    if not cache.add(lock_key, task_id, 300):
        latest_key = cache.get("media:clean:latest")
        return {"accepted": False, "task_key": latest_key}

    _set_task_status(task_key, "queued", ttl=status_ttl)
    cache.set("media:clean:latest", task_key, status_ttl)
    _run_media_clean.delay(task_key, scan_key, lock_key, status_ttl)
    return {"accepted": True, "task_key": task_key}


# --- Database Backup ---
def list_backups():
    backup_dir = settings.BASE_DIR / "backups"
    if not backup_dir.exists():
        return []
        
    backups = []
    for f in backup_dir.iterdir():
        if f.is_file() and (f.suffix == ".json" or f.suffix == ".zip"):
            stat = f.stat()
            backups.append({
                "name": f.name,
                "size": stat.st_size,
                "mtime": datetime.fromtimestamp(stat.st_mtime),
                "path": str(f)
            })
    backups.sort(key=lambda x: x["mtime"], reverse=True)
    return backups

def create_backup(filename=None):
    backup_dir = settings.BASE_DIR / "backups"
    backup_dir.mkdir(exist_ok=True)
    
    if not filename:
        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backup_{timestamp}.json"
    
    file_path = backup_dir / filename
    
    with open(file_path, "w", encoding="utf-8") as f:
        call_command(
            "dumpdata", 
            exclude=["contenttypes", "auth.permission", "admin.logentry", "sessions.session"],
            indent=2, 
            stdout=f
        )
    return filename

def delete_backup(filename):
    backup_dir = settings.BASE_DIR / "backups"
    file_path = backup_dir / filename
    
    # 安全检查
    if not file_path.resolve().is_relative_to(backup_dir.resolve()):
        raise ValueError("Invalid path")
        
    if file_path.exists():
        os.remove(file_path)
        return True
    return False

def restore_backup(filename):
    backup_dir = settings.BASE_DIR / "backups"
    file_path = backup_dir / filename
    
    if not file_path.resolve().is_relative_to(backup_dir.resolve()):
         raise ValueError("Invalid path")
         
    if not file_path.exists():
        raise FileNotFoundError("Backup file not found")
        
    call_command("loaddata", str(file_path))
    return True


def schedule_post_image_processing(post_id, delay_seconds=None):
    delay = delay_seconds
    if delay is None:
        delay = int(getattr(settings, "IMAGE_PROCESSING_DELAY", 120))
    status_ttl = int(getattr(settings, "IMAGE_QUEUE_STATUS_TTL", 86400))
    queue_key = f"image:post:{post_id}"
    if not cache.add(queue_key, "queued", delay + status_ttl):
        return False
    _process_post_image.apply_async(
        args=[post_id, queue_key, status_ttl], countdown=delay
    )
    return True
