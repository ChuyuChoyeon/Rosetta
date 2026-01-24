from unittest.mock import MagicMock

import pytest
from django.db import models

from core.utils import generate_unique_slug


class MockModel(models.Model):
    slug = models.SlugField()

    class Meta:
        app_label = "core"
        managed = False


@pytest.mark.django_db
def test_generate_unique_slug():
    # Mock the objects.filter method
    MockModel.objects = MagicMock()
    # First call returns False (no collision), second returns True (collision), third False
    MockModel.objects.filter.return_value.exists.side_effect = [
        False,
        True,
        False,
    ]

    # Case 1: No collision
    slug1 = generate_unique_slug(MockModel, "Test Title")
    assert slug1 == "test-title"

    # Case 2: Collision
    # Reset side effect for collision scenario
    MockModel.objects.filter.return_value.exists.side_effect = [True, False]
    slug2 = generate_unique_slug(MockModel, "Test Title")
    assert slug2 == "test-title-1"


@pytest.mark.django_db
def test_generate_unique_slug_fallback():
    MockModel.objects = MagicMock()
    MockModel.objects.filter.return_value.exists.return_value = False

    # Test with characters that slugify might strip (if allow_unicode=False)
    # Assuming default slugify behavior for empty result fallback
    # We pass a string that slugifies to empty string to trigger fallback
    # But django slugify handles unicode by default if configured? No, default is ascii.
    # So "你好" -> ""

    slug = generate_unique_slug(MockModel, "你好", allow_unicode=False)
    # Should use UUID fallback (length 8)
    assert len(slug) == 8
    # Should not be empty
    assert slug != ""
