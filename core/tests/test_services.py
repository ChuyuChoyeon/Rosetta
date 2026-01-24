import pytest
from django.contrib.auth import get_user_model
from blog.models import Category, Tag, Post, Comment
from core.models import FriendLink, Navigation, SearchPlaceholder
from core.services import MockDataGenerator, generate_mock_data
from users.models import Notification

User = get_user_model()

@pytest.mark.django_db
class TestMockDataGenerator:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.generator = MockDataGenerator()

    def test_rand_text(self):
        text = self.generator._rand_text(length=10)
        assert len(text) == 10
        assert isinstance(text, str)

    def test_generate_markdown_content(self):
        content = self.generator._generate_markdown_content()
        assert isinstance(content, str)
        assert len(content) > 0
        assert "## " in content  # Should contain headers

    def test_create_users(self):
        users = self.generator.create_users(count=3)
        assert len(users) == 3
        assert User.objects.count() >= 3
        for user in users:
            assert user.check_password("password123")
            assert user.email
            assert user.date_joined

    def test_create_categories(self):
        categories = self.generator.create_categories(count=3)
        assert len(categories) == 3
        assert Category.objects.count() >= 3
        for cat in categories:
            assert cat.name
            assert cat.slug

    def test_create_tags(self):
        tags = self.generator.create_tags(count=3)
        assert len(tags) == 3
        assert Tag.objects.count() >= 3

    def test_create_posts(self):
        # Need prerequisites
        users = self.generator.create_users(count=1)
        categories = self.generator.create_categories(count=1)
        tags = self.generator.create_tags(count=1)
        
        posts = self.generator.create_posts(count=3, users=users, categories=categories, tags=tags)
        assert len(posts) == 3
        assert Post.objects.count() >= 3
        for post in posts:
            assert post.author in users
            assert post.category in categories
            assert post.tags.count() > 0

    def test_create_comments(self):
        # Need prerequisites
        users = self.generator.create_users(count=2)
        posts = self.generator.create_posts(count=1, users=users)
        
        comments = self.generator.create_comments(count=5, users=users, posts=posts)
        assert len(comments) == 5
        assert Comment.objects.count() >= 5
        
        # Check notifications
        assert Notification.objects.count() > 0

    def test_create_friend_links(self):
        links = self.generator.create_friend_links(count=3)
        assert len(links) == 3
        assert FriendLink.objects.count() >= 3

    def test_create_navigations(self):
        navs = self.generator.create_navigations()
        assert len(navs) > 0
        assert Navigation.objects.count() >= len(navs)

    def test_create_search_placeholders(self):
        placeholders = self.generator.create_search_placeholders()
        assert len(placeholders) > 0
        assert SearchPlaceholder.objects.count() >= len(placeholders)

@pytest.mark.django_db
def test_generate_mock_data_service():
    """Test the main entry point function"""
    result = generate_mock_data(
        users_count=2,
        categories_count=2,
        tags_count=2,
        posts_count=2,
        comments_count=2,
        generate_extras=True
    )
    
    assert result["users"] == 2
    assert result["categories"] == 2
    assert result["tags"] == 2
    assert result["posts"] == 2
    assert result["comments"] == 2
    assert result["friend_links"] > 0
    assert result["navigations"] > 0
    assert result["placeholders"] > 0
    
    assert User.objects.count() >= 2
    assert Post.objects.count() >= 2
