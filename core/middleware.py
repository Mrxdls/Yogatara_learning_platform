import logging
import json
import time
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

class GlobalExceptionMiddleware(MiddlewareMixin):
    """Catch all exceptions globally - works with ANY view type"""
    
    def process_exception(self, request, exception):
        logger.error(f"Exception: {exception}", exc_info=True)
        
        # Map exception types to status codes
        error_map = {
            ValueError: (400, 'Bad request'),
            KeyError: (400, 'Missing required field'),
            PermissionError: (403, 'Permission denied'),
            FileNotFoundError: (404, 'Not found'),
        }
        
        status_code = 500
        message = 'Internal server error'
        
        for exc_type, (code, msg) in error_map.items():
            if isinstance(exception, exc_type):
                status_code = code
                message = msg
                break
        
        return JsonResponse({
            'error': message,
            'detail': str(exception) if status_code < 500 else None
        }, status=status_code)

class ResponseTimeMiddleware(MiddlewareMixin):
    """Add X-Response-Time header to all responses"""
    
    def process_request(self, request):
        request._start_time = time.time()
    
    def process_response(self, request, response):
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time
            response['X-Response-Time'] = f'{duration:.3f}s'  # e.g., "0.045s"
            response['X-Response-Time-Ms'] = f'{int(duration * 1000)}ms'  # e.g., "45ms"
        return response