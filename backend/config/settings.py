from pathlib import Path
import os

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(name, default=False):
	return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}


USE_POSTGRES = env_bool("USE_POSTGRES", False)
USE_UPSTASH_REDIS = env_bool("USE_UPSTASH_REDIS", False)

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "false").lower() == "true"

ALLOWED_HOSTS = [
	host.strip()
	for host in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
	if host.strip()
]

from urllib.parse import urlparse

# Normalize RENDER_EXTERNAL_HOSTNAME: accept either a plain hostname or a full URL
raw_render_hostname = os.getenv("RENDER_EXTERNAL_HOSTNAME", "").strip()
render_external_hostname = ""
if raw_render_hostname:
	# If a scheme is present, urlparse will parse hostname; otherwise force-with-slashes
	parsed = urlparse(raw_render_hostname if "://" in raw_render_hostname else f"//{raw_render_hostname}")
	render_external_hostname = (parsed.hostname or raw_render_hostname).strip().strip("/")
	if render_external_hostname and render_external_hostname not in ALLOWED_HOSTS:
		ALLOWED_HOSTS.append(render_external_hostname)

# NOTE: do not add hardcoded fallback hosts here; rely on `RENDER_EXTERNAL_HOSTNAME`

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
		**(
			{
				"ENGINE": "django.db.backends.sqlite3",
				"NAME": os.getenv("DB_NAME", str(BASE_DIR / "db.sqlite3")),
			}
			if not DATABASE_URL and not USE_POSTGRES
			else {}
		),
	}
}

if DATABASE_URL:
	if DATABASE_URL.startswith(("postgres://", "postgresql://")):
		from urllib.parse import urlparse

		parsed_db = urlparse(DATABASE_URL)
		DATABASES["default"] = {
			"ENGINE": "django.db.backends.postgresql",
			"NAME": parsed_db.path.lstrip("/") or os.getenv("DB_NAME", ""),
			"USER": parsed_db.username or os.getenv("DB_USER", ""),
			"PASSWORD": parsed_db.password or os.getenv("DB_PASSWORD", ""),
			"HOST": parsed_db.hostname or os.getenv("DB_HOST", ""),
			"PORT": str(parsed_db.port or os.getenv("DB_PORT", "")),
		}
	elif DATABASE_URL.startswith("sqlite"):
		from urllib.parse import urlparse

		parsed_db = urlparse(DATABASE_URL)
		DATABASES["default"] = {
			"ENGINE": "django.db.backends.sqlite3",
			"NAME": parsed_db.path or os.getenv("DB_NAME", str(BASE_DIR / "db.sqlite3")),
		}

elif USE_POSTGRES:
	DATABASES["default"] = {
		"ENGINE": os.getenv("DB_ENGINE_PROD", os.getenv("DB_ENGINE", "django.db.backends.postgresql")),
		"NAME": os.getenv("DB_NAME_PROD", os.getenv("DB_NAME", "")),
		"USER": os.getenv("DB_USER_PROD", os.getenv("DB_USER", "")),
		"PASSWORD": os.getenv("DB_PASSWORD_PROD", os.getenv("DB_PASSWORD", "")),
		"HOST": os.getenv("DB_HOST_PROD", os.getenv("DB_HOST", "")),
		"PORT": os.getenv("DB_PORT_PROD", os.getenv("DB_PORT", "")),
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

# Ensure render host and https origin are allowed for CORS/CSRF and enable cookie settings
if render_external_hostname:
	# Add scheme'd origins for CORS/CSRF if needed
	https_origin = f"https://{render_external_hostname}"
	if https_origin not in CORS_ALLOWED_ORIGINS:
		CORS_ALLOWED_ORIGINS.append(https_origin)
	if https_origin not in CSRF_TRUSTED_ORIGINS:
		CSRF_TRUSTED_ORIGINS.append(https_origin)

# Ensure the public Render domain is permitted
	# (no hardcoded fallback here)

# Allow a FRONTEND_URL env var (accepts full URL or hostname+path). We add the origin (scheme+hostname)
raw_frontend_url = os.getenv("FRONTEND_URL", "").strip()
if raw_frontend_url:
	parsed_frontend = urlparse(raw_frontend_url if "://" in raw_frontend_url else f"//{raw_frontend_url}")
	frontend_scheme = parsed_frontend.scheme or "https"
	frontend_host = parsed_frontend.hostname
	if frontend_host:
		frontend_origin = f"{frontend_scheme}://{frontend_host}"
		if frontend_origin not in CORS_ALLOWED_ORIGINS:
			CORS_ALLOWED_ORIGINS.append(frontend_origin)
		if frontend_origin not in CSRF_TRUSTED_ORIGINS:
			CSRF_TRUSTED_ORIGINS.append(frontend_origin)

# Allow local dev frontend in CSRF trusted origins (required for cross-site cookie tests)
if "http://localhost:5173" not in CSRF_TRUSTED_ORIGINS:
	CSRF_TRUSTED_ORIGINS.append("http://localhost:5173")

# Ensure localhost dev origin is also present in CORS_ALLOWED_ORIGINS
if "http://localhost:5173" not in CORS_ALLOWED_ORIGINS:
	CORS_ALLOWED_ORIGINS.append("http://localhost:5173")

# Cookie settings: enable cross-site cookies when appropriate
# Use `None` Samesite to allow cross-site cookie sending; `Secure` is enabled in non-DEBUG.
SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "None")
CSRF_COOKIE_SAMESITE = os.getenv("CSRF_COOKIE_SAMESITE", "None")
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

# Use the Render external hostname as the session cookie domain when available
if render_external_hostname:
	SESSION_COOKIE_DOMAIN = render_external_hostname


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
