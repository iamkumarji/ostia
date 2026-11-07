import os

from .base import *  # noqa: F401,F403

DEBUG = False
SECRET_KEY = os.environ.get("SECRET_KEY", "")
ALLOWED_HOSTS = [h for h in os.environ.get("ALLOWED_HOSTS", "").split(",") if h]

# Forms return 403 behind a proxy without these. Origins include the scheme: https://example.com
CSRF_TRUSTED_ORIGINS = [o for o in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",") if o]
if os.environ.get("SECURE_SSL_REDIRECT", "").lower() == "true":
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
