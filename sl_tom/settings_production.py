from .settings import *

import os

SECRET_KEY = os.environ["SECRET_KEY"]
DEBUG = False

ALLOWED_HOSTS = [
    "tom.black-hole-hunters.org",
    "0.0.0.0",
]

CSRF_TRUSTED_ORIGINS = [
    "https://tom.black-hole-hunters.org",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": os.environ["POSTGRES_HOST"],
        "NAME": os.environ["POSTGRES_DB"],
        "USER": os.environ["POSTGRES_USER"],
        "PASSWORD": os.environ["POSTGRES_PASSWORD"],
    }
}

STATIC_ROOT = "/srv/sl_tom/static"
STATIC_URL = "/"

MEDIA_ROOT = "/srv/sl_tom/media"

# CELERY_BROKER_URL = (
#     f'amqp://{os.environ["CELERY_RABBITMQ_USER"]}:{os.environ["CELERY_RABBITMQ_PASS"]}'
#     f'@{os.environ["CELERY_RABBITMQ_HOST"]}/{os.environ["CELERY_RABBITMQ_VHOST"]}'
# )

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=os.environ["SENTRY_DSN"],
    integrations=[DjangoIntegration()],
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0,
    # If you wish to associate users to errors (assuming you are using
    # django.contrib.auth) you may enable sending PII data.
    send_default_pii=True,
)
