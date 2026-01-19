import pytest
from django.urls import reverse
from django.test import RequestFactory
from core.models import FriendLink
from blog.models import Post, Category, Tag
from users.models import User
from .schemas import FriendLinkSchema, PostSchema
from administration.views import FriendLinkListView
from blog.views import HomeView

@pytest.mark.django_db
class TestUIContextConsistency:
    """
    Ensures that the data passed to UI templates matches the expected Pydantic schemas.
    This guarantees that the UI has the necessary data to render consistently.
    """

    def test_friendlink_list_context(self, rf):
        # Setup data
        FriendLink.objects.create(name="Test Link", url="https://example.com", is_active=True)
        
        # Setup request
        request = rf.get(reverse("administration:friendlink_list"))
        request.user = User.objects.create_superuser("admin", "admin@example.com", "password")
        
        # Get view response
        view = FriendLinkListView.as_view()
        response = view(request)
        
        # Extract context
        # Note: Response from as_view() is TemplateResponse, which has context_data
        assert response.status_code == 200
        context = response.context_data
        object_list = context['friendlinks']
        
        # Validate with Pydantic
        for link in object_list:
            # We validate that the model instance has the fields required by the schema
            validated = FriendLinkSchema.model_validate(link)
            assert validated.name == link.name
            assert validated.url == link.url

    def test_post_list_context(self, rf):
        # Setup data
        user = User.objects.create_user("user", "user@example.com", "password")
        category = Category.objects.create(name="Tech", slug="tech")
        post = Post.objects.create(
            title="Test Post", 
            slug="test-post", 
            content="Content", 
            status="published",
            author=user,
            category=category
        )
        
        # Setup request
        request = rf.get(reverse("home"))
        request.user = user
        
        # Get view response
        view = HomeView.as_view()
        response = view(request)
        
        assert response.status_code == 200
        context = response.context_data
        posts = context['posts']
        
        # Validate with Pydantic
        for post_obj in posts:
            validated = PostSchema.model_validate(post_obj)
            assert validated.title == "Test Post"
            assert validated.category.name == "Tech"
