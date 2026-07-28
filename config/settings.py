
# import os
# from pathlib import Path
# from dotenv import load_dotenv
# from mongoengine import connect
# import certifi

# load_dotenv()

# BASE_DIR = Path(__file__).resolve().parent.parent

# from pathlib import Path

# # Build paths inside the project like this: BASE_DIR / 'subdir'.
# BASE_DIR = Path(__file__).resolve().parent.parent



# # SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = 'django-insecure-#ef&y8@(6z7msmvh5)7ky_lrq7s2lijdvlncvw45ven8h)ufak'

# # SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = True

# ALLOWED_HOSTS = []


# # Application definition

# INSTALLED_APPS = [
#     'django.contrib.admin',
#     'django.contrib.auth',
#     'django.contrib.contenttypes',
#     'django.contrib.sessions',
#     'django.contrib.messages',
#     'django.contrib.staticfiles',
#      "rest_framework",
#     "corsheaders",
#     "drf_spectacular",

#     "authentication",
#     "users",
#     "courts",
#     "bookings",
#     "products",
#     "carts",
#     "orders",
#     "reviews",
#     "notifications",
#     "payments",
    
# ]

# MIDDLEWARE = [
#     'django.middleware.security.SecurityMiddleware',
#     'django.contrib.sessions.middleware.SessionMiddleware',
#     'django.middleware.common.CommonMiddleware',
#     'django.middleware.csrf.CsrfViewMiddleware',
#     'django.contrib.auth.middleware.AuthenticationMiddleware',
#     'django.contrib.messages.middleware.MessageMiddleware',
#     'django.middleware.clickjacking.XFrameOptionsMiddleware',
#     "corsheaders.middleware.CorsMiddleware",

#     "django.middleware.security.SecurityMiddleware",
#     "django.contrib.sessions.middleware.SessionMiddleware",
#     "django.middleware.common.CommonMiddleware",
#     "django.middleware.csrf.CsrfViewMiddleware",
#     "django.contrib.auth.middleware.AuthenticationMiddleware",
#     "django.contrib.messages.middleware.MessageMiddleware",
#     "django.middleware.clickjacking.XFrameOptionsMiddleware",
# ]

# ROOT_URLCONF = 'config.urls'

# TEMPLATES = [
#     {
#         'BACKEND': 'django.template.backends.django.DjangoTemplates',
#         'DIRS': [],
#         'APP_DIRS': True,
#         'OPTIONS': {
#             'context_processors': [
#                 'django.template.context_processors.request',
#                 'django.contrib.auth.context_processors.auth',
#                 'django.contrib.messages.context_processors.messages',
#             ],
#         },
#     },
# ]

# WSGI_APPLICATION = 'config.wsgi.application'


# # Database
# # https://docs.djangoproject.com/en/6.0/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }


# # Password validation
# # https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

# AUTH_PASSWORD_VALIDATORS = [
#     {
#         'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
#     },
# ]


# # Internationalization
# # https://docs.djangoproject.com/en/6.0/topics/i18n/

# LANGUAGE_CODE = 'en-us'

# TIME_ZONE = 'UTC'

# USE_I18N = True

# USE_TZ = True

# CORS_ALLOW_ALL_ORIGINS = True


# # Static files (CSS, JavaScript, Images)
# # https://docs.djangoproject.com/en/6.0/howto/static-files/

# STATIC_URL = 'static/'



# REST_FRAMEWORK = {
#     "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
# }

# MONGO_URI = os.getenv("MONGO_URI")

# connect(
#     host=MONGO_URI,
#     tls=True,
#     tlsCAFile=certifi.where()
# )


import os
import sys
from pathlib import Path

import certifi
from dotenv import load_dotenv
from mongoengine import connect


# =========================================================
# BASE CONFIGURATION
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "django-insecure-development-key",
)

DEBUG = os.getenv(
    "DEBUG",
    "True",
).lower() == "true"

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv(
        "ALLOWED_HOSTS",
        "127.0.0.1,localhost",
    ).split(",")
    if host.strip()
]


# =========================================================
# APPLICATIONS
# =========================================================

INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "rest_framework",
    "corsheaders",
    "drf_spectacular",

    # Project apps
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


# =========================================================
# MIDDLEWARE
# =========================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",

    # CorsMiddleware phải đặt trước CommonMiddleware
    "corsheaders.middleware.CorsMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "config.urls"


# =========================================================
# TEMPLATES
# =========================================================

TEMPLATES = [
    {
        "BACKEND": (
            "django.template.backends.django."
            "DjangoTemplates"
        ),
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                (
                    "django.template.context_processors."
                    "request"
                ),
                (
                    "django.contrib.auth."
                    "context_processors.auth"
                ),
                (
                    "django.contrib.messages."
                    "context_processors.messages"
                ),
            ],
        },
    },
]


WSGI_APPLICATION = "config.wsgi.application"


# =========================================================
# DJANGO DATABASE
# =========================================================
# SQLite vẫn được Django sử dụng cho admin, session...
# Dữ liệu chính của project được lưu trong MongoDB.

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# =========================================================
# MONGODB / MONGOENGINE
# =========================================================

IS_TESTING = "test" in sys.argv

if IS_TESTING:
    MONGO_URI = os.getenv("MONGO_TEST_URI")
else:
    MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    variable_name = (
        "MONGO_TEST_URI"
        if IS_TESTING
        else "MONGO_URI"
    )

    raise ValueError(
        f"{variable_name} is missing in .env"
    )


connect(
    alias="default",
    host=MONGO_URI,
    tls=True,
    tlsCAFile=certifi.where(),
)


# =========================================================
# PASSWORD VALIDATION
# =========================================================

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


# =========================================================
# INTERNATIONALIZATION
# =========================================================

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Ho_Chi_Minh"

USE_I18N = True
USE_TZ = True


# =========================================================
# CORS
# =========================================================

CORS_ALLOW_ALL_ORIGINS = DEBUG

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "",
    ).split(",")
    if origin.strip()
]


# =========================================================
# STATIC FILES
# =========================================================

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# =========================================================
# DJANGO REST FRAMEWORK
# =========================================================

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": (
        "drf_spectacular.openapi.AutoSchema"
    ),
}


# =========================================================
# SWAGGER
# =========================================================

SPECTACULAR_SETTINGS = {
    "TITLE": "Sport Booking API",
    "DESCRIPTION": (
        "API hệ thống đặt sân và mua sản phẩm thể thao"
    ),
    "VERSION": "1.0.0",
}
