"""Vercel Python entry point.

Exposes both ``app`` (ASGI, used by Alfred for native async streaming) and
``application`` (WSGI fallback). Vercel detects ASGI when the callable has
the ASGI signature, so ``app = ASGI`` is what production runs.

For local dev we use ``manage.py runserver`` which serves ASGI for async views
when ``ASGI_APPLICATION`` is set.
"""

import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_portfolio.settings")

from django.core.asgi import get_asgi_application  # noqa: E402
from django.core.wsgi import get_wsgi_application  # noqa: E402

app = get_asgi_application()
application = get_wsgi_application()
