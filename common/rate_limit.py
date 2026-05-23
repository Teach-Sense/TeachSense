"""Per-user rate limiting utilities for API endpoints."""
import time
from functools import wraps
from django.core.cache import cache
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework import status


def rate_limit(requests_per_minute=60, key_func=None):
    """
    Decorator for per-user rate limiting on DRF views.
    
    Args:
        requests_per_minute: Max requests per minute (default: 60) or callable that returns int
        key_func: Custom function to extract rate limit key. Default: user ID or IP.
    
    Usage:
        @rate_limit(requests_per_minute=10)
        def post(self, request):
            ...
        
        # With env var:
        @rate_limit(requests_per_minute=lambda: int(os.environ.get('RATE_LIMIT_AUTH_REQUESTS_PER_MINUTE', 30)))
        def post(self, request):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            request = args[1] if len(args) > 1 else kwargs.get('request')
            if not request:
                return func(*args, **kwargs)
            
            # Resolve requests_per_minute if callable
            limit = requests_per_minute() if callable(requests_per_minute) else requests_per_minute
            
            # Extract rate limit key
            if key_func:
                limit_key = key_func(request)
            elif request.user and request.user.is_authenticated:
                limit_key = f"rl:user:{request.user.id}"
            else:
                # Fall back to IP address for anonymous users
                ip = get_client_ip(request)
                limit_key = f"rl:ip:{ip}"
            
            # Get current count from cache
            cache_key = f"{limit_key}:count"
            window_key = f"{limit_key}:window"
            
            current_time = time.time()
            window_start = cache.get(window_key)
            count = cache.get(cache_key, 0)
            
            # Reset window if expired
            if window_start is None or (current_time - window_start) > 60:
                count = 0
                window_start = current_time
                cache.set(window_key, window_start, 60)
            
            # Check rate limit
            if count >= limit:
                return Response(
                    {
                        'error': 'Rate limit exceeded',
                        'message': f'Maximum {limit} requests per minute allowed',
                        'retry_after': int(60 - (current_time - window_start))
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                    headers={'Retry-After': str(int(60 - (current_time - window_start)))}
                )
            
            # Increment counter
            count += 1
            cache.set(cache_key, count, 60)
            
            # Call the original function
            response = func(*args, **kwargs)
            
            # Add rate limit headers to response
            if hasattr(response, '__setitem__'):
                response['X-RateLimit-Limit'] = str(limit)
                response['X-RateLimit-Remaining'] = str(limit - count)
                response['X-RateLimit-Reset'] = str(int(window_start + 60))
            elif isinstance(response, Response):
                response['X-RateLimit-Limit'] = str(limit)
                response['X-RateLimit-Remaining'] = str(limit - count)
                response['X-RateLimit-Reset'] = str(int(window_start + 60))
            
            return response
        
        return wrapper
    return decorator


def get_client_ip(request):
    """Extract client IP from request, handling proxies."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
    return ip
