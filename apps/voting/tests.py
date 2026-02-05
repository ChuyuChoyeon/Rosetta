
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Poll, Choice, Vote

User = get_user_model()

class PollTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="voter", password="password")
        self.poll = Poll.objects.create(
            title="Favorite Color",
            description="What is your favorite color?",
            is_active=True,
            allow_multiple_choices=False
        )
        self.choice_red = Choice.objects.create(poll=self.poll, text="Red")
        self.choice_blue = Choice.objects.create(poll=self.poll, text="Blue")

    def test_poll_list_view(self):
        response = self.client.get(reverse("voting:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Favorite Color")

    def test_poll_detail_view(self):
        response = self.client.get(reverse("voting:detail", kwargs={"pk": self.poll.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Red")
        self.assertContains(response, "Blue")
        self.assertFalse(response.context["has_voted"])

    def test_poll_detail_view_voted(self):
        Vote.objects.create(poll=self.poll, user=self.user, choice=self.choice_red)
        self.client.force_login(self.user)
        response = self.client.get(reverse("voting:detail", kwargs={"pk": self.poll.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["has_voted"])

    def test_vote_single_choice(self):
        self.client.force_login(self.user)
        url = reverse("voting:vote", kwargs={"pk": self.poll.pk})
        
        # No choice selected
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("alert-warning", response.content.decode())

        # Vote for Red
        response = self.client.post(url, {"choice": self.choice_red.pk})
        self.assertEqual(response.status_code, 200)
        self.choice_red.refresh_from_db()
        self.assertEqual(self.choice_red.votes_count, 1)
        self.assertTrue(Vote.objects.filter(poll=self.poll, user=self.user, choice=self.choice_red).exists())

        # Try to vote again (should fail/return results)
        response = self.client.post(url, {"choice": self.choice_blue.pk})
        self.assertEqual(response.status_code, 200)
        # Votes count should not change for Blue
        self.choice_blue.refresh_from_db()
        self.assertEqual(self.choice_blue.votes_count, 0)

    def test_vote_multiple_choices(self):
        self.poll.allow_multiple_choices = True
        self.poll.save()
        self.client.force_login(self.user)
        url = reverse("voting:vote", kwargs={"pk": self.poll.pk})

        # Vote for Red
        response = self.client.post(url, {"choice": self.choice_red.pk})
        self.assertEqual(response.status_code, 200)
        self.choice_red.refresh_from_db()
        self.assertEqual(self.choice_red.votes_count, 1)

        # Vote for Blue (allowed)
        response = self.client.post(url, {"choice": self.choice_blue.pk})
        self.assertEqual(response.status_code, 200)
        self.choice_blue.refresh_from_db()
        self.assertEqual(self.choice_blue.votes_count, 1)

        # Vote for Red again (not allowed - already voted for this choice)
        response = self.client.post(url, {"choice": self.choice_red.pk})
        self.assertEqual(response.status_code, 200)
        self.choice_red.refresh_from_db()
        self.assertEqual(self.choice_red.votes_count, 1) # Still 1

    def test_vote_unauthenticated(self):
        url = reverse("voting:vote", kwargs={"pk": self.poll.pk})
        response = self.client.post(url, {"choice": self.choice_red.pk})
        self.assertEqual(response.status_code, 302) # Redirect to login
