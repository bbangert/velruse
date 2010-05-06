"""Utilities for the auth functionality"""
import uuid

try:
    import simplejson as json
except ImportError:
    import json

import webob.exc as exc
from routes import URLGenerator
from openid.oidutil import autoSubmitHTML
from webob import Response

from velruse.baseconvert import base_encode
from velruse.errors import error_string


def redirect_form(end_point, token):
    return """
<form action="%s" method="post" accept-charset="UTF-8" enctype="application/x-www-form-urlencoded">
<input type="hidden" name="token" value="%s" />
<input type="submit" value="Continue"/></form>
""" % (end_point, token)

def generate_token():
    """Generate a random token"""
    return base_encode(uuid.uuid4().int)


class RouteResponder(object):
    def __call__(self, req):
        results = self.map.routematch(environ=req.environ)
        if not results:
            return exc.HTTPNotFound()
        match = results[0]
        kwargs = match.copy()
        link = URLGenerator(self.map, req.environ)
        req.environ['wsgiorg.routing_args'] = ((), match)
        req.link = link
        self.map.environ = req.environ
        action = kwargs.pop('action')
        return getattr(self, action)(req, **kwargs)
    
    def _error_redirect(self, error_code):
        """Redirect the user to the endpoint, save the error
        status to the storage under the token"""
        token = generate_token()
        self.storage.store(token, error_string(error_code))
        form_html = redirect_form(self.end_point, token)
        return Response(body=autoSubmitHTML(form_html))


class _Missing(object):
    def __repr__(self):
        return 'no value'

    def __reduce__(self):
        return '_missing'

_missing = _Missing()

class cached_property(object):
    """A decorator that converts a function into a lazy property.  The
    function wrapped is called the first time to retrieve the result
    and then that calculated result is used the next time you access
    the value::

        class Foo(object):

            @cached_property
            def foo(self):
                # calculate something important here
                return 42

    The class has to have a `__dict__` in order for this property to
    work.

    """
    # implementation detail: this property is implemented as non-data
    # descriptor.  non-data descriptors are only invoked if there is
    # no entry with the same name in the instance's __dict__.
    # this allows us to completely get rid of the access function call
    # overhead.  If one choses to invoke __get__ by hand the property
    # will still work as expected because the lookup logic is replicated
    # in __get__ for manual invocation.

    def __init__(self, func, name=None, doc=None):
        self.__name__ = name or func.__name__
        self.__module__ = func.__module__
        self.__doc__ = doc or func.__doc__
        self.func = func

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        value = obj.__dict__.get(self.__name__, _missing)
        if value is _missing:
            value = self.func(obj)
            obj.__dict__[self.__name__] = value
        return value
