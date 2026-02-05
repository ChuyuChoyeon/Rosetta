
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from captcha.models import CaptchaStore
from .models import GuestbookEntry
from .forms import GuestbookForm

User = get_user_model()

class GuestbookViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("guestbook:index")
        self.user = User.objects.create_user(username="testuser", password="password", nickname="Test Nickname")

    def test_guestbook_view_get(self):
        # Create some entries
        for i in range(20):
            GuestbookEntry.objects.create(
                nickname=f"User {i}",
                content=f"Message {i}",
                is_public=True
            )
            
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "guestbook/index.html")
        self.assertIn("entries", response.context)
        self.assertTrue(response.context["is_paginated"])
        self.assertEqual(len(response.context["entries"]), 18)

    def test_guestbook_post_authenticated(self):
        self.client.login(username="testuser", password="password")
        
        # Create a captcha
        captcha_hash = CaptchaStore.generate_key()
        # Get the response (answer) for this key
        # In test mode it might be different, but let's try to get the real answer from DB
        captcha_instance = CaptchaStore.objects.get(hashkey=captcha_hash)
        captcha_response = captcha_instance.response
        
        data = {
            "nickname": "Test Nickname",
            "email": "test@example.com",
            "content": "Hello from authenticated user",
            "captcha_0": captcha_hash,
            "captcha_1": captcha_response
        }
        response = self.client.post(self.url, data)
        if response.status_code != 302:
             print(f"Form errors (auth): {response.context['form'].errors}")
        self.assertEqual(response.status_code, 302) # Redirect
        
        entry = GuestbookEntry.objects.first()
        self.assertEqual(entry.content, "Hello from authenticated user")
        self.assertEqual(entry.user, self.user)
        self.assertEqual(entry.nickname, "Test Nickname")

    def test_guestbook_post_anonymous(self):
        # Create a captcha
        captcha_hash = CaptchaStore.generate_key()
        captcha_instance = CaptchaStore.objects.get(hashkey=captcha_hash)
        captcha_response = captcha_instance.response
        
        data = {
            "nickname": "Anon",
            "email": "anon@example.com",
            "content": "Hello from anon",
            "captcha_0": captcha_hash,
            "captcha_1": captcha_response
        }
        response = self.client.post(self.url, data)
        if response.status_code != 302:
             print(f"Form errors (anon): {response.context['form'].errors}")
        self.assertEqual(response.status_code, 302)
        entry = GuestbookEntry.objects.first()
        self.assertEqual(entry.nickname, "Anon")
        self.assertIsNone(entry.user)

    def test_pagination(self):
        for i in range(25):
            GuestbookEntry.objects.create(content=f"Msg {i}", is_public=True)
            
        response = self.client.get(self.url + "?page=2")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["entries"]), 7) # 25 - 18 = 7
