from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache

User = get_user_model()


class CoreApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            "admin", "admin@example.com", "password"
        )
        self.client.force_login(self.admin_user)

    def test_debug_api_stats(self):
        url = reverse("debug_api_stats")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("counts", response.json())

    def test_debug_api_system(self):
        url = reverse("debug_api_system")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("resources", response.json())

    def test_debug_api_migrations(self):
        url = reverse("debug_api_migrations")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("pending", response.json())


class DebugExecuteCommandTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            "admin", "admin@example.com", "password"
        )
        self.url = reverse("debug_execute_command")
        self.client.force_login(self.admin_user)

    def test_get_method_not_allowed(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_command_not_allowed(self):
        response = self.client.post(self.url, {"command": "rm"})
        self.assertEqual(response.status_code, 403)

    def test_command_success(self):
        response = self.client.post(self.url, {"command": "clearsessions"})
        if response.json()["status"] != "ok":
            print(f"Command failed: {response.json().get('error')}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_command_exception(self):
        response = self.client.post(
            self.url, {"command": "check", "args": "--invalid-arg"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "error")
