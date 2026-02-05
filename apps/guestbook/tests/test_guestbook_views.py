import pytest
from django.urls import reverse
from users.models import User
from guestbook.models import GuestbookEntry
from unittest.mock import patch

@pytest.mark.django_db
class TestGuestbookView:
    @pytest.fixture(autouse=True)
    def setup(self, client):
        self.client = client
        self.url = reverse("guestbook:index")
        self.user = User.objects.create_user(username="user", password="password", nickname="TestUser", email="test@example.com")

    def test_list_entries(self):
        GuestbookEntry.objects.create(nickname="Public", content="Public Msg", is_public=True)
        GuestbookEntry.objects.create(nickname="Private", content="Private Msg", is_public=False)
        
        response = self.client.get(self.url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Public Msg" in content
        assert "Private Msg" not in content

    @patch("captcha.fields.CaptchaField.clean")
    def test_create_entry_authenticated(self, mock_clean):
        mock_clean.return_value = "PASSED"
        self.client.force_login(self.user)
        data = {
            "nickname": "ShouldBeIgnored",
            "email": "ignore@example.com",
            "content": "Auth Message",
            "captcha_0": "dummy",
            "captcha_1": "PASSED"
        }
        response = self.client.post(self.url, data)
        if response.status_code == 200:
            print(response.context['form'].errors)
        assert response.status_code == 302
        
        entry = GuestbookEntry.objects.first()
        assert entry.content == "Auth Message"
        assert entry.user == self.user
        # View logic:
        # form.instance.nickname = self.request.user.nickname or self.request.user.username
        assert entry.nickname == "TestUser" 
        assert entry.email == "test@example.com"

    @patch("captcha.fields.CaptchaField.clean")
    def test_create_entry_anonymous(self, mock_clean):
        mock_clean.return_value = "PASSED"
        data = {
            "nickname": "Guest",
            "email": "guest@example.com",
            "content": "Guest Message",
            "captcha_0": "dummy",
            "captcha_1": "PASSED"
        }
        response = self.client.post(self.url, data)
        if response.status_code == 200:
            print(response.context['form'].errors)
        assert response.status_code == 302
        
        entry = GuestbookEntry.objects.first()
        assert entry.content == "Guest Message"
        assert entry.user is None
        assert entry.nickname == "Guest"
