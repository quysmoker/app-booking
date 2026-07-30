

import os
import sys
from pathlib import Path

import certifi
from dotenv import load_dotenv
from mongoengine import connect


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "django-insecure-development-key-change-before-production",
)

DEBUG = os.getenv("DEBUG", "True").lower() == "true"

if (
    not DEBUG
    and SECRET_KEY
    == "django-insecure-development-key-change-before-production"
):
    raise ValueError(
        "SECRET_KEY must be configured when DEBUG is False"
    )

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv(
        "ALLOWED_HOSTS",
        "127.0.0.1,localhost",
    ).split(",")
    if host.strip()
]


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "drf_spectacular",
    "authentication",
    "users",
    "courts",
    "bookings",
    "products",
    "carts",
    "orders",
    "vouchers",
    "reviews",
    "notifications",
    "payments",
    "dashboard",
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


IS_TESTING = "test" in sys.argv
USE_MOCK_DB = (
    IS_TESTING
    and os.getenv("USE_MOCK_DB", "True").lower() == "true"
)

if USE_MOCK_DB:
    import mongomock

    connect(
        alias="default",
        db=os.getenv("MONGO_TEST_DB", "app_booking_test"),
        host="mongodb://localhost",
        mongo_client_class=mongomock.MongoClient,
    )
else:
    mongo_variable = "MONGO_TEST_URI" if IS_TESTING else "MONGO_URI"
    mongo_uri = os.getenv(mongo_variable)

    if not mongo_uri:
        raise ValueError(f"{mongo_variable} is missing in .env")

    connect_options = {
        "alias": "default",
        "host": mongo_uri,
    }

    if mongo_uri.startswith("mongodb+srv://"):
        connect_options.update(
            {
                "tls": True,
                "tlsCAFile": certifi.where(),
            }
        )

    connect(**connect_options)


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]


LANGUAGE_CODE = "vi"
TIME_ZONE = "Asia/Ho_Chi_Minh"
USE_I18N = True
USE_TZ = True


CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "",
    ).split(",")
    if origin.strip()
]


STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Sport Booking API",
    "DESCRIPTION": (
        "API hệ thống đặt sân và mua sản phẩm thể thao"
    ),
    "VERSION": "1.0.0",
}
