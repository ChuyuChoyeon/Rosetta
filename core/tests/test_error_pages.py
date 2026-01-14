from django.test import TestCase, override_settings
from django.urls import reverse


class ErrorPageTests(TestCase):
    @override_settings(
        ROOT_URLCONF="core.tests.urls",
        MIDDLEWARE=[
            "django.middleware.security.SecurityMiddleware",
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.middleware.common.CommonMiddleware",
            "django.middleware.csrf.CsrfViewMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.contrib.messages.middleware.MessageMiddleware",
            "django.middleware.clickjacking.XFrameOptionsMiddleware",
            "django_htmx.middleware.HtmxMiddleware",
            "simple_history.middleware.HistoryRequestMiddleware",
            "watson.middleware.SearchContextMiddleware",
        ],
    )
    def test_404_page_render(self):
        response = self.client.get("/test/404/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "404.html")
        self.assertContains(response, "页面未找到")

    @override_settings(
        ROOT_URLCONF="core.tests.urls",
        MIDDLEWARE=[
            "django.middleware.security.SecurityMiddleware",
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.middleware.common.CommonMiddleware",
            "django.middleware.csrf.CsrfViewMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.contrib.messages.middleware.MessageMiddleware",
            "django.middleware.clickjacking.XFrameOptionsMiddleware",
            "django_htmx.middleware.HtmxMiddleware",
            "simple_history.middleware.HistoryRequestMiddleware",
            "watson.middleware.SearchContextMiddleware",
        ],
    )
    def test_403_page_render(self):
        response = self.client.get("/test/403/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "403.html")
        self.assertContains(response, "禁止访问")

    @override_settings(
        ROOT_URLCONF="core.tests.urls",
        MIDDLEWARE=[
            "django.middleware.security.SecurityMiddleware",
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.middleware.common.CommonMiddleware",
            "django.middleware.csrf.CsrfViewMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.contrib.messages.middleware.MessageMiddleware",
            "django.middleware.clickjacking.XFrameOptionsMiddleware",
            "django_htmx.middleware.HtmxMiddleware",
            "simple_history.middleware.HistoryRequestMiddleware",
            "watson.middleware.SearchContextMiddleware",
        ],
    )
    def test_500_page_render(self):
        response = self.client.get("/test/500/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "500.html")
        self.assertContains(response, "服务器出错了")

    @override_settings(
        ROOT_URLCONF="core.tests.urls",
        MIDDLEWARE=[
            "django.middleware.security.SecurityMiddleware",
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.middleware.common.CommonMiddleware",
            "django.middleware.csrf.CsrfViewMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.contrib.messages.middleware.MessageMiddleware",
            "django.middleware.clickjacking.XFrameOptionsMiddleware",
            "django_htmx.middleware.HtmxMiddleware",
            "simple_history.middleware.HistoryRequestMiddleware",
            "watson.middleware.SearchContextMiddleware",
        ],
    )
    def test_502_page_render(self):
        response = self.client.get("/test/502/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "502.html")
        self.assertContains(response, "网关错误")
