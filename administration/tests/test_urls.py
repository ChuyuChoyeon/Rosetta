import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from model_bakery import baker
from blog.models import Post, Category, Tag, Comment
from core.models import Page, Navigation, FriendLink

User = get_user_model()


@pytest.mark.django_db
class TestAdministrationUrls:

    @pytest.fixture(autouse=True)
    def setup_data(self, client):
        self.client = client
        self.user = User.objects.create_superuser(username="admin", password="password")
        self.client.force_login(self.user)

        self.category = baker.make(Category)
        self.tag = baker.make(Tag)
        self.post_obj = baker.make(Post, author=self.user)
        self.comment = baker.make(Comment, post=self.post_obj, user=self.user)
        self.page = baker.make(Page)
        self.navigation = baker.make(Navigation)
        self.friendlink = baker.make(FriendLink)

        # Helper to map object types to instances
        self.instances = {
            "post": self.post_obj,
            "category": self.category,
            "tag": self.tag,
            "comment": self.comment,
            "page": self.page,
            "navigation": self.navigation,
            "friendlink": self.friendlink,
            "user": self.user,
        }

    @pytest.mark.parametrize(
        "url_name, obj_key",
        [
            ("administration:index", None),
            # Post
            ("administration:post_list", None),
            ("administration:post_create", None),
            ("administration:post_edit", "post"),
            ("administration:post_delete", "post"),
            # Duplicate (POST only, but here we check URL resolution)
            # Since DuplicateView is POST-only logic (in the view implementation), a GET might return 405 or redirect.
            # But here we are just checking if the URL resolves and is accessible (even if it redirects or 405s).
            # Wait, the current test checks status_code == 200.
            # PostDuplicateView is a View with only 'post' method defined?
            # Let's check administration/views.py.
            # class PostDuplicateView(..., View): def post(self, request, pk): ...
            # It only has a post method. So GET will return 405 Method Not Allowed.
            # The current test assertion is `response.status_code == 200`.
            # So I should NOT add it to this parametrized test list which expects 200.
            # I should create a separate test for it or skip it here.
            
            # Category
            ("administration:category_list", None),
            ("administration:category_create", None),
            ("administration:category_edit", "category"),
            ("administration:category_delete", "category"),
            # Tag
            ("administration:tag_list", None),
            ("administration:tag_create", None),
            ("administration:tag_edit", "tag"),
            ("administration:tag_delete", "tag"),
            # Comment
            ("administration:comment_list", None),
            ("administration:comment_edit", "comment"),
            ("administration:comment_delete", "comment"),
            # Page
            ("administration:page_list", None),
            ("administration:page_create", None),
            ("administration:page_edit", "page"),
            ("administration:page_delete", "page"),
            # Navigation
            ("administration:navigation_list", None),
            ("administration:navigation_create", None),
            ("administration:navigation_edit", "navigation"),
            ("administration:navigation_delete", "navigation"),
            # FriendLink
            ("administration:friendlink_list", None),
            ("administration:friendlink_create", None),
            ("administration:friendlink_edit", "friendlink"),
            ("administration:friendlink_delete", "friendlink"),
            # User
            ("administration:user_list", None),
            ("administration:user_edit", "user"),
            # Settings
            ("administration:settings", None),
        ],
    )
    def test_url_access(self, url_name, obj_key):
        kwargs = {}
        if obj_key:
            kwargs["pk"] = self.instances[obj_key].pk

        url = reverse(url_name, kwargs=kwargs)
        response = self.client.get(url)

        assert (
            response.status_code == 200
        ), f"Failed to access {url_name} with kwargs {kwargs}. Status: {response.status_code}"
