import pytest
from blog.models import Category, Tag, Post
from core.models import Page
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="password")

@pytest.mark.django_db
class TestSlugGeneration:
    def test_category_slug_uniqueness(self):
        c1 = Category.objects.create(name="Python")
        assert c1.slug == "python"
        
        c2 = Category.objects.create(name="Python")
        assert c2.slug == "python-1"
        
        c3 = Category.objects.create(name="Python")
        assert c3.slug == "python-2"

    def test_tag_slug_uniqueness(self):
        t1 = Tag.objects.create(name="Django")
        assert t1.slug == "django"
        
        t2 = Tag.objects.create(name="Django")
        assert t2.slug == "django-1"

    def test_post_slug_uniqueness(self, user):
        p1 = Post.objects.create(title="Hello World", content="Content", author=user)
        assert p1.slug == "hello-world"
        
        p2 = Post.objects.create(title="Hello World", content="Content", author=user)
        assert p2.slug == "hello-world-1"

    def test_page_slug_uniqueness(self):
        p1 = Page.objects.create(title="About", content="Content")
        assert p1.slug == "about"
        
        p2 = Page.objects.create(title="About", content="Content")
        assert p2.slug == "about-1"
