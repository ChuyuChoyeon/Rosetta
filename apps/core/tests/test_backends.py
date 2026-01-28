import pytest
from constance import config
from core.backends import ConstanceEmailBackend

@pytest.mark.django_db
class TestConstanceEmailBackend:
    def test_init_defaults(self):
        # Default config in memory backend might be None or default values
        # Let's set some values
        config.SMTP_HOST = "smtp.example.com"
        config.SMTP_PORT = 587
        config.SMTP_USER = "user"
        config.SMTP_PASSWORD = "password"
        config.SMTP_USE_TLS = True

        backend = ConstanceEmailBackend()
        
        assert backend.host == "smtp.example.com"
        assert backend.port == 587
        assert backend.username == "user"
        assert backend.password == "password"
        assert backend.use_tls is True
        assert backend.use_ssl is False

    def test_init_overrides(self):
        backend = ConstanceEmailBackend(
            host="custom.example.com",
            port=25,
            username="custom",
            password="custom_password",
            use_tls=False
        )
        
        assert backend.host == "custom.example.com"
        assert backend.port == 25
        assert backend.username == "custom"
        assert backend.password == "custom_password"
        assert backend.use_tls is False

    def test_ssl_auto_config(self):
        config.SMTP_USE_TLS = True
        
        # Port 465 should force SSL
        backend = ConstanceEmailBackend(port=465)
        assert backend.use_ssl is True
        assert backend.use_tls is False

        # Port 587 should use TLS if enabled
        backend = ConstanceEmailBackend(port=587)
        assert backend.use_tls is True
        assert backend.use_ssl is False
