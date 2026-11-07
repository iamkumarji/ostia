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

# Serve collected static files straight from Gunicorn, so the site needs no
# separate web server in front of it. Compression without a manifest: a missing
# asset reference degrades to a 404 rather than breaking the whole page.
MIDDLEWARE = [
    *MIDDLEWARE,  # noqa: F405
]
MIDDLEWARE.insert(
    MIDDLEWARE.index("django.middleware.security.SecurityMiddleware") + 1,
    "whitenoise.middleware.WhiteNoiseMiddleware",
)

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}
WHITENOISE_MAX_AGE = 31536000
