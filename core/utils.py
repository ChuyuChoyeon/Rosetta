from django.utils.text import slugify
import uuid

def generate_unique_slug(model_class, source_text, slug_field="slug", allow_unicode=False):
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
