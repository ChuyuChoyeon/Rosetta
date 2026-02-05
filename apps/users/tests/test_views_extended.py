import pytest
from django.urls import reverse
from users.models import User, UserPreference
from unittest.mock import patch
import json

@pytest.mark.django_db
class TestUsersViewsExtended:
    @pytest.fixture(autouse=True)
    def setup(self, client):
        self.client = client
        self.user = User.objects.create_user(username="user", password="password")
        self.other = User.objects.create_user(username="other", password="password")
        self.profile_url = reverse("users:user_public_profile", kwargs={"username": self.user.username})

    @patch("users.views.config")
    def test_registration_disabled(self, mock_config):
        mock_config.ENABLE_REGISTRATION = False
        url = reverse("users:register")
        response = self.client.get(url)
        assert response.status_code == 302
        assert response.url == reverse("home")

    def test_update_theme_invalid(self):
        self.client.force_login(self.user)
        url = reverse("users:update_theme")
        
        # Invalid theme name (XSS attempt)
        response = self.client.post(
            url, 
            json.dumps({"theme": "<script>alert(1)</script>"}), 
            content_type="application/json"
        )
        assert response.status_code == 400
        assert response.json()["message"] == "Invalid theme name"

    @patch("users.views.UserPreference.objects.update_or_create")
    def test_update_theme_generic_error(self, mock_update):
        mock_update.side_effect = Exception("Generic Error")
        self.client.force_login(self.user)
        url = reverse("users:update_theme")
        
        response = self.client.post(
            url, 
            json.dumps({"theme": "dark"}), 
            content_type="application/json"
        )
        assert response.status_code == 400
        assert response.json()["message"] == "Generic Error"

    def test_private_profile_access(self):
        # Set 'other' user profile to private
        pref, _ = UserPreference.objects.get_or_create(user=self.other)
        pref.public_profile = False
        pref.save()
        
        # Access as 'user' (authenticated but not owner/staff)
        self.client.force_login(self.user)
        url = reverse("users:user_public_profile", kwargs={"username": self.other.username})
        
        response = self.client.get(url)
        assert response.status_code == 200
        assert response.context["is_private_profile"] is True
        # Should verify content is hidden? context['posts'] shouldn't exist
        assert "posts" not in response.context

    def test_profile_tabs(self):
        self.client.force_login(self.user)
        
        # Comments tab
        response = self.client.get(self.profile_url, {"tab": "comments"})
        assert response.status_code == 200
        assert response.context["active_tab"] == "comments"
        
        # Security tab (private)
        response = self.client.get(self.profile_url, {"tab": "security"})
        assert response.status_code == 200
        assert response.context["active_tab"] == "security"
        assert "password_form" in response.context

    def test_profile_password_change(self):
        self.client.force_login(self.user)
        
        # Success
        data = {
            "change_password": "1",
            "old_password": "password",
            "new_password1": "newpassword123",
            "new_password2": "newpassword123"
        }
        response = self.client.post(self.profile_url, data)
        assert response.status_code == 302
        assert "tab=security" in response.url
        
        # Verify login still works (session updated)
        response = self.client.get(self.profile_url)
        assert response.status_code == 200 # Still logged in
        
        # Verify new password
        self.user.refresh_from_db()
        assert self.user.check_password("newpassword123")

    def test_profile_password_change_fail(self):
        self.client.force_login(self.user)
        
        # Failure (mismatch)
        data = {
            "change_password": "1",
            "old_password": "password",
            "new_password1": "newpassword123",
            "new_password2": "mismatch"
        }
        response = self.client.post(self.profile_url, data)
        assert response.status_code == 200 # Re-render
        assert "password_form" in response.context
        assert response.context["password_form"].errors
