from django.utils.text import slugify
from django.conf import settings
from django.core.cache import cache
from django.core.management import call_command
from datetime import datetime
from django.utils import timezone
from celery import shared_task
import uuid
import os


"""
核心工具模块 (Core Utils)

本模块包含项目通用的辅助函数和异步任务，主要功能包括：
- Slug 生成：支持中文拼音回退
- 缓存连接：适配 django-constance
- 异步任务状态管理：统一的 Redis 状态跟踪
- 搜索索引重建 (Watson)
- 图片异步处理 (缩略图生成)
- 孤儿文件清理 (Orphaned Media Cleaner)
- 数据库备份与恢复
"""


def generate_unique_slug(
    model_class, source_text, slug_field="slug", allow_unicode=False
):
    """
    为模型实例生成唯一的 Slug。

    策略：
    1. 尝试使用 Django 的 slugify (默认仅支持 ASCII)。
    2. 如果结果为空（例如纯中文且 allow_unicode=False），则尝试转为拼音。
    3. 如果还为空，则使用 UUID 前8位作为兜底。
    4. 如果生成的 Slug 已存在，则在后缀追加 "-1", "-2" 等数字直到唯一。

    Args:
        model_class: Django 模型类
        source_text: 来源文本（通常是标题）
        slug_field: 模型中存储 slug 的字段名 (默认: "slug")
        allow_unicode: 是否允许 Unicode 字符 (默认: False)
    """
    origin_slug = slugify(source_text, allow_unicode=allow_unicode)

    # 兜底方案：处理 slugify 结果为空的情况 (如纯中文环境)
    if not origin_slug:
        # 尝试使用 xpinyin 将中文转换为拼音
        try:
            from xpinyin import Pinyin

            p = Pinyin()
            # source_text 可能包含特殊字符，先转拼音再 slugify
            origin_slug = slugify(p.get_pinyin(source_text, ""))
        except ImportError:
            pass

        # 如果依然为空（极其罕见），使用随机 UUID
        if not origin_slug:
            origin_slug = str(uuid.uuid4())[:8]

    # 统一转换为小写
    origin_slug = origin_slug.lower()

    unique_slug = origin_slug
    n = 1
    # 检查 Slug 是否冲突
    # 注意：这里主要用于新对象的自动生成，未排除自身 ID (如果是更新操作)
    # 对于简单的自动生成场景通常够用
    while model_class.objects.filter(**{slug_field: unique_slug}).exists():
        unique_slug = f"{origin_slug}-{n}"
        n += 1

    return unique_slug


class ConstanceRedisConnection:
    """
    Constance Redis 连接辅助类。

    django-constance 需要一个能返回 Redis 客户端的类。
    这里复用 django-redis 的连接池，避免创建额外的连接。
    """

    def __new__(cls):
        from django_redis import get_redis_connection

        return get_redis_connection("default")


def _set_task_status(task_key, status, detail=None, ttl=86400):
    """
    更新单个异步任务的状态到 Redis。

    Args:
        task_key: Redis 键名。
        status: 任务状态 (如 "running", "success", "error")。
        detail: 可选的详细信息或错误消息。
        ttl: 状态在 Redis 中的过期时间 (秒)，默认 24 小时。

    Returns:
        dict: 写入 Redis 的数据字典。
    """
    payload = {"status": status, "updated_at": timezone.now().isoformat()}
    if detail:
        payload["detail"] = detail
    cache.set(task_key, payload, ttl)
    return payload


def _set_queue_status(task_key, status, ttl=86400, **extra):
    """
    更新批量队列任务的状态到 Redis (包含进度信息)。

    Args:
        task_key: Redis 键名。
        status: 任务状态。
        ttl: 过期时间。
        **extra: 额外的进度信息 (queued, processed, failed, skipped 等)。

    Returns:
        dict: 写入 Redis 的数据字典。
    """


def _process_post_cover_image(post_id):
    """
    处理单篇文章的封面图：生成缩略图和 WebP 优化版。
    """
    from blog.models import Post

    post = Post.objects.filter(id=post_id).first()
    if not post or not post.cover_image:
        return "skipped"

    # 依次处理缩略图 (thumbnail) 和优化图 (optimized)
    specs = [post.cover_thumbnail, post.cover_optimized]
    for spec in specs:
        # imagekit 的 ImageSpecField 是懒加载的，访问其 url 或 generate() 会触发生成
        if hasattr(spec, "generate"):
            spec.generate()
        else:
            _ = spec.url
    return "done"


@shared_task
def _run_watson_rebuild(task_key, lock_key, status_ttl):
    """
    Celery 任务：重建 Watson 搜索索引。
    这是耗时操作，必须异步执行。
    """
    _set_task_status(task_key, "running", ttl=status_ttl)
    try:
        call_command("buildwatson")
        _set_task_status(task_key, "success", ttl=status_ttl)
    except Exception as exc:
        import traceback

        traceback.print_exc()
        _set_task_status(task_key, "error", str(exc), ttl=status_ttl)
    finally:
        # 任务结束，释放锁
        cache.delete(lock_key)


def trigger_watson_rebuild_async():
    """
    触发重建搜索索引的异步任务。
    包含去重锁机制，防止短时间内重复触发。
    """
    task_id = uuid.uuid4().hex
    task_key = f"watson:rebuild:{task_id}"
    lock_key = "watson:rebuild:lock"
    status_ttl = int(getattr(settings, "WATSON_REBUILD_STATUS_TTL", 86400))
    lock_ttl = int(getattr(settings, "WATSON_REBUILD_LOCK_TTL", 3600))

    # 尝试获取锁，如果锁已存在，说明有任务正在运行
    if not cache.add(lock_key, task_id, lock_ttl):
        latest_key = cache.get("watson:rebuild:latest")
        return {"accepted": False, "task_key": latest_key}

    _set_task_status(task_key, "queued", ttl=status_ttl)
    cache.set("watson:rebuild:latest", task_key, status_ttl)

    # 发送 Celery 任务
    _run_watson_rebuild.delay(task_key, lock_key, status_ttl)
    return {"accepted": True, "task_key": task_key}


@shared_task
def _run_image_queue(task_key, delay, limit, status_ttl, lock_key):
    """
    Celery 任务：批量处理图片队列。
    扫描最近更新且有封面的文章，生成缺失的缩略图。
    """
    queued = 0
    processed = 0
    failed = 0
    skipped = 0
    try:
        from blog.models import Post

        # 选取最近更新的 N 篇文章
        posts = list(
            Post.objects.filter(cover_image__isnull=False)
            .exclude(cover_image="")
            .order_by("-updated_at")[:limit]
        )
        post_ids = []
        for post in posts:
            # 简单的去重：如果该文章正在处理中，则跳过
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

            # 实时更新进度
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
    """
    Celery 任务：处理单篇文章图片（用于保存文章时触发）。
    """
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
    """
    触发批量处理图片的异步任务。
    """
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
    # 延迟执行，避免频繁 I/O
    _run_image_queue.apply_async(
        args=[task_key, delay, limit, status_ttl, lock_key], countdown=delay
    )
    return {"accepted": True, "task_key": task_key}


# --- Orphaned Media Cleaner (孤儿文件清理) ---
@shared_task
def _run_media_scan(task_key, lock_key, status_ttl):
    """
    Celery 任务：扫描孤儿文件（存在于磁盘但未被数据库引用的文件）。
    分为两步：
    1. 收集数据库中所有 FileField/ImageField 的引用路径。
    2. 遍历 media 目录，找出不在引用列表中的文件。
    """
    _set_task_status(task_key, "running", ttl=status_ttl)
    try:
        from django.apps import apps
        from django.db import models
        import os

        media_root = settings.MEDIA_ROOT

        # 1. 扫描数据库引用 (优先构建白名单，减少内存占用)
        db_files = set()
        for model in apps.get_models():
            # 找出所有文件字段
            file_fields = [
                f
                for f in model._meta.get_fields()
                if isinstance(f, (models.FileField, models.ImageField))
            ]
            if not file_fields:
                continue

            for field in file_fields:
                # 优化：使用 iterator() 减少大表查询的内存占用
                paths = (
                    model.objects.exclude(**{f"{field.name}__isnull": True})
                    .exclude(**{f"{field.name}": ""})
                    .values_list(field.name, flat=True)
                    .iterator()
                )

                for path in paths:
                    if path:
                        # 归一化路径分隔符
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
                if rel_path.startswith("CACHE/"):  # ImageKit 缓存目录
                    continue

                size = os.path.getsize(full_path)
                scan_count += 1
                scan_size += size

                # 核心比对逻辑：直接检查是否在白名单中
                if rel_path not in db_files:
                    orphaned.append(
                        {
                            "path": rel_path,
                            "size": size,
                            "mtime": os.path.getmtime(full_path),
                        }
                    )
                    orphaned_size += size

        result = {
            "status": "success",
            "updated_at": timezone.now().isoformat(),
            "scan_count": scan_count,
            "scan_size": scan_size,
            "orphaned_count": len(orphaned),
            "orphaned_size": orphaned_size,
            "orphaned_files": orphaned[:100],  # 预览前100个文件
            "orphaned_files_all_key": f"{task_key}:files",
        }
        cache.set(task_key, result, status_ttl)

        # 将完整列表单独存一个 key，防止主 key 值过大
        if orphaned:
            cache.set(f"{task_key}:files", orphaned, status_ttl)

    except Exception as exc:
        import traceback

        traceback.print_exc()
        _set_task_status(task_key, "error", str(exc), ttl=status_ttl)
    finally:
        cache.delete(lock_key)


def trigger_media_scan_async():
    """
    触发媒体文件扫描任务。
    """
    task_id = uuid.uuid4().hex
    task_key = f"media:scan:{task_id}"
    lock_key = "media:scan:lock"
    status_ttl = 3600  # 1 hour

    if not cache.add(lock_key, task_id, 300):
        latest_key = cache.get("media:scan:latest")
        return {"accepted": False, "task_key": latest_key}

    _set_task_status(task_key, "queued", ttl=status_ttl)
    cache.set("media:scan:latest", task_key, status_ttl)
    _run_media_scan.delay(task_key, lock_key, status_ttl)
    return {"accepted": True, "task_key": task_key}


@shared_task
def _run_media_clean(task_key, scan_task_key, lock_key, status_ttl):
    """
    Celery 任务：执行清理操作。
    必须基于先前的扫描结果，删除确认无用的文件。
    """
    _set_task_status(task_key, "running", ttl=status_ttl)
    try:
        orphaned_files = cache.get(f"{scan_task_key}:files")
        if not orphaned_files:
            # 尝试从主结果取
            scan_result = cache.get(scan_task_key)
            if scan_result and "orphaned_files" in scan_result:
                orphaned_files = scan_result["orphaned_files"]

        if not orphaned_files:
            _set_task_status(
                task_key, "success", "No files to clean or scan expired", ttl=status_ttl
            )
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

                    # 尝试删除空目录 (清理垃圾后留下的空文件夹)
                    directory = os.path.dirname(full_path)
                    if os.path.exists(directory) and not os.listdir(directory):
                        os.rmdir(directory)
            except OSError:
                # 记录错误但不中断循环，除非是致命错误
                pass

        cache.set(
            task_key,
            {
                "status": "success",
                "updated_at": timezone.now().isoformat(),
                "cleaned_count": cleaned_count,
                "cleaned_size": cleaned_size,
            },
            status_ttl,
        )

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
    """
    触发清理任务。必须先执行扫描任务。
    """
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


# --- Database Backup (数据库备份) ---
def list_backups():
    """
    列出所有现有的数据库备份文件。
    """
    backup_dir = settings.BASE_DIR / "backups"
    if not backup_dir.exists():
        return []

    backups = []
    for f in backup_dir.iterdir():
        if f.is_file() and (f.suffix == ".json" or f.suffix == ".zip"):
            stat = f.stat()
            backups.append(
                {
                    "name": f.name,
                    "size": stat.st_size,
                    "mtime": datetime.fromtimestamp(stat.st_mtime),
                    "path": str(f),
                }
            )
    backups.sort(key=lambda x: x["mtime"], reverse=True)
    return backups


def create_backup(filename=None):
    """
    创建新的数据库备份。
    自动检测数据库类型：
    - SQLite: 执行文件级二进制备份 (更完整，恢复更快)
    - 其他: 执行 dumpdata (JSON 格式)
    """
    import shutil
    from pathlib import Path

    backup_dir = settings.BASE_DIR / "backups"
    backup_dir.mkdir(exist_ok=True)

    db_conf = settings.DATABASES["default"]
    engine = db_conf["ENGINE"]
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")

    # SQLite 二进制备份
    if "sqlite3" in engine:
        if not filename:
            filename = f"db_backup_{timestamp}.sqlite3"

        db_path = Path(db_conf["NAME"])

        # 确保源文件存在
        if not db_path.exists():
            raise FileNotFoundError(f"Database file not found at {db_path}")

        shutil.copy(db_path, backup_dir / filename)
        return filename

    # 其他数据库使用 dumpdata
    if not filename:
        filename = f"backup_{timestamp}.json"

    file_path = backup_dir / filename

    with open(file_path, "w", encoding="utf-8") as f:
        # 排除 contenttypes 和 auth.permission 等元数据表，以及 session 日志
        call_command(
            "dumpdata",
            exclude=[
                "contenttypes",
                "auth.permission",
                "admin.logentry",
                "sessions.session",
            ],
            indent=2,
            stdout=f,
        )
    return filename


def delete_backup(filename):
    """
    删除指定的备份文件。
    """
    backup_dir = settings.BASE_DIR / "backups"
    file_path = backup_dir / filename

    # 安全检查：防止路径遍历攻击
    if not file_path.resolve().is_relative_to(backup_dir.resolve()):
        raise ValueError("Invalid path")

    if file_path.exists():
        os.remove(file_path)
        return True
    return False


def restore_backup(filename):
    """
    从备份文件恢复数据库。
    自动检测备份类型：
    - .sqlite3: 替换当前 SQLite 数据库文件 (如果是 SQLite)
    - .json/.json.gz: 使用 loaddata
    """
    import shutil
    from pathlib import Path

    backup_dir = settings.BASE_DIR / "backups"
    file_path = backup_dir / filename

    if not file_path.resolve().is_relative_to(backup_dir.resolve()):
        raise ValueError("Invalid path")

    if not file_path.exists():
        raise FileNotFoundError("Backup file not found")

    # SQLite 二进制恢复
    if filename.endswith(".sqlite3"):
        db_conf = settings.DATABASES["default"]
        if "sqlite3" not in db_conf["ENGINE"]:
            raise ValueError("Cannot restore SQLite backup to non-SQLite database")

        db_path = Path(db_conf["NAME"])

        # Create a temp backup of current state just in case
        if db_path.exists():
            shutil.copy(db_path, f"{db_path}.pre_restore")

        # Restore
        shutil.copy(file_path, db_path)
        return True

    # JSON 恢复 (Universal)
    if filename.endswith(".json") or filename.endswith(".json.gz"):
        call_command("loaddata", str(file_path))
        return True

    raise ValueError(f"Unsupported backup format: {filename}")


def schedule_post_image_processing(post_id, delay_seconds=None):
    """
    调度单篇文章的图片处理任务（例如保存文章后）。
    使用 Redis 锁防止重复调度。
    """
    delay = delay_seconds
    if delay is None:
        delay = int(getattr(settings, "IMAGE_PROCESSING_DELAY", 120))
    status_ttl = int(getattr(settings, "IMAGE_QUEUE_STATUS_TTL", 86400))
    queue_key = f"image:post:{post_id}"

    # 如果已经在队列中，则不重复添加
    if not cache.add(queue_key, "queued", delay + status_ttl):
        return False

    _process_post_image.apply_async(
        args=[post_id, queue_key, status_ttl], countdown=delay
    )
    return True
