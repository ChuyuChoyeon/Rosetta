import importlib
import logging
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from core.models import Notification
from django.urls import reverse

User = get_user_model()


class NotificationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")

    def test_create_notification(self):
        notification = Notification.objects.create(
            user=self.user,
            title="Test Notification",
            message="This is a test notification",
            level="info",
        )
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(notification.user, self.user)
        self.assertFalse(notification.is_read)

    def test_notification_ordering(self):
        n1 = Notification.objects.create(user=self.user, title="First", message="First")
        n2 = Notification.objects.create(
            user=self.user, title="Second", message="Second"
        )

        # Default ordering is -created_at
        notifications = Notification.objects.all()
        self.assertEqual(notifications[0], n2)
        self.assertEqual(notifications[1], n1)


class HealthCheckTests(TestCase):
    def test_health_check_ok(self):
        response = self.client.get(reverse("health_check"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("status"), "ok")


class DebugExecuteCommandTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username="staff", password="password", is_staff=True
        )
        self.user = User.objects.create_user(username="user", password="password")

    def test_execute_command_requires_staff(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("debug_execute_command"))
        self.assertEqual(response.status_code, 302)

    def test_execute_command_method_not_allowed(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("debug_execute_command"))
        self.assertEqual(response.status_code, 405)

    def test_execute_command_success(self):
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse("debug_execute_command"),
            data={"command": "check"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("status"), "ok")
        self.assertIn("output", response.json())

    def test_execute_command_forbidden(self):
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse("debug_execute_command"),
            data={"command": "migrate"},  # migrate is not in allowed list
        )
        self.assertEqual(response.status_code, 403)


class SitemapTests(TestCase):
    def test_sitemap_xml(self):
        response = self.client.get("/sitemap.xml")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<urlset")
        self.assertContains(response, reverse("home"))
        self.assertContains(response, reverse("users:login"))
        self.assertContains(response, reverse("users:register"))


class RootUrlsTests(TestCase):
    def test_root_urls_debug_patterns(self):
        import Rosetta.urls as root_urls

        with override_settings(DEBUG=True):
            importlib.reload(root_urls)
            patterns = [
                str(p.pattern) for p in root_urls.urlpatterns if hasattr(p, "pattern")
            ]
            self.assertIn("test/404/", patterns)
            self.assertIn("test/403_csrf/", patterns)

        with override_settings(DEBUG=False):
            importlib.reload(root_urls)


class LoguruInterceptHandlerTests(TestCase):
    def test_intercept_handler_emit(self):
        from core.logging import InterceptHandler, setup_loguru_logging

        handler = InterceptHandler()

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="hello",
            args=(),
            exc_info=None,
        )
        handler.emit(record)

        record2 = logging.LogRecord(
            name="test",
            level=55,
            pathname=__file__,
            lineno=1,
            msg="custom",
            args=(),
            exc_info=None,
        )
        record2.levelname = "CUSTOM"
        handler.emit(record2)

        setup_loguru_logging()
