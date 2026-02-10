import factory
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from blog.models import Post, Category, Tag, Comment
from core.models import Page, Navigation, FriendLink, SearchPlaceholder, Notification

User = get_user_model()


@pytest.fixture(autouse=True)
def override_constance_settings(settings):
    settings.CONSTANCE_BACKEND = "constance.backends.memory.MemoryBackend"


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    nickname = factory.LazyAttribute(lambda obj: obj.username.title())
    password = factory.PostGenerationMethodCall("set_password", "password123")


class AdminUserFactory(UserFactory):
    is_staff = True
    is_superuser = True


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Sequence(lambda n: f"Category {n}")
    slug = factory.LazyAttribute(lambda obj: obj.name.lower().replace(" ", "-"))


class TagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tag

    name = factory.Sequence(lambda n: f"Tag {n}")
    slug = factory.LazyAttribute(lambda obj: obj.name.lower().replace(" ", "-"))


class PostFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Post

    title = factory.Sequence(lambda n: f"Post {n}")
    slug = factory.LazyAttribute(lambda obj: obj.title.lower().replace(" ", "-"))
    content = factory.Faker("paragraph")
    author = factory.SubFactory(UserFactory)
    category = factory.SubFactory(CategoryFactory)
    status = "published"

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for tag in extracted:
                self.tags.add(tag)
        else:
            self.tags.add(TagFactory())


class PageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Page

    title = factory.Sequence(lambda n: f"Page {n}")
    slug = factory.LazyAttribute(lambda obj: obj.title.lower().replace(" ", "-"))
    content = factory.Faker("paragraph")
    status = "published"


class NavigationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Navigation

    title = factory.Sequence(lambda n: f"Nav {n}")
    url = factory.LazyAttribute(lambda obj: f"/{obj.title.lower().replace(' ', '-')}/")
    location = "header"


class FriendLinkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FriendLink

    name = factory.Sequence(lambda n: f"Friend {n}")
    url = factory.LazyAttribute(
        lambda obj: f"https://{obj.name.lower().replace(' ', '')}.com"
    )


class CommentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Comment

    content = factory.Faker("sentence")
    post = factory.SubFactory(PostFactory)
    user = factory.SubFactory(UserFactory)
    active = True


class NotificationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Notification

    user = factory.SubFactory(UserFactory)
    title = factory.Sequence(lambda n: f"Notification {n}")
    message = factory.Faker("sentence")


class SearchPlaceholderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SearchPlaceholder

    text = factory.Sequence(lambda n: f"Search {n}")


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def admin_user(db):
    return AdminUserFactory()


@pytest.fixture
def category(db):
    return CategoryFactory()


@pytest.fixture
def tag(db):
    return TagFactory()


@pytest.fixture
def post(db):
    return PostFactory()


@pytest.fixture
def page(db):
    return PageFactory()


@pytest.fixture
def comment(db):
    return CommentFactory()


@pytest.fixture
def navigation(db):
    return NavigationFactory()


@pytest.fixture
def friendlink(db):
    return FriendLinkFactory()


@pytest.fixture
def notification(db):
    return NotificationFactory()


@pytest.fixture
def user_factory():
    return UserFactory


@pytest.fixture
def admin_user_factory():
    return AdminUserFactory


@pytest.fixture
def category_factory():
    return CategoryFactory


@pytest.fixture
def tag_factory():
    return TagFactory


@pytest.fixture
def post_factory():
    return PostFactory


@pytest.fixture
def comment_factory():
    return CommentFactory


@pytest.fixture
def navigation_factory():
    return NavigationFactory


@pytest.fixture
def friendlink_factory():
    return FriendLinkFactory


@pytest.fixture
def page_factory():
    return PageFactory


@pytest.fixture
def search_placeholder_factory():
    return SearchPlaceholderFactory
