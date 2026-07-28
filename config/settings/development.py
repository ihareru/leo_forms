from .base import *


DEBUG = True

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "192.168.101.223"
]


EMAIL_BACKEND = (
    "django.core.mail.backends.console.EmailBackend"
)