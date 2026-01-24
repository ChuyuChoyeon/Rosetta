from django.utils.text import slugify
from django.conf import settings
from django.core.cache import cache
from django.core.management import call_command
from django.utils import timezone
from celery import shared_task
import uuid


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
        # Use first 8 chars of a UUID as fallback or handle as needed
        # Alternatively, could support pinyin conversion here if needed
        origin_slug = str(uuid.uuid4())[:8]

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
    spec = post.cover_thumbnail
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
