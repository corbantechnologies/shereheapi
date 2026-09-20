from pathlib import Path
from datetime import timedelta

import dj_database_url
import cloudinary
from corsheaders.defaults import default_headers
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config("SECRET_KEY", default="django-insecure-sherehe-secret-key-prod-dev-992")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config("DEBUG", default=True, cast=bool)

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="*").split(",")



# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third party apps
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    "cloudinary",
    # Local apps
    "accounts",
    "company",
    "events",
    "tickettypes",
    "bookings",
    "tickets",
    "leads",
    "mpesa",
    "coupons",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

CORS_ORIGIN_WHITELIST = config("CORS_ORIGIN_WHITELIST", default="http://localhost:3000,http://127.0.0.1:3000").split(",")
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_PRIVATE_NETWORK = True
CORS_ALLOWED_ORIGINS = config("CORS_ALLOWED_ORIGINS", default="http://localhost:3000,http://127.0.0.1:3000").split(",")
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_HEADERS = default_headers + (
    "Access-Control-Allow-Origin",
    "Access-Control-Allow-Methods",
    "Access-Control-Allow-Credentials",
    "accept",
    "authorization",
    "content-type",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
)

CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", default="http://localhost:3000,http://127.0.0.1:3000").split(",")

AUTH_USER_MODEL = "accounts.User"

ROOT_URLCONF = "shereheapi.urls"

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

WSGI_APPLICATION = "shereheapi.wsgi.application"


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

db_config = dj_database_url.config(default=config("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"))
DATABASES = {"default": db_config}


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Africa/Nairobi"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "static"
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"


REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
        "rest_framework.renderers.MultiPartRenderer",
    ),
    "TEST_REQUEST_RENDERER_CLASSES": (
        "rest_framework.renderers.MultiPartRenderer",
        "rest_framework.renderers.JSONRenderer",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 500,
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
}

# cloudinary settings
cloudinary.config(
    cloud_name=config("CLOUDINARY_NAME", default="dnbvhyj3x"),
    api_key=config("CLOUDINARY_API_KEY", default="1234567890"),
    api_secret=config("CLOUDINARY_API_SECRET", default="abcdefghijklmnopqrstuvwxyz"),
)

# Safaricom Mpesa Daraja API
MPESA_CONSUMER_KEY = config("MPESA_CONSUMER_KEY", default="")
MPESA_CONSUMER_SECRET = config("MPESA_CONSUMER_SECRET", default="")
MPESA_SHORTCODE = config("MPESA_SHORTCODE", default="")
MPESA_PASSKEY = config("MPESA_PASSKEY", default="")
MPESA_CALLBACK_URL = config("MPESA_CALLBACK_URL", default="https://api.sherehe.co.ke/api/mpesa/callback/")
MPESA_API_URL = config("MPESA_API_URL", default="https://sandbox.safaricom.co.ke")

# Resend
RESEND_API_KEY = config("RESEND_API_KEY", default="")

# Bookings
PAYMENT_TIMEOUT_MINUTES = config("PAYMENT_TIMEOUT_MINUTES", default="15")

# Basic Settings
BASE_URL = config("BASE_URL", default="http://localhost:8000")
SITE_URL = config("SITE_URL", default="http://localhost:3000")
SUPPORT_EMAIL = config("SUPPORT_EMAIL", default="support@sherehe.co.ke")
SUPPORT_PHONE = config("SUPPORT_PHONE", default="+254700000000")

# LJK Marketing Agency Gateway Integration
MARKETING_AGENCY_API_URL = config("MARKETING_AGENCY_API_URL", default="http://localhost:8001")
MARKETING_AGENCY_API_KEY = config("MARKETING_AGENCY_API_KEY", default="")
