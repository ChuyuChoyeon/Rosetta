import logging
from loguru import logger
from django.conf import settings


class InterceptHandler(logging.Handler):
    """
    Loguru 日志拦截处理器 (Loguru Intercept Handler)
    
    将 Python 标准 logging 模块的日志记录重定向到 Loguru 日志系统。
    这解决了在使用 Loguru 时，Django 或其他第三方库仍使用标准 logging 导致的日志分散问题。
    
    工作原理:
    1. 捕获标准 logging 的 LogRecord。
    2. 获取对应的 Loguru 日志级别。
    3. 回溯调用栈 (Stack Unwinding) 以找到真实的日志调用位置，而非 InterceptHandler 自身。
    4. 将日志转发给 Loguru 处理。
    """
    def emit(self, record):
        # 获取对应的 Loguru 日志级别
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # 回溯调用栈，找到日志产生的原始位置
        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame and (
            frame.f_code.co_filename == logging.__file__
            or frame.f_code.co_filename == __file__
        ):
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_loguru_logging():
    """
    配置 Loguru 日志系统 (Setup Loguru Logging)
    
    此函数目前作为占位符保留。
    推荐在 Django 的 settings.LOGGING 配置中直接使用 InterceptHandler，
    以保持配置的集中和一致性。
    """
    # 实际配置应在 settings.py 中完成
    pass


# We will configure LOGGING in settings.py to use this handler
