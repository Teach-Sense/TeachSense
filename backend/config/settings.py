from pathlib import Path
import os

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(name, default=False):
	return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}


USE_POSTGRES = env_bool("USE_POSTGRES", False)
USE_UPSTASH_REDIS = env_bool("USE_UPSTASH_REDIS", False)

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "false").lower() == "true"

ALLOWED_HOSTS = [
	host.strip()
	for host in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
	if host.strip()
]

INSTALLED_APPS = [
	"django.contrib.admin",
	"django.contrib.auth",
	"django.contrib.contenttypes",
	"django.contrib.sessions",
	"django.contrib.messages",
	"django.contrib.staticfiles",
	"corsheaders",
	"rest_framework",
	"drf_spectacular",
	"channels",
	"apps.core",
	"apps.users",
	"apps.lecturers",
	"apps.students",
	"apps.lectures",
	"apps.devices",
	"apps.transcripts",
	"apps.summaries",
	"apps.questions",
	"apps.responses",
	"apps.evaluations",
	"apps.scores",
	"apps.analytics",
	"apps.dashboards",
	"apps.integrations",
	"apps.notifications",
    "storages",
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

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

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

DATABASES = {
	"default": {
		"ENGINE": os.getenv(
			"DB_ENGINE_PROD" if USE_POSTGRES else "DB_ENGINE_DEV",
			os.getenv("DB_ENGINE", "django.db.backends.sqlite3"),
		),
		"NAME": os.getenv(
			"DB_NAME_PROD" if USE_POSTGRES else "DB_NAME_DEV",
			os.getenv("DB_NAME", str(BASE_DIR / "db.sqlite3")),
		),
		"USER": os.getenv("DB_USER_PROD" if USE_POSTGRES else "DB_USER_DEV", os.getenv("DB_USER", "")),
		"PASSWORD": os.getenv(
			"DB_PASSWORD_PROD" if USE_POSTGRES else "DB_PASSWORD_DEV",
			os.getenv("DB_PASSWORD", ""),
		),
		"HOST": os.getenv("DB_HOST_PROD" if USE_POSTGRES else "DB_HOST_DEV", os.getenv("DB_HOST", "")),
		"PORT": os.getenv("DB_PORT_PROD" if USE_POSTGRES else "DB_PORT_DEV", os.getenv("DB_PORT", "")),
	}
}

AUTH_PASSWORD_VALIDATORS = [
	{"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
	{"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
	{"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
	{"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOWED_ORIGINS = [
	origin.strip()
	for origin in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
	if origin.strip()
]

CSRF_TRUSTED_ORIGINS = [
	origin.strip()
	for origin in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",")
	if origin.strip()
]

REST_FRAMEWORK = {
	"DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
	"DEFAULT_AUTHENTICATION_CLASSES": (
		"rest_framework_simplejwt.authentication.JWTAuthentication",
		"rest_framework.authentication.SessionAuthentication",
	),
	"DEFAULT_PERMISSION_CLASSES": (
		"rest_framework.permissions.IsAuthenticated",
	),
	"DEFAULT_PAGINATION_CLASS": "common.pagination.StandardResultsSetPagination",
	"PAGE_SIZE": 20,
	"DEFAULT_FILTER_BACKENDS": (
		"django_filters.rest_framework.DjangoFilterBackend",
		"rest_framework.filters.SearchFilter",
		"rest_framework.filters.OrderingFilter",
	),
	"EXCEPTION_HANDLER": "common.middleware.exception_handler.custom_exception_handler",
	"DEFAULT_RENDERER_CLASSES": (
		"rest_framework.renderers.JSONRenderer",
	),
}

SPECTACULAR_SETTINGS = {
	"TITLE": "TeachSense API",
	"DESCRIPTION": "TeachSense classroom intelligence backend API",
	"VERSION": "0.1.0",
}

# JWT Configuration
from datetime import timedelta

SIMPLE_JWT = {
	"ACCESS_TOKEN_LIFETIME": timedelta(hours=24),
	"REFRESH_TOKEN_LIFETIME": timedelta(days=7),
	"ROTATE_REFRESH_TOKENS": True,
	"BLACKLIST_AFTER_ROTATION": False,
	"UPDATE_LAST_LOGIN": True,
	"ALGORITHM": "HS256",
	"SIGNING_KEY": SECRET_KEY,
	"VERIFYING_KEY": None,
	"AUDIENCE": None,
	"ISSUER": None,
	"JTI_CLAIM": "jti",
	"TOKEN_TYPE_CLAIM": "token_type",
	"SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
	"SLIDING_TOKEN_LIFETIME": timedelta(minutes=5),
	"SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1),
	"AUTH_HEADER_TYPES": ("Bearer",),
	"AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
	"TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",
	"JTI_CLAIM": "jti",
	"SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
}

# CORS Configuration
CORS_ALLOWED_ORIGINS += [
	"http://localhost:3000",
	"http://localhost:8080",
	"http://localhost:5173",
	"http://127.0.0.1:3000",
	"http://127.0.0.1:8080",
	"http://127.0.0.1:5173",
]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
	"accept",
	"accept-encoding",
	"authorization",
	"content-type",
	"dnt",
	"origin",
	"user-agent",
	"x-csrftoken",
	"x-requested-with",
	"x-device-token",
	"x-api-key",
]

REDIS_URL = os.getenv(
	"REDIS_URL_PROD" if USE_UPSTASH_REDIS else "REDIS_URL_DEV",
	os.getenv("REDIS_URL", "redis://localhost:6379/0"),
)

CELERY_BROKER_URL = os.getenv(
	"CELERY_BROKER_URL_PROD" if USE_UPSTASH_REDIS else "CELERY_BROKER_URL_DEV",
	os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1"),
)
CELERY_RESULT_BACKEND = os.getenv(
	"CELERY_RESULT_BACKEND_PROD" if USE_UPSTASH_REDIS else "CELERY_RESULT_BACKEND_DEV",
	os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2"),
)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

# Authentication
AUTH_USER_MODEL = "users.User"
# Channels Configuration
CHANNEL_LAYERS = {
	"default": {
		"BACKEND": "channels_redis.core.RedisChannelLayer",
		"CONFIG": {
			"hosts": [REDIS_URL],
			"capacity": 1500,
			"expiry": 10,
		},
	},
}

# Backblaze B2 (S3-compatible) storage support
USE_B2 = os.getenv("USE_B2", "false").lower() == "true"
if USE_B2:
	# Use django-storages with boto3 (S3 compatible API)
	DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
	AWS_ACCESS_KEY_ID = os.getenv("B2_KEY_ID")
	AWS_SECRET_ACCESS_KEY = os.getenv("B2_APPLICATION_KEY")
	AWS_STORAGE_BUCKET_NAME = os.getenv("B2_BUCKET_NAME")
	AWS_S3_ENDPOINT_URL = os.getenv("B2_ENDPOINT_URL")
	AWS_S3_REGION_NAME = os.getenv("B2_REGION")
	AWS_S3_SIGNATURE_VERSION = "s3v4"
	AWS_S3_ADDRESSING_STYLE = os.getenv("AWS_S3_ADDRESSING_STYLE", "virtual")