from .base import *


DEBUG = False


SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"


SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True


SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)


SECURE_SSL_REDIRECT = True


SECURE_HSTS_SECONDS = 3600
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False


CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=[
        "https://forms.leovit.ru",
        "https://forms.ihare.ru",
    ],
)