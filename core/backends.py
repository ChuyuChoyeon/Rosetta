from django.core.mail.backends.smtp import EmailBackend
from constance import config

class ConstanceEmailBackend(EmailBackend):
    """
    基于 Constance 动态配置的邮件后端
    
    允许在运行时通过管理后台动态修改 SMTP 配置，无需重启服务。
    继承自 Django 原生 EmailBackend。
    """
    def __init__(self, host=None, port=None, username=None, password=None,
                 use_tls=None, fail_silently=False, use_ssl=None, timeout=None,
                 ssl_keyfile=None, ssl_certfile=None,
                 **kwargs):
        
        # 如果未显式提供参数，则从 Constance 动态配置中获取
        if host is None:
            host = getattr(config, 'SMTP_HOST', None)
        if port is None:
            port = getattr(config, 'SMTP_PORT', None)
        if username is None:
            username = getattr(config, 'SMTP_USER', None)
        if password is None:
            password = getattr(config, 'SMTP_PASSWORD', None)
        
        # TLS/SSL 自动判断逻辑
        # 如果用户启用了 SMTP_USE_TLS，我们需要根据端口判断是使用 use_tls 还是 use_ssl
        # 通常约定：端口 465 -> SSL, 端口 587 -> TLS
        config_use_tls = getattr(config, 'SMTP_USE_TLS', False)
        
        if use_tls is None and use_ssl is None:
            if int(port or 25) == 465:
                use_ssl = config_use_tls
                use_tls = False
            else:
                use_tls = config_use_tls
                use_ssl = False

        super().__init__(host=host, port=port, username=username, password=password,
                         use_tls=use_tls, fail_silently=fail_silently, use_ssl=use_ssl,
                         timeout=timeout, ssl_keyfile=ssl_keyfile, ssl_certfile=ssl_certfile,
                         **kwargs)
