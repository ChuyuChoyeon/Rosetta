import pytest
from core.models import FriendLink, Notification
from users.models import User

@pytest.mark.django_db
class TestCoreModels:
    def test_friend_link_creation(self):
        """Test FriendLink model creation"""
        link = FriendLink.objects.create(
            name="Test Site",
            url="https://example.com",
            description="A test site",
            is_active=True
        )
        assert link.name == "Test Site"
        assert str(link) == "Test Site"
        assert FriendLink.objects.count() == 1

    def test_notification_creation(self):
        """Test Notification model creation"""
        user = User.objects.create_user(username="testuser", password="password")
        notif = Notification.objects.create(
            user=user,
            title="Test Notification",
            message="This is a test message",
            level="info"
        )
        assert notif.user == user
        assert notif.title == "Test Notification"
        assert notif.is_read is False
        assert str(notif) == "Test Notification"
        assert Notification.objects.count() == 1
