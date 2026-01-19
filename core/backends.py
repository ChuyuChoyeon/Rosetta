from django.core.mail.backends.smtp import EmailBackend
from constance import config

class ConstanceEmailBackend(EmailBackend):
    """
    Custom EmailBackend that reads configuration from Constance dynamic settings.
    """
    def __init__(self, host=None, port=None, username=None, password=None,
                 use_tls=None, fail_silently=False, use_ssl=None, timeout=None,
                 ssl_keyfile=None, ssl_certfile=None,
                 **kwargs):
        
        # Override with Constance values if not explicitly provided
        if host is None:
            host = getattr(config, 'SMTP_HOST', None)
        if port is None:
            port = getattr(config, 'SMTP_PORT', None)
        if username is None:
            username = getattr(config, 'SMTP_USER', None)
        if password is None:
            password = getattr(config, 'SMTP_PASSWORD', None)
        
        # Logic for TLS/SSL
        # If user configures SMTP_USE_TLS, we need to decide if it applies to use_tls or use_ssl
        # Usually Port 465 -> SSL, Port 587 -> TLS
        config_use_tls = getattr(config, 'SMTP_USE_TLS', False)
        
        if use_tls is None and use_ssl is None:
            if int(port) == 465:
                use_ssl = config_use_tls
                use_tls = False
            else:
                use_tls = config_use_tls
                use_ssl = False

        super().__init__(host=host, port=port, username=username, password=password,
                         use_tls=use_tls, fail_silently=fail_silently, use_ssl=use_ssl,
                         timeout=timeout, ssl_keyfile=ssl_keyfile, ssl_certfile=ssl_certfile,
                         **kwargs)
