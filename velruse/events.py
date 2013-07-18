import functools

def with_events(event=None):
    """Decorator to create event book ends on a method."""
    def decorator(method):
        @functools.wraps(method)
        def new_method(obj, request):
            request.registry.notify(event(request, obj.type))
            response = method(obj, request)
            return response
        return new_method
    return decorator


class AuthenticationStarted(object):
    def __init__(self, request, provider):
        self.request = request
        self.provider = provider

