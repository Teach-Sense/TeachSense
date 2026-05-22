import os

from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
from django.db import connections
from common.rate_limit import rate_limit, get_client_ip


def check_db():
    try:
        connections['default'].cursor()
        return {'ok': True}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


def is_production_database():
    """Check if using a production database (MySQL/PostgreSQL) vs SQLite."""
    engine = os.getenv("DB_ENGINE", "django.db.backends.sqlite3")
    return "mysql" in engine or "postgres" in engine


def check_redis(required=False):
    """Check Redis connectivity. Mark as optional in development."""
    url = getattr(settings, 'REDIS_URL', os.environ.get('REDIS_URL'))
    if not url:
        return {'ok': False, 'error': 'REDIS_URL not set', 'required': required}
    try:
        import redis
        client = redis.from_url(url, socket_connect_timeout=2)
        client.ping()
        return {'ok': True, 'required': required}
    except Exception as e:
        return {'ok': False, 'error': str(e), 'required': required}


def check_celery(required=False):
    """Check Celery/broker connectivity. Mark as optional in development."""
    try:
        from config.celery import app as celery_app
        insp = celery_app.control.inspect(timeout=1)
        res = insp.ping() if insp else None
        if res:
            return {'ok': True, 'workers': res, 'required': required}
        return {'ok': False, 'error': 'no workers or broker unreachable', 'required': required}
    except Exception as e:
        return {'ok': False, 'error': str(e), 'required': required}


def check_storage():
    try:
        from django.core.files.storage import default_storage
        # Attempt a simple exists() call; some storages may not support listdir
        _ = default_storage.exists('health-check-placeholder.tmp')
        return {'ok': True, 'storage': default_storage.__class__.__name__}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


class HealthCheckView(APIView):
    """Simple health/status endpoint for verifying core services.

    Returns service readiness for database, redis, celery, and storage,
    plus the configured mode for Anthropic/Mistral keys, and rate limit status.
    
    Service requirement logic:
    - SQLite (development): Redis and Celery are optional
    - MySQL/PostgreSQL (production): Redis and Celery are required
    
    Rate limiting: 60 requests per minute per user/IP.
    """
    permission_classes = []
    authentication_classes = []

    @rate_limit(requests_per_minute=60)
    def get(self, request):
        env = os.environ.get('DJANGO_ENV', getattr(settings, 'DJANGO_ENV', 'development'))
        is_prod_db = is_production_database()
        
        # Redis/Celery required if: (1) using production DB or (2) not in dev environment
        require_services = is_prod_db or env not in ('development', 'dev', 'local')
        
        db_check = check_db()
        redis_check = check_redis(required=require_services)
        celery_check = check_celery(required=require_services)
        storage_check = check_storage()
        
        # Rate limit config from .env
        rate_limit_config = {
            'auth_requests_per_minute': int(os.environ.get('RATE_LIMIT_AUTH_REQUESTS_PER_MINUTE', 30)),
            'api_requests_per_minute': int(os.environ.get('RATE_LIMIT_API_REQUESTS_PER_MINUTE', 100)),
            'health_requests_per_minute': int(os.environ.get('RATE_LIMIT_HEALTH_REQUESTS_PER_MINUTE', 60)),
        }
        
        data = {
            'ok': True,
            'environment': env,
            'database_engine': settings.DATABASES['default']['ENGINE'],
            'database_name': settings.DATABASES['default']['NAME'],
            'redis_url_mode': 'production' if os.environ.get('USE_UPSTASH_REDIS', 'false').lower() == 'true' else 'development',
            'services': {
                'database': db_check,
                'redis': redis_check,
                'celery': celery_check,
                'storage': storage_check,
            },
            'modes': {
                'anthropic': getattr(settings, 'ANTHROPIC_MODE', os.environ.get('ANTHROPIC_MODE', 'disabled')),
                'mistral': getattr(settings, 'MISTRAL_MODE', os.environ.get('MISTRAL_MODE', 'disabled')),
            },
            'rate_limits': rate_limit_config,
            'client_info': {
                'ip': get_client_ip(request),
                'user': request.user.id if request.user.is_authenticated else None,
            }
        }

        # Check only required services and always database
        if not db_check.get('ok', False):
            data['ok'] = False
        
        for svc_name, svc in {'redis': redis_check, 'celery': celery_check}.items():
            is_required = svc.get('required', True)
            if is_required and not svc.get('ok', False):
                data['ok'] = False
                break

        return Response(data)



