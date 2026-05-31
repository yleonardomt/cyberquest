from django.core.cache import cache
from django.http import JsonResponse
from functools import wraps

def ratelimit(key='ip', rate=5, timeout=300):
    """
    Decorador para limitar intentos de peticiones
    key: 'ip' o 'user' para identificar al solicitante
    rate: número máximo de intentos permitidos
    timeout: tiempo de bloqueo en segundos (5 minutos por defecto)
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.method == 'POST':
                if key == 'ip':
                    identifier = request.META.get('REMOTE_ADDR')
                elif key == 'user':
                    identifier = request.user.id if request.user.is_authenticated else request.META.get('REMOTE_ADDR')
                else:
                    identifier = request.META.get('REMOTE_ADDR')
                
                cache_key = f'ratelimit_{identifier}_{view_func.__name__}'
                attempts = cache.get(cache_key, 0)
                
                if attempts >= rate:
                    return JsonResponse({
                        'error': f'Demasiados intentos. Espera {timeout // 60} minutos.'
                    }, status=429)
                
                cache.set(cache_key, attempts + 1, timeout)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
