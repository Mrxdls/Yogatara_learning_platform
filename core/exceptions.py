from rest_framework.views import exception_handler
from rest_framework.response import Response
import logging
import time
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

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

def custom_exception_handler(exc, context):
    """DRF exception handler - catches all DRF errors"""
    
    logger.error(f"DRF Exception: {exc}", exc_info=True)
    
    # Get standard DRF response
    response = exception_handler(exc, context)
    
    # If DRF handled it, return the response
    if response is not None:
        return response
    
    # If not, it's a non-DRF exception - return generic error
    return Response(
        {'error': 'Internal server error', 'detail': str(exc)},
        status=500
    )