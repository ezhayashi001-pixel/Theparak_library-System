"""
WSGI config for theparak_library project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'theparak_library.settings')

application = get_wsgi_application()
