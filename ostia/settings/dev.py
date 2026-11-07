from .base import *  # noqa: F401,F403

DEBUG = True
SECRET_KEY = "django-insecure-ostia-dev-key-change-me"
ALLOWED_HOSTS = ["*"]
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
