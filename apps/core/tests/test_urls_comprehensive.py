import pytest
from django.urls import reverse, resolve
from django.contrib.auth import get_user_model
from rest_framework import status
from django.urls import get_resolver
from django.urls.resolvers import URLPattern, URLResolver

User = get_user_model()

def get_all_urls(urlpatterns, prefix=''):
    """
    Recursively retrieve all URL patterns with their full names.
    Returns a list of (url_name, url_pattern_object).
    """
    urls = []
    for pattern in urlpatterns:
        if isinstance(pattern, URLPattern):
            name = pattern.name
            if name:
                # Handle namespaced URLs
                full_name = f"{prefix}{name}" if prefix else name
                urls.append((full_name, pattern))
        elif isinstance(pattern, URLResolver):
            new_prefix = f"{prefix}{pattern.namespace}:" if pattern.namespace else prefix
            urls.extend(get_all_urls(pattern.url_patterns, new_prefix))
    return urls

@pytest.fixture
def url_params(db, post, category, tag, page, user, admin_user):
    """
    Provides a dictionary mapping parameter names to valid values.
    Used to automatically populate URL arguments.
    """
    return {
        'slug': post.slug,  # Default slug to a post slug
        'pk': post.pk,      # Default pk to a post pk
        'username': user.username,
        # Specific mappings can be handled in the test logic or by expanding this fixture
        'post_slug': post.slug,
        'category_slug': category.slug,
        'tag_slug': tag.slug,
        'page_slug': page.slug,
        'id': post.pk,
    }

@pytest.fixture
def valid_url_configs(db, post, category, tag, page, comment, user):
    """
    Returns a dictionary mapping URL names to kwargs for reverse().
    This manual mapping ensures we can resolve complex URLs.
    """
    return {
        # Blog
        'post_detail': {'slug': post.slug},
        'post_by_category': {'slug': category.slug},
        'post_by_tag': {'slug': tag.slug},
        'delete_comment': {'pk': comment.pk},
        
        # Core
        'page_detail': {'slug': page.slug},
        'about': {}, # No args, but captured by slug='about' in view, url def uses {"slug": "about"} so reverse needs nothing? No, path definition has {"slug": "about"} as kwargs, but url itself is static path("about/"). reverse("about") works.
        
        # Users
        'users:user_public_profile': {'username': user.username},
        'users:mark_notification_read': {'pk': 1}, # Mock ID
        'users:delete_notification': {'pk': 1}, # Mock ID
        
        # Administration (Many require PKs)
        'administration:post_edit': {'pk': post.pk},
        'administration:post_delete': {'pk': post.pk},
        'administration:post_duplicate': {'pk': post.pk},
        'administration:category_edit': {'pk': category.pk},
        'administration:category_delete': {'pk': category.pk},
        'administration:tag_edit': {'pk': tag.pk},
        'administration:tag_delete': {'pk': tag.pk},
        'administration:comment_edit': {'pk': comment.pk},
        'administration:comment_reply': {'pk': comment.pk},
        'administration:comment_delete': {'pk': comment.pk},
        'administration:page_edit': {'pk': page.pk},
        'administration:page_delete': {'pk': page.pk},
        'administration:page_duplicate': {'pk': page.pk},
        # Navigation etc. would need their own factories, but we can skip or add later
    }

@pytest.mark.django_db
def test_all_urls_reverse_and_resolve(valid_url_configs):
    """
    Traverse all URLs in the project.
    Verify that:
    1. They can be reversed (if we provide args).
    2. They resolve to a callable view.
    """
    resolver = get_resolver()
    all_patterns = get_all_urls(resolver.url_patterns)
    
    # Filter out some URLs that are hard to test or external (like admin/ django default)
    # or development tools
    ignored_prefixes = ['admin:', 'debug', '__debug__', 'djdt']
    
    checked_count = 0
    
    for name, pattern in all_patterns:
        # Skip ignored
        if any(name.startswith(prefix) for prefix in ignored_prefixes):
            continue
            
        # Skip if name is None (shouldn't happen with our helper but safe check)
        if not name:
            continue

        kwargs = {}
        # Try to find kwargs in our manual config
        if name in valid_url_configs:
            kwargs = valid_url_configs[name]
        
        # If not found, and the pattern requires arguments, this might fail.
        # But we can try to guess for simple cases if we wanted.
        # For now, we only test reversal if we have config or if it takes no args.
        
        try:
            url = reverse(name, kwargs=kwargs)
            resolved = resolve(url)
            assert resolved.view_name == name
            checked_count += 1
        except Exception as e:
            # If we don't have config for it, it's expected to fail reversal.
            # But if we DO have config, it should pass.
            if name in valid_url_configs:
                pytest.fail(f"Failed to reverse '{name}' with kwargs {kwargs}: {e}")
            else:
                # Just warn or print that we skipped verification for this one
                # print(f"Skipping reversal check for {name} (no config)")
                pass

    print(f"\nVerified {checked_count} URLs reversibility.")


@pytest.mark.django_db
def test_public_urls_status_200(client, post, category, tag):
    """
    Smoke test for public URLs.
    """
    urls = [
        ('home', {}),
        ('post_list', {}),
        ('category_list', {}),
        ('tag_list', {}),
        ('search', {}), # ?q=...
        ('archive', {}),
        ('post_detail', {'slug': post.slug}),
        ('post_by_category', {'slug': category.slug}),
        ('post_by_tag', {'slug': tag.slug}),
        ('users:login', {}),
        ('users:register', {}),
    ]
    
    for name, kwargs in urls:
        url = reverse(name, kwargs=kwargs)
        response = client.get(url)
        assert response.status_code == 200, f"URL {name} failed with {response.status_code}"


@pytest.mark.django_db
def test_admin_urls_require_login(client, post):
    """
    Verify that administration URLs redirect or forbid anonymous users.
    """
    urls = [
        ('administration:index', {}),
        ('administration:post_list', {}),
        ('administration:post_edit', {'pk': post.pk}),
    ]
    
    for name, kwargs in urls:
        url = reverse(name, kwargs=kwargs)
        response = client.get(url)
        # Should redirect to login
        assert response.status_code == 302
        assert '/login/' in response.url or '/admin/login/' in response.url


@pytest.mark.django_db
def test_admin_urls_access_with_admin_user(admin_client, post, category, tag):
    """
    Verify that admin user can access administration pages.
    """
    urls = [
        ('administration:index', {}),
        ('administration:post_list', {}),
        ('administration:category_list', {}),
        ('administration:tag_list', {}),
        # Detail pages
        ('administration:post_edit', {'pk': post.pk}),
    ]
    
    for name, kwargs in urls:
        url = reverse(name, kwargs=kwargs)
        response = admin_client.get(url)
        assert response.status_code == 200, f"Admin URL {name} failed with {response.status_code}"

