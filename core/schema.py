"""
OpenAPI Schema customization hooks for drf-spectacular
"""


def add_response_time_headers(endpoints):
    """
    Preprocessing hook to add response time headers to ALL endpoints automatically.
    This adds the headers to the OpenAPI schema without touching individual views.
    
    Args:
        endpoints: List of (path, path_regex, method, callback) tuples
        
    Returns:
        Modified endpoints with response time headers added to all responses
    """
    for path, path_regex, method, callback in endpoints:
        # Get the schema from the callback
        if hasattr(callback, 'cls'):
            # Add response time headers to the schema
            if not hasattr(callback.cls, '_spectacular_annotation'):
                callback.cls._spectacular_annotation = {}
            
            # Define response headers
            response_headers = {
                'X-Response-Time': {
                    'description': 'Response time in seconds',
                    'schema': {'type': 'string', 'example': '0.045s'}
                },
                'X-Response-Time-Ms': {
                    'description': 'Response time in milliseconds', 
                    'schema': {'type': 'string', 'example': '45ms'}
                }
            }
            
            # Store the headers annotation
            if 'headers' not in callback.cls._spectacular_annotation:
                callback.cls._spectacular_annotation['headers'] = response_headers
    
    return endpoints


def response_headers_postprocessing(result, generator, request, public):
    """
    Postprocessing hook to add response headers to all operations in the schema.
    This ensures all endpoints show response time headers in Swagger UI.
    
    Args:
        result: The generated OpenAPI schema
        generator: The schema generator instance
        request: The HTTP request
        public: Whether this is a public schema
        
    Returns:
        Modified OpenAPI schema with response time headers
    """
    # Define response headers
    response_headers = {
        'X-Response-Time': {
            'description': 'Response time in seconds',
            'schema': {'type': 'string', 'example': '0.045s'}
        },
        'X-Response-Time-Ms': {
            'description': 'Response time in milliseconds',
            'schema': {'type': 'string', 'example': '45ms'}
        }
    }
    
    # Add headers to all paths and operations
    if 'paths' in result:
        for path, path_item in result['paths'].items():
            for method, operation in path_item.items():
                if method in ['get', 'post', 'put', 'patch', 'delete', 'options', 'head']:
                    if 'responses' in operation:
                        for status_code, response in operation['responses'].items():
                            if 'headers' not in response:
                                response['headers'] = {}
                            response['headers'].update(response_headers)
    
    return result
