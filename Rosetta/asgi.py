"""
ASGI config for Rosetta project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os
import dotenv

from django.core.asgi import get_asgi_application

dotenv.load_dotenv()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Rosetta.settings")

application = get_asgi_application()
