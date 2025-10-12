# settings/settings/local.py

from .base import *  # noqa

DEBUG = True
ALLOWED_HOSTS = ["*"]

# --- гарантированный SECRET_KEY в DEV ---
try:
    from decouple import config
    SECRET_KEY = config(
        "SECRET_KEY",
        default=config(
            "DJANGO_SECRET_KEY",
            default=config("DJANGORLAR_SECRET_KEY", default="dev-secret-btick"),
        ),
    )
except Exception:
    SECRET_KEY = "dev-secret-btick"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "btick-dev",
    }
}

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
CSRF_TRUSTED_ORIGINS = ["https://*.cloudshell.dev", "https://*.apps.googleusercontent.com"]
