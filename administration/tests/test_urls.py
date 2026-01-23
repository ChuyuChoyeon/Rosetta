
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from model_bakery import baker
from blog.models import Post, Category, Tag, Comment
from core.models import Page, Navigation, FriendLink

User = get_user_model()

@pytest.fixture
def admin_data(client):
    user = User.objects.create_superuser(username="admin", password="password")
    client.force_login(user)
    
    post_obj = baker.make(Post, author=user)
    category = baker.make(Category)
    tag = baker.make(Tag)
    comment = baker.make(Comment, post=post_obj, user=user)
    page = baker.make(Page)
    navigation = baker.make(Navigation)
    friendlink = baker.make(FriendLink)
    
    return {
        "post": post_obj,
        "category": category,
        "tag": tag,
        "comment": comment,
        "page": page,
        "navigation": navigation,
        "friendlink": friendlink,
        "user": user,
    }

@pytest.mark.django_db
class TestAdministrationUrls:

    @pytest.mark.parametrize(
        "url_name, obj_key",
        [
            ("administration:index", None),
            # Post
            ("administration:post_list", None),
            ("administration:post_create", None),
            ("administration:post_edit", "post"),
            ("administration:post_delete", "post"),
            
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
    def test_url_access(self, client, admin_data, url_name, obj_key):
        kwargs = {}
        if obj_key:
            kwargs["pk"] = admin_data[obj_key].pk

        url = reverse(url_name, kwargs=kwargs)
        
        try:
            response = client.get(url)
        except Exception as e:
             print(f"FAILED URL: {url} | Error: {e}")
             raise e

        if response.status_code != 200:
            print(f"FAILED URL: {url} | Status: {response.status_code}")
            if hasattr(response, 'context') and response.context:
                print(f"Context keys: {list(response.context[0].keys())}")
            else:
                print("No context available")

        assert (
            response.status_code == 200
        ), f"Failed to access {url_name} with kwargs {kwargs}. Status: {response.status_code}"
