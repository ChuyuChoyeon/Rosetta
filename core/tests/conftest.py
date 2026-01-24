import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from blog.models import Post, Category, Tag, Comment
from core.models import Page, Navigation, FriendLink, SearchPlaceholder, Notification

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="password123",
        nickname="Test User"
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="password123",
        nickname="Admin User"
    )


@pytest.fixture
def category(db):
    return Category.objects.create(name="Test Category", slug="test-category")


@pytest.fixture
def tag(db):
    return Tag.objects.create(name="Test Tag", slug="test-tag")


@pytest.fixture
def post(db, user, category, tag):
    post = Post.objects.create(
        title="Test Post",
        slug="test-post",
        content="Test content",
        author=user,
        category=category,
        status="published"
    )
    post.tags.add(tag)
    return post


@pytest.fixture
def page(db):
    return Page.objects.create(
        title="Test Page",
        slug="test-page",
        content="Page content",
        status="published"
    )
