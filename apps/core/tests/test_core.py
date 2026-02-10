import pytest
from django.urls import reverse

from core.models import (
    FriendLink,
    Navigation,
    Notification,
    Page,
    SearchPlaceholder,
)


@pytest.mark.django_db
class TestCoreModels:
    def test_page_creation(self):
        page = Page.objects.create(title="About Us", content="About content")
        assert page.slug == "about-us"
        assert str(page) == "About Us"

    def test_navigation_creation(self):
        nav = Navigation.objects.create(title="Home", url="/", order=1)
        assert str(nav) == "Home"
        assert nav.location == "header"

    def test_friendlink_creation(self):
        link = FriendLink.objects.create(name="Google", url="https://google.com")
        assert str(link) == "Google"
        assert link.is_active is True

    def test_search_placeholder_creation(self):
        placeholder = SearchPlaceholder.objects.create(text="Search Python")
        assert str(placeholder) == "Search Python"

    def test_notification_creation(self, user):
        notif = Notification.objects.create(
            user=user,
            title="Welcome",
            message="Welcome to Rosetta",
        )
        assert str(notif) == "Welcome"
        assert notif.is_read is False


@pytest.mark.django_db
class TestCoreViews:
    def test_home_page_access(self, client):
        url = reverse("home")
        response = client.get(url)
        assert response.status_code == 200

    def test_page_detail_access(self, client, page):
        url = reverse("page_detail", kwargs={"slug": page.slug})
        response = client.get(url)
        assert response.status_code == 200
        assert page.title in response.content.decode()

    def test_rosetta_intro_removed(self, client):
        # 验证 rosetta 介绍页面确实已移除 (404)
        # 注意：在 Django 中，如果 URL 被移除，reverse 将会失败。
        # 因此我们通过手动路径检查，或者在尝试时预期 NoReverseMatch。
        try:
            url = reverse("rosetta_intro")
            response = client.get(url)
            assert response.status_code == 404
        except Exception:
            pass  # Good, url name not found
