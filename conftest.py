import pytest
from constance import config

@pytest.fixture(autouse=True)
def override_constance_settings(settings):
    settings.CONSTANCE_BACKEND = "constance.backends.memory.MemoryBackend"
