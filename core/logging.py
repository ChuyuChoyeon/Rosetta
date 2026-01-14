import logging
from loguru import logger
from django.conf import settings


class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

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
    # Remove all existing loggers
    # logging.root.handlers = [] # Warning: this might affect other things. Better to configure via LOGGING settings.
    # Actually, the cleanest way is to route logging via settings.LOGGING
    pass


# We will configure LOGGING in settings.py to use this handler
