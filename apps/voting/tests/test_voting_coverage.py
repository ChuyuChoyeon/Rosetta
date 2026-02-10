import pytest
from django.utils import timezone
from django.contrib.auth.models import AnonymousUser
from datetime import timedelta

from voting.models import Poll, Vote, Choice
from voting.templatetags.voting_extras import has_voted, get_active_polls


@pytest.mark.django_db
class TestVotingExtras:
    @pytest.fixture
    def user(self, django_user_model):
        return django_user_model.objects.create_user(
            username="voter", password="password"
        )

    @pytest.fixture
    def poll(self):
        return Poll.objects.create(
            title="Test Poll", description="Description", is_active=True
        )

    def test_has_voted_anonymous(self, poll):
        anon = AnonymousUser()
        assert has_voted(anon, poll) is False

    def test_has_voted_authenticated_no_vote(self, user, poll):
        assert has_voted(user, poll) is False

    def test_has_voted_authenticated_voted(self, user, poll):
        choice = Choice.objects.create(poll=poll, text="Choice 1")
        Vote.objects.create(user=user, poll=poll, choice=choice)
        assert has_voted(user, poll) is True

    def test_get_active_polls(self):
        now = timezone.now()

        # 1. Active, no end date
        p1 = Poll.objects.create(title="P1", is_active=True)

        # 2. Active, future end date
        p2 = Poll.objects.create(
            title="P2", is_active=True, end_date=now + timedelta(days=1)
        )

        # 3. Active, past end date (should not be returned)
        p3 = Poll.objects.create(
            title="P3", is_active=True, end_date=now - timedelta(days=1)
        )

        # 4. Inactive
        p4 = Poll.objects.create(title="P4", is_active=False)

        active_polls = get_active_polls()

        assert p1 in active_polls
        assert p2 in active_polls
        assert p3 not in active_polls
        assert p4 not in active_polls

    def test_get_active_polls_limit(self):
        for i in range(5):
            Poll.objects.create(title=f"Poll {i}", is_active=True)

        active_polls = get_active_polls(limit=3)
        assert active_polls.count() == 3
